"""Acha o id 'clássico' da Página (usado pelo Business Suite) a partir da URL de perfil. python fb_page_id.py <porta> <url>"""
import sys, time, re, collections
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.connect_over_cdp(f"http://127.0.0.1:{int(sys.argv[1])}")
    pg = b.contexts[0].new_page()
    pg.goto(sys.argv[2], wait_until="domcontentloaded", timeout=90000)
    time.sleep(8)
    h = pg.content()
    for chave in ("delegate_page_id", "pageID", "page_id", "associated_page_id", "delegate_page", "profile_delegate_page_id"):
        achou = collections.Counter(re.findall(rf'"{chave}"\s*:\s*"?(\d{{6,20}})', h))
        if achou:
            print(chave, achou.most_common(4))
    pg.close()
