"""Entra num site com a conta Google do cofre (botão "Google") e fotografa cada passo.
Uso: python cadastro_google.py <url_login> <prefixo_print> [conta]
Para no CAPTCHA (verificação humana) e avisa; nunca tenta passar por ela."""
import re, sys, time
sys.path.insert(0, r"D:\logins-google")
import cofre
from playwright.sync_api import sync_playwright

URL, PREF = sys.argv[1], sys.argv[2]
CONTA = sys.argv[3] if len(sys.argv) > 3 else "aulacomia@gmail.com"
PASTA = r"D:\hipercool-materiais\fluxo-anuncio-api\provas"
n = 0


def foto(pg, nome):
    global n
    n += 1
    try:
        pg.screenshot(path=rf"{PASTA}\{PREF}_{n:02d}_{nome}.png", timeout=15000)
    except Exception:  # noqa: BLE001
        pass
    print(f"print {n:02d} {nome} | {pg.url[:130]}", flush=True)


porta, proc = cofre.abrir(CONTA, url="about:blank", visivel=True)
with sync_playwright() as pw:
    br = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
    try:
        ctx = br.contexts[0]
        antigas = set(ctx.pages)   # o perfil reabre abas antigas: elas não contam
        pg = ctx.new_page()
        cdp = ctx.new_cdp_session(pg)
        cdp.send("Network.enable")
        cdp.send("Network.setCacheDisabled", {"cacheDisabled": True})  # o cache do perfil está quebrado
        pg.goto(URL, wait_until="networkidle", timeout=90000)
        pg.wait_for_timeout(int(4 * 1000))
        foto(pg, "inicio")
        alvo = pg.locator("button:has-text('Google'), a:has-text('Google'), [data-provider*=google i], [aria-label*=Google i]").first
        if alvo.count() and alvo.is_visible():
            alvo.click(timeout=15000)
            print("clicou Google", flush=True)
        fim, viu_google = time.time() + 120, False
        while time.time() < fim:
            pg.wait_for_timeout(int(3 * 1000))
            print("abas novas:", [p.url[:60] for p in ctx.pages if not p.is_closed() and p not in antigas], flush=True)
            for p in [p for p in ctx.pages if not p.is_closed() and p not in antigas]:
                if "accounts.google" in p.url:
                    # primeiro os botões da tela de permissão (ela também mostra o e-mail), depois a escolha da conta
                    for sel in ('button:has-text("Continuar")', 'button:has-text("Continue")', 'button:has-text("Permitir")', 'button:has-text("Allow")',
                                f'[data-identifier="{CONTA}"]', f'[data-email="{CONTA}"]', f'li:has-text("{CONTA}")'):
                        try:
                            el = p.locator(sel).first
                            if el.count() and el.is_visible():
                                el.click(timeout=4000)
                                print("google:", sel, flush=True)
                                pg.wait_for_timeout(int(3 * 1000))
                                break
                        except Exception as e:  # noqa: BLE001
                            print("  falhou", sel[:40], str(e)[:120].replace("\n", " "), flush=True)
            novas = [p for p in ctx.pages if not p.is_closed() and p not in antigas]
            if any("accounts.google" in p.url for p in novas):
                viu_google = True
            vivas = [p for p in novas if "accounts.google" not in p.url and p.url != "about:blank"]
            if viu_google and vivas and not any("accounts.google" in p.url for p in novas):
                atual = vivas[-1]
                if any(f.url and ("recaptcha/api2/bframe" in f.url or "hcaptcha" in f.url or "challenges.cloudflare" in f.url) for f in atual.frames):
                    foto(atual, "verificacao_humana")
                    print("PARAR: verificação humana", flush=True)
                    break
                if "login" not in atual.url and "register" not in atual.url and "signin" not in atual.url:
                    break
        pg.wait_for_timeout(int(6 * 1000))
        for p in [p for p in ctx.pages if not p.is_closed() and p.url != "about:blank" and p not in antigas]:
            foto(p, "fim")
            try:
                print(re.sub(r"\s+", " ", p.inner_text("body", timeout=20000))[:900], flush=True)
            except Exception:  # noqa: BLE001
                pass
    finally:
        cofre.fechar(proc, br, nome=CONTA)
