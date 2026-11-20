"""Abre o composer de reel do Business Suite e o seletor 'Postar em'; print + itens. Só olha (fecha sem salvar).
    python fb_explorar_postar_em.py <porta> <asset_id>"""
import sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright
LOG = Path(__file__).resolve().parent.parent / "logs"
with sync_playwright() as p:
    b = p.chromium.connect_over_cdp(f"http://127.0.0.1:{int(sys.argv[1])}")
    pg = b.contexts[0].new_page()
    pg.set_viewport_size({"width": 1366, "height": 900})
    pg.goto(f"https://business.facebook.com/latest/reels_composer?asset_id={sys.argv[2]}", wait_until="domcontentloaded", timeout=60000)
    time.sleep(12)
    for _ in range(3):
        pg.keyboard.press("Escape"); time.sleep(1)
        for e in pg.query_selector_all('[aria-label="Fechar"], [aria-label="Close"]'):
            try:
                if e.is_visible():
                    e.click(); time.sleep(1)
            except Exception:
                pass
    pg.screenshot(path=str(LOG / "fb_bs_antes.png"))
    pg.get_by_text("Postar em", exact=True).first.scroll_into_view_if_needed()
    caixa = pg.locator("div[role=combobox], div[role=button][aria-haspopup]").filter(has_text="msenergycap").first
    if not caixa.count():
        caixa = pg.get_by_text("MS energy e msenergycap").first
    caixa.click()
    time.sleep(3)
    pg.screenshot(path=str(LOG / "fb_bs_postar_em.png"))
    for e in pg.query_selector_all("[role=checkbox], [role=option], input[type=checkbox], [role=switch]"):
        if e.is_visible():
            print("item:", e.get_attribute("aria-label"), e.get_attribute("aria-checked"), (e.inner_text() or "")[:50])
    pg.close()
