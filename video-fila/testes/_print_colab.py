# Print do card COLAB do painel :8790 (24/10). python _print_colab.py <largura> <saida.png>
import sys
from playwright.sync_api import sync_playwright

larg, saida = int(sys.argv[1]), sys.argv[2]
with sync_playwright() as p:
    br = p.chromium.launch()
    pg = br.new_page(viewport={"width": larg, "height": 900})
    erros = []
    pg.on("pageerror", lambda e: erros.append(str(e)))
    pg.goto("http://127.0.0.1:8790/#geral", wait_until="domcontentloaded", timeout=60000)
    pg.wait_for_timeout(15000)
    pg.evaluate("medir()")
    pg.wait_for_selector('[data-h="colab"]', state="attached", timeout=120000)
    card = pg.locator('[data-h="colab"]')
    card.locator("summary").click()
    card.locator("input").fill("energy")
    pg.wait_for_timeout(500)
    card.scroll_into_view_if_needed()
    card.screenshot(path=saida)
    print("linhas visíveis com filtro 'energy':", card.locator(".ccol:visible").count())
    print("largura da página:", pg.evaluate("document.documentElement.scrollWidth"), "janela:", larg)
    print("erros JS:", erros[:5] or "nenhum")
    br.close()
