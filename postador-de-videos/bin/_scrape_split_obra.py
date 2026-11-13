#!/usr/bin/env python3
"""Baixa + corta caps de QUALQUER obra. KEYLESS (scrape + split). NAO toca Gemini.
Uso: python _scrape_split_obra.py <slug_local> <url_slug_site> <start> <end>
Ex:  python _scrape_split_obra.py the-meek-cat the-meek-cat 11 30
     python _scrape_split_obra.py perverts-daily-life a-perverts-daily-life 6 144
Pula caps ja baixados. Detecta placeholder (3 imgs pequenas). Para apos 3 vazios seguidos."""
import importlib.util
import sys
import time
import subprocess
from pathlib import Path

sys.path.insert(0, "bin")
spec = importlib.util.spec_from_file_location("hf", "bin/hiper-fetcher.py")
hf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hf)

LOCAL_SLUG = sys.argv[1]
SITE_SLUG = sys.argv[2]
START = int(sys.argv[3])
END = int(sys.argv[4])
PYEXE = r"D:\hipercool-videos\venv\Scripts\python.exe"
BASE = f"https://tiamanhwa.com/manhwa/{SITE_SLUG}/capitulo-{{}}/"
MIN_IMGS = 5
# Apos quantos vazios SEGUIDOS assumir fim de obra. Algumas obras tem buracos
# (ex: perverts caps 6-9 vazios, conteudo volta no 10), entao usar margem alta.
MAX_CONSEC_EMPTY = int(sys.argv[5]) if len(sys.argv) > 5 else 6

logf = Path(f"logs/scrape_{LOCAL_SLUG}.log")
logf.parent.mkdir(exist_ok=True)


def w(msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(logf, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def is_placeholder(imgs):
    """3 imgs pequenas (500x700 etc) = pagina 'em breve'."""
    if len(imgs) > MIN_IMGS:
        return False
    try:
        from PIL import Image
        for p in imgs:
            if Image.open(p).size[1] > 1000:  # strip real e alto
                return False
        return True
    except Exception:
        return len(imgs) < MIN_IMGS


w(f"=== INICIO {LOCAL_SLUG} cap {START}..{END} (site={SITE_SLUG}) ===")
ok, vazios, erros = [], [], []
consec_empty = 0

for c in range(START, END + 1):
    slug = f"{LOCAL_SLUG}-cap{c:02d}"
    pout = Path(f"workspace/panels/{slug}")
    if pout.exists() and len(list(pout.glob("*.jpg"))) > MIN_IMGS:
        w(f"cap{c:02d}: JA EXISTE ({len(list(pout.glob('*.jpg')))} painéis) — pulando")
        ok.append(c)
        consec_empty = 0
        continue
    try:
        out = hf.fetch_chapter(BASE.format(c), slug, headed=False)
    except Exception as e:
        w(f"cap{c:02d}: ERRO scrape ({type(e).__name__}: {str(e)[:60]})")
        erros.append(c)
        continue
    imgs = list(Path(out).glob("*.jpg")) if out else []
    if not out or is_placeholder(imgs):
        w(f"cap{c:02d}: placeholder/vazio ({len(imgs)} imgs)")
        vazios.append(c)
        consec_empty += 1
        # limpa cache falso
        if out:
            import shutil
            try:
                shutil.rmtree(out)
            except Exception:
                pass
        if consec_empty >= MAX_CONSEC_EMPTY:
            w("3 caps vazios seguidos — parando (fim da obra publicada).")
            break
        continue
    consec_empty = 0
    subprocess.run(
        [PYEXE, "bin/panel-splitter.py", "--split",
         "--input", str(out) + "/", "--out", str(pout) + "/"],
        capture_output=True, text=True,
    )
    n = len(list(pout.glob("*.jpg"))) if pout.exists() else 0
    w(f"cap{c:02d}: {len(imgs)} strips → {n} painéis  [{slug}]")
    ok.append(c)

w(f"=== FIM {LOCAL_SLUG}. OK={ok} vazios={vazios} erros={erros} ===")
