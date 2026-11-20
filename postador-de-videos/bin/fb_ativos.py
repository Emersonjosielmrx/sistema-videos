"""Acha o asset_id (Business Suite) de cada página: abre o seletor de ativos e clica em cada página, lendo o asset_id da URL.
    python fb_ativos.py <porta> "<Nome 1>" ["<Nome 2>" ...]"""
import sys, time, re
from playwright.sync_api import sync_playwright
import fb_reel_bs as F
with sync_playwright() as p:
    b = p.chromium.connect_over_cdp(f"http://127.0.0.1:{int(sys.argv[1])}")
    pg = b.contexts[0].new_page()
    pg.set_viewport_size({"width": 1366, "height": 900})
    pg.goto("https://business.facebook.com/latest/home", wait_until="domcontentloaded", timeout=90000)
    time.sleep(12)
    F._fechar_avisos(pg)
    for nome in sys.argv[2:]:
        pg.mouse.click(105, 94)
        time.sleep(4)
        alvo = pg.get_by_text(nome, exact=True)
        ok = False
        for i in range(alvo.count()):
            if alvo.nth(i).is_visible():
                alvo.nth(i).click(); ok = True; break
        time.sleep(8)
        m = re.search(r"asset_id=(\d+)", pg.url)
        print(nome, "->", m.group(1) if (ok and m) else f"NAO ACHOU ({pg.url[:100]})")
        if not ok:
            pg.screenshot(path=str(F.LOG / "fb_ativos.png"))
            pg.keyboard.press("Escape")
    pg.close()
