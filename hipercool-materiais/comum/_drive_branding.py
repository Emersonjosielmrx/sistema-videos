r"""rclone-recap (2032): mostra a página Branding; com 'ver' só mostra. Com 'publicar' tenta Público-alvo > Publicar app.
Prints em D:\tmp\drive_chave\."""
import re
import sys
from pathlib import Path

sys.path.insert(0, r"D:\logins-google")
import cofre  # noqa: E402

SAIDA = Path(r"D:\tmp\drive_chave")
porta, _ = cofre.abrir("emersonjosiel2032@gmail.com", "about:blank", visivel=True)
from playwright.sync_api import sync_playwright  # noqa: E402

with sync_playwright() as p:
    ctx = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}").contexts[0]
    pg = ctx.new_page()
    if "publicar" in sys.argv:
        pg.goto("https://console.cloud.google.com/auth/audience?project=rclone-recap", timeout=120000,
                wait_until="domcontentloaded")
        pg.wait_for_timeout(15000)
        pg.get_by_role("button", name=re.compile(r"Publicar app|Publish app", re.I)).first.click(timeout=15000)
        pg.wait_for_timeout(5000)
        pg.screenshot(path=str(SAIDA / "publicar_1.png"), timeout=30000)
        print(pg.inner_text("body")[-1500:], flush=True)
        b = pg.get_by_role("button", name=re.compile(r"^\s*(Confirmar|Confirm)\s*$", re.I))
        if b.count():
            b.last.click(timeout=15000)
            pg.wait_for_timeout(8000)
        pg.screenshot(path=str(SAIDA / "publicar_2.png"), full_page=True, timeout=30000)
        t = pg.inner_text("body")
        i = t.find("Status de publica")
        print("DEPOIS:", t[i:i + 300], flush=True)
    else:
        pg.goto("https://console.cloud.google.com/auth/branding?project=rclone-recap", timeout=120000,
                wait_until="domcontentloaded")
        pg.wait_for_timeout(15000)
        pg.screenshot(path=str(SAIDA / "branding.png"), full_page=True, timeout=30000)
        t = pg.inner_text("body")
        i = t.find("Informações do app")
        print(t[max(0, i):i + 2500] if i >= 0 else t[:2500], flush=True)
