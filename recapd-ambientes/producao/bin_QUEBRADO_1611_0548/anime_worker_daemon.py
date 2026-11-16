#!/usr/bin/env python3
"""anime_worker_daemon.py — daemon de render para PC2 (192.168.18.7).

Roda no PC2 (worker) e recebe tarefas via HTTP do PC principal.
O daemon é STATELESS: cada POST /run-anime é uma tarefa independente.

Para iniciar no PC2:
  cd C:\\hipercool-videos
  venv\\Scripts\\python.exe bin\\anime_worker_daemon.py --port 8772

Do PC principal (anime_auto.py), configura o worker:
  export ANIME_WORKER_HOST=192.168.18.7
  export ANIME_WORKER_PORT=8772
  python bin/anime_auto.py --modo short --worker ...

API:
  GET  /health              -> 200 {"ok": true, "cores": N, "ram_gb": float, "ffmpeg": bool}
  POST /run-anime           -> 200 {"ok": bool, "video_path": str, "roteiro_path": str, "log": str}
      body: {"video_url": str, "titulo": str, "modo": "short"|"deitado",
              "target_lines": int, "work_dir": str}
  GET  /download/<path>      -> streaming do arquivo gerado (para buscar resultado)
"""
import http.server
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import urllib.parse
from pathlib import Path
from functools import partial

# ── Config ────────────────────────────────────────────────────────────
PROJECT_DIR = Path(__file__).resolve().parent.parent
WORKSPACE = PROJECT_DIR / "workspace" / "anime"
VENV_PYTHON = PROJECT_DIR / "venv" / "Scripts" / "python.exe"

PORT = int(os.environ.get("ANIME_WORKER_PORT", "8772"))
HOST = os.environ.get("ANIME_WORKER_HOST", "0.0.0.0")
LOG_FILE = PROJECT_DIR / "workspace" / "anime_worker_daemon.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("worker")


# ── Helpers ──────────────────────────────────────────────────────────

def get_hw_info():
    """Info básica de hardware do worker."""
    import platform
    try:
        import psutil
        return {
            "cores": psutil.cpu_count(logical=False) or os.cpu_count(),
            "ram_gb": round(psutil.virtual_memory().total / (1024**3), 1),
            "python": sys.version.split()[0],
            "platform": platform.system(),
        }
    except ImportError:
        return {
            "cores": os.cpu_count() or 4,
            "ram_gb": 0,
            "python": sys.version.split()[0],
            "platform": platform.system(),
        }


def check_ffmpeg():
    try:
        r = subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5)
        return r.returncode == 0
    except Exception:
        return False


def run_anime_task(payload):
    """Executa uma tarefa de anime no worker. Retorna dict de resultado."""
    work_dir = payload.get("work_dir", "")
    video_url = payload.get("video_url", "")
    titulo = payload.get("titulo", "anime")
    modo = payload.get("modo", "short")
    target_lines = payload.get("target_lines", 10)

    if not work_dir:
        work_dir = tempfile.mkdtemp(prefix="anime_worker_")
    work_path = Path(work_dir)
    work_path.mkdir(parents=True, exist_ok=True)

    log.info(f"Tarefa recebida: {modo} | {titulo[:40]} | work_dir={work_dir}")

    try:
        # 1. Baixar vídeo-fonte
        import anime_fetch
        video_path = anime_fetch.download_video(video_url, work_path)
        if not video_path:
            return {"ok": False, "error": "download_failed", "work_dir": work_dir}

        # 2. Transcrição
        txt, lang = anime_fetch.fetch_captions(video_url, work_path)
        if not txt:
            txt, lang = anime_fetch.transcribe_whisper(str(video_path))
        if not txt:
            return {"ok": False, "error": "no_transcript", "work_dir": work_dir}

        # 3. Roteiro
        import anime_script
        import anime_probe
        roteiro_path = work_path / "roteiro.txt"
        orig_dur = anime_probe.video_duration(str(video_path))
        if modo == "short":
            # short: teto de 10 linhas (recap curtíssimo 9:16)
            t_lines = min(10, max(5, int(orig_dur / 4.5))) if orig_dur else 8
        else:
            # deitado: manter ~99% da duração original (reduz só ~1%).
            # ratio medido em jobs reais: ~6.6s de narração por frase.
            SEC_PER_LINE = 6.6
            KEEP = 0.99
            t_lines = max(40, round(orig_dur * KEEP / SEC_PER_LINE)) if orig_dur else 40
        log.info(f"target_lines={t_lines} (modo={modo}, orig_dur={orig_dur:.0f}s)")
        n = anime_script.rewrite_to_file(txt, str(roteiro_path), target_lines=t_lines)
        if n == 0:
            return {"ok": False, "error": "script_failed", "work_dir": work_dir}

        # 4. Pipeline de render
        auto_py = PROJECT_DIR / "bin" / "anime-pipeline.py"
        formato = "short" if modo == "short" else "deitado"
        final_name = f"final_anime_{formato}.mp4"

        cmd = [
            str(VENV_PYTHON), str(auto_py),
            "--video-source", str(video_path),
            "--script", str(roteiro_path),
            "--titulo", titulo,
            "--formato", formato,
        ]
        env = dict(os.environ, PYTHONUTF8="1", PYTHONPATH=str(PROJECT_DIR))
        r = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=3600)
        if r.returncode != 0:
            return {
                "ok": False,
                "error": "pipeline_failed",
                "rc": r.returncode,
                "log": (r.stdout + "\n" + r.stderr)[-2000:],
                "work_dir": work_dir,
            }

        # 5. Localizar o vídeo final
        final_path = work_path / final_name
        if not final_path.exists():
            # Procurar
            found = list(work_path.glob("final_anime_*.mp4"))
            if found:
                final_path = found[0]

        return {
            "ok": True,
            "video_path": str(final_path),
            "roteiro_path": str(roteiro_path),
            "work_dir": work_dir,
            "log": (r.stdout + "\n" + r.stderr)[-1000:],
        }

    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "timeout", "work_dir": work_dir}
    except Exception as e:
        import traceback
        log.error(f"Exceção na tarefa: {e}\n{traceback.format_exc()}")
        return {"ok": False, "error": str(e), "work_dir": work_dir}


# ── HTTP Handler ─────────────────────────────────────────────────────

class AnimeWorkerHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        log.info(fmt % args)

    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def do_GET(self):
        if self.path == "/health":
            info = get_hw_info()
            info["ffmpeg"] = check_ffmpeg()
            info["ok"] = True
            self.send_json(info)
        elif self.path.startswith("/download/"):
            # /download/<path_base64>
            import base64
            encoded = self.path[len("/download/"):]
            try:
                rel_path = base64.urlsafe_b64decode(encoded.encode()).decode()
                file_path = Path(rel_path)
                if not file_path.exists():
                    self.send_json({"error": "file_not_found"}, 404)
                    return
                # Streaming
                self.send_response(200)
                self.send_header("Content-Type", "video/mp4")
                self.send_header("Content-Disposition",
                                f'attachment; filename="{file_path.name}"')
                self.end_headers()
                with open(file_path, "rb") as f:
                    shutil.copyfileobj(f, self.wfile)
                return
            except Exception as e:
                self.send_json({"error": str(e)}, 400)
        else:
            self.send_json({"error": "not_found"}, 404)

    def do_POST(self):
        if self.path == "/run-anime":
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length)
                payload = json.loads(body.decode("utf-8"))
            except Exception as e:
                self.send_json({"ok": False, "error": f"bad_request: {e}"}, 400)
                return

            # Rodar em thread separada para não bloquear
            def run_in_thread():
                result = run_anime_task(payload)
                self._result = result

            self._result = None
            t = threading.Thread(target=run_in_thread)
            t.start()
            t.join(timeout=4000)  # 4 min max

            if self._result is None:
                self.send_json({"ok": False, "error": "task_timeout"}, 408)
            else:
                self.send_json(self._result)
        else:
            self.send_json({"error": "not_found"}, 404)


def run_server(port=PORT, host=HOST):
    server = http.server.HTTPServer((host, port), AnimeWorkerHandler)
    log.info(f"Anime Worker Daemon ouvindo em http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("Daemon encerrado.")
        server.shutdown()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Anime Worker Daemon (PC2)")
    parser.add_argument("--port", type=int, default=PORT, help="Porta HTTP")
    parser.add_argument("--host", default=HOST, help="Host para bindar")
    args = parser.parse_args()

    # Adicionar project_dir ao sys.path para poder importar anime_fetch, etc.
    sys.path.insert(0, str(PROJECT_DIR / "bin"))

    log.info(f"Iniciando daemon (port={args.port}, host={args.host})")
    run_server(port=args.port, host=args.host)
