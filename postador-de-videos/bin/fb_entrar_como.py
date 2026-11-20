"""Troca o perfil ativo para <nome> pelo menu da foto (canto direito): 'Seu perfil' -> 'Ver todos os perfis' -> <nome>.
Função usada pelos scripts de foto/capa/postagem. Teste: python fb_entrar_como.py <conta> "<nome>" """
import sys, time
from pathlib import Path
LOG = Path(__file__).resolve().parent.parent / "logs"


def _vis(loc):
    for i in range(loc.count()):
        if loc.nth(i).is_visible():
            return loc.nth(i)
    return None


def entrar_como_cookie(ctx, page_id, nome=None):
    """20/11 (do navegador-sem-navegador): o Facebook decide quem age pelo cookie i_user = id da Página. Põe o cookie no
    Chrome e confere na home (USER_ID). Sem menu, sem clique (o menu era o passo que travava). True/False."""
    if not page_id:
        return False
    ctx.add_cookies([{"name": "i_user", "value": str(page_id), "domain": ".facebook.com", "path": "/",
                      "secure": True, "sameSite": "None"}])
    pg = ctx.new_page()
    try:
        pg.goto("https://www.facebook.com/", wait_until="domcontentloaded", timeout=90000)
        time.sleep(5)
        h = pg.content()
        ok = f'"USER_ID":"{page_id}"' in h or (nome and f"No que você está pensando, {nome}?" in pg.inner_text("body"))
        return bool(ok)
    except Exception:
        return False
    finally:
        pg.close()


def entrar_como(pg, nome):
    pg.goto("https://www.facebook.com/", wait_until="domcontentloaded", timeout=90000)
    time.sleep(8)
    pg.locator('[aria-label="Seu perfil"]').first.click()
    time.sleep(3)
    atual = _vis(pg.get_by_text(nome, exact=True))
    ver = _vis(pg.get_by_text("Ver todos os perfis", exact=False))
    if ver:
        ver.click(); time.sleep(3)
    alvo = _vis(pg.get_by_text(nome, exact=True))
    if not alvo:
        pg.screenshot(path=str(LOG / "fb_entrar_como_falhou.png"))
        raise RuntimeError(f"perfil '{nome}' não está no menu")
    alvo.click()
    time.sleep(12)
    for nome_b in ("Usar Página", "Agora não"):
        u = _vis(pg.get_by_role("button", name=nome_b, exact=True))
        if u:
            u.click(); time.sleep(3)
    # confere: o menu "Seu perfil" agora mostra o nome
    pg.goto("https://www.facebook.com/", wait_until="domcontentloaded", timeout=90000)
    time.sleep(6)
    txt = pg.inner_text("body")
    ok = f"No que você está pensando, {nome}?" in txt or _vis(pg.locator(f'[aria-label="{nome}"]')) is not None
    return ok


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from playwright.sync_api import sync_playwright
    import fb_contas
    porta, proc = fb_contas.abrir(sys.argv[1])
    try:
        with sync_playwright() as p:
            pg = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}").contexts[0].new_page()
            pg.set_viewport_size({"width": 1366, "height": 900})
            print("entrou como", sys.argv[2], "->", entrar_como(pg, sys.argv[2]))
            pg.screenshot(path=str(LOG / "fb_entrar_como.png"))
            pg.close()
    finally:
        fb_contas.fechar(proc)
