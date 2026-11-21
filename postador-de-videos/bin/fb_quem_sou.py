"""Descobre QUEM está logado na janela (porta CDP): id, nome e e-mail(s) da conta, pela própria página de contato do FB.
Não muda nada. python fb_quem_sou.py <porta>"""
import json, re, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

LOG = Path(__file__).resolve().parent.parent / "logs"
if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
porta = int(sys.argv[1])
with sync_playwright() as p:
    ctx = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}").contexts[0]
    ck = {c["name"]: c["value"] for c in ctx.cookies("https://www.facebook.com")}
    uid = ck.get("c_user")
    print("c_user:", uid)
    if not uid:
        print("não está logada"); sys.exit(0)
    pg = ctx.new_page()
    pg.goto("https://www.facebook.com/", wait_until="domcontentloaded", timeout=120000)
    time.sleep(5)
    nome = (re.search(r'"NAME":"([^"]+)"', pg.content()) or ["", "?"])[1]
    print("nome:", nome)
    # e-mail: página de configurações de contato
    emails = set()
    for url in ("https://www.facebook.com/settings?tab=account&section=email",
                "https://accountscenter.facebook.com/personal_info/contact_points",
                "https://www.facebook.com/settings/?tab=account"):
        try:
            pg.goto(url, wait_until="domcontentloaded", timeout=60000); time.sleep(6)
            for m in re.findall(r"[\w.\-+]+@[\w.\-]+\.\w+", pg.inner_text("body")):
                if "facebook" not in m and "meta.com" not in m:
                    emails.add(m)
        except Exception:
            pass
    print("e-mails na conta:", sorted(emails) or "não achei na tela")
    # telefone (mascarado)
    tel = re.findall(r"\+?\d[\d\s\-]{6,}\d\d", pg.inner_text("body"))
    pg.screenshot(path=str(LOG / f"fb_quem_{porta}.png"))
    print("salvo print:", LOG / f"fb_quem_{porta}.png")
