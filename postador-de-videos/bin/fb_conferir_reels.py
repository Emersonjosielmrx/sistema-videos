"""Confere os Reels publicados de uma Página (aba /reels) e tira print. python fb_conferir_reels.py <conta> <url_pagina> <tag>"""
import sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright
import fb_contas
LOG = Path(__file__).resolve().parent.parent / "logs"
conta, url, tag = sys.argv[1:4]
porta, proc = fb_contas.abrir(conta)
try:
    with sync_playwright() as p:
        pg = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}").contexts[0].new_page()
        pg.set_viewport_size({"width": 1366, "height": 900})
        sep = "&sk=reels_tab" if "profile.php" in url else "reels/"
        pg.goto(url + sep if "profile.php" in url else url.rstrip("/") + "/reels/", wait_until="domcontentloaded", timeout=90000)
        time.sleep(12)
        links = {a.get_attribute("href").split("?")[0] for a in pg.query_selector_all("a[href*='/reel/']")}
        print(tag, "reels visíveis:", len(links), sorted(links)[:5])
        pg.screenshot(path=str(LOG / f"fb_reels_{tag}.png"))
        pg.close()
finally:
    fb_contas.fechar(proc)
