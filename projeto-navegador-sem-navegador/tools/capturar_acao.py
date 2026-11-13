# -*- coding: utf-8 -*-
r"""tools/capturar_acao.py — abre o Chrome do cofre escondido, vai a uma página, (opcional) roda passos JS que clicam/
preenchem como a pessoa faria, e grava os pedidos XHR/fetch (com resposta) do domínio pedido, inclusive de workers.
Serve para capturar a chamada REAL de uma ação antes de fazê-la por HTTP (regra: nada de endpoint inventado).

    python tools\capturar_acao.py <perfil_cofre> <url> <dominio> <saida.jsonl> [espera_s=15] [passos.json]
passos.json = [{"js": "...", "espera": 3}, ...]   (o valor de cada js é impresso)
"""
import json
import sys
import time
import urllib.request
from pathlib import Path

import websocket

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, r"D:\logins-google")
sys.path.insert(0, r"D:\postador-de-videos\bin\netbooks")
from core.cdp_aba import Aba  # noqa: E402


def main():
    perfil, url, dominio, saida = sys.argv[1:5]
    espera = int(sys.argv[5]) if len(sys.argv) > 5 else 15
    passos = json.loads(Path(sys.argv[6]).read_text("utf-8")) if len(sys.argv) > 6 else []
    import chrome_conta
    import cofre
    chrome_conta._liberar_ram()
    porta, proc = cofre.abrir(perfil, url="about:blank", visivel=False)
    log = open(saida, "w", encoding="utf-8")
    pedidos, prontos, a = {}, [], None
    try:
        for _ in range(30):
            try:
                a = Aba.da_porta(porta, nova="about:blank")
                break
            except Exception:  # noqa: BLE001
                time.sleep(1)

        def pedido(ev):
            r = ev["request"]
            if dominio in r["url"] and ev.get("type") in ("XHR", "Fetch", "Document", "WebSocket"):
                pedidos[ev["requestId"]] = {"t": time.strftime("%H:%M:%S"), "metodo": r["method"], "url": r["url"],
                                            "enviado": r.get("postData"), "sessao": ev.get("_sessao"),
                                            "cab": {k: v for k, v in (r.get("headers") or {}).items()
                                                    if k.lower() != "cookie"}}

        def fim(ev):
            if ev["requestId"] in pedidos:
                prontos.append(ev["requestId"])

        def filho(ev):
            a.ws.send(json.dumps({"id": 800000 + int(time.time() * 1000) % 99999, "sessionId": ev["sessionId"],
                                  "method": "Network.enable", "params": {"maxPostDataSize": 200000}}))

        def gravar():
            while prontos:
                rid = prontos.pop(0)
                p = pedidos.pop(rid)
                try:
                    p["resposta"] = a.chamar("Network.getResponseBody", {"requestId": rid}, timeout=15,
                                             sessao=p["sessao"]).get("body", "")[:300000]
                except Exception as e:  # noqa: BLE001
                    p["resposta"] = f"(sem corpo: {str(e)[:80]})"
                log.write(json.dumps(p, ensure_ascii=False) + "\n")
                log.flush()

        a.em("Network.requestWillBeSent", pedido)
        a.em("Network.loadingFinished", fim)
        a.em("Target.attachedToTarget", filho)
        a.chamar("Network.enable", {"maxPostDataSize": 200000})
        a.chamar("Target.setAutoAttach", {"autoAttach": True, "waitForDebuggerOnStart": False, "flatten": True})
        a.chamar("Page.enable")
        a.chamar("Page.navigate", {"url": url})
        time.sleep(espera)
        gravar()
        for p in passos:
            try:
                if "clicar" in p:  # clique de mouse de verdade no ponto [x, y] que o JS devolver
                    xy = a.js(p["clicar"])
                    if xy:
                        for t in ("mouseMoved", "mousePressed", "mouseReleased"):
                            a.chamar("Input.dispatchMouseEvent", {"type": t, "x": xy[0], "y": xy[1], "button": "left",
                                                                  "clickCount": 1})
                    print("passo: clique em", xy, flush=True)
                elif "foto" in p:  # print da aba (conferir o que a página mostra)
                    import base64
                    Path(p["foto"]).write_bytes(base64.b64decode(a.chamar("Page.captureScreenshot")["data"]))
                    print("passo: foto em", p["foto"], flush=True)
                elif "seletor_arquivos" in p:  # clique de mouse no botão [x, y] e responde a janela de arquivos
                    abertos = []  # (clique por JS não conta como gesto: o Chrome não abre a janela)
                    a.em("Page.fileChooserOpened", abertos.append)
                    a.chamar("Page.setInterceptFileChooserDialog", {"enabled": True})
                    xy = a.js(p["seletor_arquivos"])
                    for t in ("mouseMoved", "mousePressed", "mouseReleased"):
                        a.chamar("Input.dispatchMouseEvent", {"type": t, "x": xy[0], "y": xy[1], "button": "left",
                                                              "clickCount": 1})
                    print("passo: clique no botão em", xy, flush=True)
                    for _ in range(20):
                        if abertos:
                            break
                        time.sleep(0.5)
                    if abertos:
                        a.chamar("DOM.setFileInputFiles", {"files": [p["arquivo"]],
                                                           "backendNodeId": abertos[0]["backendNodeId"]})
                    a.chamar("Page.setInterceptFileChooserDialog", {"enabled": False})
                    print("passo: janela de arquivos", "respondida" if abertos else "NÃO abriu", flush=True)
                elif "arquivo" in p:  # escolhe arquivo no <input type=file> (como o seletor de arquivos faria)
                    # objectId pelo JS, como a produção (_escolher_arquivo): o nodeId do DOM.querySelectorAll pegava
                    # outro campo e o Studio não recebia a capa (29/10)
                    sel = json.dumps(p.get("seletor", "input[type=file]"))
                    obj = a.chamar("Runtime.evaluate", {"expression": f"document.querySelector({sel})"})["result"]
                    a.chamar("DOM.setFileInputFiles", {"files": [p["arquivo"]], "objectId": obj["objectId"]})
                    print("passo: arquivo em", obj.get("description"), flush=True)
                elif "digitar" in p:  # digita como teclado (o React só vê texto que chega por evento de entrada)
                    a.chamar("Input.insertText", {"text": p["digitar"]})
                    print("passo: digitou", len(p["digitar"]), "letras", flush=True)
                elif "tecla" in p:
                    for t in ("rawKeyDown", "char", "keyUp"):
                        a.chamar("Input.dispatchKeyEvent", {"type": t, "key": p["tecla"], "code": p["tecla"],
                                                            "windowsVirtualKeyCode": 13,
                                                            **({"text": "\r"} if t == "char" else {})})
                    print("passo: tecla", p["tecla"], flush=True)
                else:
                    print("passo:", json.dumps(a.js(p["js"]), ensure_ascii=False)[:p.get("mostrar", 300)], flush=True)
            except Exception as e:  # noqa: BLE001
                print("passo falhou:", str(e)[:200], flush=True)
            time.sleep(p.get("espera", 3))
            gravar()
        time.sleep(3)
        gravar()
    finally:
        log.close()
        if a:
            a.fechar(fechar_aba=True)
        if proc:
            try:
                v = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{porta}/json/version", timeout=10).read())
                w = websocket.create_connection(v["webSocketDebuggerUrl"], timeout=10, suppress_origin=True)
                w.send(json.dumps({"id": 1, "method": "Browser.close"}))
                w.close()
            except Exception:  # noqa: BLE001
                pass
            cofre.fechar(proc, None, perfil)
    for x in (json.loads(l) for l in Path(saida).read_text("utf-8").split("\n") if l):  # splitlines quebra no U+2028
        print(x["t"], x["metodo"], x["url"][:120], "|", (x["enviado"] or "")[:120].replace("\n", " "),
              "| resp", len(x["resposta"]))


if __name__ == "__main__":
    main()
