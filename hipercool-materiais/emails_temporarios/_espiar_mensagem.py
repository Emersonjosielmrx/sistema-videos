"""Temporário: descobre o endpoint do emailnator que devolve o CORPO de uma mensagem (clicando no site)."""
from emailnator import Emailnator, LIMPA

e = Emailnator()
pg = e.page
try:
    em = e.criar("dotGmail")
    st, j = e.post("/api/message-list", {"email": em})
    print("email", em, "msgs", len(j.get("messages", [])), flush=True)
    vistos = []
    pg.on("request", lambda r: r.resource_type in ("xhr", "fetch") and "emailnator.com" in r.url and
          vistos.append((r.method, r.url, (r.post_data or "")[:200])))
    pg.goto(f"https://www.emailnator.com/inbox/{em}", timeout=60000, wait_until="domcontentloaded")
    pg.wait_for_timeout(8000)
    pg.evaluate(LIMPA)
    print("URL", pg.url, flush=True)
    links = pg.locator("a[href*='/inbox/']").all()
    print("links", len(links), [l.get_attribute("href")[:80] for l in links[:5]], flush=True)
    alvo = [l for l in links if l.get_attribute("href").count("/") >= 3 and len(l.get_attribute("href")) > 60]
    if alvo:
        alvo[0].click()
        pg.wait_for_timeout(8000)
        print("URL2", pg.url, flush=True)
    for v in vistos:
        print("XHR", *v, flush=True)
    print("TEXTO", pg.evaluate("() => document.body.innerText")[:500].replace("\n", " | "))
finally:
    e.fechar()
