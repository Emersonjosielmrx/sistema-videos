"""Lê (só lê) os e-mails do Facebook no Gmail de uma conta do cofre, pelo IP fixo dela (fish_proxy), e fecha o Chrome
que abriu. Para saber em que pé está o Facebook da conta (recuperação, código, bloqueio) sem tocar no Facebook.
    python fb_ler_emails.py <email>"""
import re, sys, time
sys.path.insert(0, r"D:\logins-google"); sys.path.insert(0, r"D:\hipercool-materiais\comum\fish_audio")
import fish_audio
from playwright.sync_api import sync_playwright

if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
email = sys.argv[1]
cofre, n = fish_audio.checar_conta(email)  # recusa Kaggle; exige IP próprio
px = fish_audio._subir_ponte(n)
porta, proc = cofre.abrir(email, extra=(f"--proxy-server=127.0.0.1:{px}",))
try:
    with sync_playwright() as p:
        ctx = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}").contexts[0]
        pg = ctx.new_page()
        for tent in range(2):  # pelo proxy o Gmail às vezes demora a abrir
            try:
                pg.goto("https://mail.google.com/mail/u/0/#search/facebook", wait_until="commit", timeout=120000)
                break
            except Exception:
                if tent:
                    raise
                time.sleep(10)
        time.sleep(20)
        t = " ".join(pg.inner_text("body").split())
        i = t.find("Conversations") if "Conversations" in t else t.find("Conversas")
        print(f"== {email} (saída rnprmtfo-{n})")
        print(t[i:i + 3000] if i >= 0 else t[:1500])
        pg.close()
finally:
    cofre.fechar(proc, nome=email.split("@")[0]) if hasattr(cofre, "fechar") else None
