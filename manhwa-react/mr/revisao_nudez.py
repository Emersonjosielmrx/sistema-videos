# -*- coding: utf-8 -*-
"""revisao_nudez.py — "análise do vídeo pronto" (nudez) pra qualquer projeto de vídeo.

Por quê: 16/10 o canal pt do hipercool levou advertência ("Nudez e conteúdo sexual") por vídeo que ninguém assistiu
pronto. Hipercool, anime e parceiro já passam pelo D:\\hipercool-videos\\bin\\revisao_video.py; o react passava só
pela aprovação humana — e o "aprovar --tudo" aprovava sem olhar.

Roda o revisao_video do hipercool num processo à parte, com o Python do hipercool (importar aqui poria o bin dele na
frente do sys.path e o projeto passaria a carregar módulos de mesmo nome de lá — 2 pipelines quebraram assim em
16/10). O veredito fica em <video>.revisao.json (formato do hipercool; reaproveitado se o arquivo não mudou).
Regra do dono: só nudez/ato segura o vídeo ("reprovado"); defeito visual não trava.

    revisar(mp4)  -> {"status": ok|reprovado|incompleto|erro, "problemas": n, "quadros": n}
    portao(mp4)   -> ("aprovado"|"rejeitado"|None, nota)   None = não deu pra analisar: não decide no escuro
    ja_tem(mp4)   -> veredito gravado e válido deste arquivo (sem analisar), ou None
"""
import json
import os
import subprocess
import sys
from pathlib import Path

HIPER_BIN = Path(r"D:\hipercool-videos\bin")
HIPER_PY = Path(r"D:\hipercool-videos\venv\Scripts\python.exe")

_SCRIPT = r"""
import json, sys
sys.path.insert(0, sys.argv[1])
import revisao_video as R
if sys.argv[4] == "ler":
    ok, motivo = R.aprovado(sys.argv[2])
    v = R.ler(sys.argv[2]) if (ok or (R.ler(sys.argv[2]) or {}).get("status") == "reprovado") else None
else:
    R.PASSO_S = float(sys.argv[3])
    v = R.revisar(sys.argv[2])
print("VEREDITO " + json.dumps(None if v is None else {"status": v.get("status"),
                                                      "problemas": len(v.get("problemas") or []),
                                                      "quadros": v.get("quadros")}))
"""


def _duracao(mp4):
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(mp4)],
                           capture_output=True, text=True, timeout=60)
        return float(r.stdout.strip())
    except (ValueError, OSError, subprocess.SubprocessError):
        return 0.0


def _rodar(mp4, modo, timeout):
    mp4 = Path(mp4)
    passo = os.environ.get("REVISAO_PASSO") or ("0.5" if _duracao(mp4) <= 180 else "3.0")  # 40 min a 0,5 s = ~4.800 quadros
    py = str(HIPER_PY if HIPER_PY.exists() else sys.executable)
    try:
        r = subprocess.run([py, "-c", _SCRIPT, str(HIPER_BIN), str(mp4), passo, modo], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout, cwd=str(HIPER_BIN.parent))
        for linha in reversed((r.stdout or "").splitlines()):
            if linha.startswith("VEREDITO "):
                return json.loads(linha[len("VEREDITO "):])
        return {"status": "erro", "detalhe": (r.stderr or r.stdout or "")[-300:]}
    except subprocess.TimeoutExpired:
        return {"status": "erro", "detalhe": f"passou de {timeout} s"}
    except OSError as e:
        return {"status": "erro", "detalhe": str(e)}


def revisar(mp4, timeout=3600):
    """Analisa (ou reaproveita a análise válida) e devolve o veredito. Nunca aprova no escuro."""
    return _rodar(mp4, "revisar", timeout)


def ja_tem(mp4):
    """Veredito gravado deste MESMO arquivo ("ok" válido ou "reprovado"), sem analisar; None se não há."""
    v = _rodar(mp4, "ler", 120)
    return v if v and v.get("status") in ("ok", "reprovado") else None


def portao(mp4):
    v = revisar(mp4)
    st = v.get("status")
    if st == "ok":
        return "aprovado", f"análise do vídeo pronto: ok ({v.get('quadros', '?')} quadros)"
    if st == "reprovado":
        return "rejeitado", f"análise do vídeo pronto: {v.get('problemas', '?')} trecho(s) com nudez"
    return None, f"análise {st}" + (f": {v['detalhe'][:150]}" if v.get("detalhe") else "")
