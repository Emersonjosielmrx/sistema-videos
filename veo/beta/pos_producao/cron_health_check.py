"""cron_health_check: valida que componentes da pipeline estao saudaveis.

Uso: python -m pos_producao.cron_health_check
Log: D:/veo/beta/pos_producao/cron_logs/cron_health_check.jsonl

Verifica:
  - ffmpeg executa
  - edge-tts instalado
  - onnxruntime instalado
  - parallax_engine importa
  - Gemini API key configurada
"""

import json
import os
import shutil
import subprocess
from pathlib import Path
from datetime import datetime, timezone

_BASE = Path(r"D:/veo/beta")
_FFMPEG = r"D:\hipercool-materiais\bin\ffmpeg.exe"
_LOGS = _BASE / "pos_producao" / "cron_logs"
_LOG_FILE = _LOGS / "cron_health_check.jsonl"


def _log(obj: dict):
    obj["ts"] = datetime.now(timezone.utc).isoformat()
    obj["agente"] = "cron_health_check"
    line = json.dumps(obj, ensure_ascii=False)
    with _LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line, flush=True)


def _check_ffmpeg():
    if not Path(_FFMPEG).exists():
        return False, f"ffmpeg nao encontrado em {_FFMPEG}"
    try:
        r = subprocess.run([_FFMPEG, "-version"], capture_output=True, text=True, timeout=10)
        ver = (r.stdout or "").split("\n", 1)[0]
        return True, ver
    except Exception as e:
        return False, str(e)


def _check_edge_tts():
    try:
        import edge_tts  # noqa
        return True, "edge_tts instalado"
    except ImportError as e:
        return False, str(e)


def _check_onnxruntime():
    try:
        import onnxruntime  # noqa
        return True, f"onnxruntime {onnxruntime.__version__}"
    except ImportError as e:
        return False, str(e)


def _check_parallax_engine():
    try:
        sys_path = r"D:\hipercool-videos\ambientes\3-exp\bin"
        import sys
        sys.path.insert(0, sys_path)
        import parallax_engine  # noqa
        return True, "parallax_engine OK"
    except Exception as e:
        return False, str(e)


def _check_gemini():
    key = (os.environ.get("GEMINI_API_KEY")
           or os.environ.get("GOOGLE_API_KEY")
           or os.environ.get("LLM_API_KEY"))
    return (bool(key), "key presente" if key else "key ausente")


def _check_disk():
    total, used, free = shutil.disk_usage("D:/")
    pct = round(used / total * 100, 1)
    return (pct < 90, f"{pct}% usado ({free // 1024 // 1024 // 1024} GB livres)")


def run():
    checks = {}
    for nome, fn in [
        ("ffmpeg", _check_ffmpeg),
        ("edge_tts", _check_edge_tts),
        ("onnxruntime", _check_onnxruntime),
        ("parallax_engine", _check_parallax_engine),
        ("gemini_key", _check_gemini),
        ("disk_space", _check_disk),
    ]:
        try:
            ok, detalhe = fn()
        except Exception as e:
            ok, detalhe = False, f"excecao: {e}"
        checks[nome] = {"ok": ok, "detalhe": detalhe}
    all_ok = all(c["ok"] for c in checks.values())
    _log({
        "acao": "health_check", "status": "ok" if all_ok else "warn",
        "detalhes": checks,
    })


if __name__ == "__main__":
    run()