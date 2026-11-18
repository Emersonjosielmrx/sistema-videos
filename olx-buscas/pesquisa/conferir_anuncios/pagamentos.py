"""Lê as páginas de pagamento/ajuda das lojas.
Uso: python pagamentos.py saida.json"""
import json, sys, time
from playwright.sync_api import sync_playwright

URLS = [
    "https://www.accsmarket.com/en/faq",
    "https://www.accsmarket.com/en/payment",
    "https://www.accsmarket.com/en/rules",
    "https://fameswap.com/escrow",
    "https://fameswap.com/faq",
    "https://basefy.io/p/contas-gmail-novas-entrega-rapida?variante=gmail-conta-para-youtube-1-unidade",
    "https://basefy.io/p/conta-de-youtube-com-217-inscritos",
]
out = {}
with sync_playwright() as p:
    br = p.chromium.launch(channel="chrome", headless=False, args=["--window-position=-2000,0", "--disable-blink-features=AutomationControlled"])
    pg = br.new_context(locale="pt-BR", viewport={"width": 1280, "height": 1800}).new_page()
    for u in URLS:
        try:
            pg.goto(u, wait_until="domcontentloaded", timeout=45000); time.sleep(6)
            out[u] = {"final": pg.url, "texto": pg.inner_text("body")[:15000]}
        except Exception as e:
            out[u] = {"erro": str(e)[:200]}
        print(u, len(out[u].get("texto", "")), flush=True)
    br.close()
json.dump(out, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
