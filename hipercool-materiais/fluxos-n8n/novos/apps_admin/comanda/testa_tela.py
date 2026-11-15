# Abre o painel e a mesa num Chrome sem janela, clica de verdade e tira prints. Uso: python testa_tela.py <codigo_loja> <senha>
import sys, json, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = "https://webhookn8n6.inovareinteligenciaartificial.com/webhook"
LOJA, SENHA = sys.argv[1], sys.argv[2]
OUT = Path(__file__).parent / "prints"; OUT.mkdir(exist_ok=True)
erros = []


def api(acao, **d):
    req = urllib.request.Request(BASE + "/comanda-api", data=json.dumps({"acao": acao, **d}).encode(), headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=60).read())


with sync_playwright() as p:
    b = p.chromium.launch(headless=True, channel="chrome", args=["--disable-gpu"])
    for nome, vp in (("pc", {"width": 1366, "height": 860}), ("cel", {"width": 390, "height": 844})):
        ctx = b.new_context(viewport=vp, locale="pt-BR", is_mobile=(nome == "cel"), has_touch=(nome == "cel"))
        pg = ctx.new_page()
        pg.on("pageerror", lambda e: erros.append(f"{nome}: {e}"))
        pg.on("console", lambda m: m.type == "error" and erros.append(f"{nome} console: {m.text}"))
        pg.on("dialog", lambda d: d.accept("teste de cancelamento"))
        pg.goto(f"{BASE}/comanda-painel?l={LOJA}")
        pg.fill("#sn", SENHA); pg.click("#ent")
        pg.wait_for_selector(".mesas", timeout=20000); pg.wait_for_timeout(800)
        pg.screenshot(path=OUT / f"{nome}_1_mesas.png", full_page=True)
        # lança itens na mesa 3 pelo painel
        pg.click('[data-m="3"]'); pg.wait_for_selector("[data-add]"); pg.click("[data-add]")
        pg.wait_for_selector("[data-p]"); pg.locator("[data-p]").first.click()
        pg.wait_for_selector("#ob"); pg.fill("#ob", "sem cebola"); pg.locator("#ok").last.click()
        pg.wait_for_timeout(300); pg.screenshot(path=OUT / f"{nome}_2_lancar.png")
        pg.click("#env"); pg.wait_for_selector("[data-receber], [data-add]", timeout=15000); pg.wait_for_timeout(600)
        pg.screenshot(path=OUT / f"{nome}_3_comanda.png")
        pg.keyboard.press("Escape"); pg.locator(".modal-fundo").first.click(position={"x": 5, "y": 5}) if pg.locator(".modal-fundo").count() else None
        for aba in ("cozinha", "caixa", "produtos", "estoque", "relatorios", "equipe", "config"):
            pg.evaluate(f"abrir('{aba}')"); pg.wait_for_timeout(1800)
            pg.screenshot(path=OUT / f"{nome}_4_{aba}.png", full_page=(nome == "pc"))
        # editar produto (modal) e receber a mesa 3
        pg.evaluate("abrir('produtos')"); pg.wait_for_selector("[data-ep]"); pg.locator("[data-ep]").first.click(); pg.wait_for_timeout(500)
        pg.screenshot(path=OUT / f"{nome}_5_editar_produto.png"); pg.locator("[data-fechar]").last.click()
        pg.evaluate("abrir('mesas')"); pg.wait_for_selector('[data-m="3"]'); pg.click('[data-m="3"]'); pg.wait_for_selector("[data-receber]")
        pg.click("[data-receber]"); pg.wait_for_selector("#fin"); pg.wait_for_timeout(800)
        pg.screenshot(path=OUT / f"{nome}_6_receber.png")
        pg.click("#fin"); pg.wait_for_timeout(1500)
        ctx.close()
    # mesa do cliente (celular)
    t = api("config_ver", token=api("login", loja=LOJA, login="dono", senha=SENHA)["token"])["qrs"][1]["t"]
    ctx = b.new_context(viewport={"width": 390, "height": 844}, locale="pt-BR", is_mobile=True, has_touch=True)
    pg = ctx.new_page(); pg.on("pageerror", lambda e: erros.append(f"mesa: {e}"))
    pg.goto(f"{BASE}/comanda-mesa?l={LOJA}&m=2&t={t}"); pg.wait_for_selector("[data-p]", timeout=20000); pg.wait_for_timeout(600)
    pg.screenshot(path=OUT / "mesa_1_cardapio.png")
    pg.locator("[data-p]").first.click(); pg.wait_for_selector("#ok"); pg.screenshot(path=OUT / "mesa_2_item.png")
    pg.click("#ok"); pg.wait_for_timeout(400); pg.click("#vc"); pg.wait_for_selector("#env"); pg.click("#env"); pg.wait_for_timeout(1500)
    pg.screenshot(path=OUT / "mesa_3_enviado.png")
    ctx.close(); b.close()
print("ERROS:", erros or "nenhum")
print("prints em", OUT)
