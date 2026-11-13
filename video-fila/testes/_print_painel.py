# Print do painel :8790 em uma largura + erros de JavaScript (24/10). python _print_painel.py <largura> <saida.png> [#aba]
import sys
from playwright.sync_api import sync_playwright

larg, saida = int(sys.argv[1]), sys.argv[2]
aba = sys.argv[3] if len(sys.argv) > 3 else "#geral"
with sync_playwright() as p:
    br = p.chromium.launch()
    pg = br.new_page(viewport={"width": larg, "height": 900})
    erros = []
    pg.on("pageerror", lambda e: erros.append(str(e)))
    pg.on("console", lambda m: erros.append(m.text) if m.type == "error" else None)
    pg.goto("http://127.0.0.1:8790/" + aba, wait_until="domcontentloaded", timeout=60000)
    pg.wait_for_timeout(20000)
    el = pg.locator("#geral-pcs")
    el.scroll_into_view_if_needed()
    el.screenshot(path=saida)
    print("largura da pÃ¡gina:", pg.evaluate("document.documentElement.scrollWidth"), "janela:", larg)
    print("kanban carregado:", pg.evaluate("!!(window.K || (typeof K !== 'undefined' && K))"), "selects:", pg.locator(".kmover").count())
    print("erros JS:", erros[:5] or "nenhum")
    br.close()


