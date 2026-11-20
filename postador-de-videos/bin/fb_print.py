"""Print das abas do Chrome na porta CDP (só olha, não clica). python fb_print.py <porta> <saida.png>"""
import sys
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.connect_over_cdp(f"http://127.0.0.1:{int(sys.argv[1])}")
    pgs = [pg for pg in b.contexts[0].pages if pg.url.startswith("http")]
    for i, pg in enumerate(pgs):
        print(i, pg.url[:120])
    if pgs:
        pgs[-1].screenshot(path=sys.argv[2])
