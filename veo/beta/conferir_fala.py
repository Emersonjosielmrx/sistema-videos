# -*- coding: utf-8 -*-
"""conferir_fala.py — o Veo falou o que a gente pediu, em portugues?
(item AT-01 de docs\\PLANO_MELHORIAS_VEO.md)

O `ffprobe` diz que existe audio; nao diz o que foi dito. O Veo as vezes fala em
ingles, fala outra frase, ou so poe som ambiente. Ate 15/10/2026 nada conferia
isso: o video entrava no cache como SUCESSO, virava `postar.json` e alimentava a
replicacao de formulas "vencedoras". O sistema aprendia a agradar o critico de
texto, nunca o ouvido.

COMO FUNCIONA
  1. extrai o audio em wav mono 16 kHz (ffmpeg);
  2. transcreve com a cadeia que ja existe e e usada pelo
     D:\\postador-de-videos\\bin\\limpar_veo.py: `mr.transcribe` do manhwa-react
     (Groq Whisper pelo proxy Webshare e, se nao houver proxy, faster-whisper
     LOCAL — medido em 16/10: ~15 s por clipe de 8 s, sem rede e sem chave);
  3. compara o que foi OUVIDO com o que foi PEDIDO, por trigramas de caracteres.

POR QUE COMPARAR O TEXTO EM VEZ DE OLHAR O IDIOMA
  `mr.transcribe` devolve `language` igual ao que voce PEDIU (transcribe.py:119
  faz `"language": lang`), porque o Whisper e forcado a transcrever em pt. Ou
  seja, esse campo nunca denuncia um video falado em ingles. Ja a comparacao
  denuncia: audio em ingles transcrito a forca para portugues vira texto
  foneticamente embaralhado, e a semelhanca com a fala pedida despenca.

DEGRADACAO: se nao der para transcrever (sem Groq, sem modelo local, ffmpeg
ausente), devolve veredito None = "nao sei". Quem chama NAO deve reprovar o video
por isso — so registrar. Nunca travar a producao por causa da conferencia.

    from conferir_fala import conferir
    r = conferir("video.mp4", "Nao pisque, isso vai bugar a sua mente")
    r["ok"]           # True aprovado, False reprovado, None nao deu para saber
    r["semelhanca"]   # 0..1
    r["texto_ouvido"]
"""
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

_BASE = Path(__file__).resolve().parent
_MANHWA = Path(r"D:\manhwa-react")
_PY_MANHWA = _MANHWA / ".venv" / "Scripts" / "python.exe"
_FFMPEG = r"D:\hipercool-materiais\bin\ffmpeg.exe"

# Abaixo disto a fala ouvida nao tem nada a ver com a pedida. O manhwa-react usa
# 0,30 para dizer que dois textos sao O MESMO (mr\memoria.py::repetido_texto);
# aqui o uso e o inverso (quao perto do pedido), por isso o limiar e mais baixo:
# o Veo troca palavras e improvisa, e isso e aceitavel.
SEMELHANCA_MINIMA = 0.35
# Quanto da fala PEDIDA precisa ter sido dita. Pega o caso em que o Veo fala so o
# comeco da frase (nao cabe em 8 s) — ai a semelhanca da 1,00 e so a cobertura
# denuncia. 0,60 deixa passar o Veo trocar uma palavra ou cortar o fim da frase,
# e reprova quando falta metade.
COBERTURA_MINIMA = 0.60
TIMEOUT_S = 240


def _normalizar(txt: str) -> str:
    """minusculas, sem acento e sem pontuacao — para comparar som, nao grafia."""
    t = unicodedata.normalize("NFKD", (txt or "").lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9 ]+", " ", t).strip()


def _trigramas(txt: str) -> set:
    """Trigramas de caracteres. Mesma ideia do mr\\memoria.py::_trigramas, mas por
    caractere (nao por palavra): aguenta o Veo trocar uma palavra ou flexionar."""
    t = re.sub(r"\s+", " ", _normalizar(txt))
    return {t[i:i + 3] for i in range(max(0, len(t) - 2))}


def semelhanca(a: str, b: str) -> float:
    """0..1 — quanto do texto MENOR aparece no maior (Szymkiewicz-Simpson).

    Nao uso Jaccard porque a fala pedida e curta (~12 palavras) e o Veo costuma
    falar um pouco mais; Jaccard puniria isso sem motivo.

    CUIDADO: sozinha ela nao serve para aprovar video. Como divide pelo MENOR
    conjunto, qualquer PEDACO da fala pedida da 1,00 — "Cansado" contra "Cansado
    de recomecar? Entao pare de desistir" da 1,00. Para aprovar use cobertura()
    junto (e o que conferir() faz): falar so o comeco e o defeito mais comum em
    clipe de 8 s, quando a frase nao cabe no tempo.
    """
    ta, tb = _trigramas(a), _trigramas(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / min(len(ta), len(tb))


def cobertura(pedida: str, ouvida: str) -> float:
    """0..1 — quanto da fala PEDIDA aparece na ouvida. Assimetrica de proposito.

    Responde "ele falou a frase inteira?", que a semelhanca nao responde.
    """
    tp, to = _trigramas(pedida), _trigramas(ouvida)
    if not tp:
        return 0.0
    return len(tp & to) / len(tp)


def transcrever(mp4, idioma="pt", timeout=TIMEOUT_S) -> dict | None:
    """Transcreve pelo venv do manhwa-react (tem faster-whisper e o modelo local).

    Subprocesso de proposito: isola as dependencias pesadas do processo do cron,
    e e o mesmo caminho que o limpar_veo.py ja usa em producao.
    Devolve {texto, palavras, motor} ou None.
    """
    mp4 = Path(mp4)
    if not mp4.is_file():
        return None
    if not _PY_MANHWA.exists():
        return None
    script = r'''
import sys, json, subprocess, tempfile
from pathlib import Path
sys.path.insert(0, r"D:\manhwa-react")
from mr import transcribe
cfg = json.loads(Path(r"D:\manhwa-react\config.json").read_text("utf-8"))
mp4, idioma = sys.argv[1], sys.argv[2]
with tempfile.TemporaryDirectory() as td:
    wav = Path(td) / "a.wav"
    p = subprocess.run([cfg["paths"]["ffmpeg"], "-v", "error", "-y", "-i", mp4,
                        "-ac", "1", "-ar", "16000", str(wav)],
                       capture_output=True, text=True)
    if p.returncode != 0 or not wav.exists() or wav.stat().st_size < 1000:
        # o arquivo esta ilegivel: isso e defeito DO VIDEO. Avisa de forma
        # distinta de "a cadeia de transcricao caiu", senao o porteiro trata
        # video corrompido como "nao sei" e deixa passar.
        print("@@JSON@@" + json.dumps({"texto": "", "palavras": 0, "motor": "erro_ffmpeg"}))
        raise SystemExit(0)
    res = transcribe.transcribe(cfg, wav, idioma)
texto = " ".join(s["text"] for s in res.get("segments") or []).strip()
print("@@JSON@@" + json.dumps({"texto": texto,
                               "palavras": len(res.get("words") or []),
                               "motor": res.get("engine")}, ensure_ascii=False))
'''
    # 3.3 do CONTINUAR_DAQUI (16/10): se o Groq cair, o mr.transcribe usa o whisper LOCAL (pesado); com a trava de
    # render (trava_render.py) ele nao roda junto de uma montagem/legenda. Pelo Groq a trava fica ~6 s. Ocupada por
    # mais de 15 min: None ("nao deu para saber"), que o porteiro nao reprova.
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from trava_render import TravaOcupada, trava_render
        with trava_render("conferir_fala", esperar_s=900):
            r = subprocess.run([str(_PY_MANHWA), "-c", script, str(mp4), idioma],
                               capture_output=True, text=True, timeout=timeout,
                               encoding="utf-8", errors="replace",
                               creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except Exception:  # TravaOcupada incluida: sem transcricao = nao julga
        return None
    for linha in (r.stdout or "").splitlines():
        if linha.startswith("@@JSON@@"):
            try:
                return json.loads(linha[len("@@JSON@@"):])
            except ValueError:
                return None
    return None


def conferir(mp4, fala_pedida, mimimo=None, idioma="pt") -> dict:
    """O video falou o que foi pedido? Devolve dict; nunca levanta excecao.

    ok=True  aprovado
    ok=False reprovado (transcreveu e nao bate)
    ok=None  nao deu para saber (sem transcricao) — NAO reprove por isso
    """
    limiar = SEMELHANCA_MINIMA if mimimo is None else float(mimimo)
    rel = {"ok": None, "semelhanca": None, "texto_ouvido": None,
           "motor": None, "motivo": "", "limiar": limiar}
    if not (fala_pedida or "").strip():
        rel["motivo"] = "sem fala pedida para comparar"
        return rel

    t = transcrever(mp4, idioma=idioma)
    if t is None:
        # a CADEIA falhou (sem Groq, sem modelo local, subprocesso morto): nao da
        # para julgar o video. ok=None e quem chamou nao deve reprovar por isso.
        rel["motivo"] = "nao consegui transcrever (sem Groq/proxy e sem modelo local?)"
        return rel
    if t.get("motor") == "erro_ffmpeg":
        # o audio nao saiu do arquivo: isso e defeito DO VIDEO, nao da cadeia.
        rel["ok"] = False
        rel["motivo"] = "nao deu para extrair o audio: o arquivo esta ilegivel"
        return rel
    if not (t.get("texto") or "").strip():
        # transcreveu e nao ouviu nada: video mudo ou so som ambiente
        rel["ok"] = False
        rel["motor"] = t.get("motor")
        rel["motivo"] = "ninguem fala no video (transcricao vazia)"
        return rel

    rel["texto_ouvido"] = t["texto"]
    rel["motor"] = t.get("motor")
    s = semelhanca(fala_pedida, t["texto"])
    c = cobertura(fala_pedida, t["texto"])
    rel["semelhanca"] = round(s, 3)
    rel["cobertura"] = round(c, 3)
    if s < limiar:
        rel["ok"] = False
        rel["motivo"] = (f"a fala ouvida nao bate com a pedida ({s:.2f} < {limiar:.2f}): "
                         f"ouvido {t['texto'][:80]!r}")
    elif c < COBERTURA_MINIMA:
        rel["ok"] = False
        rel["motivo"] = (f"falou so parte da frase (disse {c:.0%} do que foi pedido): "
                         f"ouvido {t['texto'][:80]!r}")
    else:
        rel["ok"] = True
        rel["motivo"] = f"fala confere ({s:.2f}, disse {c:.0%} do pedido)"
    return rel


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('uso: conferir_fala.py <video.mp4> ["fala que foi pedida"]')
        sys.exit(1)
    arq = sys.argv[1]
    pedida = sys.argv[2] if len(sys.argv) > 2 else ""
    if pedida:
        r = conferir(arq, pedida)
        print(f"veredito: {r['ok']} | semelhanca: {r['semelhanca']} | motor: {r['motor']}")
        print(f"motivo: {r['motivo']}")
        print(f"ouvido: {r['texto_ouvido']}")
    else:
        t = transcrever(arq)
        print(json.dumps(t, ensure_ascii=False, indent=1) if t else "nao transcreveu")
