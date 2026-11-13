import os
import json
import subprocess
import time
import re
import psutil
import threading
from pathlib import Path
from collections import Counter
import mimetypes
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'bin'))
try:
    import worker_client
except ImportError:
    worker_client = None
from http.server import HTTPServer, SimpleHTTPRequestHandler

# Reuse text parsing logic from existing painel_dashboard.py
from painel_dashboard import (
    find_latest_log, parse_log, get_recent_videos, check_gemini_radar, format_eta
)

DASHBOARD_DIR = Path("D:/hipercool-inferior-fix/workspace/dashboard")
DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)
DATA_FILE = DASHBOARD_DIR / "data.json"
PROJECT_DIR = Path("D:/hipercool-inferior-fix")
QUEUE_STATE = PROJECT_DIR / "workspace" / "queue_state.json"

import platform as _plat
try:
    _cpu_out = subprocess.check_output('wmic cpu get name', shell=True).decode('cp1252', errors='replace')
    _CPU_MODEL = next((l.strip() for l in _cpu_out.splitlines() if l.strip() and 'Name' not in l), _plat.processor())
except Exception:
    _CPU_MODEL = _plat.processor() or "Unknown"
_RAM_TOTAL_GB = round(psutil.virtual_memory().total / (1024**3), 1)

# In-memory data store (thread-safe) — evita race condition de leitura/escrita no disco
_live_data_json = b'{}'
_live_img_json = b'{}'
_live_data_lock = threading.Lock()


class DashboardHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            with open(DASHBOARD_DIR / "index.html", "rb") as fh:
                self.wfile.write(fh.read())
            return

        # Serve static files from dashboard directory
        if self.path.startswith('/css/') or self.path.startswith('/js/') or self.path.startswith('/assets/'):
            file_path = DASHBOARD_DIR / self.path.lstrip('/')
            if file_path.exists():
                self.send_response(200)
                ext = file_path.suffix.lower()
                content_type = {
                    '.css': 'text/css',
                    '.js': 'application/javascript',
                    '.json': 'application/json',
                    '.png': 'image/png',
                    '.jpg': 'image/jpeg',
                    '.svg': 'image/svg+xml'
                }.get(ext, 'application/octet-stream')
                self.send_header('Content-Type', content_type)
                self.end_headers()
                with open(file_path, "rb") as fh:
                    self.wfile.write(fh.read())
                return
            else:
                self.send_response(404)
                self.end_headers()
                return

        if self.path == '/data.json':

            with _live_data_lock:
                payload = _live_data_json
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(payload)))
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            self.wfile.write(payload)
            return
        if self.path == '/img.json':
            with _live_data_lock:
                payload = _live_img_json
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(payload)))
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            self.wfile.write(payload)
            return
        super().do_GET()

    def do_POST(self):
        if self.path == '/api/command':
            content_length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(content_length)) if content_length else {}
            action = body.get('action', '')
            target = body.get('target', 'all')
            valid_actions = {'skip', 'pause', 'stop'}
            valid_targets = {'all', 'audio', 'video', 'worker'}
            if action in valid_actions and target in valid_targets:
                suffix = '' if target == 'all' else f'_{target.upper()}'
                cmd_file = PROJECT_DIR / f'COMMAND_{action.upper()}{suffix}.txt'
                if cmd_file.exists():
                    cmd_file.unlink(missing_ok=True)
                    status = "cleared"
                else:
                    cmd_file.write_text("1")
                    status = "set"
                self._json_response({"ok": True, "action": action, "target": target, "status": status})
            else:
                self._json_response({"ok": False, "error": "invalid action/target"}, 400)
            return

        if self.path == '/api/open':
            content_length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(content_length)) if content_length else {}
            path = body.get('path', '').replace('/', '\\')
            if path and os.path.exists(path):
                os.startfile(path)
                self._json_response({"ok": True})
            else:
                self._json_response({"ok": False, "error": "not found"}, 404)
            return

        self.send_response(405)
        self.end_headers()

    def _json_response(self, data, code=200):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())





def serve_html():
    os.chdir(str(DASHBOARD_DIR))
    PORT = 8080
    with HTTPServer(("", PORT), DashboardHandler) as httpd:
        print(f"Servidor Web iniciado em http://localhost:{PORT}")
        httpd.serve_forever()

def image_to_base64(img_path):
    import base64
    if not img_path or not os.path.exists(img_path): return None
    try:
        with open(img_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except: return None

# GPU monitor em thread separada (Get-Counter leva ~3-5s, não pode bloquear o HTTP)
_gpu_pct_cache = 0.0
_gpu_lock = threading.Lock()

# Health check de chaves API (roda a cada 5min em background)
_keys_health = {"gemini": [], "eleven": [], "last_check": "", "checking": False}
_keys_lock = threading.Lock()

def _keys_health_check():
    """Testa chaves Gemini com request mínimo e atualiza cache de status."""
    import urllib.request
    import urllib.error
    from datetime import datetime as _dt

    while True:
        try:
            with _keys_lock:
                _keys_health["checking"] = True

            # Gemini keys
            gk_file = PROJECT_DIR / "secrets" / "gemini_keys.json"
            gemini_results = []
            if gk_file.exists():
                gdata = json.loads(gk_file.read_text(encoding="utf-8"))
                for k in gdata:
                    token = k.get("token") or k.get("key")
                    kid = k.get("id", k.get("note", "?"))
                    if not token:
                        gemini_results.append({"id": kid, "status": "invalid", "detail": "sem token"})
                        continue
                    try:
                        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={token}"
                        req = urllib.request.Request(url, method="GET")
                        resp = urllib.request.urlopen(req, timeout=8)
                        gemini_results.append({"id": kid, "status": "ok", "detail": ""})
                    except urllib.error.HTTPError as e:
                        code = e.code
                        if code == 429:
                            gemini_results.append({"id": kid, "status": "quota", "detail": "429 quota"})
                        elif code == 403:
                            gemini_results.append({"id": kid, "status": "blocked", "detail": "403 forbidden"})
                        elif code == 400:
                            gemini_results.append({"id": kid, "status": "geo", "detail": "400 location"})
                        else:
                            gemini_results.append({"id": kid, "status": "error", "detail": f"HTTP {code}"})
                    except Exception as e:
                        gemini_results.append({"id": kid, "status": "timeout", "detail": str(e)[:30]})

            # ElevenLabs keys
            ek_file = PROJECT_DIR / "secrets" / "elevenlabs_keys.json"
            eleven_results = []
            if ek_file.exists():
                edata = json.loads(ek_file.read_text(encoding="utf-8"))
                ekeys = edata.get("keys", []) if isinstance(edata, dict) else edata
                for k in ekeys:
                    token = k.get("token") or k.get("api_key")
                    name = k.get("name", "?")
                    if not token:
                        eleven_results.append({"id": name, "status": "invalid", "detail": "sem token"})
                        continue
                    try:
                        url = "https://api.elevenlabs.io/v1/user/subscription"
                        req = urllib.request.Request(url, headers={"xi-api-key": token})
                        resp = urllib.request.urlopen(req, timeout=8)
                        data = json.loads(resp.read())
                        remaining = data.get("character_limit", 0) - data.get("character_count", 0)
                        eleven_results.append({"id": name, "status": "ok", "detail": f"{remaining} chars left"})
                    except urllib.error.HTTPError as e:
                        eleven_results.append({"id": name, "status": "error", "detail": f"HTTP {e.code}"})
                    except Exception as e:
                        eleven_results.append({"id": name, "status": "timeout", "detail": str(e)[:30]})

            with _keys_lock:
                _keys_health["gemini"] = gemini_results
                _keys_health["eleven"] = eleven_results
                _keys_health["last_check"] = _dt.now().strftime("%H:%M:%S")
                _keys_health["checking"] = False

        except Exception:
            with _keys_lock:
                _keys_health["checking"] = False

        time.sleep(300)  # Re-check a cada 5 minutos

def _gpu_monitor_loop():
    global _gpu_pct_cache
    while True:
        try:
            r = subprocess.run(
                ['powershell', '-ExecutionPolicy', 'Bypass', '-Command',
                 "(Get-Counter '\\GPU Engine(*)\\Utilization Percentage' -ErrorAction Stop).CounterSamples | "
                 "Measure-Object -Property CookedValue -Sum | Select-Object -ExpandProperty Sum"],
                capture_output=True, text=False, timeout=8)
            stdout = r.stdout.decode('cp1252', errors='replace') if r.stdout else ''
            if r.returncode == 0 and stdout.strip():
                with _gpu_lock:
                    _gpu_pct_cache = round(float(stdout.strip()), 1)
        except Exception:
            pass
        time.sleep(5)

def _humanizar_linhas(linhas):
    """Converte linhas técnicas do log em mensagens legíveis pro painel."""
    result = []
    for raw in linhas:
        msg = raw
        if "[ensemble] lote" in raw:
            m = re.search(r"lote (\d+)-(\d+)/(\d+)", raw)
            if m:
                msg = f"Gerando narração... lote {m.group(1)}-{m.group(2)} de {m.group(3)} painéis"
        elif "[ensemble] verdade lida" in raw:
            msg = "Lendo balões dos painéis..."
        elif "[ensemble] sem auditor" in raw:
            msg = "Auditor indisponível, usando melhor candidato"
        elif "[ensemble] auditado" in raw:
            msg = "Narração auditada com sucesso"
        elif "TTS:" in raw and "[CACHE]" in raw:
            m = re.search(r"TTS: (\S+)", raw)
            persona = m.group(1) if m else "?"
            msg = f"Áudio do cache: {persona}"
        elif "TTS:" in raw and "[NOVO]" in raw:
            m = re.search(r"TTS: (\S+)", raw)
            persona = m.group(1) if m else "?"
            msg = f"Gerando áudio novo: {persona}"
        elif "Clip " in raw and "painel=" in raw:
            m = re.search(r"Clip (\d+)/(\d+).*persona=(\S+)", raw)
            if m:
                msg = f"Montando clip {m.group(1)}/{m.group(2)} ({m.group(3)})"
        elif "Meme inserido" in raw:
            msg = "Meme inserido no vídeo"
        elif "Censura visual:" in raw and "processando" in raw:
            m = re.search(r"(\d+) painéis", raw)
            n = m.group(1) if m else "?"
            msg = f"Aplicando censura em {n} painéis +18"
        elif "panel_" in raw and "score=" in raw:
            m = re.search(r"(panel_\d+).*?(leve|forte).*?score=([\d.]+)", raw)
            if m:
                msg = f"Censurado {m.group(1)} ({m.group(2)}, score {m.group(3)})"
        elif "Censura visual:" in raw and "censurados" in raw:
            msg = "Censura visual concluída"
        elif "Concatenando" in raw:
            m = re.search(r"(\d+) clips", raw)
            n = m.group(1) if m else "?"
            msg = f"Juntando {n} clips com transições"
        elif "xfade" in raw and "falhou" in raw:
            msg = "Transição avançada falhou, usando fallback"
        elif "[TRILHA]" in raw and "Bloco" in raw:
            m = re.search(r"Bloco (\d+)/(\d+).*?→ (.+?)$", raw)
            if m:
                trilha = m.group(3).split(".")[0][:30]
                msg = f"Trilha {m.group(1)}/{m.group(2)}: {trilha}"
        elif "Trilha dinâmica adicionada" in raw:
            msg = "Trilha sonora aplicada"
        elif "Legenda curta" in raw:
            m = re.search(r"(\d+) cards", raw)
            n = m.group(1) if m else "?"
            msg = f"Gerando {n} legendas karaoke"
        elif "Legendas + watermark" in raw:
            msg = "Legendas e marca d'água aplicadas"
        elif "Vídeo final:" in raw:
            m = re.search(r"(\d+\.?\d*) MB", raw)
            sz = m.group(1) if m else "?"
            msg = f"Vídeo principal pronto ({sz} MB)"
        elif "Versão censurada:" in raw:
            msg = "Versão censurada finalizada"
        elif "Auto-validação: APROVADO" in raw:
            msg = "Validação automática: APROVADO"
        elif "Vídeo pronto:" in raw:
            msg = "Produção completa! Pronto pra publicar"
        elif "Pipeline:" in raw:
            m = re.search(r"Pipeline: (.+?) \((\d+) painéis\)", raw)
            if m:
                msg = f"Iniciando: {m.group(1)} ({m.group(2)} painéis)"
        elif "Pulando" in raw and "painel" in raw:
            msg = "Removendo créditos/capa..."
        elif "Gemini LLM HTTP" in raw:
            msg = "Gemini indisponível, rotacionando..."
        elif "claude" in raw.lower() and "erro" in raw.lower():
            msg = "Auditor Claude offline, usando fallback"
        else:
            msg = re.sub(r"^\[\d{2}:\d{2}:\d{2}\]\s*", "", msg)
            msg = msg[:80]
        result.append(msg)
    return result

def main():
    # Proteção contra instâncias duplicadas
    import socket
    test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        test_sock.bind(("", 8080))
        test_sock.close()
    except OSError:
        print("ERRO: Porta 8080 já em uso — outra instância do painel está rodando. Saindo.")
        sys.exit(1)

    # GPU monitor thread
    _gpu_t = threading.Thread(target=_gpu_monitor_loop, daemon=True)
    _gpu_t.start()

    # Keys health check thread
    _keys_t = threading.Thread(target=_keys_health_check, daemon=True)
    _keys_t.start()

    last_net_io = psutil.net_io_counters()
    last_net_time = time.time()

    # Roda o servidor local em thread separada
    th = threading.Thread(target=serve_html, daemon=True)
    th.start()

    print("\n===========================================")
    print("Painel HTML gerado!")
    print("ABRA SEU NAVEGADOR EM: http://localhost:8080")
    print("===========================================\n")
    print("A tela da janela de comando ficará vazia. O monitoramento acontece no navegador.")

    while True:
        try:
            log_path = find_latest_log()
            recent_vids = get_recent_videos()
            info = parse_log(log_path) if log_path else None

            # Hora da última modificação do log
            from datetime import datetime as _dt
            log_last_modified = ""
            if log_path and log_path.exists():
                mtime = log_path.stat().st_mtime
                log_last_modified = _dt.fromtimestamp(mtime).strftime("%H:%M:%S")

            if not info:
                info = {"linhas_recentes": [], "lista_caps": [], "caps_concluidos": [], "obra": "?", "cap_atual": "?", "cap_pct": 0, "tts_cache":0, "tts_new":0, "cap_fase": "...", "ultima_img": None, "personas": Counter(), "sfx_count": 0, "memes_count": 0, "censura_count": 0, "censura_n2": 0, "erros_vistos": 0, "ult_atividade": "Aguardando..."}

            api_radar = check_gemini_radar()
            # Limpar Rich markup → texto puro (frontend usa textContent)
            api_st_txt = api_radar["status_html"]
            for tag in ("[bold red]", "[/bold red]", "[bold yellow]", "[/bold yellow]",
                        "[bold green]", "[/bold green]", "[dim]", "[/dim]"):
                api_st_txt = api_st_txt.replace(tag, "")

            net, last_net_time, dn, up = psutil.net_io_counters(), time.time(), 0, 0
            dt = last_net_time - (time.time() - 2)
            dn = (net.bytes_recv - last_net_io.bytes_recv) / 2 / 1024 / 1024
            up = (net.bytes_sent - last_net_io.bytes_sent) / 2 / 1024 / 1024
            last_net_io = net

            worker_online = False
            worker_cores = "?"
            try:
                if worker_client:
                    h = worker_client.health("192.168.18.7", 8771, timeout=0.8)
                    if h and h.get("ok"):
                        worker_online = True
                        worker_cores = h.get("cores", "?")
            except: pass

            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory()
            disk = psutil.disk_usage('D:\\')

            # GPU (lido pela thread de background)
            with _gpu_lock:
                gpu_pct = _gpu_pct_cache

            # ffmpeg ativos
            ffmpeg_count = len([p for p in psutil.process_iter(['name'])
                               if 'ffmpeg' in (p.info['name'] or '').lower()])

            # Swap
            swap = psutil.swap_memory()

            # Fila e Tempo
            lista = info.get("lista_caps", [])
            atual = info.get("cap_atual", 0)
            totais = len(lista) if lista else 1
            feitos = len(info.get("caps_concluidos", []))
            tm = 38 * 60  # tempo médio real observado (~38min/cap)
            eta_l = format_eta(max(0, (totais - feitos) * tm))
            cap_pct = info.get("cap_pct", 0)
            # ETA baseada no tempo real do log (mtime inicio vs agora)
            cap_eta = "00m 00s"
            if cap_pct > 0 and cap_pct < 100 and log_path and log_path.exists():
                elapsed = time.time() - log_path.stat().st_ctime
                if elapsed > 10 and cap_pct > 2:
                    remaining = (elapsed / cap_pct) * (100 - cap_pct)
                    cap_eta = format_eta(int(remaining))
                else:
                    cap_eta = format_eta(int((100 - cap_pct) / 100 * tm))

            # Se roda solo (sem queue-runner), construir lista a partir do disco
            if not lista and atual:
                obra_slug = re.sub(r"[^a-z0-9]+", "-", info.get("obra", "?").lower()).strip("-")
                obra_vdir = PROJECT_DIR / "workspace" / "videos" / obra_slug
                if not obra_vdir.exists():
                    videos_base = PROJECT_DIR / "workspace" / "videos"
                    if videos_base.exists():
                        best_dir = None
                        best_count = 0
                        for d in videos_base.iterdir():
                            if not d.is_dir():
                                continue
                            cap_subs = [s for s in d.iterdir() if s.is_dir() and s.name.startswith("cap") and s.name[3:].isdigit()]
                            if len(cap_subs) > best_count:
                                best_count = len(cap_subs)
                                best_dir = d
                        if best_dir:
                            obra_vdir = best_dir
                if obra_vdir.exists():
                    disk_caps = sorted([int(d.name.replace("cap","")) for d in obra_vdir.iterdir()
                                       if d.is_dir() and d.name.startswith("cap") and d.name[3:].isdigit()])
                    if disk_caps:
                        lista = disk_caps
                        feitos = len([c for c in disk_caps if c != atual])
                        totais = len(disk_caps)

            recent_caps = lista if lista else ([atual] if atual else [])

            re_vid_out = []
            for v in (recent_vids or [])[:12]:
                folder_path = str(v.parent.resolve()).replace('\\', '/')
                video_path = str(v.resolve()).replace('\\', '/')
                size = f"{(v.stat().st_size / (1024*1024)):.1f}MB"
                parts = v.parts
                if "videos" in parts:
                    idx_v = parts.index("videos")
                    sp = parts[idx_v+1:]
                    if len(sp) >= 4:
                        name = f"CAP {sp[1].upper().replace('CAP','')} → {sp[3].upper()}"
                    elif len(sp) == 1:
                        name = sp[0][:40] + ("..." if len(sp[0])>40 else "")
                    else:
                        name = "/".join(sp)
                else:
                    name = v.name
                re_vid_out.append({"name": name, "video": video_path, "folder": folder_path, "size": size})

            personas_list = [{"name": p, "count": c} for p, c in info.get("personas", Counter()).most_common(3)]

            # Converte a ultima_img para Base64 para exibir no navegador
            img_b64 = image_to_base64(info.get("ultima_img"))

            # Comandos ativos (botões controle) — geral + per-process
            commands_active = {
                "pause": (PROJECT_DIR / "COMMAND_PAUSE.txt").exists(),
                "skip": (PROJECT_DIR / "COMMAND_SKIP.txt").exists(),
                "stop": (PROJECT_DIR / "COMMAND_STOP.txt").exists(),
                "pause_audio": (PROJECT_DIR / "COMMAND_PAUSE_AUDIO.txt").exists(),
                "skip_audio": (PROJECT_DIR / "COMMAND_SKIP_AUDIO.txt").exists(),
                "stop_audio": (PROJECT_DIR / "COMMAND_STOP_AUDIO.txt").exists(),
                "pause_video": (PROJECT_DIR / "COMMAND_PAUSE_VIDEO.txt").exists(),
                "skip_video": (PROJECT_DIR / "COMMAND_SKIP_VIDEO.txt").exists(),
                "stop_video": (PROJECT_DIR / "COMMAND_STOP_VIDEO.txt").exists(),
                "pause_worker": (PROJECT_DIR / "COMMAND_PAUSE_WORKER.txt").exists(),
                "skip_worker": (PROJECT_DIR / "COMMAND_SKIP_WORKER.txt").exists(),
                "stop_worker": (PROJECT_DIR / "COMMAND_STOP_WORKER.txt").exists(),
            }

            # Detectar processo de áudio ativo (parsear log)
            audio_status = {"active": False, "panel": "", "persona": "", "voice": "", "progress": ""}
            video_renders = []
            if info.get("linhas_recentes"):
                for line in reversed(info["linhas_recentes"]):
                    if not audio_status["active"] and ("TTS:" in line or "Pre-aquecimento" in line):
                        audio_status["active"] = True
                        audio_status["progress"] = line.strip()[:80]
                        import re as _re
                        m = _re.search(r"TTS:\s*(\S+)\s*\(([^)]+)\)", line)
                        if m:
                            audio_status["persona"] = m.group(1)
                            audio_status["voice"] = m.group(2)

            # Detectar ffmpeg ativos com detalhes
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
                try:
                    if 'ffmpeg' in (proc.info['name'] or '').lower():
                        cmdline = proc.info.get('cmdline') or []
                        output_file = ""
                        for i, arg in enumerate(cmdline):
                            if arg in ('-o', '-y') and i + 1 < len(cmdline) and cmdline[i+1].endswith('.mp4'):
                                output_file = cmdline[i+1]
                            elif arg.endswith('.mp4') and i == len(cmdline) - 1:
                                output_file = arg
                        elapsed = int(time.time() - (proc.info.get('create_time') or time.time()))
                        video_renders.append({
                            "pid": proc.info['pid'],
                            "output": os.path.basename(output_file) if output_file else "renderizando...",
                            "elapsed": format_eta(elapsed)
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            # Worker task — tentar pegar mais info
            worker_task_info = None
            if worker_online:
                try:
                    factory_state = PROJECT_DIR / "workspace" / "factory_state"
                    if factory_state.exists():
                        running = [f.stem.replace('.audio_ready', '') for f in factory_state.glob("*.running")]
                        if running:
                            worker_task_info = f"Gerando: {running[0]}"
                except Exception:
                    pass

            # Cap paths (links pra abrir vídeo/pasta)
            cap_paths = {}
            obra_slug = re.sub(r"[^a-z0-9]+", "-", info.get("obra", "?").lower()).strip("-")
            videos_dir = PROJECT_DIR / "workspace" / "videos"
            for c in recent_caps:
                # Tenta estrutura organizada: videos/{obra}/cap{XX}/
                cap_folder = videos_dir / obra_slug / f"cap{c:02d}"
                if cap_folder.exists():
                    mp4s = list(cap_folder.rglob("*.mp4"))
                    mp4s.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                    cap_paths[c] = {
                        "folder": str(cap_folder).replace("\\", "/"),
                        "video": str(mp4s[0]).replace("\\", "/") if mp4s else None
                    }
                else:
                    # Busca arquivos soltos na raiz de videos/ com cap no nome
                    patterns = [f"*cap*{c:02d}*ULTIMO*.mp4", f"*cap*tulo-{c}*ULTIMO*.mp4", f"*cap*tulo-{c:02d}*ULTIMO*.mp4"]
                    found_mp4s = []
                    for pat in patterns:
                        found_mp4s.extend(videos_dir.glob(pat))
                    if found_mp4s:
                        found_mp4s.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                        cap_paths[c] = {
                            "folder": str(videos_dir).replace("\\", "/"),
                            "video": str(found_mp4s[0]).replace("\\", "/")
                        }

            # Stats extras (queue_state + disco)
            stats_avg_time = "N/A"
            stats_video_count = 0
            stats_disk_videos = "..."
            try:
                if QUEUE_STATE.exists():
                    qs = json.loads(QUEUE_STATE.read_text(encoding="utf-8"))
                    all_ts = []
                    for obra_data in qs.values():
                        for cap_data in obra_data.values():
                            if cap_data.get("status") == "ok" and cap_data.get("ts"):
                                all_ts.append(cap_data["ts"])
                    if len(all_ts) >= 2:
                        from datetime import datetime as _dt
                        sorted_ts = sorted(all_ts)
                        deltas = []
                        for i in range(1, len(sorted_ts)):
                            t1 = _dt.fromisoformat(sorted_ts[i-1])
                            t2 = _dt.fromisoformat(sorted_ts[i])
                            d = (t2 - t1).total_seconds()
                            if 60 < d < 7200:
                                deltas.append(d)
                        if deltas:
                            avg = sum(deltas) / len(deltas)
                            stats_avg_time = format_eta(int(avg))
            except Exception:
                pass
            try:
                vdir = PROJECT_DIR / "workspace" / "videos"
                if vdir.exists():
                    all_mp4 = list(vdir.rglob("*.mp4"))
                    stats_video_count = len(all_mp4)
                    total_bytes = sum(f.stat().st_size for f in all_mp4)
                    stats_disk_videos = f"{total_bytes / (1024**3):.1f} GB"
            except Exception:
                pass

            with _keys_lock:
                keys_health_snap = {
                    "gemini": list(_keys_health.get("gemini", [])),
                    "eleven": list(_keys_health.get("eleven", [])),
                    "last_check": _keys_health.get("last_check", ""),
                    "checking": _keys_health.get("checking", False),
                }

            data = {
                "log_name": log_path.name if log_path else None,
                "log_last_modified": log_last_modified,
                "cpu": cpu, "cpu_cores": psutil.cpu_count(), "cpu_model": _CPU_MODEL,
                "ram": ram.percent, "ram_total_gb": _RAM_TOTAL_GB,
                "disk_free": f"{disk.free / (1024**3):.1f}",
                "net_down": f"{dn:.1f}", "net_up": f"{up:.1f}",
                "gpu_pct": gpu_pct, "ffmpeg_count": ffmpeg_count,
                "swap_used": f"{swap.used // (1024**2)}",
                "swap_total": f"{swap.total // (1024**2)}",
                "worker_online": worker_online, "worker_cores": worker_cores,
                "worker_task": None,

                "commands_active": commands_active,
                "cap_paths": cap_paths,
                "stats_avg_time": stats_avg_time,
                "stats_video_count": stats_video_count,
                "stats_disk_videos": stats_disk_videos,
                "audio_status": audio_status,
                "video_renders": video_renders,
                "worker_task_info": worker_task_info,

                "keys_health": keys_health_snap,

                "obra": info.get("obra", "?"),
                "feitos": feitos, "totais": totais, "eta_lote": eta_l,
                "minutos_gerados": feitos * 8 if feitos else 0,
                "lista_recentes": recent_caps,
                "concluidos": info.get("caps_concluidos", []),
                "cap_atual": atual,

                "api_status": api_st_txt,
                "api_429": api_radar["errors_429"],
                "api_rots": api_radar["rotations"],
                "api_engine": api_radar["engine_atual"],
                "api_last_err": api_radar.get("gemini_last_err", ""),
                "gemini_keys_total": api_radar["gemini_keys_total"],
                "gemini_keys_blocked": api_radar["gemini_keys_blocked"],
                "eleven_keys_total": api_radar["eleven_keys_total"],
                "eleven_keys_used": api_radar["eleven_keys_used"],

                "ultima_img_b64": img_b64,

                "cap_fase": info.get("cap_fase", ""),
                "cap_progresso_txt": info.get("cap_progresso_txt", ""),
                "cap_pct": cap_pct,
                "cap_eta": cap_eta,
                "tts_cache": info.get("tts_cache", 0),
                "tts_new": info.get("tts_new", 0),
                "tts_total": info.get("tts_cache", 0) + info.get("tts_new", 0),
                "tts_pct": round(info.get("tts_cache", 0) / max(1, info.get("tts_cache", 0) + info.get("tts_new", 0)) * 100),
                "ult_atividade": info.get("ult_atividade", ""),
                "linhas_recentes": _humanizar_linhas(info.get("linhas_recentes", [])[-8:]),

                "recent_videos": re_vid_out,

                "erros_vistos": info.get("erros_vistos", 0),
                "censura_count": info.get("censura_count", 0),
                "censura_n2": info.get("censura_n2", 0),
                "sfx_count": info.get("sfx_count", 0),
                "memes_count": info.get("memes_count", 0),

                "personas": personas_list
            }

            # Separar imagem do payload principal (419KB a cada 1s trava o browser)
            img_payload = {}
            if data.get("ultima_img_b64"):
                img_payload = {"ultima_img_b64": data.pop("ultima_img_b64")}

            # Gravar na memória (thread-safe) — o do_GET serve daqui
            global _live_data_json, _live_img_json
            data_bytes = json.dumps(data).encode("utf-8")
            img_bytes = json.dumps(img_payload).encode("utf-8")
            with _live_data_lock:
                _live_data_json = data_bytes
                _live_img_json = img_bytes

            # Disco como fallback (debug)
            try:
                with open(DATA_FILE, "w", encoding="utf-8") as fw:
                    fw.write(data_bytes.decode("utf-8"))
            except Exception:
                pass

            time.sleep(1)

        except Exception as e:
            print('Loop error:', e)
            time.sleep(2)

if __name__ == "__main__":
    main()
