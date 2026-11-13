"""Os NOSSOS Shorts com views de 48-120 h (30/10), carregados uma vez na importação. Antes cada script fazia
exec() da metade de cima do alcance_projetos.py (cortada no texto "FX =") — mexer naquele arquivo quebrava
medir_nossos, relatorio_semanal e os outros sem aviso.

    from dados_nossos import L, led, ms, med, BR

L   = [{vid, v (views), projeto "projeto/tipo", canal, hora (BR), fonte, titulo}]
led = {video_id: linha do uploads_ledger}   ms = metricas_studio.json   med = medidas_48h do telegram_estado
"""
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
POST = Path(r"D:\postador-de-videos")
BR = timezone(timedelta(hours=-3))


def _ler_json(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


med = _ler_json(POST / "config" / "telegram_estado.json").get("medidas_48h") or {}
ms = _ler_json(POST / "_analise" / "metricas_studio.json")
led = {}
for ln in (POST / "logs" / "uploads_ledger.jsonl").read_text("utf-8").splitlines():
    try:
        r = json.loads(ln)
    except ValueError:
        continue
    if r.get("video_id"):
        led[r["video_id"]] = r
views = {vid: m["views"] for vid, m in med.items() if m.get("views") is not None}
for vid, m in ms.items():
    if isinstance(m, dict) and vid not in views and m.get("views") is not None and 40 <= (m.get("idade_h") or 0) <= 120:
        views[vid] = m["views"]
L = []
for vid, v in views.items():
    r = led.get(vid)
    if not r:
        continue
    f = {}
    try:
        f = json.loads((Path(r["caminho"]).parent / "postar.json").read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        pass
    try:
        dt = datetime.fromisoformat((r.get("publish_at") or r["ts"]).replace("Z", "+00:00")).astimezone(BR)
    except Exception:  # noqa: BLE001
        dt = None
    L.append(dict(vid=vid, v=float(v), projeto=f"{r.get('projeto')}/{r.get('tipo')}", canal=r.get("canal_id"),
                  hora=dt.hour if dt else None, fonte=f.get("fonte"), titulo=f.get("titulo") or ""))
