# -*- coding: utf-8 -*-
"""publicar_app_oauth.py — tira o app OAuth do modo "Teste" (token morre em 7 dias) pra "Em produção" (token não
expira), pelo navegador do cofre da PRÓPRIA conta (09/11, dona: "faça eles renovarem sozinhos pra não perder os tokens
nunca"). 1 conta por execução; tira print de cada passo em D:\\video-fila\\_tmp_oauth_publicar\\.

    python publicar_app_oauth.py <email> <project_id> [--clicar]
Sem --clicar: só abre a página do público-alvo e tira print (pra ver o que tem). Com --clicar: aperta "Publicar app"
e confirma.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, r"D:\logins-google")
import cofre  # noqa: E402

OUT = Path(r"D:\video-fila\_tmp_oauth_publicar")


def main():
    email, projeto = sys.argv[1], sys.argv[2]
    clicar = "--clicar" in sys.argv
    OUT.mkdir(exist_ok=True)
    nome = email.split("@")[0]
    porta, _proc = cofre.abrir(email, "about:blank", visivel=True)
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
        pg = br.contexts[0].new_page()
        pg.goto(f"https://console.cloud.google.com/auth/audience?project={projeto}", timeout=120000)
        pg.wait_for_timeout(15000)
        pg.screenshot(path=str(OUT / f"{nome}_1_publico.png"))
        corpo = " ".join(pg.inner_text("body").split())
        print("PÁGINA:", corpo[:900])
        if not clicar:
            return
        botao = pg.get_by_role("button", name=re.compile(r"Publicar app|Publish app", re.I))
        if not botao.count():
            print("sem botão 'Publicar app' (já publicado ou falta Branding) — ver print")
            return
        botao.first.click()
        pg.wait_for_timeout(4000)
        pg.screenshot(path=str(OUT / f"{nome}_2_confirmar.png"))
        conf = pg.get_by_role("button", name=re.compile(r"^(Confirmar|Confirm)$", re.I))
        if conf.count():
            conf.first.click()
            pg.wait_for_timeout(8000)
        pg.screenshot(path=str(OUT / f"{nome}_3_depois.png"))
        print("DEPOIS:", " ".join(pg.inner_text("body").split())[:600])


if __name__ == "__main__":
    main()
