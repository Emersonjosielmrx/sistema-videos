"""Teste dos modelos no papel do MELHORADOR (dona 29/10): o mesmo vídeo real, cada modelo faz analista + decisor +
revisor em ENSAIO (nada aplicado, nada escrito no DECISOES), resultado guardado aqui; depois a sessão Opus faz a
própria análise do mesmo vídeo e compara (qual modelo chega mais perto). Gemini puro = régua.

    D:\\veo\\venv\\Scripts\\python.exe rodar.py <video.json> [modelo ...]
"""
import json
import sys
import time
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, r"D:\postador-de-videos\bin")
from produto import melhorador as mel  # noqa: E402

MODELOS = ["agy/gemini-3.8-flash-high", "argon-flash", "argon-gemini", "argon-pro", "gweb/gemini-3.1-pro"]

_cfg_original = mel.cfg


def _cfg_teste():
    c = _cfg_original()
    c["modelos_desligados"] = []  # só no teste: o argon-pro está desligado na config
    return c


mel.cfg = _cfg_teste
mel._decisoes = lambda linhas: None  # ensaio do teste não escreve no DECISOES.md


def main():
    js = Path(sys.argv[1])
    modelos = sys.argv[2:] or MODELOS
    for m in modelos:
        import os
        nome = m.replace("/", "_") + os.environ.get("SUFIXO", "")  # SUFIXO=_v2: rodada com o prompt novo
        t0 = time.time()
        try:
            r = mel.ciclo(True, js, so_modelo=m)
            erro = None
        except Exception as e:  # noqa: BLE001
            r, erro = None, f"{type(e).__name__}: {str(e)[:300]}"
        out = {"modelo": m, "video": js.name, "quando": datetime.now().isoformat(timespec="seconds"),
               "segundos": round(time.time() - t0), "erro": erro, "resultado": r}
        (AQUI / f"{js.stem}__{nome}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str), "utf-8")
        print(f"== {m}: {out['segundos']} s, "
              + (f"ERRO {erro}" if erro else f"{len((r or {}).get('achados') or [])} achados, "
                 f"{len((r or {}).get('mudancas') or [])} mudanças, {(r or {}).get('aprovadas')} aprovadas"), flush=True)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
