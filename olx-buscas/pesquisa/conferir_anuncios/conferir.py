"""Abre cada anúncio num Chromium anônimo (sem conta), tira print e extrai o texto principal.
Uso: python conferir.py urls.txt  -> resultado.json + prints/NN.png na mesma pasta."""
import json, re, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

AQUI = Path(__file__).parent
PRINTS = AQUI / "prints"; PRINTS.mkdir(exist_ok=True)
urls = [l.strip() for l in open(sys.argv[1], encoding="utf-8-sig") if l.strip().startswith("http")]
res = []
with sync_playwright() as p:
    br = p.chromium.launch(channel="chrome", headless=False,args=["--window-position=-2000,0", "--disable-blink-features=AutomationControlled"])
    ctx = br.new_context(locale="pt-BR", viewport={"width": 1280, "height": 1800},
                         user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36")
    for i, u in enumerate(urls, 1):
        r = {"n": i, "url": u}
        pg = ctx.new_page()
        try:
            resp = pg.goto(u, wait_until="domcontentloaded", timeout=45000)
            r["http"] = resp.status if resp else None
            time.sleep(8)
            r["url_final"] = pg.url
            r["titulo"] = pg.title()[:150]
            t = re.sub(r"\s+", " ", pg.evaluate("() => document.body.innerText"))
            r["precos"] = list(dict.fromkeys(re.findall(r"R\$\s?\d[\d.]*,\d{2}|US\$\s?\d+[.,]\d{2}|\$\s?\d+\.\d{2}", t)))[:8]
            low = t.lower()
            r["sinais"] = [k for k in ("esgotado", "indisponível", "pausado", "não encontrado", "404", "estoque",
                                       "disponíveis", "pix", "2fa", "sms", "just a moment", "verify you are human") if k in low]
            r["texto"] = t[:1500]
            pg.screenshot(path=str(PRINTS / f"{i:02d}.png"))
        except Exception as e:
            r["erro"] = f"{type(e).__name__}: {str(e)[:150]}"
        pg.close()
        res.append(r)
        print(i, r.get("http"), r.get("titulo", r.get("erro")), r.get("precos"), flush=True)
    br.close()
json.dump(res, open(AQUI / "resultado.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
