"""Abre na tela, numa janela já aberta (porta CDP), a busca de e-mails do Facebook no Gmail e lista os assuntos +
horários. Mostra também o e-mail mais recente aberto. Só leitura.
    python fb_abrir_emails_tela.py <porta>"""
import re, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

LOG = Path(__file__).resolve().parent.parent / "logs"
if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
porta = int(sys.argv[1])
with sync_playwright() as p:
    ctx = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}").contexts[0]
    g = next((x for x in ctx.pages if "mail.google" in x.url), None) or ctx.new_page()
    g.goto("https://mail.google.com/mail/u/0/#search/from%3Afacebook+OR+c%C3%B3digo+OR+recupera%C3%A7%C3%A3o",
           wait_until="commit", timeout=120000)
    time.sleep(15)
    g.bring_to_front()
    t = " ".join(g.inner_text("body").split())
    i = t.find("Conversas") if "Conversas" in t else t.find("Conversations")
    print(t[i:i + 2200] if i >= 0 else t[:1500], flush=True)
    g.screenshot(path=str(LOG / f"fb_emails_tela_{porta}.png"))
    print("\n(janela do Gmail trazida pra frente na tela)", flush=True)
