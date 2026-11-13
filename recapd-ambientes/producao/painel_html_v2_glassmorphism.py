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

# In-memory data store (thread-safe) — evita race condition de leitura/escrita no disco
_live_data_json = b'{}'
_live_img_json = b'{}'
_live_data_lock = threading.Lock()


class DashboardHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
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
            path = body.get('path', '')
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

html_template = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Hipercool Control Station</title>
<style>
:root {
  --bg: #000000;
  --card-bg: rgba(15, 18, 25, 0.85);
  --card-border: rgba(255,255,255,0.06);
  --accent-cyan: #22d3ee;
  --accent-green: #34d399;
  --accent-yellow: #fbbf24;
  --accent-red: #f87171;
  --accent-purple: #a78bfa;
  --text: #e2e8f0;
  --text-dim: #94a3b8;
  --font: 'Inter','SF Pro Display',-apple-system,system-ui,'Segoe UI',sans-serif;
  --mono: 'JetBrains Mono','Fira Code','Cascadia Code',monospace;
  --glow-cyan: 0 0 20px rgba(34,211,238,0.3);
  --glow-green: 0 0 20px rgba(52,211,153,0.3);
  --glow-red: 0 0 20px rgba(248,113,113,0.3);
  --glow-purple: 0 0 20px rgba(167,139,250,0.3);
}
* { margin:0; padding:0; box-sizing:border-box; }
body { background:var(--bg); color:var(--text); font-family:var(--font); min-height:100vh; overflow-x:hidden; }
.grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(380px,1fr)); gap:16px; padding:16px; max-width:1800px; margin:0 auto; }
.card { background:var(--card-bg); backdrop-filter:blur(16px); border:1px solid var(--card-border); border-radius:14px; padding:16px; transition:box-shadow 0.3s ease, border-color 0.3s ease; position:relative; overflow:hidden; }
.card:hover { border-color:rgba(255,255,255,0.12); }
.card h2 { font-size:13px; text-transform:uppercase; letter-spacing:1.2px; color:var(--text-dim); margin-bottom:12px; font-weight:600; }
.card.glow-active { animation:pulse-glow 2s ease-in-out infinite; }
.mono { font-family:var(--mono); font-size:13px; }
.badge { display:inline-flex; align-items:center; gap:4px; padding:3px 8px; border-radius:6px; font-size:11px; font-family:var(--mono); background:rgba(255,255,255,0.05); }
.badge.green { color:var(--accent-green); background:rgba(52,211,153,0.1); }
.badge.red { color:var(--accent-red); background:rgba(248,113,113,0.1); }
.badge.yellow { color:var(--accent-yellow); background:rgba(251,191,36,0.1); }
.badge.cyan { color:var(--accent-cyan); background:rgba(34,211,238,0.1); }
.badge.purple { color:var(--accent-purple); background:rgba(167,139,250,0.1); }

/* Header */
#header { display:flex; align-items:center; justify-content:space-between; padding:12px 20px; border-bottom:1px solid var(--card-border); position:sticky; top:0; z-index:100; background:rgba(0,0,0,0.92); backdrop-filter:blur(12px); }
#header h1 { font-size:15px; letter-spacing:2px; font-weight:700; background:linear-gradient(90deg,var(--accent-cyan),var(--accent-purple)); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
#header .right { display:flex; align-items:center; gap:14px; font-size:12px; color:var(--text-dim); }
#conn-dot { width:8px; height:8px; border-radius:50%; background:var(--accent-green); box-shadow:var(--glow-green); transition:background 0.3s; }
#conn-dot.off { background:var(--accent-red); box-shadow:var(--glow-red); }

/* Progress bar */
.pbar-wrap { background:rgba(255,255,255,0.05); border-radius:8px; height:22px; overflow:hidden; position:relative; }
.pbar-fill { height:100%; border-radius:8px; background:linear-gradient(90deg,var(--accent-cyan),var(--accent-purple)); transition:width 0.4s ease; position:relative; }
.pbar-fill::after { content:''; position:absolute; top:0; left:0; right:0; bottom:0; background:linear-gradient(90deg,transparent,rgba(255,255,255,0.3),transparent); animation:shimmer 2s infinite; }
.pbar-text { position:absolute; top:0; left:0; right:0; bottom:0; display:flex; align-items:center; justify-content:center; font-size:11px; font-family:var(--mono); font-weight:600; color:#fff; text-shadow:0 1px 3px rgba(0,0,0,0.5); }

/* Mini progress */
.mini-bar { height:4px; border-radius:2px; background:rgba(255,255,255,0.08); overflow:hidden; flex:1; }
.mini-bar-fill { height:100%; border-radius:2px; transition:width 0.3s; }

/* Buttons */
.btn { border:none; padding:6px 12px; border-radius:7px; font-size:11px; font-weight:600; cursor:pointer; transition:all 0.2s ease; font-family:var(--font); }
.btn-pause { background:rgba(251,191,36,0.15); color:var(--accent-yellow); }
.btn-pause:hover { background:rgba(251,191,36,0.3); }
.btn-pause.active { background:var(--accent-yellow); color:#000; }
.btn-skip { background:rgba(34,211,238,0.15); color:var(--accent-cyan); }
.btn-skip:hover { background:rgba(34,211,238,0.3); }
.btn-stop { background:rgba(248,113,113,0.15); color:var(--accent-red); }
.btn-stop:hover { background:rgba(248,113,113,0.3); }
.btn-action { background:rgba(255,255,255,0.06); color:var(--text); font-size:13px; padding:4px 8px; }
.btn-action:hover { background:rgba(255,255,255,0.12); }

/* Log area */
.log-box { background:rgba(0,0,0,0.4); border-radius:8px; padding:8px; max-height:200px; overflow-y:auto; scroll-behavior:smooth; font-family:var(--mono); font-size:11px; line-height:1.6; }
.log-box::-webkit-scrollbar { width:4px; }
.log-box::-webkit-scrollbar-thumb { background:rgba(255,255,255,0.1); border-radius:2px; }
.log-line { padding:1px 4px; border-radius:3px; }
.log-line.error { color:var(--accent-red); background:rgba(248,113,113,0.05); }
.log-line.tts { color:var(--accent-purple); }
.log-line.clip { color:var(--accent-cyan); }

/* Keys grid */
.keys-grid { display:flex; flex-wrap:wrap; gap:4px; }
.key-dot { width:14px; height:14px; border-radius:4px; cursor:pointer; transition:transform 0.2s, box-shadow 0.2s; position:relative; }
.key-dot:hover { transform:scale(1.5); z-index:10; }
.key-dot.ok { background:var(--accent-green); }
.key-dot.quota { background:var(--accent-yellow); }
.key-dot.blocked { background:var(--accent-red); }
.key-tooltip { position:absolute; bottom:120%; left:50%; transform:translateX(-50%); background:#1a1a2e; border:1px solid var(--card-border); padding:6px 10px; border-radius:6px; font-size:10px; white-space:nowrap; display:none; z-index:20; color:var(--text); }
.key-dot:hover .key-tooltip { display:block; }

/* Toast */
#toast-area { position:fixed; top:60px; right:16px; z-index:200; display:flex; flex-direction:column; gap:8px; }
.toast { background:rgba(15,18,25,0.95); border:1px solid var(--accent-green); border-radius:10px; padding:12px 16px; font-size:12px; animation:slide-in 0.3s ease; box-shadow:var(--glow-green); }
.toast.hiding { opacity:0; transform:translateX(100px); transition:all 0.3s ease; }

/* HW badges */
.hw-row { display:flex; flex-wrap:wrap; gap:8px; }
.hw-item { display:flex; align-items:center; gap:6px; background:rgba(255,255,255,0.03); padding:6px 10px; border-radius:8px; min-width:100px; }
.hw-item .label { font-size:10px; color:var(--text-dim); text-transform:uppercase; }
.hw-item .val { font-family:var(--mono); font-size:13px; font-weight:600; }

/* Controls grid */
.ctrl-section { display:grid; grid-template-columns:1fr 1fr; gap:8px; }
.ctrl-group { display:flex; flex-direction:column; gap:6px; padding:10px; background:rgba(255,255,255,0.02); border-radius:8px; }
.ctrl-group .ctrl-title { font-size:11px; color:var(--text-dim); display:flex; align-items:center; gap:6px; }
.ctrl-group .ctrl-btns { display:flex; gap:4px; }
.ctrl-status { width:6px; height:6px; border-radius:50%; background:var(--accent-green); }
.ctrl-status.paused { background:var(--accent-yellow); }
.ctrl-status.stopped { background:var(--accent-red); }

/* Queue caps */
.cap-list { display:flex; flex-wrap:wrap; gap:6px; }
.cap-item { display:flex; align-items:center; gap:4px; padding:4px 8px; border-radius:6px; font-size:12px; font-family:var(--mono); background:rgba(255,255,255,0.04); }
.cap-item.done { border-left:3px solid var(--accent-green); }
.cap-item.active { border-left:3px solid var(--accent-cyan); background:rgba(34,211,238,0.08); }
.cap-item.pending { border-left:3px solid var(--text-dim); }

/* Video list */
.video-list { max-height:180px; overflow-y:auto; display:flex; flex-direction:column; gap:4px; }
.video-item { display:flex; align-items:center; justify-content:space-between; padding:6px 8px; border-radius:6px; background:rgba(255,255,255,0.03); font-size:12px; }

/* Stats grid */
.stats-grid { display:grid; grid-template-columns:1fr 1fr; gap:8px; }
.stat-item { text-align:center; padding:8px; background:rgba(255,255,255,0.03); border-radius:8px; }
.stat-item .stat-val { font-family:var(--mono); font-size:18px; font-weight:700; }
.stat-item .stat-label { font-size:10px; color:var(--text-dim); margin-top:2px; }

/* Mini TV */
#tv-frame img { width:100%; border-radius:8px; opacity:0.9; }

/* Filter buttons */
.log-filters { display:flex; gap:4px; margin-bottom:6px; }
.log-filters .btn { font-size:10px; padding:3px 8px; }
.log-filters .btn.active { background:rgba(34,211,238,0.2); color:var(--accent-cyan); }

/* Updated animation */
.updated { animation:fade-update 0.4s ease; }

/* Worker */
.worker-info { display:flex; align-items:center; gap:10px; }
.worker-dot { width:10px; height:10px; border-radius:50%; }
.worker-dot.online { background:var(--accent-green); box-shadow:var(--glow-green); }
.worker-dot.offline { background:var(--accent-red); box-shadow:var(--glow-red); }

/* Animations */
@keyframes shimmer { 0%{transform:translateX(-100%)} 100%{transform:translateX(100%)} }
@keyframes pulse-glow { 0%,100%{box-shadow:0 0 5px rgba(34,211,238,0.2), inset 0 0 5px rgba(34,211,238,0.05)} 50%{box-shadow:0 0 20px rgba(34,211,238,0.4), inset 0 0 10px rgba(34,211,238,0.1)} }
@keyframes slide-in { from{opacity:0;transform:translateX(100px)} to{opacity:1;transform:translateX(0)} }
@keyframes fade-update { 0%{opacity:0.4} 100%{opacity:1} }

/* Responsive */
@media(max-width:860px) { .grid{grid-template-columns:1fr} .ctrl-section{grid-template-columns:1fr} }
</style>
</head>
<body>
<div id="header">
  <h1>⚡ HIPERCOOL CONTROL STATION</h1>
  <div class="right">
    <span id="clock" class="mono">--:--:--</span>
    <div id="conn-dot"></div>
  </div>
</div>

<div id="toast-area"></div>

<div class="grid">

  <!-- Hardware Metrics -->
  <div class="card" id="sys-hw">
    <h2>🖥️ Hardware</h2>
    <div class="hw-row">
      <div class="hw-item"><span class="label">CPU</span><span class="val" id="hw-cpu">--%</span><div class="mini-bar"><div class="mini-bar-fill" id="hw-cpu-bar" style="width:0%;background:var(--accent-cyan)"></div></div></div>
      <div class="hw-item"><span class="label">RAM</span><span class="val" id="hw-ram">--%</span><div class="mini-bar"><div class="mini-bar-fill" id="hw-ram-bar" style="width:0%;background:var(--accent-purple)"></div></div></div>
      <div class="hw-item"><span class="label">GPU</span><span class="val" id="hw-gpu">--%</span><div class="mini-bar"><div class="mini-bar-fill" id="hw-gpu-bar" style="width:0%;background:var(--accent-green)"></div></div></div>
      <div class="hw-item"><span class="label">SWAP</span><span class="val" id="hw-swap">--</span></div>
      <div class="hw-item"><span class="label">DISCO</span><span class="val" id="hw-disk">-- GB</span></div>
      <div class="hw-item"><span class="label">FFmpeg</span><span class="val" id="hw-ffmpeg">0</span></div>
      <div class="hw-item"><span class="label">↓</span><span class="val" id="hw-net-down">0</span></div>
      <div class="hw-item"><span class="label">↑</span><span class="val" id="hw-net-up">0</span></div>
    </div>
  </div>

  <!-- Queue Status -->
  <div class="card" id="fila-geral">
    <h2>📋 Fila de Produção</h2>
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px">
      <span style="font-size:14px;font-weight:600" id="fila-obra">--</span>
      <span class="badge cyan" id="fila-progresso">0/0</span>
      <span class="badge purple" id="fila-eta">ETA --</span>
    </div>
    <div class="cap-list" id="fila-caps"></div>
  </div>

  <!-- Active Monitor -->
  <div class="card glow-active" id="monitor-ativo">
    <h2>🔥 Monitor Ativo</h2>
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">
      <span class="badge cyan" id="mon-cap">Cap --</span>
      <span class="badge purple" id="mon-fase">--</span>
      <span class="badge green" id="mon-eta">ETA --</span>
    </div>
    <div class="pbar-wrap" style="margin-bottom:8px">
      <div class="pbar-fill" id="mon-pbar" style="width:0%"></div>
      <div class="pbar-text" id="mon-pbar-text">0%</div>
    </div>
    <div style="display:flex;gap:8px;margin-bottom:8px">
      <span class="badge green" id="mon-tts-cache">Cache: --</span>
      <span class="badge yellow" id="mon-tts-new">Novos: --</span>
      <span class="badge" id="mon-tts-total">Total: --</span>
    </div>
    <div class="log-filters">
      <button class="btn active" data-filter="all">Todos</button>
      <button class="btn" data-filter="error">Erros</button>
      <button class="btn" data-filter="tts">TTS</button>
      <button class="btn" data-filter="clip">Clips</button>
    </div>
    <div class="log-box" id="sys-log"></div>
  </div>

  <!-- Controls -->
  <div class="card" id="controls">
    <h2>🎛️ Controles</h2>
    <div class="ctrl-section">
      <div class="ctrl-group">
        <div class="ctrl-title"><div class="ctrl-status" id="ctrl-general-status"></div>Geral</div>
        <div class="ctrl-btns">
          <button class="btn btn-pause" id="btn-pause" onclick="sendCmd('pause','all')">⏸ Pausar</button>
          <button class="btn btn-skip" id="btn-skip" onclick="sendCmd('skip','all')">⏭ Pular</button>
          <button class="btn btn-stop" id="btn-stop" onclick="sendCmd('stop','all')">⏹ Parar</button>
        </div>
      </div>
      <div class="ctrl-group">
        <div class="ctrl-title"><div class="ctrl-status" id="ctrl-audio-status"></div>Áudio</div>
        <div class="ctrl-btns">
          <button class="btn btn-pause" id="btn-pause-audio" onclick="sendCmd('pause','audio')">⏸</button>
          <button class="btn btn-skip" id="btn-skip-audio" onclick="sendCmd('skip','audio')">⏭</button>
          <button class="btn btn-stop" id="btn-stop-audio" onclick="sendCmd('stop','audio')">⏹</button>
        </div>
      </div>
      <div class="ctrl-group">
        <div class="ctrl-title"><div class="ctrl-status" id="ctrl-video-status"></div>Vídeo</div>
        <div class="ctrl-btns">
          <button class="btn btn-pause" id="btn-pause-video" onclick="sendCmd('pause','video')">⏸</button>
          <button class="btn btn-skip" id="btn-skip-video" onclick="sendCmd('skip','video')">⏭</button>
          <button class="btn btn-stop" id="btn-stop-video" onclick="sendCmd('stop','video')">⏹</button>
        </div>
      </div>
      <div class="ctrl-group">
        <div class="ctrl-title"><div class="ctrl-status" id="ctrl-worker-status"></div>Worker</div>
        <div class="ctrl-btns">
          <button class="btn btn-pause" id="btn-pause-worker" onclick="sendCmd('pause','worker')">⏸</button>
          <button class="btn btn-skip" id="btn-skip-worker" onclick="sendCmd('skip','worker')">⏭</button>
          <button class="btn btn-stop" id="btn-stop-worker" onclick="sendCmd('stop','worker')">⏹</button>
        </div>
      </div>
    </div>
  </div>

  <!-- API Radar -->
  <div class="card" id="api-radar">
    <h2>📡 API Radar</h2>
    <div style="display:flex;flex-wrap:wrap;gap:8px;align-items:center">
      <span class="badge" id="api-engine">Engine: --</span>
      <span id="api-status-html">--</span>
      <span class="badge yellow" id="api-429">429: 0</span>
      <span class="badge" id="api-rots">Rotações: 0</span>
    </div>
    <div style="margin-top:10px;display:flex;gap:12px;flex-wrap:wrap">
      <div><span class="label" style="font-size:10px;color:var(--text-dim)">Gemini</span> <span class="mono" id="api-gemini-count">--/--</span></div>
      <div><span class="label" style="font-size:10px;color:var(--text-dim)">ElevenLabs</span> <span class="mono" id="api-eleven-count">--/--</span></div>
    </div>
  </div>

  <!-- Keys Dashboard -->
  <div class="card" id="keys-dashboard">
    <h2>🔑 Chaves</h2>
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
      <span class="mono" style="font-size:11px;color:var(--text-dim)" id="keys-last-check">Último check: --</span>
      <button class="btn btn-action" id="keys-refresh-btn" onclick="refreshKeys()">🔄 Atualizar</button>
    </div>
    <div style="margin-bottom:6px;font-size:11px;color:var(--text-dim)">Gemini</div>
    <div class="keys-grid" id="keys-gemini"></div>
    <div style="margin:8px 0 6px;font-size:11px;color:var(--text-dim)">ElevenLabs</div>
    <div class="keys-grid" id="keys-eleven"></div>
  </div>

  <!-- Video Outputs -->
  <div class="card" id="recent-videos">
    <h2>🎬 Vídeos Recentes</h2>
    <div class="video-list" id="video-list"></div>
  </div>

  <!-- Stats -->
  <div class="card" id="stats">
    <h2>📊 Estatísticas</h2>
    <div class="stats-grid">
      <div class="stat-item"><div class="stat-val" id="st-avg-time">--</div><div class="stat-label">Tempo médio/cap</div></div>
      <div class="stat-item"><div class="stat-val" id="st-videos">0</div><div class="stat-label">Vídeos totais</div></div>
      <div class="stat-item"><div class="stat-val" id="st-disk">--</div><div class="stat-label">Disco usado</div></div>
      <div class="stat-item"><div class="stat-val" id="st-minutos">0</div><div class="stat-label">Min. gerados</div></div>
      <div class="stat-item"><div class="stat-val" id="st-erros">0</div><div class="stat-label">Erros</div></div>
      <div class="stat-item"><div class="stat-val" id="st-censura">0</div><div class="stat-label">Censura</div></div>
      <div class="stat-item"><div class="stat-val" id="st-sfx">0</div><div class="stat-label">SFX</div></div>
      <div class="stat-item"><div class="stat-val" id="st-memes">0</div><div class="stat-label">Memes</div></div>
    </div>
    <div style="margin-top:10px">
      <div style="font-size:11px;color:var(--text-dim);margin-bottom:4px">Top Personas</div>
      <div id="st-personas" style="display:flex;flex-wrap:wrap;gap:6px"></div>
    </div>
  </div>

  <!-- Mini TV -->
  <div class="card" id="tv-frame">
    <h2>📺 Último Frame</h2>
    <img id="tv-img" src="" alt="Preview" style="display:none">
    <div id="tv-empty" style="text-align:center;color:var(--text-dim);padding:20px;font-size:12px">Sem preview</div>
  </div>

  <!-- Worker -->
  <div class="card" id="worker-card">
    <h2>⚙️ Worker Remoto</h2>
    <div class="worker-info">
      <div class="worker-dot" id="worker-dot"></div>
      <span id="worker-label" class="mono">--</span>
    </div>
    <div style="margin-top:8px;font-size:12px;color:var(--text-dim)" id="worker-task-info">Nenhuma tarefa</div>
  </div>

</div>

<script>
var D = {}, prevD = {}, logFilter = 'all', prevConcluidos = [];

function $(id) { return document.getElementById(id); }

function sendCmd(action, target) {
  fetch('/api/command', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({action:action, target:target})})
    .then(function(r) { if(r.ok) showToast('Comando: '+action+' → '+target); })
    .catch(function() { showToast('Erro ao enviar comando', true); });
}

function openPath(path) {
  fetch('/api/open', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({path:path})}).catch(function(){});
}

function refreshKeys() {
  var btn = $('keys-refresh-btn');
  btn.textContent = '⏳ Atualizando...';
  btn.disabled = true;
  setTimeout(function() { btn.textContent = '🔄 Atualizar'; btn.disabled = false; }, 3000);
}

function showToast(msg, isError) {
  var t = document.createElement('div');
  t.className = 'toast';
  if(isError) t.style.borderColor = 'var(--accent-red)';
  t.textContent = msg;
  $('toast-area').appendChild(t);
  setTimeout(function() { t.classList.add('hiding'); setTimeout(function() { t.remove(); }, 300); }, 5000);
}

function animateVal(el, newText) {
  if(!el) return;
  if(el.textContent !== newText) { el.textContent = newText; el.classList.add('updated'); setTimeout(function() { el.classList.remove('updated'); }, 400); }
}

function classifyLog(line) {
  var l = line.toLowerCase();
  if(l.includes('erro') || l.includes('error') || l.includes('falha') || l.includes('429')) return 'error';
  if(l.includes('tts') || l.includes('narr')) return 'tts';
  if(l.includes('clip') || l.includes('ffmpeg') || l.includes('render')) return 'clip';
  return '';
}

function setCtrlBtn(id, active) {
  var el = $(id);
  if(el) el.classList.toggle('active', !!active);
}

function updateCtrlStatus(id, paused, stopped) {
  var el = $(id);
  if(!el) return;
  if(stopped) el.className = 'ctrl-status stopped';
  else if(paused) el.className = 'ctrl-status paused';
  else el.className = 'ctrl-status';
}

function renderKeys(container, keys) {
  if(!keys || !keys.length) { container.innerHTML = '<span style="font-size:11px;color:var(--text-dim)">--</span>'; return; }
  container.innerHTML = keys.map(function(k) {
    var st = k.status === 'ok' ? 'ok' : k.status === 'quota' ? 'quota' : 'blocked';
    var label = '#'+(k.id)+' — '+k.status+(k.detail ? ' ('+k.detail+')' : '');
    return '<div class="key-dot '+st+'"><div class="key-tooltip">'+label+'</div></div>';
  }).join('');
}

function updateData() {
  fetch('/data.json').then(function(r){return r.json();}).then(function(data) {
    D = data;
    $('conn-dot').classList.remove('off');
    document.title = (data.cap_pct||0)+'% Cap '+(data.cap_atual||'?')+' — Hipercool';

    // HW
    animateVal($('hw-cpu'), (data.cpu||0)+'%');
    animateVal($('hw-ram'), (data.ram||0)+'%');
    animateVal($('hw-gpu'), (data.gpu_pct||0)+'%');
    animateVal($('hw-swap'), (data.swap_used||0)+'/'+(data.swap_total||0)+'MB');
    animateVal($('hw-disk'), (data.disk_free||'--')+' GB');
    animateVal($('hw-ffmpeg'), String(data.ffmpeg_count||0));
    animateVal($('hw-net-down'), (data.net_down||'0')+' MB/s');
    animateVal($('hw-net-up'), (data.net_up||'0')+' MB/s');
    $('hw-cpu-bar').style.width = (data.cpu||0)+'%';
    $('hw-ram-bar').style.width = (data.ram||0)+'%';
    $('hw-gpu-bar').style.width = (data.gpu_pct||0)+'%';

    // Queue
    animateVal($('fila-obra'), data.obra || '--');
    animateVal($('fila-progresso'), (data.feitos||0)+'/'+(data.totais||0));
    animateVal($('fila-eta'), 'ETA '+(data.eta_lote||'--'));
    var caps = data.lista_recentes || [];
    var done = data.concluidos || [];
    var atual = data.cap_atual;
    $('fila-caps').innerHTML = caps.map(function(c) {
      var st = done.includes(c) ? 'done' : c === atual ? 'active' : 'pending';
      var icon = st==='done'?'✅':st==='active'?'🔥':'⏳';
      var paths = (data.cap_paths||{})[String(c)] || {};
      var btns = paths.video ? '<button class="btn btn-action" onclick="openPath(\''+paths.video.replace(/\\/g,'/')+'\')">▶️</button>' : '';
      var fbtn = paths.folder ? '<button class="btn btn-action" onclick="openPath(\''+paths.folder.replace(/\\/g,'/')+'\')">📁</button>' : '';
      return '<div class="cap-item '+st+'">'+icon+' Cap '+c+' '+btns+fbtn+'</div>';
    }).join('');

    // Toast on cap completion
    if(prevConcluidos.length && done.length > prevConcluidos.length) {
      done.filter(function(c){ return !prevConcluidos.includes(c); }).forEach(function(c){ showToast('✅ Capítulo '+c+' concluído!'); });
    }
    prevConcluidos = done.slice();

    // Monitor
    animateVal($('mon-cap'), 'Cap '+(data.cap_atual||'--'));
    animateVal($('mon-fase'), data.cap_fase||'--');
    animateVal($('mon-eta'), 'ETA '+(data.cap_eta||'--'));
    $('mon-pbar').style.width = (data.cap_pct||0)+'%';
    $('mon-pbar-text').textContent = (data.cap_pct||0)+'% — '+(data.cap_progresso_txt||'');
    animateVal($('mon-tts-cache'), 'Cache: '+(data.tts_cache||0));
    animateVal($('mon-tts-new'), 'Novos: '+(data.tts_new||0));
    animateVal($('mon-tts-total'), 'Total: '+(data.tts_total||0));

    // Log
    var logBox = $('sys-log');
    var lines = data.linhas_recentes || [];
    logBox.innerHTML = lines.map(function(l) {
      var cls = classifyLog(l);
      if(logFilter !== 'all' && cls !== logFilter) return '';
      return '<div class="log-line '+cls+'">'+l+'</div>';
    }).filter(Boolean).join('');
    logBox.scrollTop = logBox.scrollHeight;

    // Controls
    var cmds = data.commands_active || {};
    setCtrlBtn('btn-pause', cmds.pause);
    setCtrlBtn('btn-pause-audio', cmds.pause_audio);
    setCtrlBtn('btn-pause-video', cmds.pause_video);
    setCtrlBtn('btn-pause-worker', cmds.pause_worker);
    updateCtrlStatus('ctrl-general-status', cmds.pause, cmds.stop);
    updateCtrlStatus('ctrl-audio-status', cmds.pause_audio, cmds.stop_audio);
    updateCtrlStatus('ctrl-video-status', cmds.pause_video, cmds.stop_video);
    updateCtrlStatus('ctrl-worker-status', cmds.pause_worker, cmds.stop_worker);

    // API Radar
    animateVal($('api-engine'), 'Engine: '+(data.api_engine||'--'));
    $('api-status-html').innerHTML = data.api_status || '--';
    animateVal($('api-429'), '429: '+(data.api_429||0));
    animateVal($('api-rots'), 'Rotações: '+(data.api_rots||0));
    var gOk = (data.gemini_keys_total||0)-(data.gemini_keys_blocked||0);
    animateVal($('api-gemini-count'), gOk+'/'+(data.gemini_keys_total||0));
    var eOk = (data.eleven_keys_total||0)-(data.eleven_keys_used||0);
    animateVal($('api-eleven-count'), eOk+'/'+(data.eleven_keys_total||0));

    // Keys
    var kh = data.keys_health || {};
    renderKeys($('keys-gemini'), kh.gemini);
    renderKeys($('keys-eleven'), kh.eleven);
    if(kh.last_check) $('keys-last-check').textContent = 'Último check: '+kh.last_check;

    // Videos
    var vids = data.recent_videos || [];
    $('video-list').innerHTML = vids.length ? vids.map(function(v) {
      return '<div class="video-item"><span>'+v.name+' <span class="badge">'+(v.size||'')+'</span></span><span>'
        +'<button class="btn btn-action" onclick="openPath(\''+( v.video||'').replace(/\\/g,'/')+'\')">▶️</button>'
        +'<button class="btn btn-action" onclick="openPath(\''+(v.folder||'').replace(/\\/g,'/')+'\')">📁</button>'
        +'</span></div>';
    }).join('') : '<div style="color:var(--text-dim);font-size:12px;padding:8px">Nenhum vídeo ainda</div>';

    // Stats
    animateVal($('st-avg-time'), data.stats_avg_time||'--');
    animateVal($('st-videos'), String(data.stats_video_count||0));
    animateVal($('st-disk'), data.stats_disk_videos||'--');
    animateVal($('st-minutos'), String(data.minutos_gerados||0));
    animateVal($('st-erros'), String(data.erros_vistos||0));
    animateVal($('st-censura'), (data.censura_count||0)+' (N2: '+(data.censura_n2||0)+')');
    animateVal($('st-sfx'), String(data.sfx_count||0));
    animateVal($('st-memes'), String(data.memes_count||0));
    var personas = data.personas || [];
    $('st-personas').innerHTML = personas.map(function(p){ return '<span class="badge purple">'+p.name+': '+p.count+'</span>'; }).join('');

    // Mini TV — carregado separadamente (imagem pesada, não travar polling)

    // Worker
    var wOn = data.worker_online;
    $('worker-dot').className = 'worker-dot '+(wOn?'online':'offline');
    animateVal($('worker-label'), wOn ? 'Online — '+(data.worker_cores||0)+' cores' : 'Offline');
    $('worker-task-info').textContent = data.worker_task_info || data.worker_task || 'Nenhuma tarefa';

    prevD = data;
  }).catch(function() { $('conn-dot').classList.add('off'); });
}

// Mini TV fetch separado (a cada 5s, não trava o polling de 1s)
function updateImg() {
  fetch('/img.json').then(function(r){return r.json();}).then(function(d){
    if(d.ultima_img_b64) { $('tv-img').src='data:image/jpeg;base64,'+d.ultima_img_b64; $('tv-img').style.display='block'; $('tv-empty').style.display='none'; }
    else { $('tv-img').style.display='none'; $('tv-empty').style.display='block'; }
  }).catch(function(){});
}

// Clock
function updateClock() { $('clock').textContent = new Date().toLocaleTimeString('pt-BR'); }

// Log filters
document.querySelectorAll('.log-filters .btn').forEach(function(btn) {
  btn.addEventListener('click', function() {
    document.querySelectorAll('.log-filters .btn').forEach(function(b){ b.classList.remove('active'); });
    btn.classList.add('active');
    logFilter = btn.dataset.filter;
  });
});

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
  if(e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
  if(e.key === 'p' || e.key === 'P') { sendCmd('pause','all'); e.preventDefault(); }
  else if(e.key === 's' || e.key === 'S') { sendCmd('skip','all'); e.preventDefault(); }
  else if(e.key === 'Escape') { sendCmd('stop','all'); }
});

// Init
updateClock();
setInterval(updateClock, 1000);
updateData();
setInterval(updateData, 1000);
updateImg();
setInterval(updateImg, 5000);
</script>
</body>
</html>
"""

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
                capture_output=True, text=True, timeout=8)
            if r.returncode == 0 and r.stdout.strip():
                with _gpu_lock:
                    _gpu_pct_cache = round(float(r.stdout.strip()), 1)
        except Exception:
            pass
        time.sleep(5)

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

    # Inicializa o HTML
    with open(DASHBOARD_DIR / "index.html", "w", encoding="utf-8") as f:
        f.write(html_template)

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
            api_st_html = api_radar["status_html"]
            api_st_html = api_st_html.replace("[bold red]", "<strong class='red'>").replace("[/bold red]", "</strong>")
            api_st_html = api_st_html.replace("[bold yellow]", "<strong class='yellow'>").replace("[/bold yellow]", "</strong>")
            api_st_html = api_st_html.replace("[bold green]", "<strong class='green'>").replace("[/bold green]", "</strong>")
            api_st_html = api_st_html.replace("[dim]", "<span class='dim'>").replace("[/dim]", "</span>")

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
            tm = 15 * 60
            eta_l = format_eta(max(0, (totais - feitos) * tm))
            cap_pct = info.get("cap_pct", 0)
            cap_eta = "00m 00s" if cap_pct == 100 else format_eta(int((100 - cap_pct) / 100 * tm))

            idx = max(0, lista.index(atual) - 3) if (lista and atual in lista) else 0
            recent_caps = lista[idx:idx+15] if lista else []

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
                "cpu": cpu, "cpu_cores": psutil.cpu_count(), "ram": ram.percent,
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
                "minutos_gerados": feitos * 12,
                "lista_recentes": recent_caps,
                "concluidos": info.get("caps_concluidos", []),
                "cap_atual": atual,

                "api_status": api_st_html,
                "api_429": api_radar["errors_429"],
                "api_rots": api_radar["rotations"],
                "api_engine": api_radar["engine_atual"],
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
                "ult_atividade": info.get("ult_atividade", ""),
                "linhas_recentes": info.get("linhas_recentes", [])[-6:],

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
