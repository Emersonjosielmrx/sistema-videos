# -*- coding: utf-8 -*-
r"""core/cdp_aba.py — fala CDP direto com UMA aba pelo websocket (sem Playwright).

Por quê (28/10): no Chrome 156 o connect_over_cdp do Playwright trava 5 min nos alvos "browser_ui" do Chrome do Veo
(porta 9260 com 1 aba só). Aqui não há anexo ao navegador inteiro: só a aba escolhida.

    from core.cdp_aba import Aba
    a = Aba.do_flow(9260); a.js("location.href"); a.chamar("Network.getAllCookies")
"""
import itertools
import json
import threading
import time
import urllib.request

import websocket


class Aba:
    def __init__(self, ws_url):
        self.ws = websocket.create_connection(ws_url, timeout=60, suppress_origin=True)
        self._id = itertools.count(1)
        self._resp, self._ouvintes = {}, {}
        self._cond = threading.Condition()
        self._envio = threading.Lock()  # ouvinte (thread de leitura) e principal mandam ao mesmo tempo
        threading.Thread(target=self._ler, daemon=True).start()

    @classmethod
    def da_porta(cls, porta, url_contem="", nova=None):
        """Aba cuja URL contém `url_contem` (ou uma nova em `nova`)."""
        if nova:
            req = urllib.request.Request(f"http://127.0.0.1:{porta}/json/new?{nova}", method="PUT")
            alvo = json.loads(urllib.request.urlopen(req, timeout=20).read())
        else:
            alvos = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{porta}/json", timeout=20).read())
            alvo = next((t for t in alvos if t["type"] == "page" and url_contem in t["url"]), None)
            if alvo is None:  # StopIteration solto vira erro mudo dentro de gerador/thread
                raise RuntimeError(f"porta {porta}: nenhuma aba com {url_contem!r} na URL")
        a = cls(alvo["webSocketDebuggerUrl"])
        a.alvo, a.porta = alvo, porta
        return a

    def _ler(self):
        while True:
            try:
                m = json.loads(self.ws.recv())
            except websocket.WebSocketTimeoutException:
                # 30/10: 60 s sem evento NÃO é aba fechada (ex.: Flow gerando por HTTP minutos a fio). Antes a thread
                # morria aqui e toda chamada seguinte (outro token, estender, corrigir) dava "sem resposta".
                continue
            except ValueError:
                continue  # quadro que não é JSON: ignora
            except Exception:  # noqa: BLE001 — aba fechada
                with self._cond:
                    self._resp[None] = "fechado"
                    self._cond.notify_all()
                return
            if "id" in m:
                with self._cond:
                    if m["id"] in getattr(self, "_atrasados", ()):
                        self._atrasados.discard(m["id"])  # quem pediu já desistiu
                        continue
                    self._resp[m["id"]] = m
                    self._cond.notify_all()
            elif m.get("method") in self._ouvintes:
                try:
                    p = m.get("params", {})
                    if "sessionId" in m:  # evento de alvo filho (flatten): quem ouve sabe de onde veio
                        p = {**p, "_sessao": m["sessionId"]}
                    self._ouvintes[m["method"]](p)
                except Exception as e:  # noqa: BLE001
                    print("ouvinte", m["method"], e)

    def chamar(self, metodo, params=None, timeout=60, sessao=None):
        """sessao = sessionId de um alvo filho (iframe/worker anexado com Target.setAutoAttach flatten)."""
        i = next(self._id)
        msg = json.dumps({"id": i, "method": metodo, "params": params or {}, **({"sessionId": sessao} if sessao else {})})
        with self._envio:
            self.ws.send(msg)
        fim = time.time() + timeout
        with self._cond:
            while i not in self._resp:
                resta = fim - time.time()
                if None in self._resp:
                    raise TimeoutError(f"{metodo}: a aba fechou")
                if resta <= 0:
                    self._atrasados = getattr(self, "_atrasados", set()) | {i}  # resposta tardia não fica acumulada
                    raise TimeoutError(f"{metodo} sem resposta")
                self._cond.wait(resta)
            m = self._resp.pop(i)
        if "error" in m:
            raise RuntimeError(f"{metodo}: {m['error']}")
        return m.get("result", {})

    def em(self, evento, fn):
        self._ouvintes[evento] = fn

    def js(self, expr, aguardar=True, timeout=60):
        r = self.chamar("Runtime.evaluate", {"expression": expr, "awaitPromise": aguardar, "returnByValue": True},
                        timeout=timeout)
        if r.get("exceptionDetails"):
            raise RuntimeError(f"js: {r['exceptionDetails'].get('exception', {}).get('description', r)}"[:400])
        return r.get("result", {}).get("value")

    def fechar(self, fechar_aba=False):
        try:
            if fechar_aba and getattr(self, "alvo", None):
                urllib.request.urlopen(f"http://127.0.0.1:{self.porta}/json/close/{self.alvo['id']}", timeout=10)
        except OSError:  # Chrome já fechado: a aba foi junto
            pass
        finally:
            self.ws.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.fechar()
