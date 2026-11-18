"""Busca anúncios de contas com canal do YouTube (sem login, Chrome anônimo).
AccsMarket: catálogo youtube + itens Gmail que dizem 'Youtube channel created'.
Basefy: páginas de busca -> lista de links /p/.
Uso: python canais_busca.py saida.json"""
import json, re, sys, time
from playwright.sync_api import sync_playwright

out = {"accs": [], "basefy_links": {}, "accs_paginas": {}}
with sync_playwright() as p:
    br = p.chromium.launch(channel="chrome", headless=False, args=["--window-position=-2000,0", "--disable-blink-features=AutomationControlled"])
    pg = br.new_context(locale="en-US", viewport={"width": 1280, "height": 1800}).new_page()
    for cat in ("youtube", "gmail"):
        u = f"https://accsmarket.com/en/catalog/{cat}"
        try:
            pg.goto(u, wait_until="domcontentloaded", timeout=60000); time.sleep(8)
            out["accs_paginas"][cat] = pg.url
            linhas = pg.evaluate("""() => [...document.querySelectorAll('a[href*="/item/"]')].map(a => {
                let el = a; for (let i = 0; i < 6 && el.parentElement; i++) { el = el.parentElement; if (/Price per pc/.test(el.innerText)) break; }
                return [a.href, el.innerText.replace(/\\s+/g, ' ').trim()]; })""")
        except Exception as e:
            out["accs_paginas"][cat] = f"erro {e}"[:200]; continue
        vistos = set()
        for href, txt in linhas:
            if href in vistos: continue
            if cat == "gmail" and not re.search(r"(?i)youtube", txt): continue
            vistos.add(href)
            preco = re.search(r"from \$\s?([\d.,]+)", txt)
            est = re.search(r"(?:\d+\+|\d+-\d+)\s+(\d[\d ]*?)\s*pcs", txt)
            out["accs"].append({"cat": cat, "usd": float(preco.group(1).replace(",", "")) if preco else None,
                                "estoque": est.group(1).replace(" ", "") if est else None,
                                "titulo": txt[:700], "url": href})
        print(cat, len(out["accs"]), flush=True)
    pg2 = br.new_context(locale="pt-BR", viewport={"width": 1280, "height": 1800}).new_page()
    for q in ("canal youtube", "canal do youtube", "conta youtube", "canal monetizado", "youtube inscritos", "canal youtube antigo"):
        u = "https://basefy.io/busca?q=" + q.replace(" ", "+")
        try:
            pg2.goto(u, wait_until="domcontentloaded", timeout=60000); time.sleep(8)
            for _ in range(4):
                pg2.mouse.wheel(0, 3000); time.sleep(1.5)
            itens = pg2.evaluate("""() => [...document.querySelectorAll('a[href*="/p/"]')].map(a => [a.href, a.innerText.replace(/\\s+/g,' ').trim().slice(0,250)])""")
            out["basefy_links"][q] = {"url_final": pg2.url, "itens": list({h: t for h, t in itens}.items())}
        except Exception as e:
            out["basefy_links"][q] = {"erro": str(e)[:200]}
        print(q, len(out["basefy_links"][q].get("itens", [])), flush=True)
    br.close()
json.dump(out, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
