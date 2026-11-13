# -*- coding: utf-8 -*-
r"""
tools/capturar_rede.py — Grava as chamadas de rede reais de uma página (Flow, Studio, Instagram...) enquanto
o fluxo de navegador que JÁ FUNCIONA roda. É assim que se descobre o endpoint de verdade para depois repetir
só por HTTP (o padrão do gemini_http.py), em vez de chutar URL.

Fica escutando a porta CDP do Chrome da conta (espera ela abrir), liga em todas as abas e grava cada pedido
cujo endereço casa com o filtro: método, URL, cabeçalhos, corpo enviado e o começo da resposta.

    python tools\capturar_rede.py 9260 --filtro "aisandbox-pa|labs.google/fx/api" --saida capturas\flow.jsonl
    (em outro terminal, rode o fluxo normal: python D:\flow-imagens\gera_imagem.py ... --conta mundosolar)

Para sozinho quando a porta fecha (o fluxo normal fecha o Chrome que abriu) ou com Ctrl+C.
"""
import argparse
import json
import re
import socket
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIMITE_CORPO = 200_000  # resposta grande (vídeo/imagem em base64) corta aqui


def _porta_aberta(porta):
    with socket.socket() as s:
        s.settimeout(1)
        return s.connect_ex(("127.0.0.1", porta)) == 0


def capturar(porta, filtro, saida, espera_abrir=600):
    from playwright.sync_api import sync_playwright
    rx = re.compile(filtro, re.I)
    saida.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    while not _porta_aberta(porta):
        if time.time() - t0 > espera_abrir:
            print(f"porta {porta} não abriu em {espera_abrir}s")
            return 0
        time.sleep(1)
    print(f"porta {porta} aberta — gravando em {saida}")
    n = 0
    arq = saida.open("a", encoding="utf-8")

    def ao_responder(resp):
        nonlocal n
        req = resp.request
        if not rx.search(req.url):
            return
        try:
            corpo = resp.text()
        except Exception as e:  # noqa: BLE001 — binário ou já descartado
            corpo = f"<sem texto: {type(e).__name__}>"
        reg = {
            "t": time.strftime("%H:%M:%S"),
            "metodo": req.method,
            "url": req.url,
            "cabecalhos": req.all_headers(),
            "enviado": req.post_data,
            "status": resp.status,
            "resposta_cabecalhos": resp.all_headers(),
            "resposta": corpo[:LIMITE_CORPO],
            "resposta_tamanho": len(corpo),
        }
        arq.write(json.dumps(reg, ensure_ascii=False) + "\n")
        arq.flush()
        n += 1
        print(f"  [{reg['t']}] {req.method} {resp.status} {req.url[:140]}")

    with sync_playwright() as pw:
        br = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
        ligados = set()

        def ligar(ctx):
            if id(ctx) not in ligados:
                ligados.add(id(ctx))
                ctx.on("response", ao_responder)

        try:
            while _porta_aberta(porta):
                for ctx in br.contexts:
                    ligar(ctx)
                # os eventos só chegam enquanto o Playwright processa a fila: um wait curto numa aba qualquer
                pags = [p for c in br.contexts for p in c.pages]
                if pags:
                    try:
                        pags[0].wait_for_timeout(500)
                    except Exception:  # noqa: BLE001 — aba fechou
                        time.sleep(0.5)
                else:
                    time.sleep(0.5)
        except KeyboardInterrupt:
            pass
        except Exception as e:  # noqa: BLE001 — Chrome fechou no meio
            print(f"conexão encerrada: {type(e).__name__}")
    arq.close()
    print(f"fim: {n} chamadas gravadas")
    return n


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("porta", type=int)
    ap.add_argument("--filtro", default=r"aisandbox-pa|labs\.google/fx/api|/_/.*batchexecute|/youtubei/|/api/v1/")
    ap.add_argument("--saida", default=str(ROOT / "capturas" / "rede.jsonl"))
    ap.add_argument("--espera", type=int, default=600, help="segundos esperando a porta abrir")
    a = ap.parse_args()
    sys.exit(0 if capturar(a.porta, a.filtro, Path(a.saida), a.espera) else 1)
