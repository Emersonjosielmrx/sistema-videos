"""Abre páginas e devolve links (filtrados por padrão) e trechos de texto com palavras-chave."""
import json, re, sys, time
from playwright.sync_api import sync_playwright

ALVOS = [
    ("https://basefy.io/c/emails?q=gmail%20antigo", r"/p/", None),
    ("https://accsmarket.com/en/catalog/gmail", r"/item/", r"(?i)(old|aged|20[01]\d|year)"),
    ("https://accsmarket.com/en/faq", None, r"(?i)(visa|mastercard|card|pix|crypto|usdt|payment)"),
]
out = {}
with sync_playwright() as p:
    br = p.chromium.launch(channel="chrome", headless=False, args=["--window-position=-2000,0"])
    pg = br.new_context(locale="pt-BR").new_page()
    for url, padrao_link, padrao_txt in ALVOS:
        pg.goto(url, wait_until="domcontentloaded", timeout=60000); time.sleep(8)
        r = {}
        if padrao_link:
            links = pg.evaluate("() => [...document.querySelectorAll('a')].map(a => [a.innerText.replace(/\\s+/g,' ').trim(), a.href])")
            r["links"] = [l for l in links if re.search(padrao_link, l[1]) and l[0]][:60]
        if padrao_txt:
            t = pg.evaluate("() => document.body.innerText")
            r["trechos"] = [re.sub(r"\s+", " ", l)[:300] for l in t.splitlines() if re.search(padrao_txt, l)][:60]
        out[url] = r
    br.close()
json.dump(out, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("ok")
