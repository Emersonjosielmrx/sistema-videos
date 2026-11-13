# -*- coding: utf-8 -*-
r"""tools/capturar_fotos.py — captura as chamadas reais do Google Fotos (batchexecute: pedido + resposta) numa busca,
rolando a página para pegar a paginação. Também guarda o HTML (AF_initDataCallback) e os cookies .google.com.

    python tools\capturar_fotos.py <conta_do_cofre> "<busca>" [rolagens=4]
Saída: capturas\fotos_<conta>.jsonl, capturas\fotos_<conta>.html, logs não; cookies em capturas\fotos_<conta>_cookies.json
"""
import json
import sys
import time
import urllib.parse as up
import urllib.request
from pathlib import Path

import websocket

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, r"D:\logins-google")
sys.path.insert(0, r"D:\postador-de-videos\bin\netbooks")
from core.cdp_aba import Aba  # noqa: E402


def main():
    conta, busca = sys.argv[1], sys.argv[2]
    rolagens = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    import chrome_conta
    import cofre
    chrome_conta._liberar_ram()
    porta, proc = cofre.abrir(conta, url="about:blank", visivel=False)
    out = ROOT / "capturas" / f"fotos_{conta}.jsonl"
    log = out.open("w", encoding="utf-8")
    pedidos = {}
    a = None
    try:
        for _ in range(30):
            try:
                a = Aba.da_porta(porta, nova="about:blank")
                break
            except Exception:  # noqa: BLE001
                time.sleep(1)

        def pedido(ev):
            u = ev["request"]["url"]
            if "photos.google.com" in u and ("batchexecute" in u or "/_/" in u):
                rid = (up.parse_qs(up.urlparse(u).query).get("rpcids") or [""])[0]
                pedidos[ev["requestId"]] = {"rpc": rid, "url": u, "enviado": ev["request"].get("postData"),
                                            "cab": ev["request"].get("headers")}

        prontos = []

        def terminou(ev):  # roda na thread leitora: não pode chamar CDP aqui (esperaria a si mesma)
            if ev["requestId"] in pedidos:
                prontos.append(ev["requestId"])

        def gravar_prontos():
            while prontos:
                rid = prontos.pop(0)
                p = pedidos.pop(rid)
                try:
                    corpo = a.chamar("Network.getResponseBody", {"requestId": rid}, timeout=20).get("body", "")
                except Exception as e:  # noqa: BLE001
                    corpo = f"(sem corpo: {e})"
                p["resposta"] = corpo[:400000]
                log.write(json.dumps(p, ensure_ascii=False) + "\n")
                log.flush()

        a.em("Network.requestWillBeSent", pedido)
        a.em("Network.loadingFinished", terminou)
        a.chamar("Network.enable", {"maxPostDataSize": 200000})
        a.chamar("Page.enable")
        a.chamar("Page.navigate", {"url": "https://photos.google.com/search/" + up.quote(busca)})
        time.sleep(12)
        gravar_prontos()
        print("url:", a.js("location.href"), "| fotos na tela:", a.js("document.querySelectorAll('a[href*=\"/photo/\"]').length"))
        for _ in range(rolagens):
            a.chamar("Input.dispatchMouseEvent", {"type": "mouseWheel", "x": 600, "y": 400, "deltaX": 0, "deltaY": 2500})
            time.sleep(3)
            gravar_prontos()
        print("fotos na tela depois de rolar:", a.js("document.querySelectorAll('a[href*=\"/photo/\"]').length"))
        (ROOT / "capturas" / f"fotos_{conta}.html").write_text(a.js("document.documentElement.outerHTML"), "utf-8")
        ck = [{k: c[k] for k in ("name", "value", "domain", "path")} for c in a.chamar("Network.getAllCookies")["cookies"]
              if "google" in c["domain"]]
        (ROOT / "capturas" / f"fotos_{conta}_cookies.json").write_text(json.dumps(ck), "utf-8")
        time.sleep(2)
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
            cofre.fechar(proc, None, conta)
    for x in (json.loads(l) for l in out.read_text("utf-8").splitlines()):
        print(x["rpc"] or x["url"][:90], "| enviado:", (x["enviado"] or "")[:160], "| resp:", len(x["resposta"]))


if __name__ == "__main__":
    main()
