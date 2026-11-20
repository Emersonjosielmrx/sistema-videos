"""Ensaio: abre o composer, deixa só a página do FB marcada e fecha SEM postar. python fb_ensaio_postar_em.py <porta> <asset> "<nome>" """
import sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright
import fb_reel_bs as F
with sync_playwright() as p:
    b = p.chromium.connect_over_cdp(f"http://127.0.0.1:{int(sys.argv[1])}")
    pg = b.contexts[0].new_page()
    pg.set_viewport_size({"width": 1366, "height": 900})
    pg.goto(F.COMPOSER.format(sys.argv[2]), wait_until="domcontentloaded", timeout=60000)
    time.sleep(12)
    F._fechar_avisos(pg)
    print(F._so_facebook(pg, sys.argv[3]))
    pg.screenshot(path=str(F.LOG / "fb_ensaio_postar_em.png"))
    pg.close()
