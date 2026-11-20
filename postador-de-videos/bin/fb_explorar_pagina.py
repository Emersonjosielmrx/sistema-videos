"""Abre a página (perfil novo) e tira print; lista botões ligados a foto/capa. Só olha.
    python fb_explorar_pagina.py <porta> <url> <nome>"""
import sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright
LOG = Path(__file__).resolve().parent.parent / "logs"
with sync_playwright() as p:
    b = p.chromium.connect_over_cdp(f"http://127.0.0.1:{int(sys.argv[1])}")
    pg = b.contexts[0].new_page()
    pg.set_viewport_size({"width": 1366, "height": 900})
    pg.goto(sys.argv[2], wait_until="domcontentloaded", timeout=90000)
    time.sleep(10)
    pg.screenshot(path=str(LOG / f"{sys.argv[3]}.png"))
    for e in pg.query_selector_all("[aria-label], div[role=button]"):
        a = (e.get_attribute("aria-label") or e.inner_text() or "").strip()[:50]
        if e.is_visible() and any(k in a.lower() for k in ("foto", "capa", "trocar", "mudar", "alternar", "perfil", "photo", "cover", "switch")):
            print(repr(a))
    pg.close()
