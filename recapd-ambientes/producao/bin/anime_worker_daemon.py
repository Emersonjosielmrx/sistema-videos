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
import sys as _sys
if _sys.platform == "win32":  # dona 26/10: rclone/ssh/scp/python filhos SEM janela na tela (PC1 e PC2)
    for _p in (r"D:\hipercool-materiais\comum", r"C:\hipercool-materiais\comum"):
        if Path(_p, "sem_janela.py").exists():
            _sys.path.append(_p)
            import sem_janela  # noqa: F401,E402
            break

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
        # sem stdin: no pythonw a entrada herdada é inválida e o ffmpeg travava até o timeout (/health em 10 s)
        r = subprocess.run(["ffmpeg", "-version"], capture_output=True, stdin=subprocess.DEVNULL, timeout=5)
        return r.returncode == 0
    except Exception:
        return False


def _disco_info():
    """Espaco livre no disco onde o worker trabalha. Alerta cedo (o disco cheio
    ja fez render de 68min morrer com 'No space left on device')."""
    try:
        import tempfile
        alvo = Path(tempfile.gettempdir())
        u = shutil.disk_usage(str(alvo))
        livre_gb = round(u.free / (1024**3), 2)
        return {
            "livre_gb": livre_gb,
            "total_gb": round(u.total / (1024**3), 1),
            "usado_pct": round(u.used / u.total * 100, 1),
            "critico": livre_gb < 3.0,  # < 3GB = perigo de render falhar
        }
    except Exception as e:
        return {"erro": str(e)}


def _cleanup_work_dir(work_dir: str) -> dict:
    """Apaga um work_dir do PC2 com SEGURANCA (chamado pelo PC1 apos baixar).
    Trava: so apaga dentro de areas de trabalho conhecidas (workspace/ ou o
    tempdir do sistema) — nunca um caminho arbitrario, nunca a raiz do projeto."""
    if not work_dir:
        return {"ok": False, "error": "work_dir vazio"}
    try:
        alvo = Path(work_dir).resolve()
    except Exception as e:
        return {"ok": False, "error": f"path invalido: {e}"}

    import tempfile
    permitidos = [WORKSPACE.resolve(), Path(tempfile.gettempdir()).resolve()]
    dentro = any(str(alvo).startswith(str(base)) and alvo != base
                 for base in permitidos)
    if not dentro:
        return {"ok": False, "error": f"fora de area permitida: {alvo}",
                "permitidos": [str(p) for p in permitidos]}
    if not alvo.exists():
        return {"ok": True, "ja_removido": True, "work_dir": str(alvo)}
    try:
        antes = _disco_info().get("livre_gb")
        shutil.rmtree(alvo, ignore_errors=True)
        depois = _disco_info().get("livre_gb")
        log.info(f"[cleanup] removido {alvo} (livre {antes}GB -> {depois}GB)")
        return {"ok": True, "removido": str(alvo),
                "livre_gb_antes": antes, "livre_gb_depois": depois}
    except Exception as e:
        return {"ok": False, "error": str(e), "work_dir": str(alvo)}


def _auto_cleanup(work_path: Path, keep: set = None):
    """Apaga intermediários pesados após render bem-sucedido.
    Preserva arquivos em `keep` (nomes, não paths)."""
    keep = keep or set()
    pesados = ["source.mp4", "audio_cache", "clipes_landscape", "clipes_portrait",
               "clipes_short", "cap_en.en.vtt"]
    freed = 0
    for nome in pesados:
        alvo = work_path / nome
        if alvo.name in keep or not alvo.exists():
            continue
        try:
            if alvo.is_dir():
                size = sum(f.stat().st_size for f in alvo.rglob("*") if f.is_file())
                shutil.rmtree(alvo, ignore_errors=True)
            else:
                size = alvo.stat().st_size
                alvo.unlink()
            freed += size
        except Exception as e:
            log.warning(f"[auto-cleanup] erro apagando {nome}: {e}")
    for p in work_path.glob("_semlegenda_*.mp4"):
        if p.name not in keep:
            try:
                freed += p.stat().st_size
                p.unlink()
            except Exception as e:
                log.warning(f"[auto-cleanup] erro apagando {p.name}: {e}")
    log.info(f"[auto-cleanup] {work_path.name}: liberou {freed / (1024**2):.0f} MB")


def _varrer_tempdirs(horas_intermed=6, dias_final=3):
    """22/10 (dono: "nunca parar por falta de espaço"): job que FALHA (download, legenda, roteiro, render) saía
    sem limpar a pasta anime_worker_* do TEMP — o PC2 juntou 16,8 GB assim (pastas de até 3,6 GB) e ficou com 2,8 GB
    livres. Varredura em toda tarefa nova: pasta sem NENHUMA escrita há `horas_intermed` horas (nenhum job dura
    mais que o timeout de 2 h) perde os intermediários; o vídeo final (final_anime_*.mp4), se existir, fica até
    `dias_final` dias pro PC1 buscar e só então a pasta some."""
    import time as _t
    agora, liberado = _t.time(), 0
    for d in Path(tempfile.gettempdir()).glob("anime_worker_*"):
        try:
            if not d.is_dir():
                continue
            arquivos = [f for f in d.rglob("*") if f.is_file()]
            ultima = max((f.stat().st_mtime for f in arquivos), default=d.stat().st_mtime)
            idade = agora - ultima
            if idade < horas_intermed * 3600:
                continue  # pode ser o job em andamento
            finais = [f for f in arquivos if f.name.startswith("final_anime_")]
            if finais and idade < dias_final * 86400:
                for f in arquivos:
                    if f not in finais and f.name != "roteiro.txt":
                        liberado += f.stat().st_size
                        f.unlink(missing_ok=True)
                continue
            liberado += sum(f.stat().st_size for f in arquivos)
            shutil.rmtree(d, ignore_errors=True)
        except Exception as e:  # noqa: BLE001 — varredura nunca derruba a tarefa
            log.warning(f"[varredura] {d.name}: {e}")
    if liberado:
        log.info(f"[varredura] pastas anime_worker_* paradas: liberou {liberado / (1024**3):.2f} GB")
    return liberado


def run_anime_task(payload):
    """Executa uma tarefa de anime no worker. Retorna dict de resultado."""
    work_dir = payload.get("work_dir", "")
    video_url = payload.get("video_url", "")
    titulo = payload.get("titulo", "anime")
    modo = payload.get("modo", "short")
    target_lines = payload.get("target_lines", 10)

    _varrer_tempdirs()
    if not work_dir:
        work_dir = tempfile.mkdtemp(prefix="anime_worker_")
    work_path = Path(work_dir)
    work_path.mkdir(parents=True, exist_ok=True)

    log.info(f"Tarefa recebida: {modo} | {titulo[:40]} | work_dir={work_dir}")

    try:
        # 1. Baixar vídeo-fonte (pula se source.mp4 já existe no workdir)
        import anime_fetch
        existing_source = work_path / "source.mp4"
        if existing_source.exists() and existing_source.stat().st_size > 0:
            video_path = existing_source
            log.info(f"[fetch] source.mp4 já existe ({existing_source.stat().st_size / (1024**2):.0f} MB), pulando download")
        else:
            video_path = anime_fetch.download_video(video_url, work_path)
            if not video_path:
                return {"ok": False, "error": "download_failed", "work_dir": work_dir}

        # 2. Transcrição (usa enviada pelo PC1 se disponível, senão tenta obter)
        txt = payload.get("transcript_txt", "")
        lang = payload.get("transcript_lang", "en")
        if txt:
            log.info(f"[transcript] usando transcrição enviada pelo PC1 ({len(txt)} chars, lang={lang})")
            # Se PC1 enviou legenda_tempos.json, salvar
            if "legenda_tempos_json" in payload:
                (work_path / "legenda_tempos.json").write_text(payload["legenda_tempos_json"], encoding="utf-8")
                log.info("[transcript] legenda_tempos.json recebida do PC1")
        else:
            # Fallback: tenta obter transcrição localmente
            existing_caps = list(work_path.glob("cap_*.vtt"))
            if existing_caps:
                cap_path = existing_caps[0]
                log.info(f"[transcript] {cap_path.name} já existe, lendo diretamente")
                txt = cap_path.read_text(encoding="utf-8", errors="ignore")
                lang = "en" if "en" in cap_path.name else "pt"
            else:
                txt, lang = anime_fetch.fetch_captions(video_url, work_path)
                if not txt:
                    # 25/10: sem max_seconds parava nos 25 min (o longo saía feito só com o começo do original)
                    import anime_probe as _probe
                    txt, lang = anime_fetch.transcribe_whisper(
                        str(video_path), max_seconds=int(_probe.video_duration(str(video_path)) or 1440) + 60)
                    lado = Path(str(Path(video_path).with_suffix(".whisper.wav")) + ".tempos.json")
                    if txt and lado.exists() and not (work_path / "legenda_tempos.json").exists():
                        lado.replace(work_path / "legenda_tempos.json")
        if not txt:
            return {"ok": False, "error": "no_transcript", "work_dir": work_dir}

        # 3. Roteiro (usa enviado pelo PC1 se disponível, senão gera localmente)
        import anime_script
        import anime_probe
        roteiro_path = work_path / "roteiro.txt"
        roteiro_enviado = payload.get("roteiro_txt", "")
        if roteiro_enviado:
            roteiro_path.write_text(roteiro_enviado, encoding="utf-8")
            n = len([l for l in roteiro_enviado.splitlines() if l.strip()])
            log.info(f"[script] usando roteiro enviado pelo PC1 ({n} linhas)")
        else:
            # Fallback: gera roteiro localmente
            origianl_target = payload.get("target_lines", 0)
            orig_dur = anime_probe.video_duration(str(video_path))
            if origianl_target > 0:
                t_lines = origianl_target
            elif modo == "short":
                # short: teto de 10 linhas (recap curtíssimo 9:16)
                t_lines = min(10, max(5, int(orig_dur / 4.5))) if orig_dur else 8
            else:
                # deitado: manter ~99% da duração original (reduz só ~1%).
                # ratio medido em jobs reais: ~6.6s de narração por frase.
                SEC_PER_LINE = 6.6
                KEEP = 0.99
                t_lines = max(40, round(orig_dur * KEEP / SEC_PER_LINE)) if orig_dur else 40
            log.info(f"target_lines={t_lines} (modo={modo}, orig_dur={orig_dur:.0f}s)")
            n = 0
            (work_path / "roteiro_tempos.json").unlink(missing_ok=True)
            if modo != "short" and (work_path / "legenda_tempos.json").exists():  # dona 25/10: longo narra o que está na tela
                try:
                    frases, tempos = anime_script.rewrite_longo_com_tempo(
                        json.loads((work_path / "legenda_tempos.json").read_text(encoding="utf-8")), t_lines, orig_dur)
                except Exception as e:  # noqa: BLE001
                    log.warning(f"roteiro com tempo falhou ({type(e).__name__}: {e}) — roteiro normal")
                    frases, tempos = [], []
                if frases:
                    roteiro_path.write_text("\n".join(frases) + "\n", encoding="utf-8")
                    (work_path / "roteiro_tempos.json").write_text(json.dumps(tempos), encoding="utf-8")
                    n = len(frases)
            if n == 0:
                n = anime_script.rewrite_to_file(txt, str(roteiro_path), target_lines=t_lines)
        if n == 0:
            return {"ok": False, "error": "script_failed", "work_dir": work_dir}

        # 4. Pipeline de render
        auto_py = PROJECT_DIR / "bin" / "anime-pipeline.py"
        formato = "short" if modo == "short" else "deitado"
        final_name = f"final_anime_{formato}.mp4"

        cmd = [
            str(VENV_PYTHON), "-X", "utf8", str(auto_py),
            "--video-source", str(video_path),
            "--script", str(roteiro_path),
            "--titulo", titulo,
            "--formato", formato,
        ]
        env = dict(os.environ, PYTHONPATH=str(PROJECT_DIR))
        r = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=7200)
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

        # 6. Auto-cleanup: apagar intermediários pesados, preservar final + roteiro
        _auto_cleanup(work_path, keep={final_path.name, "roteiro.txt"})

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
            info["disco"] = _disco_info()  # alerta cedo de disco cheio
            self.send_json(info)
        elif self.path == "/disk":
            self.send_json(_disco_info())
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
            t.join(timeout=7500)  # 2h 5min — cobre subprocess timeout de 7200s

            if self._result is None:
                self.send_json({"ok": False, "error": "task_timeout"}, 408)
            else:
                self.send_json(self._result)
        elif self.path == "/cleanup":
            # Apaga um work_dir do PC2 DEPOIS que o PC1 confirmou que baixou.
            # PC2 e SO worker: nada pode ficar guardado apos o video pronto.
            try:
                length = int(self.headers.get("Content-Length", 0))
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
            except Exception as e:
                self.send_json({"ok": False, "error": f"bad_request: {e}"}, 400)
                return
            self.send_json(_cleanup_work_dir(payload.get("work_dir", "")))
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
