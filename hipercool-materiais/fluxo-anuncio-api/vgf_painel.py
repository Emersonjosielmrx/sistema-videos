"""Abre o painel do Very Good FFmpeg (logado pelo cofre), cria/copia a chave da API sem mostrar no log."""
import re, sys
sys.path.insert(0, r"D:\logins-google")
import cofre
from playwright.sync_api import sync_playwright

CONTA = "aulacomia@gmail.com"
PASTA = r"D:\hipercool-materiais\fluxo-anuncio-api"
porta, proc = cofre.abrir(CONTA, url="about:blank", visivel=True)
with sync_playwright() as pw:
    br = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
    try:
        ctx = br.contexts[0]
        ctx.grant_permissions(["clipboard-read", "clipboard-write"], origin="https://verygoodffmpeg.com")
        pg = ctx.new_page()
        cdp = ctx.new_cdp_session(pg)
        cdp.send("Network.enable")
        cdp.send("Network.setCacheDisabled", {"cacheDisabled": True})
        chave = ""
        # o login mandava para /dash: entra por /sign-in (já logado ele redireciona ao painel) e segue os links do menu
        pg.goto("https://verygoodffmpeg.com/sign-in", wait_until="networkidle", timeout=90000)
        pg.wait_for_timeout(8000)
        t = pg.inner_text("body", timeout=30000)
        print("##", pg.url, "|", re.sub(r"\s+", " ", t)[:500], flush=True)
        links = sorted({a.get_attribute("href") or "" for a in pg.locator("a").all()})
        print("links:", [l for l in links if l.startswith("/")][:40], flush=True)
        for l in links:
            if re.search(r"key|token|api", l, re.I) and l.startswith("/") and "docs" not in l and "reference" not in l:
                pg.goto("https://verygoodffmpeg.com" + l, wait_until="networkidle", timeout=90000)
                pg.wait_for_timeout(5000)
                print("## chaves em", pg.url, flush=True)
                break
        pg.screenshot(path=rf"{PASTA}\provas\vgf_10_painel.png", full_page=True)
        # se não houver chave ainda, cria
        for nome in ("Create API key", "Create key", "New API key", "Generate", "Create"):
            b = pg.locator("button", has_text=nome).first
            if b.count() and b.is_visible():
                b.click(timeout=8000); pg.wait_for_timeout(2500)
                campo = pg.locator("input[type=text]:visible").first
                if campo.count() and not campo.input_value():
                    campo.fill("aulas-n8n")
                    for ok in ("Create", "Save", "Confirm", "Generate"):
                        c = pg.locator("[role=dialog] button, form button", has_text=ok).first
                        if c.count() and c.is_visible():
                            c.click(timeout=8000); pg.wait_for_timeout(3000); break
                print("criou com:", nome, flush=True)
                break
        pg.screenshot(path=rf"{PASTA}\provas\vgf_11_chave.png", full_page=True)
        t = pg.inner_text("body", timeout=30000)
        vals = [i.get_attribute("value") or "" for i in pg.locator("input").all()]
        achadas = sorted(set(re.findall(r"\b(?:vgf|sk|key)?[_-]?[A-Za-z0-9_\-]{30,90}\b", t + " " + " ".join(vals))))
        for b in pg.locator("button:has-text('Copy'), [aria-label*=copy i]").all():
            try:
                pg.evaluate("navigator.clipboard.writeText('')")
                b.click(timeout=3000); pg.wait_for_timeout(700)
                c = (pg.evaluate("navigator.clipboard.readText()") or "").strip()
                if len(c) > 20 and c not in achadas:
                    achadas.append(c)
            except Exception:  # noqa: BLE001
                pass
        print("candidatas:", [a[:5] + "..." + a[-4:] + f"({len(a)})" for a in achadas], flush=True)
        if achadas:
            open(rf"{PASTA}\vgf_chave.txt", "w").write("\n".join(achadas))
    finally:
        cofre.fechar(proc, br, nome=CONTA)
