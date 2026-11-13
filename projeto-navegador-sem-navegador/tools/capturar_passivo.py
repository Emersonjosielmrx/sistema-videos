# -*- coding: utf-8 -*-
r"""tools/capturar_passivo.py — OUVE (sem clicar, sem navegar) as abas que os postadores da produção abrem no Chrome do
cofre e grava as chamadas reais de postagem: Studio do YouTube, TikTok, Instagram, Facebook/Meta Business Suite.

Por quê (29/10): para postar por HTTP sem inventar endpoint é preciso a chamada real de um upload de verdade; em vez de
postar teste, escuta o upload que a produção já faz. O CDP aceita um 2º cliente na mesma aba: só Network.enable.
Corpo grande (o vídeo) não é gravado (maxPostDataSize); cookies não são gravados.

    python tools\capturar_passivo.py [minutos=240]
Saída: capturas\passivo_<plataforma>_<AAAAMMDD>.jsonl
"""
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from core.arquivo import gravar_json  # noqa: E402
from core.cdp_aba import Aba  # noqa: E402

ALVOS = {"youtube": ("studio.youtube.com", "upload.youtube.com", "youtube.com/youtubei"),
         "tiktok": ("tiktok.com",),
         "instagram": ("instagram.com",),
         "facebook": ("facebook.com",),
         # 12/11 (dona: "o Flow perde muito tempo"): o pedido novo do Flow com agente, pra refazer o flow_gerar.py
         "flow": ("labs.google", "flow.google.com", "aisandbox-pa.googleapis.com")}
IGNORAR = re.compile(r"\.(js|css|png|jpg|jpeg|gif|webp|woff2?|svg|ico)(\?|$)|/log|/jserror|/csi|ping|beacon|"
                     r"/collect|/generate_204|/ptracking|/stats|/api/v1/web/logging|/ajax/bz|/bz\?|monitor|"
                     r"mon\.|mcs\.|/web/report|/slardar|/sentry", re.I)


_MAPA = json.loads(Path(r"D:\postador-de-videos\config\youtube_navegador.json").read_text("utf-8"))
CANAIS = {v["channel_id"]: k for k, v in _MAPA.get("canais", _MAPA).items() if isinstance(v, dict) and v.get("channel_id")}


def _portas():
    import psutil
    portas = set()
    for p in psutil.process_iter(["name", "cmdline"]):
        try:
            if (p.info["name"] or "").lower() == "chrome.exe":
                for a in p.info["cmdline"] or []:
                    if a.startswith("--remote-debugging-port="):
                        portas.add(int(a.split("=", 1)[1]))
            # 12/11: túnel ssh pro Chrome de um notebook (maquina_remota: -L <local>:127.0.0.1:946x) — o Flow roda lá
            elif (p.info["name"] or "").lower() == "ssh.exe":
                for a in p.info["cmdline"] or []:
                    m = re.match(r"^(\d+):127\.0\.0\.1:94\d\d$", a)
                    if m:
                        portas.add(int(m.group(1)))
        except (psutil.Error, ValueError):
            continue
    return sorted(portas)


def _plataforma(url):
    return next((p for p, ds in ALVOS.items() if any(d in url for d in ds)), None)


class Ouvinte:
    def __init__(self, alvo, porta):
        self.alvo, self.porta, self.pedidos, self.prontos = alvo, porta, {}, []
        self.a = Aba(alvo["webSocketDebuggerUrl"])
        self.a.em("Network.requestWillBeSent", self._pedido)
        self.a.em("Network.loadingFinished", self._fim)
        self.a.em("Target.attachedToTarget", self._filho)
        self.a.chamar("Network.enable", {"maxPostDataSize": 65536})
        # o Studio sobe o arquivo e salva o vídeo de dentro de um worker (a rede da aba não vê): ouvir os filhos
        # sem pausar nada (waitForDebuggerOnStart false = a produção não espera por nós)
        self.a.chamar("Target.setAutoAttach", {"autoAttach": True, "waitForDebuggerOnStart": False, "flatten": True})

    def _filho(self, ev):  # thread leitora: só envia, não espera resposta
        self.a.ws.send(json.dumps({"id": 700000 + len(self.pedidos) + int(time.time() * 1000) % 99999,
                                   "sessionId": ev["sessionId"], "method": "Network.enable",
                                   "params": {"maxPostDataSize": 65536}}))
        print(time.strftime("%H:%M:%S"), "filho", ev["targetInfo"].get("type"), ev["targetInfo"].get("url", "")[:90],
              flush=True)

    def _pedido(self, ev):
        r = ev["request"]
        u = r["url"]
        plat = _plataforma(u)
        if not plat or IGNORAR.search(u) or ev.get("type") not in ("XHR", "Fetch", "Document", "Other"):
            return
        if r["method"] == "GET" and ev.get("type") == "Other":
            return
        if plat == "youtube" and '"sessionInfo"' in (r.get("postData") or ""):
            # 01/11: o canal vem do documentURL do PRÓPRIO pedido (a mesma aba pode ter trocado de canal e o
            # self.alvo["url"] só é atualizado a cada ~2 s pelo laço — o token ia pro yt_sessao do canal errado).
            self._token_sessao(r["postData"], ev.get("documentURL") or self.alvo.get("url", ""))
        self.pedidos[ev["requestId"]] = {"t": time.strftime("%H:%M:%S"), "porta": self.porta, "plataforma": plat,
                                         "metodo": r["method"], "url": u, "tipo": ev.get("type"),
                                         "enviado": r.get("postData"), "tem_corpo": r.get("hasPostData"),
                                         "cab": {k: v for k, v in (r.get("headers") or {}).items()
                                                 if k.lower() not in ("cookie",)},
                                         "pagina": self.alvo.get("url", "")[:150], "sessao": ev.get("_sessao")}

    def _fim(self, ev):  # thread leitora: não chama CDP aqui
        if ev["requestId"] in self.pedidos:
            self.prontos.append((ev["requestId"], ev.get("encodedDataLength", 0)))

    def _token_sessao(self, corpo, pagina_url):
        """O upload por HTTP (services\\youtube\\upload_http.py) precisa do context.request.sessionInfo.token do canal.
        pagina_url = documentURL do pedido (o canal que de fato emitiu o token), não a url da aba (que atrasa ~2 s)."""
        cid = re.search(r"/channel/(UC[\w-]+)", pagina_url or "")
        slug = CANAIS.get(cid.group(1)) if cid else None
        try:
            tok = json.loads(corpo)["context"]["request"]["sessionInfo"]["token"]
        except (ValueError, KeyError, TypeError):
            return
        if slug and tok and tok != getattr(self, "_ultimo_token", None):
            self._ultimo_token = tok
            gravar_json(ROOT / "cookies" / f"yt_sessao_{slug}.json",  # atômico: o upload_http lê a qualquer hora
                        {"token": tok, "capturado": time.strftime("%Y-%m-%d %H:%M:%S")}, indent=None, ensure_ascii=True)

    def carona(self):
        """29/10: o Chrome da produção gira o login e derruba a nossa cópia HTTP do canal; aba do Studio aberta =
        cookies frescos de graça: copia para o cookies_youtube do gemini-argo (sem abrir Chrome)."""
        if time.time() - getattr(self, "_carona", 0) < 60:
            return
        self._carona = time.time()
        cid = re.search(r"/channel/(UC[\w-]+)", self.alvo.get("url", ""))
        slug = CANAIS.get(cid.group(1)) if cid else None
        if not slug:
            return
        ck = {c["name"]: c["value"] for c in self.a.chamar("Network.getAllCookies", timeout=15)["cookies"]
              if c.get("domain", "").endswith("youtube.com")}
        if "SAPISID" in ck:
            gravar_json(Path(r"D:\gemini-argo\cookies_youtube") / f"{slug}.json", ck, ensure_ascii=True)
            print(time.strftime("%H:%M:%S"), "carona: cookies de", slug, "atualizados", flush=True)

    def gravar(self):
        while self.prontos:
            rid, tam = self.prontos.pop(0)
            p = self.pedidos.pop(rid, None)
            if not p:
                continue
            corpo = ""
            if tam < 300000:
                try:
                    corpo = self.a.chamar("Network.getResponseBody", {"requestId": rid}, timeout=15,
                                          sessao=p.get("sessao")).get("body", "")
                except Exception as e:  # noqa: BLE001
                    corpo = f"(sem corpo: {str(e)[:80]})"
            p["resposta"] = corpo[:200000]
            arq = ROOT / "capturas" / f"passivo_{p['plataforma']}_{time.strftime('%Y%m%d')}.jsonl"
            with arq.open("a", encoding="utf-8") as f:
                f.write(json.dumps(p, ensure_ascii=False) + "\n")

    def vivo(self):
        return None not in self.a._resp


def main():
    minutos = int(sys.argv[1]) if len(sys.argv) > 1 else 240
    fim = time.time() + minutos * 60
    ouvintes = {}
    print(time.strftime("%H:%M:%S"), "ouvindo por", minutos, "min", flush=True)
    ultima_varredura = t_portas = 0
    portas = []
    while time.time() < fim:
        if time.time() - ultima_varredura > 2:  # o postador abre a aba e já sobe o vídeo: anexar ao nascer
            ultima_varredura = time.time()
            if ultima_varredura - t_portas > 10:
                t_portas, portas = ultima_varredura, _portas()
            for porta in portas:
                try:
                    alvos = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{porta}/json", timeout=3).read())
                except Exception:  # noqa: BLE001
                    continue
                for t in alvos:
                    if t.get("type") != "page":
                        continue
                    if t["id"] in ouvintes:
                        ouvintes[t["id"]].alvo["url"] = t.get("url", "")
                        continue
                    if not (_plataforma(t.get("url", "")) or t.get("url", "") in ("about:blank", "")):
                        continue
                    try:
                        ouvintes[t["id"]] = Ouvinte(t, porta)
                        print(time.strftime("%H:%M:%S"), "anexado", porta, t["url"][:100], flush=True)
                    except Exception as e:  # noqa: BLE001
                        print("não anexou", porta, t.get("url", "")[:80], e, flush=True)
        for k, o in list(ouvintes.items()):
            try:
                o.gravar()
                if o.alvo.get("url", "").startswith("https://studio.youtube.com"):
                    o.carona()
            except Exception:  # noqa: BLE001
                pass
            if not o.vivo():
                o.gravar()
                del ouvintes[k]
                print(time.strftime("%H:%M:%S"), "aba fechou", o.porta, flush=True)
        time.sleep(2)
    for o in ouvintes.values():
        try:
            o.a.ws.close()
        except Exception:  # noqa: BLE001
            pass


if __name__ == "__main__":
    main()
