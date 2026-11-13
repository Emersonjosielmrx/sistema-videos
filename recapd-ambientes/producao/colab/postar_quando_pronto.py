"""29/10 dona: "esse do Pastor tem que deixar pra postar de imediato, automático, mesmo que acabem seus tokens".
Vigia sozinho (sem chat): espera a ficha do vídeo chegar (esperar_e_publicar.py põe no Drive) e roda a postagem com
ele na frente da fila a cada 30 min até ele estar em longos_postados.json. A postagem continua SEMPRE agendada
(publishAt pelo postador) e respeita 1 longo por canal por dia e o limite do YouTube.
    pythonw postar_quando_pronto.py <id_do_youtube> [horas=36]"""
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
PY = r"D:\recapd-ambientes\producao\venv\Scripts\python.exe"
FICHAS = Path(r"D:\hipercool-materiais\animes recap\na_nuvem")
ESTADO = AQUI / "longos_postados.json"
LOG = AQUI / "postar_quando_pronto.log"

vid = sys.argv[1]
fim = time.time() + float(sys.argv[2] if len(sys.argv) > 2 else 36) * 3600


def log(m):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now():%d/%m %H:%M}] {vid}: {m}\n")


def postado():
    try:
        est = json.loads(ESTADO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return next((p for p in est.get("postados", []) if p.get("nome", "").startswith(vid + "_")), None)


log("vigia ligado")
while time.time() < fim:
    p = postado()
    if p:
        log(f"POSTADO (agendado) em {p.get('canal')}: {p.get('link', '')}")
        break
    if any(FICHAS.glob(f"{vid}_*/nuvem.json")):
        log("ficha no Drive — rodada de postagem com ele na frente")
        r = subprocess.run([PY, "-X", "utf8", str(AQUI / "postar_longos.py"), "--primeiro", vid],
                           capture_output=True, text=True, encoding="utf-8", errors="replace",
                           creationflags=0x08000000)
        log(f"rodada terminou (código {r.returncode}) {r.stderr.strip()[-200:]}")
        if postado():
            continue
        time.sleep(30 * 60)
    else:
        time.sleep(5 * 60)
else:
    log("desisti depois do prazo sem postar — ver postar_longos.log")
