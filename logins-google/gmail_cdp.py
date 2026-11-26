# D:\logins-google\gmail_cdp.py
# Procura e-mails no Gmail de um Chrome do cofre JA ABERTO (pela sessao interativa) e, se pedir, abre o 1o link.
# Uso: python -X utf8 gmail_cdp.py <porta> "<busca gmail>" [dominio_do_link]
#   ex: python -X utf8 gmail_cdp.py 9711 "from:oxylabs newer_than:1d" oxylabs
import sys, time, re, urllib.parse
from playwright.sync_api import sync_playwright
porta, busca = int(sys.argv[1]), sys.argv[2]
dominio = sys.argv[3] if len(sys.argv) > 3 else ""
with sync_playwright() as p:
    br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
    pg = br.contexts[0].new_page()
    pg.goto("https://mail.google.com/mail/u/0/#search/" + urllib.parse.quote(busca), wait_until="domcontentloaded", timeout=60000)
    time.sleep(12)
    rows = [r for r in pg.query_selector_all("tr.zA") if r.is_visible()]
    for r in rows[:8]:
        print("EMAIL:", r.inner_text().replace("\n", " ")[:160])
    if not rows:
        print("nenhum e-mail encontrado")
    elif dominio:
        rows[0].click(); time.sleep(6)
        hrefs = [a.get_attribute("href") or "" for a in pg.query_selector_all("div.a3s a")]
        cand = [h for h in hrefs if dominio in h and re.search(r"verif|confirm|activ|token", h, re.I)] or [h for h in hrefs if dominio in h]
        if cand:
            pg.goto(cand[0], wait_until="domcontentloaded", timeout=60000); time.sleep(12)
            print("ABRIU:", pg.url[:100])
        else:
            print("sem link de", dominio)
