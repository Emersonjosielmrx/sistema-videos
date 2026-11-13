# Print da aba Contas do painel :8790 (28/10). python _print_contas.py <largura> <saida.png>
import sys
from playwright.sync_api import sync_playwright

larg, saida = int(sys.argv[1]), sys.argv[2]
with sync_playwright() as p:
    br = p.chromium.launch()
    pg = br.new_page(viewport={"width": larg, "height": 1100})
    erros = []
    pg.on("pageerror", lambda e: erros.append(str(e)))
    pg.on("console", lambda m: erros.append(m.text) if m.type == "error" else None)
    pg.goto("http://127.0.0.1:8790/#contas", wait_until="domcontentloaded", timeout=60000)
    pg.wait_for_timeout(15000)
    pg.screenshot(path=saida, full_page=False)
    print("largura da página:", pg.evaluate("document.documentElement.scrollWidth"), "janela:", larg)
    print("MORTA na tabela:", pg.locator("#t-contas >> text=MORTA").count())
    print("erros JS:", erros[:5] or "nenhum")
    br.close()
