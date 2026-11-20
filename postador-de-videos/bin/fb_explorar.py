"""Explora uma URL no Chrome da porta CDP: print + botões + inputs de arquivo. Só olha.
    python fb_explorar.py <porta> <url> <nome_print>"""
import sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright
LOG = Path(__file__).resolve().parent.parent / "logs"
with sync_playwright() as p:
    b = p.chromium.connect_over_cdp(f"http://127.0.0.1:{int(sys.argv[1])}")
    pg = b.contexts[0].new_page()
    pg.set_viewport_size({"width": 1366, "height": 900})
    pg.goto(sys.argv[2], wait_until="domcontentloaded", timeout=60000)
    time.sleep(12)
    pg.keyboard.press("Escape")
    time.sleep(1)
    pg.screenshot(path=str(LOG / f"{sys.argv[3]}.png"))
    print("url:", pg.url)
    bt = [((e.inner_text() or e.get_attribute("aria-label") or "").strip()[:40]) for e in pg.query_selector_all("button, div[role=button], [role=menuitem]") if e.is_visible()]
    print("botoes:", [x for x in bt if x][:60])
    print("inputs file:", [(e.get_attribute("accept")) for e in pg.query_selector_all("input[type=file]")])
    pg.close()
