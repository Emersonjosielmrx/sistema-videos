"""Descobre as categorias da Basefy e do AccsMarket e lista anúncios de YouTube.
Uso: python canais_cats.py saida.json"""
import json, re, sys, time
from playwright.sync_api import sync_playwright

out = {}
JS_LINKS = "() => [...document.querySelectorAll('a')].map(a => [a.href, a.innerText.replace(/\\s+/g,' ').trim().slice(0,300)])"
with sync_playwright() as p:
    br = p.chromium.launch(channel="chrome", headless=False, args=["--window-position=-2000,0", "--disable-blink-features=AutomationControlled"])
    pg = br.new_context(locale="pt-BR", viewport={"width": 1280, "height": 1800}).new_page()
    pg.goto("https://basefy.io", wait_until="domcontentloaded", timeout=60000); time.sleep(7)
    cats = sorted({h for h, t in pg.evaluate(JS_LINKS) if "basefy.io/c/" in h})
    out["basefy_cats"] = cats
    print(cats, flush=True)
    alvos = [c for c in cats if re.search(r"(?i)youtube|redes|social|canal|conta", c)] or cats
    alvos = [c.split("?")[0] for c in alvos]
    for c in dict.fromkeys(alvos + ["https://basefy.io/c/youtube", "https://basefy.io/c/redes-sociais", "https://basefy.io/c/emails"]):
        u = c + "?q=youtube"
        try:
            pg.goto(u, wait_until="domcontentloaded", timeout=60000); time.sleep(7)
            for _ in range(6):
                pg.mouse.wheel(0, 3000); time.sleep(1.2)
            itens = {h: t for h, t in pg.evaluate(JS_LINKS) if "/p/" in h}
            out[u] = {"url_final": pg.url, "itens": list(itens.items())}
        except Exception as e:
            out[u] = {"erro": str(e)[:200]}
        print(u, len(out[u].get("itens", [])), flush=True)
    for u in ("https://accsmarket.com/en/catalog/gmail", "https://accsmarket.com/en"):
        try:
            pg.goto(u, wait_until="domcontentloaded", timeout=60000); time.sleep(7)
            out["accs_cats" + u[-5:]] = sorted({h for h, t in pg.evaluate(JS_LINKS) if "/catalog/" in h})
        except Exception as e:
            out["accs_cats" + u[-5:]] = str(e)[:200]
    br.close()
json.dump(out, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
