"""Lê a aba Monetização do Business Suite de uma Página (requisitos/elegibilidade). Só lê. Print em logs/.
    python fb_monetizacao.py <porta> <asset_id> <tag>"""
import sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright
import fb_reel_bs as F
porta, asset, tag = sys.argv[1:4]
with sync_playwright() as p:
    pg = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}").contexts[0].new_page()
    pg.set_viewport_size({"width": 1366, "height": 1100})
    try:
        pg.goto(f"https://business.facebook.com/latest/monetization?asset_id={asset}", wait_until="domcontentloaded", timeout=120000)
        time.sleep(15)
        F._fechar_avisos(pg)
        pg.screenshot(path=str(F.LOG / f"fb_monet_{tag}.png"), full_page=True)
        t = pg.inner_text("body")
        i = t.find("Monetiza")
        print(t[max(0, i - 50):i + 3000])
    finally:
        pg.close()
