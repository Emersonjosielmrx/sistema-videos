#!/usr/bin/env python3
"""anime_worker_daemon.py — daemon de render pro anime_auto no PC2.
API:
  GET  /health              -> 200 {"ok": true, "cores": N, "ram_gb": float, "ffmpeg": bool}
  POST /run-anime           -> 200 {"ok": bool, "video_path": str, "log": str}
      body: {"video_url": str, "titulo": str, "modo": "short"|"deitado", "work_dir": str}
"""
import http.server, json, logging, os, subprocess, sys, threading, tempfile, re, socketserver
from pathlib import Path
sys.path.insert(0, "C:/inovare-workers")
try:
    from toast_notify import toast
except Exception:
    def toast(*a, **k): pass

PROJECT_DIR = Path(__file__).resolve().parent.parent
VENV_PY = PROJECT_DIR / "venv" / "Scripts" / "python.exe"
PORT = 8772
LOG_FILE = PROJECT_DIR / "workspace" / "anime_worker_daemon.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("anime_worker")


def get_hw():
    try:
        import psutil
        return {"cores": os.cpu_count(), "ram_gb": round(psutil.virtual_memory().total / (1024**3), 1)}
    except:
        return {"cores": os.cpu_count(), "ram_gb": 0}


def check_ffmpeg():
    try:
        r = subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5)
        return r.returncode == 0
    except:
        return False


_RENDER_LOCK = threading.Lock()  # 1 render por vez DENTRO deste processo
# Lockfile em disco: protege contra daemons DUPLICADOS (o watchdog às vezes sobe 2).
# Cada processo tem seu próprio _RENDER_LOCK, então só o lockfile impede 2 daemons
# distintos de renderizarem ao mesmo tempo no mesmo workdir.
_RENDER_LOCKFILE = PROJECT_DIR / "workspace" / "render.lock"


def _acquire_disk_lock():
    """Retorna True se conseguiu o lock de disco. Lock obsoleto (>7h) é ignorado."""
    try:
        if _RENDER_LOCKFILE.exists():
            import time as _t
            age = _t.time() - _RENDER_LOCKFILE.stat().st_mtime
            if age < 7 * 3600:
                return False  # render ativo em outro processo
            log.warning("lockfile obsoleto (%.0fh) — assumindo órfão" % (age / 3600))
        _RENDER_LOCKFILE.parent.mkdir(parents=True, exist_ok=True)
        _RENDER_LOCKFILE.write_text(str(os.getpid()), encoding="utf-8")
        return True
    except Exception as e:
        log.error("falha no disk lock: %s" % e)
        return True  # não bloquear por erro de lock


def _release_disk_lock():
    try:
        _RENDER_LOCKFILE.unlink(missing_ok=True)
    except Exception:
        pass


def run_task(payload):
    work_dir = payload.get("work_dir", "") or tempfile.mkdtemp(prefix="anime_worker_")
    video_url = payload.get("video_url", "")
    titulo = payload.get("titulo", "anime")
    modo = payload.get("modo", "short")
    Path(work_dir).mkdir(parents=True, exist_ok=True)
    log.info(f"Tarefa: {modo} | {titulo[:40]}")

    tname = f"Anime: {titulo[:30]}"
    ttag = "anime-job"
    toast(tname, "Baixando vídeo...", percent=5, status="Etapa 1/5 download", tag=ttag)

    sys.path.insert(0, str(PROJECT_DIR / "bin"))

    try:
        import anime_fetch
        video = anime_fetch.download_video(video_url, Path(work_dir))
        if not video:
            toast(tname, "Falha no download", status="download_failed", tag=ttag, final=True, silent=False)
            return {"ok": False, "error": "download_failed"}

        toast(tname, "Obtendo transcrição...", percent=25, status="Etapa 2/5 legendas", tag=ttag)
        txt, lang = anime_fetch.fetch_captions(video_url, Path(work_dir))
        if not txt:
            toast(tname, "Transcrevendo áudio (Whisper)...", percent=30, status="Etapa 2/5 whisper", tag=ttag)
            txt, lang = anime_fetch.transcribe_whisper(str(video))
        if not txt:
            toast(tname, "Sem transcrição", status="no_transcript", tag=ttag, final=True, silent=False)
            return {"ok": False, "error": "no_transcript"}

        toast(tname, "Gerando roteiro...", percent=45, status="Etapa 3/5 roteiro", tag=ttag)
        import anime_script, anime_probe
        roteiro = Path(work_dir) / "roteiro.txt"
        orig_dur = anime_probe.video_duration(str(video))
        if modo == "short":
            t_lines = min(10, max(5, int(orig_dur / 4.5))) if orig_dur else 8
        else:
            # deitado: cobrir a duração INTEIRA (sem reduzir 1%). Decisão da dona
            # 2026-07-27: os efeitos (freeze/pausas/transições) já esticam o vídeo
            # além da narração, e ficar MAIOR/diferente do original é melhor pro
            # anti-ban do que ficar menor. Não vale trabalho de mirar 99%.
            # 3.8s de narração por frase (medido, edge-tts). 6.6s era pré-edge-tts.
            t_lines = max(40, round(orig_dur / 3.8)) if orig_dur else 40
        log.info("target_lines=%d (modo=%s, orig_dur=%.0fs)" % (t_lines, modo, orig_dur or 0))
        n = anime_script.rewrite_to_file(txt, str(roteiro), target_lines=t_lines)
        if n == 0:
            toast(tname, "Falha no roteiro", status="script_failed", tag=ttag, final=True, silent=False)
            return {"ok": False, "error": "script_failed"}

        auto_py = PROJECT_DIR / "bin" / "anime-pipeline.py"
        formato = "short" if modo == "short" else "deitado"
        final_name = f"final_anime_{formato}.mp4"
        cmd = [str(VENV_PY), str(auto_py), "--video-source", str(video),
                "--script", str(roteiro), "--titulo", titulo, "--formato", formato]
        # Modo deitado (1h+): desliga o teto de 1000 frases (--max-panels default)
        # que truncaria roteiros longos e cortaria a duração final do vídeo.
        if modo != "short":
            cmd += ["--max-panels", "0"]
        env = dict(os.environ, PYTHONUTF8="1", PYTHONPATH=str(PROJECT_DIR))

        toast(tname, "Renderizando clips...", percent=55, status="Etapa 4/5 render", tag=ttag)
        re_clip = re.compile(r"(?:Clip|clipe)s?\s+(\d+)/(\d+)")
        lines_out = []
        proc = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, encoding="utf-8", errors="replace", bufsize=1)
        for line in proc.stdout:
            lines_out.append(line)
            if len(lines_out) > 400:
                lines_out = lines_out[-400:]
            L = line.strip()
            m = re_clip.search(L)
            if m:
                cur, tot = int(m.group(1)), max(1, int(m.group(2)))
                pct = 55 + int(cur / tot * 35)  # render = 55..90%
                toast(tname, "Renderizando clips", percent=pct,
                      status="Clip %d/%d" % (cur, tot), tag=ttag)
            elif "concat" in L.lower():
                toast(tname, "Juntando clips", percent=92, status="Etapa 5/5 concat", tag=ttag)
            elif "legenda" in L.lower() or "caption" in L.lower():
                toast(tname, "Aplicando legendas", percent=95, status="Etapa 5/5 legendas", tag=ttag)
        proc.wait(timeout=21600)  # 6h: render deitado 1h+ pode passar de 1h
        full = "".join(lines_out)
        if proc.returncode != 0:
            toast(tname, "Erro no pipeline", status="rc=%s" % proc.returncode, tag=ttag, final=True, silent=False)
            return {"ok": False, "error": "pipeline_failed", "log": full[-2000:]}

        final_path = Path(work_dir) / final_name
        if not final_path.exists():
            found = list(Path(work_dir).glob("final_anime_*.mp4"))
            if found:
                final_path = found[0]

        # Verificação de duração: compara o vídeo final com o source. Se o modo
        # deitado saiu bem mais curto que ~85% do source, o roteiro condensou
        # demais (bug histórico). Reporta ratio pra decidir re-render.
        final_dur = anime_probe.video_duration(str(final_path)) if final_path.exists() else 0.0
        ratio = (final_dur / orig_dur) if orig_dur else 0.0
        dur_ok = ratio >= 0.85 or modo == "short"
        log.info("DURACAO final=%.0fs orig=%.0fs ratio=%.1f%% (ok=%s)"
                 % (final_dur, orig_dur or 0, ratio * 100, dur_ok))

        toast(tname, "Concluído! Vídeo pronto", percent=100, status="100% — pronto",
              tag=ttag, final=True, silent=False)
        return {"ok": True, "video_path": str(final_path),
                "roteiro_path": str(roteiro),
                "final_dur": round(final_dur, 1), "orig_dur": round(orig_dur or 0, 1),
                "dur_ratio": round(ratio, 3), "dur_ok": dur_ok, "n_frases": n,
                "work_dir": work_dir, "log": full[-1000:]}
    except Exception as e:
        import traceback
        log.error(f"Erro: {e}\n{traceback.format_exc()}")
        toast(tname, "FALHA: %s" % str(e)[:80], status="exceção", tag=ttag, final=True, silent=False)
        return {"ok": False, "error": str(e)}


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        log.info(fmt % args)

    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())

    def do_GET(self):
        if self.path == "/health":
            info = get_hw()
            info["ffmpeg"] = check_ffmpeg()
            info["ok"] = True
            self.send_json(info)
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
            # Lock duplo (1 render por vez): in-process contra POSTs simultâneos na
            # mesma instância + lockfile de disco contra daemons DUPLICADOS. Sem isso,
            # N POSTs viram N subprocessos de render no MESMO workdir e travam tudo.
            if not _RENDER_LOCK.acquire(blocking=False):
                log.warning("run-anime recusado: render em andamento nesta instância (busy)")
                self.send_json({"ok": False, "error": "busy_rendering"}, 409)
                return
            if not _acquire_disk_lock():
                _RENDER_LOCK.release()
                log.warning("run-anime recusado: render em andamento em outro daemon (busy disk)")
                self.send_json({"ok": False, "error": "busy_rendering_disk"}, 409)
                return
            try:
                result = run_task(payload)
            finally:
                _release_disk_lock()
                _RENDER_LOCK.release()
            self.send_json(result)
        else:
            self.send_json({"error": "not_found"}, 404)


class _ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    # multi-thread: /health responde na hora mesmo durante um render longo,
    # senão o watchdog (health a cada 180s) acha que caiu e sobe daemon duplicado
    # no meio do job, matando o render. daemon_threads evita threads presas no shutdown.
    daemon_threads = True
    allow_reuse_address = True


if __name__ == "__main__":
    server = _ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    log.info(f"Anime Worker Daemon ouvindo em http://0.0.0.0:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("Daemon encerrado.")
        server.shutdown()
