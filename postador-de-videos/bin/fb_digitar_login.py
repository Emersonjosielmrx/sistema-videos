"""Digita e-mail e senha no Facebook da janela já aberta (porta CDP), devagar como pessoa, e acompanha a tela.
Captcha/código = alarme e espera a dona. Senha só no argumento.
    python fb_digitar_login.py <porta> <login> <senha>"""
import ctypes, random, re, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

LOG = Path(__file__).resolve().parent.parent / "logs"
if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
porta, login, senha = int(sys.argv[1]), sys.argv[2], sys.argv[3]


def bip():
    for f in (880, 1175, 1568):
        ctypes.windll.kernel32.Beep(f, 300)


with sync_playwright() as p:
    ctx = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}").contexts[0]
    fbs = [x for x in ctx.pages if "facebook.com" in x.url]
    pg = fbs[-1]
    for x in fbs[:-1]:  # deixa só 1 aba do Facebook
        x.close()
    pg.bring_to_front()
    time.sleep(1)
    em = pg.locator("input[name=email]").first
    em.click(); time.sleep(0.6)
    em.fill("")
    pg.keyboard.type(login, delay=random.randint(90, 160)); time.sleep(0.8)
    pw = pg.locator("input[name=pass]").first
    pw.click(); time.sleep(0.5)
    pg.keyboard.type(senha, delay=random.randint(110, 180)); time.sleep(0.9)
    pg.keyboard.press("Enter")
    print("digitado; esperando a resposta do Facebook", flush=True)
    ultimo = None
    for i in range(240):  # até 20 min
        time.sleep(5)
        try:
            ck = {c["name"]: c["value"] for c in ctx.cookies("https://www.facebook.com")}
            corpo = " ".join(pg.inner_text("body").split())
        except Exception:
            continue
        u = pg.url
        if "c_user" in ck and "/login" not in u and "checkpoint" not in u and "two_step" not in u:
            nome = re.search(r'"NAME":"([^"]+)"', pg.content())
            print(f"{time.strftime('%H:%M:%S')} LOGADO como {nome.group(1) if nome else '?'} (c_user {ck['c_user']})", flush=True)
            pg.screenshot(path=str(LOG / "fb_digitar_logado.png"))
            break
        st = ("captcha" if re.search(r"Insira os caracteres|humano", corpo) else
              "senha_errada" if re.search(r"incorret|não corresponde|wrong", corpo, re.I) else
              "codigo" if re.search(r"código|code", corpo, re.I) and "two_step" in u or "checkpoint" in u else
              "login" if pg.locator("input[name=pass]").count() else u.split("?")[0][-50:])
        if st != ultimo:
            print(f"{time.strftime('%H:%M:%S')} {st} | {corpo[:200]}", flush=True)
            pg.screenshot(path=str(LOG / f"fb_digitar_{i:03d}_{st}.png"))
            if st != "login":
                bip()
            ultimo = st
        if st == "senha_errada":
            break
        if st == "login" and i > 3:
            print("voltou pro login sem logar", flush=True)
            break
