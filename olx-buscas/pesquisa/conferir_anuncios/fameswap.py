"""Lista canais do YouTube na FameSwap (até 10K inscritos) com preço.
Uso: python fameswap.py saida.json"""
import json, sys, time
from playwright.sync_api import sync_playwright

out = {}
with sync_playwright() as p:
    br = p.chromium.launch(channel="chrome", headless=False, args=["--window-position=-2000,0", "--disable-blink-features=AutomationControlled"])
    pg = br.new_context(locale="en-US", viewport={"width": 1400, "height": 2000}).new_page()
    pg.goto("https://fameswap.com/browse?platform=youtube", wait_until="domcontentloaded", timeout=60000); time.sleep(8)
    # tenta marcar o filtro "Under 10K" e ordenar por preço
    try:
        pg.get_by_text("Under 10K", exact=True).first.click(); time.sleep(6)
    except Exception as e:
        out["filtro_erro"] = str(e)[:150]
    out["url_filtro"] = pg.url
    for _ in range(8):
        pg.mouse.wheel(0, 3000); time.sleep(1.5)
    out["cards"] = pg.evaluate("""() => [...document.querySelectorAll('a[href*="/listing"], a[href*="/youtube"], a[href*="/account"]')]
        .map(a => [a.href, a.innerText.replace(/\\s+/g,' ').trim().slice(0,250)]).filter(x => x[1].length > 10)""")
    out["texto"] = pg.inner_text("body")[:12000]
    br.close()
json.dump(out, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(out.get("url_filtro"), len(out["cards"]), out.get("filtro_erro"))
