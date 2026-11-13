# -*- coding: utf-8 -*-
"""Painel web da Fabrica Viral - monitoramento e controle."""
import json
import time
import threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from config import PAINEL_PORT
from db_local import get_recent_videos, get_stats, get_historico_ideias

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Fabrica Viral - Painel</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: #0d1117; color: #c9d1d9; padding: 20px; }
h1 { color: #58a6ff; margin-bottom: 20px; font-size: 24px; }
.stats { display: flex; gap: 15px; margin-bottom: 25px; flex-wrap: wrap; }
.stat-card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 15px 20px; min-width: 120px; }
.stat-card .number { font-size: 28px; font-weight: bold; color: #58a6ff; }
.stat-card .label { font-size: 12px; color: #8b949e; text-transform: uppercase; margin-top: 4px; }
.stat-card.done .number { color: #3fb950; }
.stat-card.error .number { color: #f85149; }
.stat-card.pending .number { color: #d29922; }
table { width: 100%; border-collapse: collapse; background: #161b22; border-radius: 8px; overflow: hidden; }
th { background: #21262d; padding: 12px 15px; text-align: left; font-size: 12px; text-transform: uppercase; color: #8b949e; }
td { padding: 10px 15px; border-top: 1px solid #21262d; font-size: 13px; max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
tr:hover { background: #1c2128; }
.status-done { color: #3fb950; font-weight: bold; }
.status-error { color: #f85149; }
.status-pending { color: #d29922; }
.status-rendering { color: #58a6ff; }
.modo-criacao { background: #1f3a5f; padding: 2px 8px; border-radius: 10px; font-size: 11px; }
.modo-replica { background: #3d1f5f; padding: 2px 8px; border-radius: 10px; font-size: 11px; }
.refresh { position: fixed; top: 15px; right: 20px; background: #21262d; border: 1px solid #30363d; color: #c9d1d9; padding: 8px 16px; border-radius: 6px; cursor: pointer; }
.refresh:hover { background: #30363d; }
.section { margin-top: 25px; }
.section h2 { color: #8b949e; font-size: 14px; margin-bottom: 10px; text-transform: uppercase; }
</style>
</head>
<body>
<h1>Fabrica Viral</h1>
<button class="refresh" onclick="location.reload()">Atualizar</button>
<div class="stats">
<div class="stat-card done"><div class="number">{{done}}</div><div class="label">Prontos</div></div>
<div class="stat-card pending"><div class="number">{{pending}}</div><div class="label">Pendentes</div></div>
<div class="stat-card error"><div class="number">{{errors}}</div><div class="label">Erros</div></div>
<div class="stat-card"><div class="number">{{total}}</div><div class="label">Total</div></div>
</div>
<div class="section">
<h2>Videos Recentes</h2>
<table>
<tr><th>Status</th><th>Modo</th><th>Canal</th><th>Titulo</th><th>Prompt</th><th>Criado</th></tr>
{{rows}}
</table>
</div>
<script>setTimeout(function(){location.reload()}, 30000);</script>
</body>
</html>"""


def render_html():
    stats = get_stats()
    videos = get_recent_videos(limit=30)
    rows = ""
    for v in videos:
        status_class = f"status-{v.get('status', 'pending')}"
        modo_class = f"modo-{v.get('modo', 'criacao')}"
        created = ""
        if v.get("created_at"):
            t = time.localtime(v["created_at"])
            created = time.strftime("%d/%m %H:%M", t)
        titulo = (v.get("titulo") or "")[:60]
        prompt_short = (v.get("prompt_video") or "")[:80]
        rows += (
            f'<tr><td class="{status_class}">{v.get("status","?")}</td>'
            f'<td><span class="{modo_class}">{v.get("modo","?")}</span></td>'
            f'<td>{v.get("canal","?")}</td>'
            f'<td title="{titulo}">{titulo}</td>'
            f'<td title="{prompt_short}">{prompt_short}</td>'
            f'<td>{created}</td></tr>\n'
        )
    html = HTML_TEMPLATE
    html = html.replace("{{done}}", str(stats["done"]))
    html = html.replace("{{pending}}", str(stats["pending"]))
    html = html.replace("{{errors}}", str(stats["errors"]))
    html = html.replace("{{total}}", str(stats["total"]))
    html = html.replace("{{rows}}", rows)
    return html


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def do_GET(self):
        path = self.path.rstrip("/")
        if path == "/api/stats":
            data = json.dumps(get_stats()).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(data)
        elif path == "/api/videos":
            data = json.dumps(get_recent_videos(30), ensure_ascii=False, default=str).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(data)
        else:
            html = render_html().encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html)


def start_painel(background=True):
    """Inicia o painel web."""
    server = ThreadingHTTPServer(("0.0.0.0", PAINEL_PORT), Handler)
    if background:
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        print(f"[painel] Rodando em http://127.0.0.1:{PAINEL_PORT}")
        return server
    else:
        print(f"[painel] Rodando em http://127.0.0.1:{PAINEL_PORT}")
        server.serve_forever()


if __name__ == "__main__":
    start_painel(background=False)