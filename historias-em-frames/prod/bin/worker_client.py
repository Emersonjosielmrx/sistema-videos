# -*- coding: utf-8 -*-
"""worker_client.py — Cliente para render distribuído (2º PC).

Envia jobs de ffmpeg pro worker remoto (PC2: 100.125.7.77:8771) quando disponível.
Fallback: render local se worker offline.
"""
import os
import json
import time
import subprocess
import urllib.request
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent

WORKER_HOST = os.environ.get("WORKER_HOST", "100.125.7.77")
WORKER_PORT = int(os.environ.get("WORKER_PORT", "8771"))
WORKER_URL = f"http://{WORKER_HOST}:{WORKER_PORT}"
WORKER_TIMEOUT = int(os.environ.get("WORKER_TIMEOUT", "300"))


def _worker_available():
    """Checa se o worker remoto está online."""
    try:
        req = urllib.request.Request(f"{WORKER_URL}/health", method="GET")
        resp = urllib.request.urlopen(req, timeout=3)
        return resp.status == 200
    except Exception:
        return False


def _post_json(endpoint, data):
    """POST JSON pro worker."""
    url = f"{WORKER_URL}{endpoint}"
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST",
                                 headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req, timeout=WORKER_TIMEOUT)
    return json.loads(resp.read().decode("utf-8"))


def sync_bin():
    """Sincroniza bin/*.py pro worker."""
    try:
        req = urllib.request.Request(f"{WORKER_URL}/sync-bin", method="POST")
        resp = urllib.request.urlopen(req, timeout=30)
        return resp.status == 200
    except Exception:
        return False


def render_remote(cmd_args, input_files=None, output_file=None):
    """Tenta render no worker remoto. Retorna True se conseguiu, False pra fallback local.

    Args:
        cmd_args: lista de argumentos ffmpeg (sem 'ffmpeg' na frente)
        input_files: lista de paths locais que o worker precisa
        output_file: path local onde o resultado deve ficar
    """
    if not os.environ.get("USE_WORKER", "0") == "1":
        return False

    if not _worker_available():
        return False

    try:
        job = {
            "cmd": cmd_args,
            "input_files": [str(f) for f in (input_files or [])],
            "output_file": str(output_file) if output_file else None,
            "timestamp": time.time(),
        }
        result = _post_json("/render", job)
        return result.get("success", False)
    except Exception:
        return False


def render_clip(img_path, audio_path, out_path, ffmpeg_args):
    """Tenta render de clip individual no worker. Fallback: local."""
    if render_remote(ffmpeg_args, input_files=[img_path, audio_path], output_file=out_path):
        return True
    # Fallback local
    cmd = ["ffmpeg"] + ffmpeg_args
    try:
        subprocess.run(cmd, capture_output=True, timeout=120)
        return Path(out_path).exists()
    except Exception:
        return False


def get_worker_status():
    """Retorna status do worker (queue, CPU, RAM)."""
    try:
        req = urllib.request.Request(f"{WORKER_URL}/status", method="GET")
        resp = urllib.request.urlopen(req, timeout=5)
        return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return {"online": False}
