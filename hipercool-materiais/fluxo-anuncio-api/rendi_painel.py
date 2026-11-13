"""Abre o painel da Rendi já logado (conta do cofre), fotografa e procura a chave da API (sem mostrar no log)."""
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
        ctx.grant_permissions(["clipboard-read", "clipboard-write"], origin="https://app.rendi.dev")
        pg = ctx.new_page()
        cdp = ctx.new_cdp_session(pg)
        cdp.send("Network.enable")
        cdp.send("Network.setCacheDisabled", {"cacheDisabled": True})
        pg.goto("https://app.rendi.dev/", wait_until="networkidle", timeout=90000)
        pg.wait_for_timeout(8000)
        pg.screenshot(path=rf"{PASTA}\provas\rendi_10_painel.png")
        txt = pg.inner_text("body", timeout=30000)
        print("url:", pg.url, "|", re.sub(r"\s+", " ", txt)[:900], flush=True)
        # mostra/copia a chave se houver botão
        for sel in ("button:has-text('Reveal')", "button:has-text('Show')", "[aria-label*=show i]", "[aria-label*=reveal i]"):
            for b in pg.locator(sel).all():
                try:
                    b.click(timeout=3000); pg.wait_for_timeout(500)
                except Exception:  # noqa: BLE001
                    pass
        txt = pg.inner_text("body", timeout=30000)
        valores = [i.get_attribute("value") or "" for i in pg.locator("input").all()]
        achadas = sorted(set(re.findall(r"\b[A-Za-z0-9_\-]{30,80}\b", txt + " " + " ".join(valores))))
        copiada = ""
        # o campo da chave tem 2 ícones sem texto (olho e copiar): o último botão/svg clicável dentro da caixa da chave
        caixa = pg.locator("text=Your API Key").locator("xpath=ancestor::*[.//*[local-name()='svg']][1]")
        icones = caixa.locator("button, [role=button], svg")
        print("ícones na caixa:", icones.count(), flush=True)
        for i in range(icones.count() - 1, -1, -1):
            try:
                pg.evaluate("navigator.clipboard.writeText('')")
                icones.nth(i).click(timeout=4000, force=True); pg.wait_for_timeout(800)
                c = (pg.evaluate("navigator.clipboard.readText()") or "").strip()
                if len(c) > 30:
                    copiada = c
                    break
            except Exception as e:  # noqa: BLE001
                print("ícone", i, "falhou:", str(e)[:80], flush=True)
        if copiada:
            achadas.append(copiada)
        print("candidatas:", [a[:4] + "..." + a[-4:] + f"({len(a)})" for a in achadas], flush=True)
        if achadas:
            open(rf"{PASTA}\rendi_chave.txt", "w").write("\n".join(achadas))
        pg.screenshot(path=rf"{PASTA}\provas\rendi_11_chave.png")
    finally:
        cofre.fechar(proc, br, nome=CONTA)
