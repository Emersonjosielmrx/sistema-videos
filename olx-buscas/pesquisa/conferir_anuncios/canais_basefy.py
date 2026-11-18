"""Basefy: descobre a busca pelo campo do site e lista anúncios /p/ de canal do YouTube; depois GGMAX/DFG/accsmarket youtube.
Uso: python canais_basefy.py saida.json"""
import json, re, sys, time
from playwright.sync_api import sync_playwright

out = {}
with sync_playwright() as p:
    br = p.chromium.launch(channel="chrome", headless=False, args=["--window-position=-2000,0", "--disable-blink-features=AutomationControlled"])
    pg = br.new_context(locale="pt-BR", viewport={"width": 1280, "height": 1800},
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36").new_page()
    for q in ("canal youtube", "youtube", "canal monetizado"):
        try:
            pg.goto("https://basefy.io", wait_until="domcontentloaded", timeout=60000); time.sleep(6)
            campo = pg.locator("input[type=search], input[placeholder*='uscar' i], input[name=q], input[type=text]").first
            campo.click(); campo.fill(q); campo.press("Enter"); time.sleep(8)
            for _ in range(5):
                pg.mouse.wheel(0, 3000); time.sleep(1.5)
            itens = pg.evaluate("""() => [...document.querySelectorAll('a[href*="/p/"]')].map(a => [a.href, a.innerText.replace(/\\s+/g,' ').trim().slice(0,300)])""")
            out["basefy:" + q] = {"url_final": pg.url, "itens": list({h: t for h, t in itens}.items())}
        except Exception as e:
            out["basefy:" + q] = {"erro": str(e)[:200], "url_final": pg.url}
        print(q, out["basefy:" + q].get("url_final"), len(out["basefy:" + q].get("itens", [])), flush=True)
    for nome, u in (("ggmax", "https://ggmax.com.br/anuncios?q=canal+youtube"),
                    ("dfg", "https://www.dfg.com.br/busca?q=canal+youtube"),
                    ("accs_home", "https://accsmarket.com/en")):
        try:
            pg.goto(u, wait_until="domcontentloaded", timeout=60000); time.sleep(9)
            t = re.sub(r"\s+", " ", pg.evaluate("() => document.body.innerText"))
            links = pg.evaluate("""() => [...document.querySelectorAll('a')].map(a => [a.href, a.innerText.replace(/\\s+/g,' ').trim().slice(0,200)]).filter(x => /youtube|canal/i.test(x[0] + x[1]))""")
            out[nome] = {"url_final": pg.url, "titulo": pg.title(), "texto": t[:3000], "links": links[:80]}
        except Exception as e:
            out[nome] = {"erro": str(e)[:200]}
        print(nome, out[nome].get("url_final"), len(out[nome].get("links", [])), flush=True)
    br.close()
json.dump(out, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
