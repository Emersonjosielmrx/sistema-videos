"""Varre anúncios de canais do YouTube (Basefy várias buscas + lojas estrangeiras).
Uso: python canais_v2.py saida.json"""
import json, sys, time
from playwright.sync_api import sync_playwright

JS = "() => [...document.querySelectorAll('a')].map(a => [a.href, a.innerText.replace(/\\s+/g,' ').trim().slice(0,300)])"
URLS = []
for cat in ("outros", "emails", "instagram", "ferramentas"):
    for q in ("canal", "canal youtube", "inscritos", "monetizado", "channel"):
        URLS.append(f"https://basefy.io/c/{cat}?q={q.replace(' ', '+')}")
URLS += [
    "https://www.z2u.com/youtube",
    "https://www.g2g.com/categories/youtube-accounts",
    "https://www.playerup.com/accounts/youtube/",
    "https://fameswap.com/browse?platform=youtube",
    "https://www.dfg.com.br/youtube",
]
out = {}
with sync_playwright() as p:
    br = p.chromium.launch(channel="chrome", headless=False, args=["--window-position=-2000,0", "--disable-blink-features=AutomationControlled", "--incognito"])
    pg = br.new_context(locale="pt-BR", viewport={"width": 1280, "height": 1800}).new_page()
    for u in URLS:
        try:
            pg.goto(u, wait_until="domcontentloaded", timeout=45000); time.sleep(6)
            for _ in range(5):
                pg.mouse.wheel(0, 3000); time.sleep(1)
            out[u] = {"final": pg.url, "titulo": pg.title(), "links": pg.evaluate(JS),
                      "texto": pg.inner_text("body")[:4000]}
        except Exception as e:
            out[u] = {"erro": str(e)[:200]}
        print(u, len(out[u].get("links", [])), flush=True)
    br.close()
json.dump(out, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
