import sys
sys.path.insert(0, r"D:\logins-google")
import cofre
porta, _ = cofre.abrir("emersonjosiel2032@gmail.com", "about:blank", visivel=True)
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    ctx = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}").contexts[0]
    pg = [x for x in ctx.pages if "auth/audience" in (x.url or "")][-1]
    pg.mouse.click(568, 301)
    pg.wait_for_timeout(9000)
    pg.screenshot(path=r"D:\tmp\drive_chave\publico_salvo2.png", timeout=30000)
    t = pg.inner_text("body"); i = t.find("Usu\u00e1rios de teste")
    print(t[i:i+300])
