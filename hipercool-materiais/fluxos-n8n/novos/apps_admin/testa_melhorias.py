# Testa as melhorias de 14/11 no navegador: simulador, legenda IA, impressão da Comanda, botões novos do Instagram.
import json, time
from pathlib import Path
from playwright.sync_api import sync_playwright
B = "https://webhookn8n6.inovareinteligenciaartificial.com/webhook"
OUT = Path(__file__).parent / "prints_melhorias"; OUT.mkdir(exist_ok=True)
for f in OUT.glob("*"): f.unlink()
erros, passos, D = [], [], {}


def passo(nome, fn):
    t = time.time()
    try: fn(); passos.append(f"OK     {time.time()-t:5.1f}s {nome}")
    except Exception as e: passos.append(f"FALHOU {time.time()-t:5.1f}s {nome}: {str(e).splitlines()[0][:170]}")


with sync_playwright() as p:
    b = p.chromium.launch(headless=True, channel="chrome", args=["--disable-gpu"])

    def simulador():
        pg = b.new_page(viewport={"width": 1280, "height": 900}); pg.on("pageerror", lambda e: erros.append(f"imovel: {e}"))
        pg.goto(f"{B}/imovel?l=ana-teste-imoveis-6d8d&c=IM101"); pg.wait_for_selector("#sim", timeout=20000)
        D["sim_padrao"] = pg.inner_text("#sr").replace("\n", " ")
        pg.select_option("#ss", "price"); pg.fill("#se", "100000"); pg.wait_for_timeout(300); D["sim_price_entrada_baixa"] = pg.inner_text("#sr").replace("\n", " ")
        pg.locator("#sim").scroll_into_view_if_needed(); pg.screenshot(path=OUT / "1_simulador.png"); pg.close()
    passo("simulador de financiamento (SAC, Price, entrada baixa)", simulador)

    def legenda():
        pg = b.new_page(viewport={"width": 1280, "height": 900}); pg.on("pageerror", lambda e: erros.append(f"painel imv: {e}"))
        pg.goto(f"{B}/imoveis-painel?l=ana-teste-imoveis-6d8d"); pg.fill("#sn", "segredo1"); pg.click("#ent"); pg.wait_for_selector(".kpis")
        pg.evaluate("abrir('imoveis')"); pg.wait_for_selector("[data-v]"); pg.locator("[data-v]").first.click(); pg.wait_for_selector(".modal #ig", timeout=20000)
        pg.click(".modal #ig"); pg.wait_for_function("document.querySelector('.modal #lg') && document.querySelector('.modal #lg').value.length > 50", timeout=90000)
        D["legenda"] = pg.input_value(".modal #lg")[:500]; D["botao_postar"] = pg.locator(".modal #ps").count() == 1
        pg.screenshot(path=OUT / "2_legenda.png"); pg.close()
    passo("vitrine: Postar no Instagram → legenda da IA", legenda)

    def impressao():
        ctx = b.new_context(viewport={"width": 1280, "height": 860}); pg = ctx.new_page(); pg.on("pageerror", lambda e: erros.append(f"comanda: {e}"))
        pg.goto(f"{B}/comanda-painel?l=boteco-humano-teste-6c1e"); pg.fill("#sn", "segredo1"); pg.click("#ent"); pg.wait_for_selector(".mesas")
        pg.click('[data-m="4"]'); pg.click("[data-add]"); pg.locator(".modal [data-p]").first.click(); M = pg.locator(".modal").last; M.locator("#ob").fill("bem passado"); M.locator("#ok").click()
        pg.click("#env"); pg.wait_for_selector("[data-imp]", timeout=20000)
        with ctx.expect_page() as w: pg.click("[data-imp]")
        cupom = w.value; cupom.wait_for_load_state(); D["cupom_conta"] = cupom.inner_text("body")[:300]; cupom.screenshot(path=OUT / "3_cupom_conta.png")
        pg.locator(".modal-fundo").last.click(position={"x": 3, "y": 3}); pg.evaluate("abrir('cozinha')"); pg.wait_for_selector("#impn")
        with ctx.expect_page() as w2: pg.click("#impn")
        c2 = w2.value; c2.wait_for_load_state(); D["cupom_cozinha"] = c2.inner_text("body")[:300]; c2.screenshot(path=OUT / "4_cupom_cozinha.png"); ctx.close()
    passo("comanda: imprimir conta e pedido da cozinha", impressao)

    def insta():
        pg = b.new_page(viewport={"width": 1280, "height": 900}); pg.on("pageerror", lambda e: erros.append(f"insta: {e}"))
        pg.goto(f"{B}/insta-painel?c=lucrocomia"); pg.fill("#sn", "segredo1"); pg.click("#ent"); pg.wait_for_selector(".kpis")
        pg.click('[data-aba="sorteio"]'); pg.wait_for_timeout(1500); D["sorteio_anunciado"] = pg.locator("text=Anunciado").count(); pg.screenshot(path=OUT / "5_sorteios.png")
        pg.click('[data-aba="gincana"]'); pg.wait_for_timeout(1500); D["gincana_arte"] = pg.locator("text=Arte do pódio").count(); pg.screenshot(path=OUT / "6_gincana.png")
        pg.click('[data-aba="mencao"]'); pg.wait_for_timeout(1500); D["mencao_erro_visivel"] = pg.locator(".selo.er").count(); pg.screenshot(path=OUT / "7_mencao.png")
        pg.click('[data-aba="site"]'); pg.wait_for_selector("#cp", timeout=15000); D["site_compartilhar"] = True; pg.close()
    passo("instagram: anunciado, arte do pódio, erro de envio visível, compartilhar site", insta)
    b.close()
print("\n".join(passos)); print("ERROS:", erros or "nenhum"); print(json.dumps(D, ensure_ascii=False, indent=1))
