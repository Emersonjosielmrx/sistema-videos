"""Só olha o que tem na janela (porta CDP): se está logada (c_user) e o texto/URL da tela. Não digita nada.
    python fb_ver_tela.py <porta>"""
import re, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

LOG = Path(__file__).resolve().parent.parent / "logs"
if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
porta = int(sys.argv[1])
with sync_playwright() as p:
    ctx = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}").contexts[0]
    ck = {c["name"]: c["value"] for c in ctx.cookies("https://www.facebook.com")}
    pg = next((x for x in ctx.pages if "facebook.com" in x.url), None) or (ctx.pages[0] if ctx.pages else None)
    print("c_user:", ck.get("c_user"))
    if pg:
        pg.bring_to_front()
        print("url:", pg.url)
        try:
            print("tela:", " ".join(pg.inner_text("body").split())[:260])
        except Exception as x:
            print("tela ilegível:", str(x)[:80])
        if ck.get("c_user"):
            m = re.search(r'"NAME":"([^"]+)"', pg.content())
            print("LOGADA como:", m.group(1) if m else "?")
        pg.screenshot(path=str(LOG / f"fb_ver_{porta}.png"))
