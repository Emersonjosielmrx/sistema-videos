"""Login no Facebook numa janela JÁ ABERTA (porta CDP), acompanhando a tela a cada 5 s enquanto a dona resolve captcha.
Lê código no Gmail da mesma conta se o FB pedir. Alarme a cada vez que precisar da dona. Senha só no argumento.
    python fb_login_janela.py <porta> <email_ou_numero> <senha> [--email-gmail <email>]"""
import ctypes, re, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

LOG = Path(__file__).resolve().parent.parent / "logs"
if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
porta, login, senha = int(sys.argv[1]), sys.argv[2], sys.argv[3]
tag = re.sub(r"\W", "", login.split("@")[0])[:20]


def bip():
    for f in (880, 1175, 1568):
        ctypes.windll.kernel32.Beep(f, 300)


def estado(pg, ctx):
    ck = {c["name"]: c["value"] for c in ctx.cookies("https://www.facebook.com")}
    corpo = " ".join(pg.inner_text("body").split())
    u = pg.url
    if "c_user" in ck and "/login" not in u and "/checkpoint" not in u and "two_step" not in u:
        return "logado", corpo
    if re.search(r"Insira os caracteres|captcha|confirmar que este login está sendo feito por um humano", corpo, re.I):
        return "captcha", corpo
    if re.search(r"aprovar|aprove|outro dispositivo|notificação.*celular|check your notifications|approve", corpo, re.I):
        return "aprovar", corpo
    if re.search(r"insira o código|digite o código|código de 6|enter.*code|código.*enviamos|enviamos um código", corpo, re.I):
        return "codigo", corpo
    if pg.locator("input[name=email]").count() and pg.locator("input[name=pass]").count():
        return "login", corpo
    return "outro", corpo


with sync_playwright() as p:
    ctx = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}").contexts[0]
    pg = next((x for x in ctx.pages if "facebook.com" in x.url), None) or ctx.new_page()
    pg.bring_to_front()
    st, corpo = estado(pg, ctx)
    if st != "login":
        pg.goto("https://www.facebook.com/", wait_until="domcontentloaded", timeout=120000); time.sleep(6)
        st, corpo = estado(pg, ctx)
    if st == "login":
        pg.fill("input[name=email]", login); time.sleep(0.4)
        pg.fill("input[name=pass]", senha); time.sleep(0.4)
        pg.keyboard.press("Enter")
        time.sleep(12)
    ultimo, avisou = None, 0
    for i in range(240):  # até 20 min
        st, corpo = estado(pg, ctx)
        if st != ultimo:
            pg.screenshot(path=str(LOG / f"fb_login_{tag}_{i:03d}_{st}.png"))
            print(f"{time.strftime('%H:%M:%S')} {st}: {corpo[:220]}", flush=True)
            ultimo = st
        if st == "logado":
            nome = re.search(r'"NAME":"([^"]+)"', pg.content())
            print("LOGADO como", nome.group(1) if nome else "?", "| c_user",
                  {c["name"]: c["value"] for c in ctx.cookies("https://www.facebook.com")}.get("c_user"), flush=True)
            break
        if st in ("captcha", "aprovar", "codigo", "outro") and time.time() - avisou > 60:
            bip(); avisou = time.time()
        if st == "login" and i > 2:
            print("voltou pro login sem logar", flush=True)
            break
        time.sleep(5)
