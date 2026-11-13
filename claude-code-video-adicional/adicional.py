"""Claude Code Video ADICIONAL — o Claude Code (Opus das contas pagas) como motor EXTRA dos nossos projetos.

Regra de ouro: o projeto NUNCA depende dele. Sem cota, desligado ou falhou no meio -> devolve None/"não usado" e o
projeto segue exatamente como faria sem ele. Nunca levanta exceção para quem chamou.

Uso num projeto (uma Sessao por vídeo — a decisão de ligar é tomada UMA vez, antes de começar o vídeo):

    sys.path.append(r"D:\\claude-code-video-adicional")
    import adicional
    s = adicional.Sessao("hipercool", "video_123")      # decide agora se liga (cota + chave liga/desliga)
    ...
    r = s.revisar_video(mp4, "Short de manhwa, legenda amarela embaixo")   # None = segue sem ele
    r = s.olhar(["capa.jpg"], "A capa tem texto cortado? JSON {...}")      # None = segue sem ele

Se uma chamada cai por falta de cota no meio do vídeo, a Sessao se desliga sozinha: as próximas chamadas daquele
vídeo nem tentam (fallback = o caminho normal do projeto). Tudo vai para estado/decisoes.jsonl.

    python adicional.py status
    python adicional.py ligar|desligar [projeto]
    python adicional.py revisar <video.mp4> [--projeto nome] [--contexto "..."]
"""
import io
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
CONFIG = RAIZ / "config.json"
DECISOES = RAIZ / "estado" / "decisoes.jsonl"
sys.path.append(r"D:\claude-code-video")         # gerente de cota e motor são do projeto principal (1 versão só)
import cota_claude  # noqa: E402
import motor  # noqa: E402

FF = r"D:\hipercool-materiais\bin\ffmpeg.exe"
FFPROBE = r"D:\hipercool-materiais\bin\ffprobe.exe"


def _cfg():
    return json.loads(CONFIG.read_text("utf-8"))


def _anotar(**d):
    DECISOES.parent.mkdir(exist_ok=True)
    d["em"] = datetime.now().isoformat(timespec="seconds")
    with DECISOES.open("a", encoding="utf-8") as f:
        f.write(json.dumps(d, ensure_ascii=False) + "\n")


class Sessao:
    def __init__(self, projeto, video_id="", custo=None):
        self.projeto, self.video_id = projeto, video_id
        self.ligado, self.motivo, self.chamadas = False, "", 0
        try:
            c = _cfg()
            if not c.get("ligado"):
                self.motivo = "desligado na config"
            elif c.get("projetos", {}).get(projeto) is False:
                self.motivo = f"desligado para {projeto}"
            else:
                custo = custo or c["custo_por_video"]
                d = cota_claude.decidir(custo, certeza=False)
                self.ligado, self.motivo = d["ligar"], d["motivo"]
        except Exception as e:  # noqa: BLE001
            self.motivo = f"erro ao decidir ({type(e).__name__}: {str(e)[:120]})"
        _anotar(projeto=projeto, video=video_id, evento="inicio", ligado=self.ligado, motivo=self.motivo)

    def _desligar(self, motivo):
        self.ligado, self.motivo = False, motivo
        _anotar(projeto=self.projeto, video=self.video_id, evento="desligou_no_meio", motivo=motivo)

    def olhar(self, imagens, pergunta, max_turnos=None):
        """O Claude OLHA as imagens e responde a pergunta (que deve pedir JSON). dict, ou None = seguir sem ele."""
        if not self.ligado:
            return None
        pasta = Path(tempfile.mkdtemp(prefix="cc_adic_"))
        try:
            nomes = []
            for i, im in enumerate(imagens):
                destino = pasta / f"img_{i + 1}{Path(im).suffix.lower() or '.jpg'}"
                shutil.copy2(im, destino)
                nomes.append(destino.name)
            prompt = (f"Use a ferramenta Read para OLHAR: {', '.join(nomes)} (pasta atual).\n\n{pergunta}\n\n"
                      "Responda SÓ o JSON pedido.")
            r = motor.chamar_json(prompt, pasta, f"adicional:{self.projeto}", "olhar",
                                  max_turnos=max_turnos or len(nomes) + 3, timeout=300)
            self.chamadas += 1
            _anotar(projeto=self.projeto, video=self.video_id, evento="olhou", ok=True)
            return r
        except motor.SemCota as e:
            self._desligar(f"cota acabou no meio: {str(e)[:120]}")
        except Exception as e:  # noqa: BLE001
            # erro que não é cota: não desliga a sessão, só esta chamada vira "sem ele"
            _anotar(projeto=self.projeto, video=self.video_id, evento="falhou", motivo=f"{type(e).__name__}: {str(e)[:160]}")
        finally:
            shutil.rmtree(pasta, ignore_errors=True)
        return None

    def revisar_video(self, mp4, contexto=""):
        """Revisão visual do vídeo pronto (8 quadros). {aprovado, nota, problemas[], comentario} ou None."""
        if not self.ligado:
            return None
        try:
            folha = folha_quadros(mp4)
        except Exception as e:  # noqa: BLE001
            _anotar(projeto=self.projeto, video=self.video_id, evento="falhou", motivo=f"quadros: {e}")
            return None
        try:
            return self.olhar([folha], f"""A imagem é uma folha com 8 quadros de um vídeo pronto, em ordem
(esquerda->direita, cima->baixo), numerados. Contexto do vídeo: {contexto or 'vídeo do nosso canal'}.
Procure defeitos que um editor profissional não deixaria passar: texto/legenda cortado na borda ou ilegível,
legenda em cima de rosto, tela preta, imagem deformada, quadro repetido/congelado, marca d'água de terceiros,
nudez/conteúdo impróprio. Não reclame de estilo.
JSON: {{"aprovado": true/false, "nota": 1-10, "problemas": [{{"quadro": 1, "o_que": "", "grave": true/false}}],
"comentario": "uma frase"}}""")
        finally:
            Path(folha).unlink(missing_ok=True)


def folha_quadros(mp4, n=8):
    """jpg com n quadros espalhados pelo vídeo (4 colunas), cada um com o número."""
    from PIL import Image, ImageDraw
    dur = float(subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                str(mp4)], capture_output=True, text=True, timeout=60).stdout.strip() or 0)
    if dur <= 0:
        raise RuntimeError("duração zero")
    quadros = []
    for i in range(n):
        png = subprocess.run([FF, "-v", "error", "-ss", f"{dur * (i + 0.5) / n:.2f}", "-i", str(mp4), "-frames:v", "1",
                              "-vf", "scale=360:-2", "-f", "image2", "-vcodec", "png", "-"], capture_output=True,
                             timeout=120).stdout
        im = Image.open(io.BytesIO(png)).convert("RGB")
        ImageDraw.Draw(im).text((8, 6), str(i + 1), fill=(255, 255, 0), stroke_width=3, stroke_fill=(0, 0, 0))
        quadros.append(im)
    w, h = quadros[0].size
    cols = 4
    folha = Image.new("RGB", (w * cols, h * ((n + cols - 1) // cols)))
    for i, im in enumerate(quadros):
        folha.paste(im.resize((w, h)), ((i % cols) * w, (i // cols) * h))
    saida = Path(tempfile.gettempdir()) / f"cc_folha_{datetime.now():%H%M%S%f}.jpg"
    folha.save(saida, quality=88)
    return saida


def _status():
    c = _cfg()
    print(f"Adicional: {'LIGADO' if c.get('ligado') else 'DESLIGADO'}  projetos: {c.get('projetos')}")
    d = cota_claude.decidir(c["custo_por_video"], certeza=False, forcar=True)
    print(("liga" if d["ligar"] else "NÃO liga") + " agora: " + d["motivo"])
    if DECISOES.exists():
        linhas = DECISOES.read_text("utf-8").splitlines()[-8:]
        print("últimas decisões:")
        for ln in linhas:
            x = json.loads(ln)
            print(f"  {x['em'][5:16]} {x['projeto']:12} {x['evento']:16} {x.get('motivo', '')[:70]}")


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    a = sys.argv[1:] or ["status"]
    if a[0] == "status":
        _status()
    elif a[0] in ("ligar", "desligar"):
        c = _cfg()
        if len(a) > 1:
            c.setdefault("projetos", {})[a[1]] = a[0] == "ligar"
        else:
            c["ligado"] = a[0] == "ligar"
        CONFIG.write_text(json.dumps(c, ensure_ascii=False, indent=2), "utf-8")
        _status()
    elif a[0] == "revisar" and len(a) > 1:
        proj = a[a.index("--projeto") + 1] if "--projeto" in a else "manual"
        ctx = a[a.index("--contexto") + 1] if "--contexto" in a else ""
        s = Sessao(proj, Path(a[1]).stem)
        print("ligado:", s.ligado, "—", s.motivo)
        r = s.revisar_video(a[1], ctx)
        print(json.dumps(r, ensure_ascii=False, indent=1) if r else f"sem o Claude (segue normal): {s.motivo}")
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
