"""metricas_longos.py — 04/11 dona ("quanto à retenção temos que estudar e ver o que podemos melhorar; algumas
visualizações são minhas, eu assisto todos do começo ao fim"): lê no Studio de cada canal, por longo postado,
views, IMPRESSÕES, CTR da capa, duração média e % ainda assistindo aos 0:30 (youtube_studio_extras --metricas, o
mesmo Chrome do canal, um por vez, respeitando a trava do postador). Grava colab\\metricas_longos.json.

    pythonw metricas_longos.py
"""
import json
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
POSTADOS = AQUI / "longos_postados.json"
SAIDA = AQUI / "metricas_longos.json"
PY = r"D:\manhwa-react\.venv\Scripts\python.exe"
EXTRAS = r"D:\postador-de-videos\bin\youtube_studio_extras.py"


def main():
    post = json.loads(POSTADOS.read_text(encoding="utf-8"))["postados"]
    try:
        res = json.loads(SAIDA.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        res = {}
    for p in post:
        yid = str(p.get("url", "")).rstrip("/").split("/")[-1].split("=")[-1]
        if not yid or (res.get(yid) or {}).get("lido", "")[:10] == datetime.now().strftime("%Y-%m-%d"):
            continue
        t0 = time.time()
        try:
            r = subprocess.run([PY, EXTRAS, "--canal", p["canal"], f"--video={yid}", "--metricas"], capture_output=True,
                               text=True, encoding="utf-8", errors="replace", timeout=3 * 3600,
                               cwd=str(Path(EXTRAS).parent), creationflags=0x08000000)
            linha = [l for l in (r.stdout + r.stderr).splitlines() if "RESULTADO" in l]
            m = re.search(r"\{.*\}", linha[-1]) if linha else None
            dados = json.loads(m.group(0)) if m else {"erro": (r.stdout + r.stderr)[-300:]}
        except Exception as e:  # noqa: BLE001
            dados = {"erro": f"{type(e).__name__}: {e}"}
        res[yid] = {"canal": p.get("canal_nome"), "titulo": p.get("titulo"), "postado": p.get("em"),
                    "duracao_s": p.get("duracao_s"), "dados": dados, "lido": datetime.now().isoformat("T", "minutes"),
                    "s": round(time.time() - t0)}
        SAIDA.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
