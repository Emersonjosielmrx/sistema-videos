"""Debug: abre o composer da Página, sobe o vídeo e mostra o que acontece ao clicar Avançar (prints). NÃO compartilha.
    python fb_debug_avancar.py <porta> <asset> "<nome>" <video>"""
import sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright
import fb_reel_bs as F
porta, asset, nome, video = sys.argv[1:5]
with sync_playwright() as p:
    ctx = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}").contexts[0]
    pg = ctx.new_page(); pg.set_viewport_size({"width": 1366, "height": 900})
    pg.goto(F.COMPOSER.format(asset), wait_until="domcontentloaded", timeout=90000); time.sleep(12)
    F._fechar_avisos(pg)
    print(F._so_facebook(pg, nome))
    with pg.expect_file_chooser(timeout=20000) as fc:
        F._botao(pg, "Adicionar vídeo").click()
    fc.value.set_files(video, timeout=300000)
    time.sleep(40)
    for i in range(3):
        bts = pg.get_by_role("button", name="Avançar", exact=True)
        print("avancar count", bts.count(), [ (bts.nth(j).is_visible(), bts.nth(j).get_attribute("aria-disabled"), bts.nth(j).bounding_box()) for j in range(bts.count())])
        b = F._botao(pg, "Avançar")
        if not b:
            break
        b.click(); time.sleep(10)
        pg.screenshot(path=str(F.LOG / f"fb_debug_av_{i}.png"))
        etapa = [t for t in ("Criar", "Editar", "Compartilhar") if pg.get_by_text(t, exact=True).count()]
        print("depois do clique", i, "url", pg.url[-60:], "dialogs:", pg.locator("[role=dialog]").count())
    pg.goto("about:blank")
    pg.close()
