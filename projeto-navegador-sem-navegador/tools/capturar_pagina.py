# -*- coding: utf-8 -*-
r"""
tools/capturar_pagina.py — abre um perfil do cofre escondido, visita as páginas pedidas e grava as chamadas de API que
o próprio site faz (CDP Network, com corpo enviado e resposta). É assim que se descobre o endpoint real antes de
repetir por HTTP. Só navega e espera: não clica nem posta nada.

    python tools\capturar_pagina.py ig_recenas.ia capturas\ig_recenas.jsonl ^
        https://www.instagram.com/recenas.ia/ https://www.instagram.com/accounts/insights/ --filtro "graphql|/api/v1/"
"""
import argparse
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, r"D:\logins-google")
sys.path.insert(0, r"D:\postador-de-videos\bin\netbooks")
LIMITE = 400_000


def capturar(perfil, saida, urls, filtro, espera):
    import cofre
    from playwright.sync_api import sync_playwright
    try:
        import chrome_conta
        chrome_conta._liberar_ram()
    except Exception:  # noqa: BLE001
        pass
    rx = re.compile(filtro, re.I)
    saida.parent.mkdir(parents=True, exist_ok=True)
    arq = saida.open("a", encoding="utf-8")
    porta, proc = cofre.abrir(perfil, url="about:blank", visivel=False)
    br = None
    n = 0
    try:
        with sync_playwright() as pw:
            br = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
            pg = br.contexts[0].new_page()
            cdp = br.contexts[0].new_cdp_session(pg)
            pend = {}

            def req(ev):
                if rx.search(ev["request"]["url"]):
                    pend[ev["requestId"]] = ev["request"]

            def fim(ev):
                nonlocal n
                r = pend.pop(ev["requestId"], None)
                if not r:
                    return
                try:
                    corpo = cdp.send("Network.getResponseBody", {"requestId": ev["requestId"]}).get("body", "")
                except Exception as e:  # noqa: BLE001
                    corpo = f"<sem corpo: {e}>"
                arq.write(json.dumps({"t": time.strftime("%H:%M:%S"), "pagina": pg.url, "metodo": r["method"],
                                      "url": r["url"], "cabecalhos": r.get("headers"), "enviado": r.get("postData"),
                                      "resposta": corpo[:LIMITE], "resposta_tamanho": len(corpo)},
                                     ensure_ascii=False) + "\n")
                arq.flush()
                n += 1
                print(f"  {r['method']} {r['url'][:140]} ({len(corpo)})", flush=True)

            cdp.on("Network.requestWillBeSent", req)
            cdp.on("Network.loadingFinished", fim)
            cdp.send("Network.enable", {"maxPostDataSize": 2_000_000})
            for u in urls:
                print(f"== {u}", flush=True)
                try:
                    pg.goto(u, wait_until="domcontentloaded", timeout=90000)
                except Exception as e:  # noqa: BLE001
                    print(f"  goto falhou: {type(e).__name__}")
                pg.wait_for_timeout(espera * 1000)
                pg.mouse.wheel(0, 2500)  # rolar puxa a segunda página da grade (paginação real)
                pg.wait_for_timeout(4000)
            pg.close()
    finally:
        cofre.fechar(proc, br, perfil)
        arq.close()
    print(f"fim: {n} chamadas em {saida}")
    return n


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("perfil")
    ap.add_argument("saida")
    ap.add_argument("urls", nargs="+")
    ap.add_argument("--filtro", default=r"graphql|/api/v1/|/api/|batchexecute|/youtubei/")
    ap.add_argument("--espera", type=int, default=10)
    a = ap.parse_args()
    capturar(a.perfil, Path(a.saida), a.urls, a.filtro, a.espera)
