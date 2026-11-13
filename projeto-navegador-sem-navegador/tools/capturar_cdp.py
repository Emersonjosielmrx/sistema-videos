# -*- coding: utf-8 -*-
r"""
tools/capturar_cdp.py — escuta a rede de um Chrome já aberto pelo protocolo do próprio Chrome (CDP Network), em todas
as abas. Diferente do capturar_rede.py (evento "response" do Playwright, que em 28/10 não viu nenhum fetch do Flow):
aqui cada pedido vem do Network.requestWillBeSent com o corpo enviado, e a resposta pelo Network.getResponseBody.

    python tools\capturar_cdp.py 9250 --filtro "batchexecute|aisandbox" --saida capturas\flow.jsonl [--segundos 600]

Só escuta: não clica, não navega. Para com a porta fechando, o tempo acabando ou Ctrl+C.
"""
import argparse
import json
import re
import time
from pathlib import Path

LIMITE = 300_000


def capturar(porta, filtro, saida, segundos):
    from playwright.sync_api import sync_playwright
    rx = re.compile(filtro, re.I)
    saida.parent.mkdir(parents=True, exist_ok=True)
    arq = saida.open("a", encoding="utf-8")
    n = 0
    with sync_playwright() as pw:
        br = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
        sessoes = {}

        def ligar(pg):
            if id(pg) in sessoes:
                return
            cdp = pg.context.new_cdp_session(pg)
            pend = {}

            def req(ev):
                r = ev["request"]
                if rx.search(r["url"]):
                    pend[ev["requestId"]] = r
                    # stream (StreamGenerateContent) pode não terminar enquanto escuto: o pedido fica gravado já aqui
                    arq.write(json.dumps({"t": time.strftime("%H:%M:%S"), "fase": "pedido", "metodo": r["method"],
                                          "url": r["url"], "cabecalhos": r.get("headers"),
                                          "enviado": r.get("postData")}, ensure_ascii=False) + "\n")
                    arq.flush()
                    print(f"  [{time.strftime('%H:%M:%S')}] -> {r['method']} {r['url'][:150]}", flush=True)

            def fim(ev):
                nonlocal n
                r = pend.pop(ev["requestId"], None)
                if not r:
                    return
                try:
                    b = cdp.send("Network.getResponseBody", {"requestId": ev["requestId"]})
                    corpo = b.get("body", "")
                except Exception as e:  # noqa: BLE001
                    corpo = f"<sem corpo: {e}>"
                reg = {"t": time.strftime("%H:%M:%S"), "metodo": r["method"], "url": r["url"],
                       "cabecalhos": r.get("headers"), "enviado": r.get("postData"), "resposta": corpo[:LIMITE],
                       "resposta_tamanho": len(corpo)}
                arq.write(json.dumps(reg, ensure_ascii=False) + "\n")
                arq.flush()
                n += 1
                print(f"  [{reg['t']}] {r['method']} {r['url'][:150]}", flush=True)

            def ws(tipo):
                def f(ev):
                    reg = {"t": time.strftime("%H:%M:%S"), "fase": tipo, "id": ev.get("requestId"),
                           "url": ev.get("url"), "dados": (ev.get("response") or {}).get("payloadData")}
                    arq.write(json.dumps(reg, ensure_ascii=False)[:LIMITE] + "\n")
                    arq.flush()
                    print(f"  [{reg['t']}] {tipo} {(reg['url'] or '')[:100]} {len(reg['dados'] or '')}", flush=True)
                return f

            # o agente do Flow (28/10) não manda o pedido por fetch: escutar WebSocket também
            for ev in ("webSocketCreated", "webSocketFrameSent", "webSocketFrameReceived"):
                cdp.on(f"Network.{ev}", ws(ev))
            cdp.on("Network.requestWillBeSent", req)
            cdp.on("Network.loadingFinished", fim)
            cdp.send("Network.enable", {"maxPostDataSize": 5_000_000})
            sessoes[id(pg)] = cdp

        t0 = time.time()
        try:
            while time.time() - t0 < segundos:
                for ctx in br.contexts:
                    for pg in ctx.pages:
                        ligar(pg)
                pags = [p for c in br.contexts for p in c.pages]
                (pags[0].wait_for_timeout(500) if pags else time.sleep(0.5))
        except KeyboardInterrupt:
            pass
        except Exception as e:  # noqa: BLE001 — Chrome fechou
            print(f"conexão encerrada: {type(e).__name__}")
    arq.close()
    print(f"fim: {n} chamadas")
    return n


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("porta", type=int)
    ap.add_argument("--filtro", default=r"batchexecute|aisandbox|/youtubei/|/api/v1/|graphql")
    ap.add_argument("--saida", required=True)
    ap.add_argument("--segundos", type=int, default=900)
    a = ap.parse_args()
    capturar(a.porta, a.filtro, Path(a.saida), a.segundos)
