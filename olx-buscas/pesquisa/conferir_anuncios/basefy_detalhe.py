"""Basefy: para cada anúncio, lê o bloco lateral (entrega, vendidos, preço, estoque, vendedor) e as opções de variante."""
import json, re, sys, time
from playwright.sync_api import sync_playwright

urls = [l.strip() for l in open(sys.argv[1], encoding="utf-8-sig") if "basefy.io/p/" in l]
out = []
with sync_playwright() as p:
    br = p.chromium.launch(channel="chrome", headless=False, args=["--window-position=-2000,0"])
    pg = br.new_context(locale="pt-BR").new_page()
    for u in urls:
        pg.goto(u, wait_until="domcontentloaded", timeout=60000); time.sleep(7)
        t = re.sub(r"\s+", " ", pg.evaluate("() => document.body.innerText"))
        m = re.search(r"ENTREGA (Manual|Autom\w+).{0,700}", t)
        bloco = m.group(0) if m else ""
        bloco = bloco.split("Populares em")[0].split("Mais de ")[0]
        opcoes = pg.evaluate("""() => [...document.querySelectorAll('button, [role=radio], label, option')]
            .map(e => e.innerText.replace(/\\s+/g,' ').trim()).filter(s => s && s.length < 90 && /20\\d\\d|ano|antig|meses|R\\$/i.test(s))""")
        out.append({"url": u, "bloco": bloco, "opcoes": list(dict.fromkeys(opcoes))[:20]})
        print(u, "|", bloco[:250], flush=True)
    pg.goto("https://basefy.io", wait_until="domcontentloaded", timeout=60000); time.sleep(5)
    t = pg.evaluate("() => document.body.innerText")
    out.append({"pagamento_home": [re.sub(r"\s+", " ", l)[:200] for l in t.splitlines() if re.search(r"(?i)pix|cart[aã]o|usdt|boleto", l)][:10]})
    br.close()
json.dump(out, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
