import sys, time
from playwright.sync_api import sync_playwright
import fb_reel_bs as F
with sync_playwright() as p:
    b = p.chromium.connect_over_cdp(f"http://127.0.0.1:{int(sys.argv[1])}")
    pg = b.contexts[0].new_page()
    pg.set_viewport_size({"width": 1366, "height": 900})
    pg.goto("https://business.facebook.com/latest/home", wait_until="domcontentloaded", timeout=90000)
    time.sleep(12)
    F._fechar_avisos(pg)
    pg.mouse.click(105, 94)
    time.sleep(5)
    pg.screenshot(path=str(F.LOG / "fb_ativos_seletor.png"))
    if len(sys.argv) > 3:
        pg.mouse.click(int(sys.argv[2]), int(sys.argv[3]))
        time.sleep(10)
        import re
        for _ in range(12):
            time.sleep(5)
            m = re.search(r"asset_id=(\d+)", pg.url)
            if m and m.group(1) != "1417861988084594":
                break
        print("asset url:", pg.url[:140])
        print("nome:", pg.locator("text=Perfil").first.locator("xpath=preceding::*[1]").inner_text()[:60] if pg.locator("text=Perfil").count() else "")
    pg.close()
