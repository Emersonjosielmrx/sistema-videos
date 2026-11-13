import re, sys
sys.path.insert(0, r"D:\logins-google")
import cofre
porta, _ = cofre.abrir("emersonjosiel2032@gmail.com", "about:blank", visivel=True)
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    ctx = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}").contexts[0]
    pg = [x for x in ctx.pages if "oauth" in (x.url or "")][-1]
    pg.get_by_role("button", name=re.compile(r"^\s*(Permitir|Allow|Continuar|Continue)\s*$", re.I)).last.click(timeout=15000)
    pg.wait_for_timeout(10000)
    print(pg.url[:100]); print(pg.inner_text("body")[:300])
