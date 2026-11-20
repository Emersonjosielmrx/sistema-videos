"""Lista as páginas que o perfil administra pelo Meta Business Suite (seletor de ativos). Só lê. Print em logs/.
    python fb_business_paginas.py <conta>"""
import sys, time
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
        pg.set_viewport_size({"width": 1366, "height": 900})
        pg.goto("https://business.facebook.com/latest/home", wait_until="domcontentloaded", timeout=60000)
        time.sleep(10)
        for _ in range(3):  # fecha avisos ("Fechar" / X)
            for el in pg.query_selector_all('[aria-label="Fechar"], [aria-label="Close"]'):
                try:
                    if el.is_visible():
                        el.click(); time.sleep(1)
                except Exception:
                    pass
        pg.keyboard.press("Escape")
        time.sleep(2)
        pg.mouse.click(105, 98)  # seletor "MS energy, ms..." no canto superior esquerdo
        time.sleep(5)
        pg.screenshot(path=str(LOG / f"fb_business_{conta}_seletor.png"))
        print(pg.inner_text("body")[:2500])
        pg.close()
finally:
    fb_contas.fechar(proc)
