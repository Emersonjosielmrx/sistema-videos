r"""Continua o OAuth do rclone na aba aberta pelo passo 20 (conta 2032): escolhe a conta, "Avançado/Acessar",
"Continuar"/"Permitir". Para se pedir senha. Prints em D:\tmp\drive_chave\."""
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, r"D:\logins-google")
import cofre  # noqa: E402

SAIDA = Path(r"D:\tmp\drive_chave")
porta, _ = cofre.abrir("emersonjosiel2032@gmail.com", "about:blank", visivel=True)
from playwright.sync_api import sync_playwright  # noqa: E402

with sync_playwright() as p:
    br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
    ctx = br.contexts[0]
    pg = [x for x in ctx.pages if "accounts.google.com" in (x.url or "") or "127.0.0.1:53682" in (x.url or "")]
    if not pg:
        print("aba do oauth não achada", [x.url[:80] for x in ctx.pages])
        sys.exit(1)
    pg = pg[-1]
    for i in range(8):
        pg.wait_for_timeout(5000)
        url = pg.url or ""
        t = pg.inner_text("body")[:2500]
        pg.screenshot(path=str(SAIDA / f"oauth_{i}.png"), timeout=30000)
        print(f"--- {i} {url[:90]}\n{t[:400]}\n", flush=True)
        if "127.0.0.1:53682" in url or "Success" in t or "sucesso" in t.lower():
            print("VOLTOU PRO RCLONE", flush=True)
            break
        if re.search(r"digite sua senha|enter your password", t, re.I):
            print("PEDE SENHA — parei", flush=True)
            break
        for rot in (r"^emersonjosiel2032@gmail\.com$", r"^Emerson2032$", r"^(Avançado|Advanced)$",
                    r"^(Acessar|Go to) .*\(não seguro\)|unsafe", r"^(Continuar|Continue)$", r"^(Permitir|Allow)$",
                    r"Selecionar tudo|Select all"):
            loc = pg.get_by_text(re.compile(rot, re.I))
            if loc.count():
                try:
                    loc.first.click(timeout=8000)
                    print("clicou", rot, flush=True)
                    break
                except Exception as e:  # noqa: BLE001
                    print("falhou clicar", rot, type(e).__name__, flush=True)
