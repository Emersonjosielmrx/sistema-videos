"""Abre a página de planos da Rendi (logado pelo cofre) e mostra as opções. Com 'ativar', clica no plano grátis
SÓ se ele não pedir cartão (para no formulário de pagamento e avisa)."""
import re, sys
sys.path.insert(0, r"D:\logins-google")
import cofre
from playwright.sync_api import sync_playwright

CONTA = "aulacomia@gmail.com"
PASTA = r"D:\hipercool-materiais\fluxo-anuncio-api\provas"
ATIVAR = "ativar" in sys.argv
porta, proc = cofre.abrir(CONTA, url="about:blank", visivel=True)
with sync_playwright() as pw:
    br = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
    try:
        ctx = br.contexts[0]
        pg = ctx.new_page()
        cdp = ctx.new_cdp_session(pg)
        cdp.send("Network.enable")
        cdp.send("Network.setCacheDisabled", {"cacheDisabled": True})
        pg.goto("https://app.rendi.dev/plans", wait_until="networkidle", timeout=90000)
        pg.wait_for_timeout(6000)
        pg.screenshot(path=rf"{PASTA}\rendi_20_planos.png", full_page=True)
        print(re.sub(r"\s+", " ", pg.inner_text("body", timeout=30000))[:2500], flush=True)
        if ATIVAR:
            # o 1º "Upgrade" é o do plano Free ($0)
            cartao = pg.locator("text=For individuals who are exploring").locator("xpath=ancestor::*[.//button][1]")
            b = cartao.locator("button:has-text('Upgrade')").first
            if not b.count():
                b = pg.locator("button:has-text('Upgrade')").first
            print("botão:", b.count() and b.inner_text(), flush=True)
            if b.count():
                b.click(timeout=10000)
                pg.wait_for_timeout(8000)
                pg.screenshot(path=rf"{PASTA}\rendi_21_depois.png", full_page=True)
                t = pg.inner_text("body", timeout=30000)
                print("depois:", pg.url, "|", re.sub(r"\s+", " ", t)[:1200], flush=True)
                if re.search(r"card number|cartão|stripe", t + pg.url, re.I) or any("stripe" in f.url for f in pg.frames):
                    print("PARAR: pede cartão", flush=True)
    finally:
        cofre.fechar(proc, br, nome=CONTA)
