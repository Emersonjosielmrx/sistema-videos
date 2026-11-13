"""Verificadores Gemini do vídeo de produto (26/10, dono: "a cada vídeo analisa o que pode melhorar e vai fazendo";
sistema copiado do lapidar do D:\\claude-code-video). 4 verificadores em paralelo olham 3 quadros por cena e dão
nota + problemas. Aqui não há corretor de código por vídeo (a montagem é Python/ffmpeg, não Remotion):
  - nota < reprovar_abaixo ou "grave" de roteiro_marca (informação inventada, erro de português) -> não vai pra fila
  - o resto entra na fila; os problemas ficam em logs\\produto_lapidar.jsonl e `resumo()` junta os que se repetem
    (a sessão que cuida do produto lê e conserta no código a cada rodada; ver docs\\PRODUTO_PROFISSIONAL.md).
"""
import json
import re
import shutil
import subprocess
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

from PIL import Image

from produto import motor

_PERIGO = re.compile(r"inventad|não está nos fatos|nao esta nos fatos|preço|preco|promessa|garant|ortogr|português|"
                     r"portugues|acento|grafia|escrit[ao] errad|letras deformadas|texto ileg[ií]vel de IA", re.I)

RAIZ = Path(__file__).resolve().parents[2]
HIST = RAIZ / "logs" / "produto_lapidar.jsonl"
FF = r"D:\hipercool-materiais\bin\ffmpeg.exe"

DESENHO = """O QUE É DO DESENHO (não é defeito): frase fixa num retângulo da cor da marca no topo; tópico numerado (círculo
da cor da marca + rótulo) que entra em cada bloco; barra de progresso fina no alto; legenda karaokê embaixo com a
palavra falada destacada; conversa de WhatsApp com selo "Simulação" (é simulação de propósito); cartão inicial com a
pergunta do cliente; cartão final com a marca, o convite e o @ da conta (o @ é OBRIGATÓRIO); o homem que fala para a
câmera é o dono da empresa (apresentador de propósito)."""

VERIFICADORES = {
    "legibilidade": """LEGIBILIDADE E ENQUADRAMENTO. Procure: texto cortado ou saindo da tela; texto importante abaixo de
y=1580 (de 1920 — lá ficam os botões do Reels) ou a menos de 60 px da lateral; letra pequena demais para ler no
celular; pouco contraste; elemento cobrindo rosto ou outro texto; legenda quebrando palavra; dois textos brigando.""",
    "movimento": """MOTION DESIGN. Procure: cena parada (quadros da mesma cena praticamente iguais); entrada de
elemento sem animação; ritmo arrastado; transição seca; todas as cenas com o mesmo molde (falta variedade);
imagem com cara de banco de imagem genérico.""",
    "roteiro_marca": """ROTEIRO, SINCRONIA E MARCA. Procure: o que está na tela não combina com a fala daquele momento;
informação inventada (número, preço, prazo, cliente que não está nos fatos); erro de português ou acento; cores fora
da paleta da marca; cartão final sem nome, sem convite ou sem o @; texto genérico/placeholder; imagem com letras
deformadas ou sem sentido (defeito de IA).""",
    "diretor": """DIRETOR DE CRIAÇÃO DE AGÊNCIA. Julgue o todo: o gancho prende nos 2 primeiros segundos? Passa
confiança de empresa séria ou parece slide/meme? Diga as 3 mudanças de MAIOR impacto para o próximo vídeo deste
molde subir de nível (concreto: o quê, em qual cena, como).""",
}


def _quadros(mp4, cenas, pasta):
    pasta.mkdir(parents=True, exist_ok=True)
    itens, ims = [], []
    for c in cenas:
        for frac in (0.2, 0.5, 0.8):
            seg = round(c["ini"] + (c["fim"] - c["ini"]) * frac, 2)
            nome = f"q{len(itens) + 1:02d}.jpg"
            subprocess.run([FF, "-y", "-v", "error", "-ss", f"{seg}", "-i", str(mp4), "-frames:v", "1",
                            "-vf", "scale=540:-2", "-q:v", "3", str(pasta / nome)], check=True, timeout=120)
            itens.append(f"{nome}: cena {c['n']} ({c['tipo']}), {seg}s, fala: \"{c['fala']}\"")
            ims.append(Image.open(pasta / nome).convert("RGB").resize((270, 480)))
    folha = Image.new("RGB", (270 * 3, 480 * len(cenas)))
    for i, im in enumerate(ims):
        folha.paste(im, ((i % 3) * 270, (i // 3) * 480))
    folha.save(pasta / "folha.jpg", quality=88)
    return itens


PARADA_PCT = 4.0  # PROMPT_LINHAS seção 3.6: menos de 4% de mudança entre 20% e 80% da cena = cena parada


def movimento(mp4, cenas):
    """% de mudança de cada cena entre os quadros de 20% e 80% (sem a faixa da legenda e o topo, que sempre mudam).
    Devolve [(n, tipo, pct)]."""
    out = []
    for c in cenas:
        ims = []
        for frac in (0.2, 0.8):
            seg = c["ini"] + (c["fim"] - c["ini"]) * frac
            r = subprocess.run([FF, "-v", "error", "-ss", f"{seg:.2f}", "-i", str(mp4), "-frames:v", "1",
                                "-vf", "crop=1080:1100:0:160,scale=216:220,format=gray", "-f", "rawvideo", "-"],
                               capture_output=True, timeout=120)
            ims.append(r.stdout)
        a, b = ims
        if not a or len(a) != len(b):
            continue
        pct = sum(abs(x - y) for x, y in zip(a, b)) / (255 * len(a)) * 100
        out.append((c["n"], c.get("tipo"), round(pct, 2)))
    return out


def _verificar(k, pasta, itens, foco, modelo, log):
    prompt = f"""Você é um VERIFICADOR exigente de um anúncio Reels (1080x1920) de {k['nome_produto']} ({k['marca']}).
Seu foco único: {VERIFICADORES[foco]}

{DESENHO}

Use Read para OLHAR folha.jpg (visão geral, cada linha = uma cena) e depois abra os quadros que precisar.
Quadros:
{chr(10).join(itens)}
Fatos permitidos: {'; '.join(k['fatos'])}

Seja duro: nota 10 = agência top sem defeito do seu foco. Aponte só problemas que você VIU, com o quadro.
Responda SÓ JSON: {{"nota": 0-10, "problemas": [{{"quadro": "q03.jpg", "cena": 1, "gravidade": "grave|media|leve",
"problema": "...", "como_corrigir": "instrução concreta"}}], "elogios": ["..."]}}"""
    reserva = (motor.cfg().get("editor") or {}).get("modelo_reserva")
    for tentativa in range(2):  # 26/10: o diretor voltou "None None"; 2ª com o modelo reserva (ccv v1.1)
        try:
            r = motor.chamar_json(prompt, pasta, f"produto_verificar_{foco}",
                                  modelo=reserva if tentativa and reserva else modelo)
            return {"foco": foco, "nota": float(r.get("nota") or 0), "problemas": r.get("problemas") or [],
                    "elogios": r.get("elogios") or []}
        except (motor.MotorErro, motor.SemCota) as e:
            log(f"    [lapidar {foco}] falhou ({tentativa + 1}/2): {str(e)[:150]}")
    return None


def verificar(mp4, side, k, log=print):
    """Nota dos 4 verificadores. Devolve dict (nota, graves, reprovar, verificadores) ou None se desligado/sem resposta."""
    c = motor.cfg()
    if not c.get("ligado") or not side.get("cenas"):
        return None
    pasta = Path(mp4).with_name(Path(mp4).stem + "_lapidar")
    itens = _quadros(mp4, side["cenas"], pasta)
    with ThreadPoolExecutor(len(VERIFICADORES)) as ex:
        vs = [v for v in ex.map(lambda f: _verificar(k, pasta, itens, f, c["modelo"], log), VERIFICADORES) if v]
    if not vs:
        shutil.rmtree(pasta, ignore_errors=True)
        return None
    nota = round(sum(v["nota"] for v in vs) / len(vs), 2)
    try:
        mov = movimento(mp4, side["cenas"])
    except Exception:  # noqa: BLE001
        mov = []
    paradas = [m for m in mov if m[2] < PARADA_PCT and m[1] != "cartao"]
    if paradas:  # medida objetiva: entra como grave do foco "movimento" (o corretor do editor recebe)
        vs.append({"foco": "medida_movimento", "nota": None, "elogios": [], "problemas": [
            {"gravidade": "grave", "quadro": "-", "cena": n, "problema": f"cena {n} ({t}) PARADA: só {p}% de mudança "
             f"entre 20% e 80% dela (mínimo {PARADA_PCT}%)",
             "como_corrigir": "zoom/pan maior no fundo e elementos entrando ao longo de toda a cena"} for n, t, p in paradas]})
    graves = [dict(p, foco=v["foco"]) for v in vs for p in v["problemas"] if p.get("gravidade") == "grave"]
    # só segura o vídeo o que é perigoso de verdade (propaganda enganosa / erro de escrita); o resto vira melhoria
    barra = [g for g in graves if g["foco"] == "roteiro_marca"
             and _PERIGO.search(f"{g.get('problema', '')} {g.get('como_corrigir', '')}")]
    reprovar = nota < c.get("reprovar_abaixo", 4.5) or bool(barra)
    res = {"nota": nota, "notas": {v["foco"]: v["nota"] for v in vs if v["nota"] is not None},
           "movimento": mov, "graves": len(graves), "reprovar": reprovar,
           "motivo": (f"nota {nota}" if nota < c.get("reprovar_abaixo", 4.5) else "")
           + ("; " if barra and nota < c.get("reprovar_abaixo", 4.5) else "")
           + ("; ".join(g.get("problema", "")[:120] for g in barra)),
           "verificadores": vs}
    HIST.parent.mkdir(exist_ok=True)
    with HIST.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"em": datetime.now().isoformat(timespec="seconds"), "conta": side.get("conta"),
                            "video": Path(mp4).name, "variante": side.get("variante"), **res}, ensure_ascii=False)
                + "\n")
    log(f"  [lapidar] nota {nota} ({', '.join(f'{v['foco']} {v['nota']:g}' for v in vs if v['nota'] is not None)}), "
        f"{len(graves)} grave(s); movimento por cena {[(n, p) for n, _, p in mov]}"
        + (f" -> REPROVADO: {res['motivo']}" if reprovar else ""))
    shutil.rmtree(pasta, ignore_errors=True)
    return res


def resumo(ultimos=20):
    """Problemas que se repetem nos últimos vídeos (por foco), para a sessão consertar no código."""
    if not HIST.exists():
        return "sem histórico"
    linhas = [json.loads(x) for x in HIST.read_text("utf-8").splitlines() if x.strip()][-ultimos:]
    out = [f"{len(linhas)} vídeos; nota média {sum(l['nota'] for l in linhas) / len(linhas):.2f}"]
    for l in linhas:
        out.append(f"- {l['em']} {l['conta']} {l.get('variante')}: {l['nota']} {l['notas']}"
                   + (" REPROVADO" if l.get("reprovar") else ""))
    cont = Counter()
    exemplos = {}
    for l in linhas:
        for v in l["verificadores"]:
            for p in v["problemas"]:
                if p.get("gravidade") in ("grave", "media"):
                    chave = f"[{v['foco']}/{p.get('gravidade')}] {p.get('problema', '')[:90]}"
                    cont[chave] += 1
                    exemplos.setdefault(chave, p.get("como_corrigir", "")[:160])
    out.append("Problemas (grave/média):")
    out += [f"  {n}x {ch} -> {exemplos[ch]}" for ch, n in cont.most_common(30)]
    return "\n".join(out)


if __name__ == "__main__":
    import sys
    if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(resumo())
