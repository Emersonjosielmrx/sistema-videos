# Prints do painel, do site e da página do imóvel (Chrome sem janela). Uso: python testa_tela.py <codigo> <senha>
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
BASE = "https://webhookn8n6.inovareinteligenciaartificial.com/webhook"
LOJA, SENHA = sys.argv[1], sys.argv[2]
OUT = Path(__file__).parent / "prints"; OUT.mkdir(exist_ok=True)
erros = []
with sync_playwright() as p:
    b = p.chromium.launch(headless=True, channel="chrome", args=["--disable-gpu", "--autoplay-policy=no-user-gesture-required"])
    for nome, vp in (("pc", {"width": 1366, "height": 860}), ("cel", {"width": 390, "height": 844})):
        ctx = b.new_context(viewport=vp, locale="pt-BR", is_mobile=(nome == "cel"), has_touch=(nome == "cel"))
        pg = ctx.new_page()
        pg.on("pageerror", lambda e, n=nome: erros.append(f"{n}: {e}"))
        pg.goto(f"{BASE}/imoveis-painel?l={LOJA}"); pg.fill("#sn", SENHA); pg.click("#ent")
        pg.wait_for_selector(".kpis", timeout=20000); pg.wait_for_timeout(700); pg.screenshot(path=OUT / f"{nome}_1_inicio.png", full_page=True)
        pg.evaluate("abrir('imoveis')"); pg.wait_for_selector(".im", timeout=15000); pg.wait_for_timeout(1500); pg.screenshot(path=OUT / f"{nome}_2_imoveis.png", full_page=True)
        pg.locator("[data-e]").first.click(); pg.wait_for_selector("#tt", timeout=15000); pg.wait_for_timeout(1500); pg.screenshot(path=OUT / f"{nome}_3_editar.png")
        pg.locator(".modal").evaluate("m => m.scrollTop = 900"); pg.wait_for_timeout(300); pg.screenshot(path=OUT / f"{nome}_3b_editar.png")
        pg.locator("[data-fechar]").last.click()
        pg.locator("[data-v]").first.click(); pg.wait_for_selector("video", timeout=15000); pg.wait_for_timeout(2500); pg.screenshot(path=OUT / f"{nome}_4_video.png")
        pg.locator("[data-fechar]").last.click()
        pg.evaluate("abrir('leads')"); pg.wait_for_timeout(1500); pg.screenshot(path=OUT / f"{nome}_5_leads.png")
        pg.goto(f"{BASE}/imoveis?l={LOJA}"); pg.wait_for_selector(".im", timeout=15000); pg.wait_for_timeout(1500); pg.screenshot(path=OUT / f"{nome}_6_site.png", full_page=True)
        pg.locator(".im").first.click(); pg.wait_for_selector("h1", timeout=15000); pg.wait_for_timeout(2500); pg.screenshot(path=OUT / f"{nome}_7_imovel.png", full_page=True)
        pg.locator("[data-i]").first.click(); pg.wait_for_timeout(800); pg.screenshot(path=OUT / f"{nome}_8_galeria.png")
        ctx.close()
    b.close()
print("ERROS:", erros or "nenhum")
