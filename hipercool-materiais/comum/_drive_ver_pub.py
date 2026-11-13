import sys
sys.path.insert(0, r"D:\logins-google")
import cofre
porta, _ = cofre.abrir("emersonjosiel2032@gmail.com", "about:blank", visivel=True)
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    ctx = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}").contexts[0]
    pg = ctx.new_page()
    pg.goto("https://console.cloud.google.com/auth/branding?project=rclone-recap", timeout=120000, wait_until="domcontentloaded")
    pg.wait_for_timeout(15000)
    campo = pg.get_by_label("Nome do app")
    print("nome do app:", repr(campo.first.input_value()) if campo.count() else "campo?")
    pg.goto("https://console.cloud.google.com/auth/overview?project=rclone-recap", timeout=120000, wait_until="domcontentloaded")
    pg.wait_for_timeout(15000)
    print(pg.inner_text("body")[:1800])
    pg.screenshot(path=r"D:\tmp\drive_chave\visao.png", full_page=True)
