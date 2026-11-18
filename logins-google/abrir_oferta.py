"""Abre contas na oferta AI Ultra, UMA por vez, e só deixa na tela a que estiver COM A OFERTA (tenta 2x no erro do
Google). As que não abrem são fechadas e puladas. Uso: abrir_oferta.py conta1 conta2 ... (para na 1ª que der certo)."""
import sys, time
sys.path.insert(0, r"D:\logins-google")
import cofre
from playwright.sync_api import sync_playwright
LINK = open(r"C:\Users\Haylla\AppData\Local\Temp\ultra_link.txt").read().strip()
for nome in sys.argv[1:]:
    email = nome if "@" in nome else nome + "@gmail.com"
    porta, proc = cofre.abrir(email, "about:blank", visivel=False)
    ok, motivo = False, ""
    with sync_playwright() as p:
        br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
        pg = br.contexts[0].pages[0] if br.contexts[0].pages else br.contexts[0].new_page()
        for tent in range(2):
            pg.goto(LINK, wait_until="domcontentloaded", timeout=90000); time.sleep(14)
            t = pg.evaluate("() => document.body.innerText")
            if ("12 meses" in t or "12-month" in t) and "indisponível" not in t and "unavailable" not in t.lower():
                ok = True; break
            motivo = t[:90].replace("\n", " / ")
            if "erro no nosso sistema" not in t and "went wrong" not in t:
                break
        if ok:
            pg.bring_to_front()
            cdp = br.new_browser_cdp_session()
            print(f"ABERTA NA TELA: {email} (porta {porta})")
            break
        print(f"pulei {email}: {motivo}")
        try:
            br.new_browser_cdp_session().send("Browser.close")
        except Exception:
            pass
