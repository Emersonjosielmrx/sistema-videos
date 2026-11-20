"""Abre o menu da foto (canto direito) -> 'Ver todos os perfis' e lista os perfis/páginas. Print em logs/.
    python fb_perfis_menu.py <conta>"""
import sys, time, re
from pathlib import Path
from playwright.sync_api import sync_playwright
import fb_contas

conta = sys.argv[1]
porta, proc = fb_contas.abrir(conta)
LOG = Path(__file__).resolve().parent.parent / "logs"
try:
    with sync_playwright() as p:
        b = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
        pg = b.contexts[0].new_page()
        pg.set_viewport_size({"width": 1280, "height": 900})
        pg.goto("https://www.facebook.com/", wait_until="domcontentloaded", timeout=45000)
        time.sleep(6)
        for sel in ['[aria-label="Seu perfil"]', '[aria-label="Your profile"]', 'div[role=button][aria-label*="perfil" i]']:
            el = pg.query_selector(sel)
            if el:
                el.click(); break
        time.sleep(3)
        for t in ("Ver todos os perfis", "See all profiles", "Ver todos os perfis e Páginas"):
            el = pg.get_by_text(t, exact=False).first
            if el.count():
                el.click(); break
        time.sleep(4)
        pg.screenshot(path=str(LOG / f"fb_perfis_{conta}.png"))
        txt = pg.inner_text("body")
        print(txt[:2500])
        pg.close()
finally:
    fb_contas.fechar(proc)
