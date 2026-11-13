# -*- coding: utf-8 -*-
"""Dashboard web Flask para visualizar os videos gerados.

Roda em http://localhost:5000

Uso:
  python dashboard.py
  # abre http://localhost:5000 no navegador
"""
import os, json
from datetime import datetime

from flask import Flask, render_template_string, jsonify, request, send_file

BASE = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE = os.path.join(BASE, "logs", "video_cache.json")
PADROES_FILE = os.path.join(BASE, "logs", "padroes_viralizacao.json")
VIDEOS_DIR = os.path.join(BASE, "videos", "cron_shorts")
THUMB_DIR = os.path.join(BASE, "thumbnails")

app = Flask(__name__)


def load_cache():
    if not os.path.exists(CACHE_FILE):
        return []
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>HiperCool Videos - Dashboard</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: #0e0e10; color: #eee; padding: 20px; }
h1 { color: #ff3366; margin-bottom: 20px; }
.stats { display: flex; gap: 20px; margin-bottom: 30px; flex-wrap: wrap; }
.stat { background: #1e1e22; padding: 15px 25px; border-radius: 8px; border-left: 4px solid #ff3366; min-width: 150px; }
.stat .n { font-size: 32px; font-weight: bold; }
.stat .label { color: #aaa; font-size: 13px; margin-top: 4px; }
.filters { display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }
.filters input, .filters select { background: #1e1e22; color: #eee; border: 1px solid #444; padding: 8px 12px; border-radius: 6px; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; }
.card { background: #1e1e22; border-radius: 8px; overflow: hidden; border: 1px solid #333; }
.card img { width: 100%; aspect-ratio: 9/16; object-fit: cover; background: #000; }
.card .body { padding: 12px; }
.card .fala { color: #fff; font-size: 14px; margin-bottom: 8px; min-height: 40px; }
.card .meta { color: #aaa; font-size: 12px; display: flex; justify-content: space-between; flex-wrap: wrap; gap: 4px; }
.card .score { background: #ff3366; color: #fff; padding: 2px 8px; border-radius: 4px; font-weight: bold; }
.card .video { display: block; margin: 8px 12px 12px; padding: 6px 12px; background: #00d4aa; color: #000; text-align: center; border-radius: 4px; text-decoration: none; font-weight: bold; }
.canal-tag { background: #444; padding: 2px 8px; border-radius: 4px; font-size: 11px; }
.metric { display: inline-block; margin-right: 8px; color: #00d4aa; }
</style>
</head>
<body>
<h1>🎬 HiperCool Videos — Dashboard</h1>

<div class="stats">
  <div class="stat"><div class="n" id="total">0</div><div class="label">Total videos</div></div>
  <div class="stat"><div class="n" id="postados">0</div><div class="label">Postados</div></div>
  <div class="stat"><div class="n" id="score-medio">0</div><div class="label">Score médio</div></div>
  <div class="stat"><div class="n" id="total-views">0</div><div class="label">Views totais</div></div>
  <div class="stat"><div class="n" id="total-likes">0</div><div class="label">Likes totais</div></div>
</div>

<div class="filters">
  <input type="text" id="search" placeholder="buscar fala..." oninput="render()">
  <select id="canal" onchange="render()">
    <option value="">todos canais</option>
  </select>
  <select id="ordenar" onchange="render()">
    <option value="ts">mais recentes</option>
    <option value="score">maior score</option>
    <option value="views">mais views</option>
    <option value="likes">mais likes</option>
  </select>
</div>

<div class="grid" id="grid"></div>

<script>
const items = {{ items | tojson }};

function init() {
  document.getElementById('total').textContent = items.length;
  document.getElementById('postados').textContent = items.filter(it => it.metrics && it.metrics.posted_url).length;
  document.getElementById('score-medio').textContent = (items.reduce((s, it) => s + (it.score || 0), 0) / items.length || 0).toFixed(1);
  document.getElementById('total-views').textContent = items.reduce((s, it) => s + (it.metrics?.views || 0), 0).toLocaleString();
  document.getElementById('total-likes').textContent = items.reduce((s, it) => s + (it.metrics?.likes || 0), 0).toLocaleString();
  const canais = [...new Set(items.map(it => it.canal))].sort();
  const sel = document.getElementById('canal');
  canais.forEach(c => {
    const o = document.createElement('option');
    o.value = c; o.textContent = c;
    sel.appendChild(o);
  });
  render();
}

function render() {
  const q = document.getElementById('search').value.toLowerCase();
  const canal = document.getElementById('canal').value;
  const ord = document.getElementById('ordenar').value;
  let list = items.filter(it => {
    if (canal && it.canal !== canal) return false;
    if (q && !(it.fala || '').toLowerCase().includes(q)) return false;
    return true;
  });
  if (ord === 'ts') list.sort((a, b) => (b.ts || '').localeCompare(a.ts || ''));
  else if (ord === 'score') list.sort((a, b) => (b.score || 0) - (a.score || 0));
  else if (ord === 'views') list.sort((a, b) => (b.metrics?.views || 0) - (a.metrics?.views || 0));
  else if (ord === 'likes') list.sort((a, b) => (b.metrics?.likes || 0) - (a.metrics?.likes || 0));
  const grid = document.getElementById('grid');
  grid.innerHTML = list.map(it => {
    const t = it.thumbnails || {};
    const thumb = t.A || t.B || t.C || '';
    const v = it.metrics || {};
    const media = it.video_path ? it.video_path.split(/[\\\\\\/]/).pop() : '';
    return `<div class="card">
      ${thumb ? `<img src="/thumb/${encodeURIComponent(thumb.split(/[\\\\\\/]/).pop())}" loading="lazy">` : ''}
      <div class="body">
        <div class="fala">${it.fala || ''}</div>
        <div class="meta">
          <span class="canal-tag">${it.canal || ''}</span>
          <span class="score">${it.score || 0}/10</span>
        </div>
        <div class="meta" style="margin-top:6px">
          <span class="metric">👁 ${(v.views || 0).toLocaleString()}</span>
          <span class="metric">❤️ ${(v.likes || 0).toLocaleString()}</span>
          ${v.engagement_rate ? `<span class="metric">${v.engagement_rate}%</span>` : ''}
        </div>
        ${v.posted_url ? `<a href="${v.posted_url}" target="_blank" class="video">ver post ${v.posted_platform || ''}</a>` : ''}
      </div>
    </div>`;
  }).join('');
}

init();
</script>
</body>
</html>"""


@app.route("/")
def index():
    items = load_cache()
    return render_template_string(HTML, items=items)


@app.route("/api/items")
def api_items():
    return jsonify(load_cache())


@app.route("/api/items/<vid_id>")
def api_item(vid_id):
    for it in load_cache():
        if it["id"] == vid_id:
            return jsonify(it)
    return jsonify({"error": "not found"}), 404


@app.route("/api/patterns")
def api_patterns():
    if not os.path.exists(PADROES_FILE):
        return jsonify({"msg": "no patterns yet - rode 'python cron_gerar_video_llm.py padroes'"})
    with open(PADROES_FILE, "r", encoding="utf-8") as f:
        return jsonify(json.load(f))


@app.route("/video/<path:filename>")
def video_file(filename):
    return send_file(os.path.join(VIDEOS_DIR, filename))


@app.route("/thumb/<path:filename>")
def thumb_file(filename):
    return send_file(os.path.join(THUMB_DIR, filename))


@app.route("/api/metrics/<vid_id>", methods=["POST"])
def api_metrics(vid_id):
    """Endpoint para atualizar metricas via POST."""
    data = request.json
    cache = load_cache()
    for it in cache:
        if it["id"] == vid_id:
            it["metrics"].update(data)
            it["metrics_updated_at"] = datetime.now().isoformat(timespec="seconds")
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
            return jsonify({"ok": True, "metrics": it["metrics"]})
    return jsonify({"error": "not found"}), 404


if __name__ == "__main__":
    port = int(os.environ.get("DASHBOARD_PORT", "5000"))
    print(f"Dashboard em http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
