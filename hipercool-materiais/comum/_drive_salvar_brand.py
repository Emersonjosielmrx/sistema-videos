import sys, re
sys.path.insert(0, r"D:\logins-google")
import cofre
porta, _ = cofre.abrir("emersonjosiel2032@gmail.com", "about:blank", visivel=True)
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    ctx = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}").contexts[0]
    pg = ctx.new_page()
    pg.goto("https://console.cloud.google.com/auth/branding?project=rclone-recap", timeout=120000, wait_until="domcontentloaded")
    pg.wait_for_timeout(15000)
    n = pg.get_by_label("Nome do app").first
    n.fill("rclone recap")
    pg.wait_for_timeout(1000)
    pg.get_by_role("button", name=re.compile(r"^\s*Salvar\s*$")).last.click(timeout=15000)
    pg.wait_for_timeout(10000)
    t = pg.inner_text("body")
    for k in ("erro", "Erro", "obrigat", "salv", "Salv"):
        for m in re.finditer(k, t):
            print("..", t[max(0, m.start()-80):m.start()+120].replace("\n", " "))
            break
    pg.screenshot(path=r"D:\tmp\drive_chave\branding_salvo.png", full_page=True)
    pg.goto("https://console.cloud.google.com/auth/audience?project=rclone-recap", timeout=120000, wait_until="domcontentloaded")
    pg.wait_for_timeout(15000)
    b = pg.get_by_role("button", name=re.compile(r"Publicar app", re.I)).first
    print("publicar desativado:", b.get_attribute("aria-disabled"))
    t = pg.inner_text("body"); i = t.find("Status de publica"); print(t[i:i+250])
