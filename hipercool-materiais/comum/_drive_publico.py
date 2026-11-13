r"""Página Público-alvo do rclone-recap (2032): mostra o estado; com 'add' adiciona a 2032 como usuária de teste."""
import re
import sys
from pathlib import Path

sys.path.insert(0, r"D:\logins-google")
import cofre  # noqa: E402

SAIDA = Path(r"D:\tmp\drive_chave")
CONTA = "emersonjosiel2032@gmail.com"
porta, _ = cofre.abrir(CONTA, "about:blank", visivel=True)
from playwright.sync_api import sync_playwright  # noqa: E402

with sync_playwright() as p:
    br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
    ctx = br.contexts[0]
    pg = ctx.new_page()
    pg.goto("https://console.cloud.google.com/auth/audience?project=rclone-recap", timeout=120000,
            wait_until="domcontentloaded")
    pg.wait_for_timeout(15000)
    t = pg.inner_text("body")
    i = t.find("Status")
    print(t[max(0, i - 200):i + 1500] if i >= 0 else t[:2000], flush=True)
    pg.screenshot(path=str(SAIDA / "publico.png"), full_page=True, timeout=30000)
    if "add" in sys.argv:
        b = pg.get_by_role("button", name=re.compile(r"Add users|Adicionar usuários", re.I))
        b.first.click(timeout=15000)
        pg.wait_for_timeout(4000)
        campo = pg.locator("[role=dialog] input, mat-dialog-container input, cfc-panel input").last
        campo.click(timeout=10000)
        campo.fill(CONTA)
        pg.keyboard.press("Enter")
        pg.wait_for_timeout(2000)
        pg.screenshot(path=str(SAIDA / "publico_add.png"), timeout=30000)
        s = pg.get_by_role("button", name=re.compile(r"^\s*(Salvar|Save)\s*$", re.I))
        s.last.click(timeout=15000)
        pg.wait_for_timeout(8000)
        pg.screenshot(path=str(SAIDA / "publico_salvo.png"), full_page=True, timeout=30000)
        t = pg.inner_text("body")
        i = t.find("Usuários de teste")
        print("DEPOIS:", t[i:i + 600] if i >= 0 else t[:800], flush=True)
