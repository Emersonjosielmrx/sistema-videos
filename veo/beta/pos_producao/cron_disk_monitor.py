"""cron_disk_monitor: monitora uso de disco D: e tamanho de saida.

Uso: python -m pos_producao.cron_disk_monitor
Log: D:/veo/beta/pos_producao/cron_logs/cron_disk_monitor.jsonl
"""

import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime, timezone

_BASE = Path(r"D:/veo/beta")
_VIDEOS_POS = _BASE / "videos_pos" / "cron_shorts"
_LOGS = _BASE / "pos_producao" / "cron_logs"
_LOG_FILE = _LOGS / "cron_disk_monitor.jsonl"


def _log(obj: dict):
    obj["ts"] = datetime.now(timezone.utc).isoformat()
    obj["agente"] = "cron_disk_monitor"
    line = json.dumps(obj, ensure_ascii=False)
    with _LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line, flush=True)


def _dir_size_gb(path: Path):
    if not path.exists():
        return 0.0
    total = 0
    for f in path.rglob("*"):
        if f.is_file():
            total += f.stat().st_size
    return round(total / 1024 / 1024 / 1024, 2)


def run():
    total, used, free = shutil.disk_usage("D:/")
    pct_disco = round(used / total * 100, 1)
    gb_videos_pos = _dir_size_gb(_VIDEOS_POS)
    alerta = pct_disco >= 85 or gb_videos_pos >= 50
    _log({
        "acao": "disk_monitor", "status": "alerta" if alerta else "ok",
        "detalhes": {
            "disco_d_pct": pct_disco,
            "disco_d_livre_gb": free // 1024 // 1024 // 1024,
            "videos_pos_gb": gb_videos_pos,
        },
    })


if __name__ == "__main__":
    run()