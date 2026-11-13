"""cron_pipeline_runner: processa MP4 novos usando a pipeline.

Uso: python -m pos_producao.cron_pipeline_runner
Log: D:/veo/beta/pos_producao/cron_logs/cron_pipeline_runner.jsonl

Le o log do cron_video_watcher e processa os videos listados la.
Respeita max_videos_per_run do config.yaml.
"""

import json
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

_BASE = Path(r"D:/veo/beta")
_LOGS = _BASE / "pos_producao" / "cron_logs"
_WATCHER_LOG = _LOGS / "cron_video_watcher.jsonl"
_LOG_FILE = _LOGS / "cron_pipeline_runner.jsonl"

# janela de quanto tempo atras considerar entradas do watcher
WATCHER_WINDOW_MIN = 15
MAX_VIDEOS = 3


def _log(obj: dict):
    obj["ts"] = datetime.now(timezone.utc).isoformat()
    obj["agente"] = "cron_pipeline_runner"
    line = json.dumps(obj, ensure_ascii=False)
    with _LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line, flush=True)


def _ler_watcher():
    """Le entradas do watcher dos ultimos WATCHER_WINDOW_MIN minutos."""
    if not _WATCHER_LOG.exists():
        return []
    cutoff = time.time() - WATCHER_WINDOW_MIN * 60
    novos = []
    for line in _WATCHER_LOG.read_text(encoding="utf-8").splitlines():
        try:
            obj = json.loads(line)
        except Exception:
            continue
        if obj.get("agente") != "cron_video_watcher":
            continue
        ts = datetime.fromisoformat(obj["ts"]).timestamp()
        if ts < cutoff:
            continue
        detalhes = obj.get("detalhes") or {}
        novos.extend(detalhes.get("novos") or [])
    # dedup por path
    seen = set()
    out = []
    for n in novos:
        if n["path"] in seen:
            continue
        seen.add(n["path"])
        out.append(n)
    return out[:MAX_VIDEOS]


def run():
    novos = _ler_watcher()
    if not novos:
        _log({"acao": "processar_lote", "status": "ok", "detalhes": {"qtd": 0}})
        return
    processados = []
    erros = []
    for item in novos:
        path = item["path"]
        stem = item["stem"]
        try:
            cmd = [sys.executable, "-m", "pos_producao.runner"]
            # usa run_one via subprocess import
            py = (
                f"from pos_producao.runner import run_one;"
                f"import sys; sys.argv=['runner'];"
                f"run_one(r'{path}', meta_extra={{'stem': '{stem}'}})"
            )
            r = subprocess.run(
                [sys.executable, "-c", py],
                cwd=str(_BASE),
                capture_output=True, text=True, timeout=600,
            )
            if r.returncode == 0:
                processados.append(stem)
            else:
                erros.append({"stem": stem, "stderr": r.stderr[-500:]})
        except Exception as e:
            erros.append({"stem": stem, "erro": str(e)})
    _log({
        "acao": "processar_lote", "status": "ok" if not erros else "warn",
        "detalhes": {"qtd": len(novos), "processados": processados, "erros": erros},
    })


if __name__ == "__main__":
    run()