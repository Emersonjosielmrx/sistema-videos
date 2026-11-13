import sys, re
sys.path.insert(0, r"D:\logins-google")
import cofre
porta, _ = cofre.abrir("emersonjosiel2032@gmail.com", "about:blank", visivel=True)
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    ctx = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}").contexts[0]
    pg = ctx.new_page()
    pg.goto("https://console.cloud.google.com/auth/audience?project=rclone-recap", timeout=120000, wait_until="domcontentloaded")
    pg.wait_for_timeout(15000)
    b = pg.get_by_role("button", name=re.compile(r"Publicar app", re.I)).first
    did = b.get_attribute("aria-describedby")
    print("describedby:", did)
    for i in (did or "").split():
        el = pg.locator(f"#{i}")
        print("msg:", el.inner_text() if el.count() else "-")
    b.hover(); pg.wait_for_timeout(2000)
    print("tooltip:", pg.locator("mat-tooltip-component, .mat-mdc-tooltip, [role=tooltip]").all_inner_texts())
