#!/usr/bin/env python3
"""Baixa + corta caps da Noona do 3 em diante. KEYLESS (scrape + split).
NAO toca Gemini. Para quando o scrape vier vazio (cap inexistente)."""
import importlib.util
import sys
import time
from pathlib import Path

sys.path.insert(0, "bin")
spec = importlib.util.spec_from_file_location("hf", "bin/hiper-fetcher.py")
hf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hf)

# splitter via subprocess (tem CLI próprio)
import subprocess

BASE = "https://tiamanhwa.com/manhwa/taming-the-new-noona/capitulo-{}/"
PYEXE = r"D:\hipercool-videos\venv\Scripts\python.exe"
START, END = 3, 30
MIN_IMGS = 5  # menos que isso = cap provavelmente inexistente/erro

log = Path("logs/noona_scrape_split.log")
log.parent.mkdir(exist_ok=True)


def w(msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(log, "a", encoding="utf-8") as f:
        f.write(line + "\n")


w(f"=== INICIO scrape+split Noona cap {START}..{END} ===")
ok, vazios, erros = [], [], []
consecutive_empty = 0

for c in range(START, END + 1):
    slug = f"taming-noona-cap{c:02d}"
    panels_out = Path(f"workspace/panels/{slug}")
    if panels_out.exists() and len(list(panels_out.glob("*.jpg"))) > MIN_IMGS:
        w(f"cap{c:02d}: JA EXISTE ({len(list(panels_out.glob('*.jpg')))} painéis) — pulando")
        ok.append(c)
        continue
    url = BASE.format(c)
    try:
        out = hf.fetch_chapter(url, slug, headed=False)
    except Exception as e:
        w(f"cap{c:02d}: ERRO scrape ({type(e).__name__}: {str(e)[:60]})")
        erros.append(c)
        continue
    if not out:
        w(f"cap{c:02d}: scrape vazio")
        vazios.append(c)
        consecutive_empty += 1
        if consecutive_empty >= 3:
            w("3 caps vazios seguidos — assumindo fim da obra, parando.")
            break
        continue
    imgs = list(Path(out).glob("*.jpg"))
    if len(imgs) < MIN_IMGS:
        w(f"cap{c:02d}: só {len(imgs)} imgs (<{MIN_IMGS}) — tratando como inexistente")
        vazios.append(c)
        consecutive_empty += 1
        if consecutive_empty >= 3:
            w("3 caps vazios seguidos — parando.")
            break
        continue
    consecutive_empty = 0
    # split
    r = subprocess.run(
        [PYEXE, "bin/panel-splitter.py", "--split",
         "--input", str(out) + "/", "--out", str(panels_out) + "/"],
        capture_output=True, text=True,
    )
    n_panels = len(list(panels_out.glob("*.jpg"))) if panels_out.exists() else 0
    w(f"cap{c:02d}: {len(imgs)} strips → {n_panels} painéis  [{slug}]")
    ok.append(c)

w(f"=== FIM. OK={ok} vazios={vazios} erros={erros} ===")
