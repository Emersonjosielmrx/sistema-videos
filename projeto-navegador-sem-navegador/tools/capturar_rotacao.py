# -*- coding: utf-8 -*-
r"""tools/capturar_rotacao.py — captura a rotação de cookies que o Chrome faz no Studio (inclusive dentro dos iframes
de accounts.*, que o Network da aba não vê) e no fim guarda os cookies novos como o `youtube_http.py sync`.

    python tools\capturar_rotacao.py <slug> [segundos=150]
Saída: capturas\rotacao_<slug>.jsonl
"""
import json
import sys
import time
import urllib.request
from pathlib import Path

import websocket

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, r"D:\gemini-argo")
sys.path.insert(0, r"D:\logins-google")
sys.path.insert(0, r"D:\postador-de-videos\bin\netbooks")
from core.arquivo import gravar_json  # noqa: E402
from core.cdp_aba import Aba  # noqa: E402
import youtube_http  # noqa: E402

FILTRO = ("Rotate", "accounts.google", "accounts.youtube", "CheckCookie", "SetSID", "ServiceLogin")


def main():
    slug, espera = sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 150
    import chrome_conta
    import cofre
    email = youtube_http._email(slug)
    chrome_conta._liberar_ram()
    porta, proc = cofre.abrir(email, url="about:blank", visivel=False)
    saida = ROOT / "capturas" / f"rotacao_{slug}.jsonl"
    log = saida.open("w", encoding="utf-8")
    a = None
    try:
        for _ in range(30):
            try:
                a = Aba.da_porta(porta, nova="about:blank")
                break
            except Exception:  # noqa: BLE001 — Chrome ainda subindo
                time.sleep(1)
        ids = iter(range(900000, 999999))

        def grava(tipo, ev, sessao=None):
            log.write(json.dumps({"t": time.strftime("%H:%M:%S"), "tipo": tipo, "sessao": sessao, **ev},
                                 ensure_ascii=False) + "\n")
            log.flush()

        def pedido(ev):
            u = ev["request"]["url"]
            if any(f in u for f in FILTRO):
                grava("pedido", {"url": u, "metodo": ev["request"]["method"], "enviado": ev["request"].get("postData"),
                                 "cab": ev["request"].get("headers"), "id": ev["requestId"]})

        def resposta_extra(ev):
            sc = {k: v for k, v in (ev.get("headers") or {}).items() if k.lower() == "set-cookie"}
            if sc:
                grava("set-cookie", {"id": ev["requestId"], "status": ev.get("statusCode"),
                                     "nomes": [x.split("=")[0] for x in "\n".join(sc.values()).split("\n")]})

        def anexou(ev):
            sid = ev["sessionId"]
            grava("iframe", {"url": ev["targetInfo"].get("url"), "tipo_alvo": ev["targetInfo"].get("type")}, sid)
            for metodo, p in (("Network.enable", {"maxPostDataSize": 100000}),
                              ("Target.setAutoAttach", {"autoAttach": True, "waitForDebuggerOnStart": True,
                                                        "flatten": True}),
                              ("Runtime.runIfWaitingForDebugger", {})):
                a.ws.send(json.dumps({"id": next(ids), "sessionId": sid, "method": metodo, "params": p}))

        a.em("Network.requestWillBeSent", pedido)
        a.em("Network.responseReceivedExtraInfo", resposta_extra)
        a.em("Target.attachedToTarget", anexou)
        a.chamar("Network.enable", {"maxPostDataSize": 100000})
        a.chamar("Target.setAutoAttach", {"autoAttach": True, "waitForDebuggerOnStart": True, "flatten": True})
        a.chamar("Page.enable")
        a.chamar("Page.navigate", {"url": youtube_http.STUDIO})
        time.sleep(espera)
        todos = a.chamar("Network.getAllCookies")["cookies"]
        ck = {c["name"]: c["value"] for c in todos if c.get("domain", "").endswith("youtube.com")}
        if "SAPISID" in ck:
            gravar_json(youtube_http.COOKIES_DIR / f"{slug}.json", ck, ensure_ascii=True)
        print(slug, "cookies youtube:", len(ck), "| SAPISID:", "SAPISID" in ck)
    finally:
        log.close()
        if a:
            a.fechar(fechar_aba=True)
        if proc:  # fecha pelo CDP (o Chrome grava os cookies) e espera sair
            try:
                v = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{porta}/json/version", timeout=10).read())
                w = websocket.create_connection(v["webSocketDebuggerUrl"], timeout=10, suppress_origin=True)
                w.send(json.dumps({"id": 1, "method": "Browser.close"}))
                w.close()
            except Exception:  # noqa: BLE001
                pass
            cofre.fechar(proc, None, email)
    linhas = [json.loads(x) for x in saida.read_text("utf-8").splitlines()]
    for x in linhas:
        if x["tipo"] != "set-cookie" or len(x.get("nomes", [])) > 0:
            print(x["t"], x["tipo"], (x.get("url") or "")[:150], x.get("metodo") or "", (x.get("enviado") or "")[:120],
                  x.get("nomes") or "")


if __name__ == "__main__":
    main()
