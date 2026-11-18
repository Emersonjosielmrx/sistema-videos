"""AccsMarket: linhas 'Registration date' do catálogo Gmail com preço, estoque e link; resposta do FAQ sobre cartão."""
import json, re, sys, time
from playwright.sync_api import sync_playwright

out = {"itens": [], "faq_cartao": ""}
with sync_playwright() as p:
    br = p.chromium.launch(channel="chrome", headless=False, args=["--window-position=-2000,0"])
    pg = br.new_context(locale="en-US").new_page()
    pg.goto("https://accsmarket.com/en/catalog/gmail", wait_until="domcontentloaded", timeout=60000); time.sleep(8)
    linhas = pg.evaluate("""() => [...document.querySelectorAll('a[href*="/item/"]')].map(a => {
        let el = a; for (let i = 0; i < 6 && el.parentElement; i++) { el = el.parentElement; if (/Price per pc/.test(el.innerText)) break; }
        return [a.href, el.innerText.replace(/\\s+/g, ' ').trim()]; })""")
    vistos = set()
    for href, txt in linhas:
        if href in vistos or not re.search(r"(?i)registration date|registered in 20|were registered in", txt):
            continue
        vistos.add(href)
        ano = re.search(r"(?:Registration date|registered in)\s*(\d{4})", txt)
        preco = re.search(r"from \$\s?([\d.,]+)", txt)
        est = re.search(r"(?:\d+\+|\d+-\d+)\s+(\d[\d ]*?)\s*pcs", txt)
        out["itens"].append({"ano": int(ano.group(1)) if ano else None,
                             "usd": float(preco.group(1).replace(",", ".")) if preco else None,
                             "estoque": est.group(1).replace(" ", "") if est else None,
                             "sms": "Confirmed" in txt or "verified" in txt.lower(),
                             "fa2": "2fa" in txt.lower(),
                             "yt": "Youtube channel" in txt,
                             "ip": (re.search(r"(USA|MIX|Russia|UA|different countries)", txt) or [None])[0],
                             "titulo": txt[:600], "url": href})
    pg.goto("https://accsmarket.com/en/faq", wait_until="domcontentloaded", timeout=60000); time.sleep(5)
    try:
        pg.get_by_text("Can I top up by credit card?").first.click(); time.sleep(2)
    except Exception:
        pass
    t = pg.evaluate("() => document.body.innerText")
    i = t.find("Can I top up by credit card?")
    out["faq_cartao"] = re.sub(r"\s+", " ", t[i:i + 900]) if i >= 0 else ""
    br.close()
json.dump(out, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(out["itens"]), "itens")
