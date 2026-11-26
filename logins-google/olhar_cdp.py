# D:\logins-google\olhar_cdp.py
# Mostra o que esta na tela de um Chrome do cofre JA ABERTO (pela sessao interativa), sem abrir Chrome novo.
# Uso: python -X utf8 olhar_cdp.py <porta> [trecho_da_url]
# Saida: abas, URL, texto (1500 chars), botoes visiveis; print em D:\logins-google\olhar_cdp.png
import sys, time
from playwright.sync_api import sync_playwright
porta = int(sys.argv[1]); trecho = sys.argv[2] if len(sys.argv) > 2 else ""
with sync_playwright() as p:
    br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
    ctx = br.contexts[0]
    pgs = [x for x in ctx.pages if trecho in x.url] or ctx.pages
    pg = pgs[-1]
    time.sleep(2)
    print("ABAS:", [x.url[:80] for x in ctx.pages])
    print("URL:", pg.url)
    print("TEXTO:", pg.inner_text("body")[:1500].replace("\n", " | "))
    print("BOTOES:", [b.inner_text()[:40] for b in pg.query_selector_all("button, a[role=button]") if b.is_visible()][:30])
    pg.screenshot(path=r"D:\logins-google\olhar_cdp.png")
