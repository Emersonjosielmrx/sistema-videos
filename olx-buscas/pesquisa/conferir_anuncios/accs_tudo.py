"""AccsMarket: TODAS as ofertas dos catálogos Gmail e YouTube com preço, estoque, nota, reembolso, ano, SMS, canal, 2FA, IP.
Uso: python accs_tudo.py saida.json"""
import json, re, sys, time
from datetime import date
from playwright.sync_api import sync_playwright

CATALOGOS = ["https://accsmarket.com/en/catalog/gmail", "https://accsmarket.com/en/catalog/youtube"]
ANO = date.today().year


def classificar(txt, href, cat):
    low = txt.lower()
    # "Confirmed via SMS", "Confirmed by SMS twice", "verified by SMS", "verified through SMS" = já confirmada.
    # "May require / Require confirmation", "required to be verified" = NÃO confirmada.
    sms_ok = bool(re.search(r"confirmed (via|by) sms|verified (by|through|via) sms|sms verified", low)) and \
        not re.search(r"required to be verified|require[sd]? (confirmation|to be verified)", low.split("price per pc")[0][:40] + "")
    if re.search(r"require[sd]? confirmation|required to be verified", low) and not re.search(r"confirmed (via|by) sms|verified (by|through) sms", low):
        sms_ok = False
    anos = [int(a) for a in re.findall(r"(?:registration date|registered in|registered from)\D{0,12}(\d{4})", low)]
    faixa = re.search(r"from (\d{4}) to (\d{4})", low)
    ano = min(anos) if anos else (int(faixa.group(1)) if faixa else None)
    preco = re.search(r"from \$\s?([\d.,]+)", txt)
    est = re.search(r"(?:\d+\+|\d+-\d+)\s+(\d[\d ]*?)\s*pcs", txt)
    nota = re.search(r"48h\s+([\d.]+)\s+([\d.]+)%", txt) or re.search(r"\b([0-5]\.\d)\s+([\d.]+)%", txt)
    vendas = re.search(r"%\s+(\d+\+|\d+-\d+)\s", txt)
    ip = re.search(r"registered (?:with|from|in ip addresses of) (?:the )?(\w+)", low)
    return {
        "cat": cat, "url": href,
        "titulo": txt.split(" 48h")[0][:400],
        "usd": float(preco.group(1).replace(",", ".")) if preco else None,
        "estoque": int(est.group(1).replace(" ", "")) if est else 0,
        "nota": float(nota.group(1)) if nota else None,
        "reembolso": float(nota.group(2)) if nota else None,
        "vendas_mes": vendas.group(1) if vendas else None,
        "ano": ano,
        "sms": sms_ok,
        "canal": "youtube channel" in low or cat == "youtube",
        "fa2": "2fa" in low,
        "ip": ip.group(1).upper() if ip else None,
    }


out = []
with sync_playwright() as p:
    br = p.chromium.launch(channel="chrome", headless=False, args=["--window-position=-2000,0"])
    pg = br.new_context(locale="en-US").new_page()
    for url in CATALOGOS:
        cat = url.rsplit("/", 1)[1]
        pg.goto(url, wait_until="domcontentloaded", timeout=90000); time.sleep(10)
        linhas = pg.evaluate("""() => [...document.querySelectorAll('a[href*="/item/"]')].map(a => {
            let el = a; for (let i = 0; i < 6 && el.parentElement; i++) { el = el.parentElement; if (/Price per pc/.test(el.innerText)) break; }
            return [a.href, el.innerText.replace(/\\s+/g, ' ').trim()]; })""")
        vistos = set()
        for href, txt in linhas:
            if href in vistos or "Price per pc" not in txt:
                continue
            vistos.add(href)
            out.append(classificar(txt, href, cat))
        print(cat, len(vistos), "ofertas", flush=True)
    br.close()
json.dump(out, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
