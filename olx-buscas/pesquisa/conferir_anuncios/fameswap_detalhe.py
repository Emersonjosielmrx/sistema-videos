"""Abre anúncios de YouTube da FameSwap e lê preço/nicho/receita.
Uso: python fameswap_detalhe.py fameswap.json saida.json"""
import json, re, sys, time
from playwright.sync_api import sync_playwright

cards = json.load(open(sys.argv[1], encoding="utf-8"))["cards"]
urls = list(dict.fromkeys(h for h, t in cards if "youtube-account" in h))
out = {}
with sync_playwright() as p:
    br = p.chromium.launch(channel="chrome", headless=False, args=["--window-position=-2000,0", "--disable-blink-features=AutomationControlled"])
    pg = br.new_context(locale="en-US", viewport={"width": 1400, "height": 2000}).new_page()
    for u in urls:
        try:
            pg.goto(u, wait_until="domcontentloaded", timeout=45000); time.sleep(4)
            tx = pg.inner_text("body")
            out[u] = tx[:3500]
        except Exception as e:
            out[u] = "ERRO " + str(e)[:150]
        print(u, len(out[u]), flush=True)
    br.close()
json.dump(out, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
