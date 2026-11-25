r"""Redefine a Chave Secreta do app da conta (25/11/2026; ela apareceu no chat em 23/11), pelo Chrome da conta.

    python fb_app_segredo.py <conta> ver        # só abre Configurações > Básico e fotografa (não muda nada)
    python fb_app_segredo.py <conta> redefinir  # clica "Redefinir", confirma, lê a chave nova, grava em secrets e
                                                #   confere pela API (app token) — nunca imprime a chave

A troca não derruba a postagem: token de Página não depende da chave; só a troca de token (fb_token_assistido) usa.
Print: logs\fb_app_<conta>_segredo.png
"""
import json
import sys
import time

sys.path.insert(0, r"D:\postador-de-videos\bin")
import fb_token_auto as t  # noqa: E402


def rodar(conta, modo):
    arq = t.SEC / f"fb_app_{conta}.json"
    app = json.loads(arq.read_text(encoding="utf-8"))
    url = f"https://developers.facebook.com/apps/{app['app_id']}/settings/basic/"

    def fazer(ctx):
        pg = ctx.new_page()
        pg.set_viewport_size({"width": 1366, "height": 1000})
        pg.goto(url, wait_until="domcontentloaded", timeout=120000)
        time.sleep(12)
        foto = str(t.LOGS / f"fb_app_{conta}_segredo.png")
        if modo == "ver":
            pg.screenshot(path=foto)
            txt = pg.inner_text("body")
            i = txt.find("Chave Secreta")
            print(txt[i:i + 200].replace("\n", " | ") if i >= 0 else "não achei 'Chave Secreta' na página")
            return
        # 25/11: o "Redefinir" só aparece depois de "Mostrar" (que pode pedir a senha da conta)
        m0 = pg.get_by_role("button", name="Mostrar")
        if m0.count():
            m0.first.click(); time.sleep(6)
        # 25/11: "Mostrar" abre "Confirmar com senha" -> botão Confirmar -> caixa de senha DENTRO do diálogo.
        # Senha só pela variável FB_SENHA (nunca em arquivo/log). 1 tentativa só (errar várias trava a conta).
        import os
        # o FB mantém diálogos escondidos na página: clica só no "Confirmar" VISÍVEL do "Confirmar com senha"
        if pg.get_by_text("Confirmar com senha").count():
            cf = pg.locator("div[role=button]:visible, button:visible").filter(has_text="Confirmar")
            if cf.count():
                cf.last.click(timeout=15000); time.sleep(8)
        pg.screenshot(path=foto.replace(".png", "_pos_confirmar.png"))
        campo = pg.locator("input[type=password]:visible")
        if campo.count():
            senha = os.environ.get("FB_SENHA")
            if not senha:
                print("o Facebook pediu a senha e não recebi FB_SENHA — parei"); pg.screenshot(path=foto); return
            campo.first.click(); campo.first.fill(senha); time.sleep(1)
            pg.screenshot(path=foto.replace(".png", "_antes_enviar.png"))
            enviou = False
            for nb in ("Enviar", "Continuar", "Confirmar", "Submit"):
                b = pg.locator("div[role=button]:visible, button:visible").filter(has_text=nb)
                if b.count():
                    b.last.click(); enviou = True; break
            if not enviou:
                campo.first.press("Enter")
            time.sleep(10)
            if pg.locator("input[type=password]:visible").count():
                print("a senha não foi aceita — parei (não tento de novo)"); pg.screenshot(path=foto); return
        m1 = pg.get_by_role("button", name="Mostrar")
        if m1.count():
            m1.first.click(); time.sleep(5)
        bt = pg.get_by_role("button", name="Redefinir")
        if not bt.count():
            print("botão Redefinir não apareceu nem depois de Mostrar"); pg.screenshot(path=foto); return
        bt.first.click(); time.sleep(4)
        d = pg.get_by_role("dialog")
        if d.count():
            for nb in ("Redefinir", "Confirmar", "Sim"):
                b = d.last.get_by_role("button", name=nb)
                if b.count():
                    b.last.click(); time.sleep(6); break
        # pode pedir a senha do Facebook: aí para (não digita senha aqui)
        if pg.locator("input[type=password]").count():
            print("o Facebook pediu a senha para mostrar/trocar a chave — parei (fazer com a dona)")
            pg.screenshot(path=foto); return
        mostrar = pg.get_by_role("button", name="Mostrar")
        if mostrar.count():
            mostrar.first.click(); time.sleep(4)
        nova = None
        for el in pg.locator("input").all():
            try:
                v = el.input_value()
            except Exception:  # noqa: BLE001
                continue
            if len(v) == 32 and all(c in "0123456789abcdef" for c in v) and v != app["app_secret"]:
                nova = v
                break
        pg.screenshot(path=foto)
        if not nova:
            print("não consegui ler a chave nova — ver o print; a antiga pode ter sido invalidada")
            return
        import fb_reel_api as A
        s = A._sessao(conta)
        r = s.get(f"{A.G}/{app['app_id']}", params={"fields": "id", "access_token": f"{app['app_id']}|{nova}"},
                  timeout=30).json()
        if r.get("id") != str(app["app_id"]):
            print("a chave lida não validou na API — NÃO gravei (ver o print)")
            return
        app["app_secret"] = nova
        arq.write_text(json.dumps(app), encoding="utf-8")
        print("chave secreta redefinida, validada pela API e gravada em secrets (não impressa)")

    t.com_chrome(conta, fazer)


if __name__ == "__main__":
    if sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    rodar(sys.argv[1], sys.argv[2])
