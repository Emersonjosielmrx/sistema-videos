r"""instagram_logar_nova.py — abre um Chrome NOVO do cofre na tela de login do Instagram; a dona loga à mão; quando a
API do Instagram confirma o login, grava a conta em config\instagram_local.json e salva os cookies em
D:\projeto-navegador-sem-navegador\cookies\cofre_ig_<conta>.json (postagem por HTTP), e fecha (o cofre grava a sessão).

    python bin\instagram_logar_nova.py ig_solar_nova     # chave do perfil no cofre
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, r"D:\logins-google")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cofre  # noqa: E402
import instagram_local as il  # noqa: E402

NSN_COOKIES = Path(r"D:\projeto-navegador-sem-navegador\cookies")
ESPERA_S = 20 * 60


def main(chave):
    from playwright.sync_api import sync_playwright
    try:
        cofre.conta(chave)
    except KeyError:
        cofre.registrar(chave, usos={"instagram": "?"}, tipo="instagram")
    with sync_playwright() as p:
        porta, proc = cofre.abrir(chave, "about:blank", visivel=True)
        br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
        try:
            ctx = br.contexts[0]
            pg = ctx.new_page()
            pg.goto("https://www.instagram.com/accounts/login/", wait_until="domcontentloaded", timeout=90000)
            pg.bring_to_front()
            print("janela aberta: faça o login", flush=True)
            fim, u = time.time() + ESPERA_S, None
            while time.time() < fim:
                pg.wait_for_timeout(5000)
                u = il._usuario_logado(pg)
                if u:
                    break
            if not u:
                print("tempo esgotado sem login", flush=True)
                return 1
            pg.wait_for_timeout(4000)
            il._clicar(pg, il.DEPOIS)
            est = il._ler(il.ESTADO)
            est.setdefault(u, {}).update({"resultado": f"logado @{u}", "t": time.time(), "cofre": chave,
                                          "_obs": f"logada à mão pela dona em {time.strftime('%d/%m/%Y')}"})
            il.ESTADO.write_text(json.dumps(est, ensure_ascii=False, indent=2), encoding="utf-8")
            ck = [c for c in ctx.cookies() if "instagram.com" in c.get("domain", "")]
            NSN_COOKIES.mkdir(parents=True, exist_ok=True)
            # 06/11: o arquivo do cofre_cookies precisa de "perfil" e "ua" (sem eles o postar.py dá KeyError 'ua' e o
            # reel da Advance das 08:00 ficou preso); grava no MESMO nome que o postador lê: cofre_<chave do cofre>.json
            ua = ctx.new_cdp_session(pg).send("Browser.getVersion")["userAgent"].replace("HeadlessChrome", "Chrome")
            dados = {"perfil": chave, "ua": ua, "quando": time.strftime("%Y-%m-%d %H:%M"),
                     "cookies": [{k: c[k] for k in ("name", "value", "domain", "path")} for c in ck]}
            for nome in {f"cofre_{chave}.json", f"cofre_ig_{u}.json"}:
                (NSN_COOKIES / nome).write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"LOGADO @{u} — {len(ck)} cookies salvos, sessionid={'sim' if any(c['name'] == 'sessionid' for c in ck) else 'NAO'}",
                  flush=True)
            return 0
        finally:
            cofre.fechar(proc, br, chave)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "ig_solar_nova"))
