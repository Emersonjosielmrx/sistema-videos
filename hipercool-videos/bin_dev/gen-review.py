#!/usr/bin/env python3
"""
gen-review.py — Generates review.html for HiperCool video QA.

Scans workspace/videos/*.mp4, reads .meta.json for each,
gets duration via ffprobe, and generates a self-contained
review dashboard HTML file.
"""

import json
import os
import subprocess
import sys
import webbrowser
from pathlib import Path

# Resolve paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
VIDEOS_DIR = PROJECT_ROOT / "workspace" / "videos"
OUTPUT_HTML = VIDEOS_DIR / "review.html"


def get_duration_ffprobe(video_path: Path) -> float:
    """Get video duration in seconds using ffprobe."""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                str(video_path),
            ],
            capture_output=True, text=True, timeout=30,
        )
        data = json.loads(result.stdout)
        return float(data["format"]["duration"])
    except Exception:
        return 0.0


def format_duration(seconds: float) -> str:
    """Format seconds as MM:SS."""
    m, s = divmod(int(seconds), 60)
    return f"{m}:{s:02d}"


def scan_videos():
    """Scan for .mp4 files and pair with .meta.json. Includes stable versions."""
    videos = []

    # Current videos (workspace/videos/*.mp4)
    for mp4 in sorted(VIDEOS_DIR.glob("*.mp4")):
        meta_path = mp4.with_suffix(".meta.json")
        meta = {}
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
            except Exception:
                pass

        duration = get_duration_ffprobe(mp4)
        videos.append({
            "filename": mp4.name,
            "path": mp4.name,  # relative for HTML src
            "meta": meta,
            "duration_s": duration,
            "duration_fmt": format_duration(duration),
            "is_stable": False,
            "version_tag": "atual",
        })

    # Stable versions (workspace/videos/stable/*.mp4)
    stable_dir = VIDEOS_DIR / "stable"
    if stable_dir.exists():
        for mp4 in sorted(stable_dir.glob("*.mp4")):
            meta_path = mp4.with_suffix(".meta.json")
            meta = {}
            if meta_path.exists():
                try:
                    meta = json.loads(meta_path.read_text(encoding="utf-8"))
                except Exception:
                    pass

            # Extract version from filename (e.g. v2.0_filename.mp4)
            version = "estável"
            if mp4.name.startswith("v"):
                parts = mp4.name.split("_", 1)
                if parts[0].startswith("v"):
                    version = parts[0]

            duration = get_duration_ffprobe(mp4)
            videos.append({
                "filename": mp4.name,
                "path": f"stable/{mp4.name}",
                "meta": meta,
                "duration_s": duration,
                "duration_fmt": format_duration(duration),
                "is_stable": True,
                "version_tag": version,
            })

    return videos


def generate_html(videos: list) -> str:
    """Generate the full review.html content."""
    video_cards = ""
    for i, v in enumerate(videos):
        meta = v["meta"]
        title = meta.get("titulo_video") or meta.get("titulo") or v["filename"]
        tags = meta.get("tags", [])
        panels = meta.get("panels_count", "?")
        size_mb = meta.get("size_mb", "?")
        created = meta.get("created_at", "")[:16].replace("T", " ")

        tags_html = "".join(f'<span class="tag">{t}</span>' for t in tags)

        duration_class = ""
        if v["duration_s"] > 0:
            mins = v["duration_s"] / 60
            if 4 <= mins <= 8:
                duration_class = "good"
            elif mins < 3 or mins > 10:
                duration_class = "bad"
            else:
                duration_class = "warn"

        # Version badge
        version_badge = ""
        if v.get("is_stable"):
            version_badge = f'<span class="version-badge stable">{v["version_tag"]}</span>'
        else:
            version_badge = '<span class="version-badge current">atual</span>'

        video_cards += f"""
    <div class="video-card{'  stable-card' if v.get('is_stable') else ''}" id="video-{i}" data-filename="{v['filename']}">
      <div class="video-side">
        <h2 class="video-title">{version_badge} {title}</h2>
        <video controls preload="metadata" width="100%">
          <source src="{v['path']}" type="video/mp4">
        </video>
        <div class="meta-row">
          <span class="meta-item">&#128249; {panels} painéis</span>
          <span class="meta-item duration {duration_class}">&#9201; {v['duration_fmt']}</span>
          <span class="meta-item">&#128190; {size_mb} MB</span>
          <span class="meta-item">&#128197; {created}</span>
        </div>
        <div class="tags-row">{tags_html}</div>
      </div>
      <div class="checklist-side">
        <h3>Checklist de Qualidade</h3>
        <label><input type="checkbox" data-video="{i}" data-q="narracao"> Narração corresponde às imagens</label>
        <label><input type="checkbox" data-video="{i}" data-q="bordas"> Sem bordas pretas visíveis</label>
        <label><input type="checkbox" data-video="{i}" data-q="transicoes"> Transições suaves entre painéis</label>
        <label><input type="checkbox" data-video="{i}" data-q="vozes"> Vozes variadas (não monotôno)</label>
        <label><input type="checkbox" data-video="{i}" data-q="trilha"> Trilha sonora presente e no volume certo</label>
        <label><input type="checkbox" data-video="{i}" data-q="efeitos"> Efeitos visuais variados (zoom, pan, cor)</label>
        <label><input type="checkbox" data-video="{i}" data-q="texto"> Texto dos balões não cortado</label>
        <label><input type="checkbox" data-video="{i}" data-q="duracao"> Duração adequada (4-8 min ideal)</label>
        <div class="notes-section">
          <label class="notes-label">Notas / O que melhorar:</label>
          <textarea class="notes-textarea" id="notes-{i}" data-video="{i}" rows="3" placeholder="Escreva observações sobre o vídeo..."></textarea>
        </div>
        <div class="verdict">
          <button class="btn-approve" onclick="setVerdict({i},'approved')">&#10004; Aprovado</button>
          <button class="btn-needs-improvement" onclick="setVerdict({i},'needs-improvement')">&#9888; Meio-termo</button>
          <button class="btn-reject" onclick="setVerdict({i},'rejected')">&#10008; Rejeitar</button>
          <span class="verdict-badge" id="badge-{i}"></span>
        </div>
      </div>
    </div>
"""

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>HiperCool — Video Review Dashboard</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #0d1117;
  color: #e6edf3;
  padding: 24px;
  min-height: 100vh;
}}
h1 {{
  text-align: center;
  font-size: 1.8rem;
  margin-bottom: 8px;
  color: #58a6ff;
}}
.subtitle {{
  text-align: center;
  color: #8b949e;
  margin-bottom: 32px;
  font-size: 0.9rem;
}}
.video-card {{
  display: flex;
  gap: 24px;
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
  transition: border-color 0.2s;
}}
.video-card:hover {{ border-color: #58a6ff; }}
.video-card.approved {{ border-color: #3fb950; background: #0d1117; }}
.video-card.rejected {{ border-color: #f85149; background: #1a0f0f; }}
.video-card.needs-improvement {{ border-color: #d29922; background: #1a1700; }}
.video-side {{
  flex: 1.2;
  min-width: 0;
}}
.checklist-side {{
  flex: 0.8;
  min-width: 280px;
}}
.video-title {{
  font-size: 1.1rem;
  margin-bottom: 12px;
  color: #f0f6fc;
}}
video {{
  border-radius: 8px;
  background: #000;
  width: 100%;
  max-height: 360px;
}}
.meta-row {{
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 12px;
}}
.meta-item {{
  background: #21262d;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 0.82rem;
  color: #8b949e;
}}
.meta-item.duration.good {{ color: #3fb950; }}
.meta-item.duration.warn {{ color: #d29922; }}
.meta-item.duration.bad {{ color: #f85149; }}
.tags-row {{
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 10px;
}}
.tag {{
  background: #1f3a5f;
  color: #58a6ff;
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
}}
.version-badge {{
  display: inline-block;
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 0.7rem;
  font-weight: bold;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  vertical-align: middle;
  margin-right: 8px;
}}
.version-badge.current {{
  background: #1f6feb;
  color: #fff;
}}
.version-badge.stable {{
  background: #2ea043;
  color: #fff;
}}
.stable-card {{
  border-left: 3px solid #2ea043;
  opacity: 0.85;
}}
.checklist-side h3 {{
  margin-bottom: 14px;
  color: #8b949e;
  font-size: 0.9rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}}
.checklist-side label {{
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 0;
  border-bottom: 1px solid #21262d;
  font-size: 0.88rem;
  cursor: pointer;
  transition: color 0.15s;
}}
.checklist-side label:hover {{ color: #58a6ff; }}
.checklist-side input[type="checkbox"] {{
  width: 18px;
  height: 18px;
  accent-color: #3fb950;
  cursor: pointer;
}}
.notes-section {{
  margin-top: 14px;
  padding-top: 10px;
  border-top: 1px solid #21262d;
}}
.notes-label {{
  display: block;
  font-size: 0.82rem;
  color: #8b949e;
  margin-bottom: 6px;
  cursor: default;
}}
.notes-textarea {{
  width: 100%;
  background: #0d1117;
  border: 1px solid #30363d;
  border-radius: 6px;
  color: #e6edf3;
  padding: 8px 10px;
  font-size: 0.84rem;
  font-family: inherit;
  resize: vertical;
  transition: border-color 0.2s;
}}
.notes-textarea:focus {{
  outline: none;
  border-color: #58a6ff;
}}
.verdict {{
  margin-top: 18px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}}
.btn-approve, .btn-reject, .btn-needs-improvement {{
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.1s, opacity 0.15s;
}}
.btn-approve {{
  background: #238636;
  color: #fff;
}}
.btn-approve:hover {{ background: #2ea043; transform: scale(1.03); }}
.btn-needs-improvement {{
  background: #9e6a03;
  color: #fff;
}}
.btn-needs-improvement:hover {{ background: #bb8009; transform: scale(1.03); }}
.btn-reject {{
  background: #da3633;
  color: #fff;
}}
.btn-reject:hover {{ background: #f85149; transform: scale(1.03); }}
.verdict-badge {{
  font-weight: 700;
  font-size: 0.78rem;
  padding: 4px 10px;
  border-radius: 12px;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}}
.verdict-badge.badge-approved {{
  background: #238636;
  color: #fff;
}}
.verdict-badge.badge-rejected {{
  background: #da3633;
  color: #fff;
}}
.verdict-badge.badge-needs-improvement {{
  background: #9e6a03;
  color: #fff;
}}
.summary {{
  text-align: center;
  margin-top: 16px;
  padding: 16px;
  background: #161b22;
  border-radius: 8px;
  border: 1px solid #30363d;
  color: #8b949e;
}}
.save-bar {{
  position: sticky;
  bottom: 0;
  background: #161b22;
  border-top: 1px solid #30363d;
  padding: 12px 24px;
  display: flex;
  justify-content: center;
  gap: 12px;
  align-items: center;
  z-index: 100;
  margin-top: 24px;
  border-radius: 8px;
}}
.btn-save {{
  padding: 10px 24px;
  border: none;
  border-radius: 6px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  background: #58a6ff;
  color: #0d1117;
  transition: transform 0.1s, background 0.15s;
}}
.btn-save:hover {{ background: #79c0ff; transform: scale(1.03); }}
.btn-download {{
  padding: 10px 24px;
  border: none;
  border-radius: 6px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  background: #30363d;
  color: #e6edf3;
  transition: transform 0.1s, background 0.15s;
}}
.btn-download:hover {{ background: #484f58; transform: scale(1.03); }}
.save-status {{
  font-size: 0.82rem;
  color: #3fb950;
  opacity: 0;
  transition: opacity 0.3s;
}}
.save-status.visible {{ opacity: 1; }}
@media (max-width: 900px) {{
  .video-card {{ flex-direction: column; }}
}}
</style>
</head>
<body>
<h1>HiperCool — Video Review</h1>
<p class="subtitle">{len(videos)} vídeo(s) encontrado(s) | Gerado automaticamente por gen-review.py</p>
{video_cards}
<div class="summary" id="summary">
  Marque os critérios e aprove/rejeite cada vídeo.
</div>
<div class="save-bar">
  <button class="btn-save" onclick="saveReviews()">&#128190; Salvar Reviews</button>
  <button class="btn-download" onclick="downloadJSON()">&#11015; Baixar JSON</button>
  <span class="save-status" id="save-status">Salvo!</span>
</div>
<script>
const STORAGE_KEY = 'hipercool-reviews';
const TOTAL_VIDEOS = {len(videos)};

function getReviewData() {{
  const reviews = {{}};
  for (let i = 0; i < TOTAL_VIDEOS; i++) {{
    const card = document.getElementById('video-' + i);
    const filename = card.dataset.filename;
    let status = 'pending';
    if (card.classList.contains('approved')) status = 'approved';
    else if (card.classList.contains('rejected')) status = 'rejected';
    else if (card.classList.contains('needs-improvement')) status = 'needs-improvement';

    const notes = document.getElementById('notes-' + i).value;

    const checklist = {{}};
    card.querySelectorAll('input[type=checkbox]').forEach(cb => {{
      checklist[cb.dataset.q] = cb.checked;
    }});

    reviews[filename] = {{ status, notes, checklist }};
  }}
  return reviews;
}}

function saveReviews() {{
  const data = getReviewData();
  localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  const statusEl = document.getElementById('save-status');
  statusEl.classList.add('visible');
  setTimeout(() => statusEl.classList.remove('visible'), 2000);
  updateSummary();
}}

function downloadJSON() {{
  const data = getReviewData();
  const blob = new Blob([JSON.stringify(data, null, 2)], {{ type: 'application/json' }});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'reviews.json';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}}

function loadReviews() {{
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) return;
  try {{
    const data = JSON.parse(raw);
    for (let i = 0; i < TOTAL_VIDEOS; i++) {{
      const card = document.getElementById('video-' + i);
      const filename = card.dataset.filename;
      const review = data[filename];
      if (!review) continue;

      if (review.status && review.status !== 'pending') {{
        setVerdict(i, review.status, true);
      }}
      if (review.notes) {{
        document.getElementById('notes-' + i).value = review.notes;
      }}
      if (review.checklist) {{
        Object.entries(review.checklist).forEach(([q, checked]) => {{
          const cb = card.querySelector(`input[data-q="${{q}}"]`);
          if (cb) cb.checked = checked;
        }});
      }}
    }}
    updateSummary();
  }} catch(e) {{
    console.warn('Failed to load reviews:', e);
  }}
}}

function setVerdict(idx, verdict, skipSave) {{
  const card = document.getElementById('video-' + idx);
  const badge = document.getElementById('badge-' + idx);
  card.classList.remove('approved', 'rejected', 'needs-improvement');
  badge.classList.remove('badge-approved', 'badge-rejected', 'badge-needs-improvement');
  card.classList.add(verdict);
  if (verdict === 'approved') {{
    badge.textContent = 'APROVADO';
    badge.classList.add('badge-approved');
  }} else if (verdict === 'needs-improvement') {{
    badge.textContent = 'MEIO-TERMO';
    badge.classList.add('badge-needs-improvement');
  }} else {{
    badge.textContent = 'REJEITADO';
    badge.classList.add('badge-rejected');
  }}
  if (!skipSave) {{
    updateSummary();
  }}
}}

function updateSummary() {{
  const cards = document.querySelectorAll('.video-card');
  let approved = 0, rejected = 0, needsImprovement = 0, pending = 0;
  cards.forEach(c => {{
    if (c.classList.contains('approved')) approved++;
    else if (c.classList.contains('rejected')) rejected++;
    else if (c.classList.contains('needs-improvement')) needsImprovement++;
    else pending++;
  }});
  document.getElementById('summary').innerHTML =
    `<strong>${{approved}}</strong> aprovado(s) | <strong>${{needsImprovement}}</strong> meio-termo | <strong>${{rejected}}</strong> rejeitado(s) | <strong>${{pending}}</strong> pendente(s)`;
}}

// Load saved reviews on page load
document.addEventListener('DOMContentLoaded', loadReviews);
</script>
</body>
</html>"""
    return html


def main():
    if not VIDEOS_DIR.exists():
        print(f"[ERRO] Diretório não encontrado: {VIDEOS_DIR}")
        sys.exit(1)

    no_open = "--no-open" in sys.argv

    print(f"[*] Escaneando vídeos em: {VIDEOS_DIR}")
    videos = scan_videos()

    if not videos:
        print("[!] Nenhum .mp4 encontrado.")
        sys.exit(0)

    print(f"[*] {len(videos)} vídeo(s) encontrado(s):")
    for v in videos:
        print(f"    - {v['filename']} ({v['duration_fmt']})")

    html = generate_html(videos)
    OUTPUT_HTML.write_text(html, encoding="utf-8")
    print(f"[*] HTML gerado: {OUTPUT_HTML}")

    if not no_open:
        webbrowser.open(f"file://{OUTPUT_HTML}")
        print("[*] Aberto no navegador.")
    else:
        print("[*] --no-open: navegador não aberto.")


if __name__ == "__main__":
    main()
