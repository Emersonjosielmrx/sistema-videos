#!/usr/bin/env python3
r"""Loga uma conta Google no claude.ai (Continuar com Google) e extrai o cookie sessionKey.

Uso:
    python claude_web_login.py canalalucinaai                 # faz login + extrai, print do header
    python claude_web_login.py canalalucinaai --passo abrir   # so abre e tira print (exploracao)
"""
import json
import sys
import time
import argparse

sys.path.insert(0, r"D:\logins-google")
import cofre
from playwright.sync_api import sync_playwright

SHOT = r"D:\gemini-argo\_claude_shot.png"


def _print_estado(pg, ctx, tag):
    try:
        pg.screenshot(path=SHOT, full_page=False)
    except Exception as e:
        print(f"[{tag}] screenshot falhou: {e}")
    url = pg.url
    cdp = ctx.new_cdp_session(pg)
    resp = cdp.send("Network.getAllCookies")
    sk = [c for c in resp["cookies"] if c.get("name") == "sessionKey" and "claude.ai" in c.get("domain", "")]
    print(f"[{tag}] url={url}")
    print(f"[{tag}] sessionKey presente: {bool(sk)}")
    # botoes visiveis
    try:
        txts = pg.locator("button, a").all_inner_texts()
        txts = [t.strip() for t in txts if t.strip()][:25]
        print(f"[{tag}] clicaveis: {txts}")
    except Exception as e:
        print(f"[{tag}] clicaveis err: {e}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("conta")
    p.add_argument("--passo", default="abrir")
    a = p.parse_args()

    porta, proc = cofre.abrir(a.conta, url="about:blank", visivel=True)
    try:
        with sync_playwright() as pw:
            br = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
            ctx = br.contexts[0]
            pg = ctx.new_page()
            pg.goto("https://claude.ai/new", wait_until="domcontentloaded", timeout=60000)
            time.sleep(6)
            _print_estado(pg, ctx, "inicial")
            print(f"PRINT salvo em {SHOT}")
            # nao fecha ainda na exploracao; deixa o chrome aberto
            if a.passo == "abrir":
                br.close()  # so desconecta o cdp, chrome segue aberto
                return
    except Exception:
        cofre.fechar(proc, None, a.conta)
        raise


if __name__ == "__main__":
    main()
