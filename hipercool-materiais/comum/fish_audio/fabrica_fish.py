"""fabrica_fish.py — CHROME QUENTE que fabrica os tokens do reCAPTCHA Enterprise do Fish Audio (molde da
fabrica_tokens.py do Flow). Quem gera a fala continua sendo HTTP puro (fish_http.py).

Por quê (medido 18/11): o 1º token de um Chrome recém-aberto leva ~40 s; depois 10 s, 5 s, 3,5 s... e 3 em paralelo
saem em 1,9 s. Abrir o Chrome a cada roteiro pagava os 40 s toda vez. Aqui o Chrome da conta fica aberto (fora da
tela, pela ponte do IP fixo dela), aquecido, com uma RESERVA de tokens prontos (o token vale ~2 min, uso único).

    GET /sessao?conta=E   -> {"token": <Bearer>, "workspace": ..., "proxy": "http://127.0.0.1:N"}  (abre se precisar)
    GET /token?conta=E    -> {"token": "<SEGREDO_REMOVIDO>"}  (da reserva; sem reserva fabrica na hora)
    GET /estado           -> contas quentes, reserva, idade
    GET /soltar?conta=E   -> fecha o Chrome dessa conta

Conta parada por OCIOSO_S (15 min) = fecha sozinha; sem nenhuma conta aberta a fábrica encerra (não fica processo à
toa). Quem chama (fish_http) sobe a fábrica sozinho se ela não responder.

Regras: só contas do pool do Fish (fish_audio.checar_conta recusa Kaggle e conta sem fish_proxy); o Chrome sai
SEMPRE pela ponte do IP da conta; 1 Chrome por conta.

    pythonw fabrica_fish.py          (oculto; o fish_http sobe assim)
"""
import itertools
import json
import os
import sys
import threading
import time
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import websocket

sys.path.insert(0, r"D:\logins-google")
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import fish_audio as fa  # noqa: E402

PORTA = int(os.environ.get("FISH_FABRICA_PORTA", "9397"))
SITEKEY = "6LfR4RwqAAAAAEvptRw9zohw7HeDU6NCqtAnJk1i"
RESERVA = int(os.environ.get("FISH_RESERVA", "3"))
VALIDADE_S = 100          # token do reCAPTCHA vale ~2 min; descarta antes
OCIOSO_S = int(os.environ.get("FISH_OCIOSO_S", str(15 * 60)))
RECARREGAR_S = 40 * 60     # aba muito velha: recarrega (sessão/reCAPTCHA renovados)
LOG = AQUI / "fabrica_fish.log"
FLAGS = ("--disable-background-timer-throttling", "--disable-renderer-backgrounding",
         "--disable-backgrounding-occluded-windows")

_JS_CARREGAR = """new Promise(r => {
  const ok = () => !!(window.grecaptcha && grecaptcha.enterprise && grecaptcha.enterprise.execute);
  const t0 = Date.now();
  let posto = false;
  const v = setInterval(() => {
    if (ok()) { clearInterval(v); return r(true); }
    // 18/11: na página ainda carregando o document.head é null -> espera o DOM antes de injetar
    if (!posto && (document.head || document.documentElement)) {
      const s = document.createElement('script');
      s.src = 'https://www.google.com/recaptcha/enterprise.js?render=%s';
      (document.head || document.documentElement).appendChild(s);
      posto = true;
    }
    if (Date.now() - t0 > 60000) { clearInterval(v); r(false); }
  }, 250);
})""" % SITEKEY

_JS_TOKEN = """new Promise((res, rej) => { const g = grecaptcha.enterprise;
  g.ready(() => g.execute('%s', {action: 'tts'}).then(res).catch(e => rej(String(e)))); })""" % SITEKEY

_JS_SESSAO = """({token: localStorage.getItem('token'),
  workspace: localStorage.getItem('active_workspace_id') || localStorage.getItem('active_team_id'),
  url: location.href, login: location.pathname.includes('/auth')})"""


def log(m):
    try:
        with LOG.open("a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%d/%m %H:%M:%S')}] {m}\n")
    except OSError:
        pass


class Aba:
    """CDP direto numa aba (sem Playwright): Runtime.evaluate com awaitPromise."""

    def __init__(self, ws_url):
        self.ws = websocket.create_connection(ws_url, timeout=90, suppress_origin=True)
        self.ids = itertools.count(1)
        self.trava = threading.Lock()

    def js(self, expr, timeout=90):
        with self.trava:
            i = next(self.ids)
            self.ws.settimeout(timeout)
            self.ws.send(json.dumps({"id": i, "method": "Runtime.evaluate",
                                     "params": {"expression": expr, "awaitPromise": True, "returnByValue": True}}))
            fim = time.time() + timeout
            while time.time() < fim:
                m = json.loads(self.ws.recv())
                if m.get("id") == i:
                    r = m.get("result", {})
                    if "exceptionDetails" in r:
                        raise RuntimeError(str(r["exceptionDetails"].get("exception", {}).get("description")
                                               or r["exceptionDetails"])[:300])
                    return r.get("result", {}).get("value")
            raise TimeoutError("js sem resposta")

    def navegar(self, url):
        with self.trava:
            self.ws.send(json.dumps({"id": next(self.ids), "method": "Page.navigate", "params": {"url": url}}))

    def fechar(self):
        try:
            self.ws.close()
        except Exception:  # noqa: BLE001
            pass


class Conta:
    def __init__(self, email):
        import cofre
        self.email = email
        self.cofre = cofre
        _, self.ip_n = fa.checar_conta(email)
        self.porta_proxy = fa._subir_ponte(self.ip_n)
        self.trava = threading.Lock()      # 1 fabricação por vez nesta aba
        self.reserva = []                  # [(criado_em, token)]
        self.uso = time.time()
        self.proc = None
        self._abrir()

    def _abrir(self):
        _, e = self.cofre.conta(self.email)
        if self.cofre._cdp_vivo(e["porta"]):
            # Chrome da conta JÁ aberto (login da dona, fish_audio.py, sobra): nunca fecha o que não abriu. Só usa se
            # ele sai pela ponte do IP DESTA conta; senão recusa (falaria pela casa ou por outro IP).
            cmds = " ".join(c for _, c in self.cofre._chrome_da_porta(e["porta"]))
            if f"127.0.0.1:{self.porta_proxy}" not in cmds:
                raise RuntimeError(f"{self.email}: Chrome da conta já aberto SEM a ponte do IP dela — feche essa janela")
        self.porta, self.proc = self.cofre.abrir(self.email, url="about:blank",
                                                 extra=(f"--proxy-server=127.0.0.1:{self.porta_proxy}", *FLAGS))
        if self.proc is not None:  # pid REAL do Chrome principal da porta (o do Popen pode ter se relançado)
            try:
                reais = [int(p) for p, _ in self.cofre._chrome_da_porta(self.porta)]
            except Exception:  # noqa: BLE001
                reais = []
            _anotar_aberto(self.porta, reais[0] if reais else self.proc.pid)
        alvos = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{self.porta}/json", timeout=20).read())
        pg = next((t for t in alvos if t["type"] == "page"), None)
        if pg is None:
            req = urllib.request.Request(f"http://127.0.0.1:{self.porta}/json/new?about:blank", method="PUT")
            pg = json.loads(urllib.request.urlopen(req, timeout=20).read())
        self.aba = Aba(pg["webSocketDebuggerUrl"])
        self._carregar_pagina()

    def _carregar_pagina(self):
        self.aba.navegar(f"https://fish.audio/pt/app/text-to-speech/?modelId={fa.VOZ_PADRAO}")
        fim = time.time() + 90
        ses = None
        while time.time() < fim:
            time.sleep(1.5)
            try:
                ses = self.aba.js(_JS_SESSAO, timeout=20)
            except Exception:  # noqa: BLE001 — página no meio da navegação
                continue
            if ses and (ses.get("token") or ses.get("login")) and "fish.audio" in (ses.get("url") or ""):
                break
        if not ses or ses.get("login") or not ses.get("token"):
            raise PermissionError(f"{self.email}: deslogada no Fish (logar pelo cofre: login_fish.py)")
        self.sessao = ses
        try:  # token Bearer + workspace guardados: saldo/escolha de conta depois saem por HTTP, sem Chrome
            import sessoes_fish
            sessoes_fish.gravar(self.email, ses["token"], ses.get("workspace"))
        except Exception as e:  # noqa: BLE001
            log(f"{self.email}: não gravei a sessão ({str(e)[:100]})")
        if not self.aba.js(_JS_CARREGAR, timeout=75):
            raise RuntimeError(f"{self.email}: reCAPTCHA Enterprise não carregou")
        self.desde = time.time()
        log(f"{self.email}: aba pronta (IP N={self.ip_n}, porta {self.porta})")

    def _fabricar(self):
        with self.trava:
            if getattr(self, "fechada", False):
                raise RuntimeError(f"{self.email}: conta já foi solta")
            if time.time() - self.desde > RECARREGAR_S:
                self.reserva.clear()
                self._carregar_pagina()
            try:
                return self.aba.js(_JS_TOKEN, timeout=90)
            except Exception as e:  # noqa: BLE001 — página recarregou sozinha (grecaptcha sumiu): recarrega 1 vez
                log(f"{self.email}: token falhou ({str(e)[:80]}) — recarregando a aba")
                self.reserva.clear()
                self._carregar_pagina()
                return self.aba.js(_JS_TOKEN, timeout=90)

    def token(self):
        self.uso = time.time()
        while self.reserva:
            criado, tok = self.reserva.pop(0)
            if time.time() - criado < VALIDADE_S:
                return tok
        return self._fabricar()

    def encher(self):
        """Mantém a reserva cheia (roda na linha de fundo). 1 enchimento por vez (zelador e /aquecer juntos)."""
        if not hasattr(self, "_enchendo"):
            self._enchendo = threading.Lock()
        if not self._enchendo.acquire(blocking=False):
            return
        try:
            self._encher()
        finally:
            self._enchendo.release()

    def _encher(self):
        self.reserva = [(c, t) for c, t in self.reserva if time.time() - c < VALIDADE_S]
        while (len(self.reserva) < RESERVA and time.time() - self.uso < OCIOSO_S
               and not getattr(self, "fechada", False)):
            try:
                self.reserva.append((time.time(), self._fabricar()))
            except Exception as e:  # noqa: BLE001
                log(f"{self.email}: falha ao encher a reserva ({str(e)[:120]})")
                return

    def fechar(self):
        self.fechada = True
        self.reserva.clear()
        self.aba.fechar()
        if self.proc is None:  # o cofre devolveu um Chrome que já estava aberto: não é nosso, não fecha
            log(f"{self.email}: soltei (Chrome não era meu, ficou aberto)")
            return
        try:  # 18/11: cofre.fechar só ESPERA o processo; quem pede para o Chrome sair é o Browser.close pelo CDP
            v = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{self.porta}/json/version", timeout=10).read())
            w = websocket.create_connection(v["webSocketDebuggerUrl"], timeout=10, suppress_origin=True)
            w.send(json.dumps({"id": 1, "method": "Browser.close"}))
            w.close()
        except Exception:  # noqa: BLE001
            pass
        try:
            self.cofre.fechar(self.proc, nome=self.email)
        except Exception:  # noqa: BLE001
            pass
        if self.cofre._cdp_vivo(self.porta):  # não saiu: mata só o Chrome desta porta (é o que abrimos)
            self.cofre._fechar_porta(self.porta)
        try:  # já fechado: tira da lista de sobras
            d = json.loads(ABERTOS.read_text("utf-8"))
            d.pop(str(self.porta), None)
            ABERTOS.write_text(json.dumps(d), "utf-8")
        except (OSError, ValueError):
            pass
        log(f"{self.email}: Chrome fechado")


_contas = {}
_geral = threading.Lock()
_abrindo = {}  # email -> Lock (2 pedidos da mesma conta não abrem 2 Chromes)


def conta(email):
    email = email.lower()
    with _geral:
        c = _contas.get(email)
        if c:
            return c
        tr = _abrindo.setdefault(email, threading.Lock())
    with tr:
        c = _contas.get(email)
        if c:
            return c
        c = Conta(email)
        with _geral:
            _contas[email] = c
        return c


def _varrer_orfaos():
    """Fecha Chrome com a ponte do Fish (--proxy-server=127.0.0.1:185xx) cuja porta CDP não é de nenhuma conta aberta
    nesta fábrica, com mais de 3 min de vida (o que está abrindo agora fica). Só os da ponte do Fish — Kaggle/Flow/
    cofre comum têm outra ponte ou nenhuma."""
    import re as _re
    import subprocess as _sp
    with _geral:
        minhas = {getattr(c, "porta", None) for c in _contas.values()}
    ps = ("Get-CimInstance Win32_Process -Filter \"Name='chrome.exe'\" | Where-Object { $_.CommandLine -match "
          "'proxy-server=127\\.0\\.0\\.1:185' -and $_.CommandLine -notmatch '--type=' } | ForEach-Object { "
          "\"$($_.ProcessId)|$($_.CreationDate.ToString('o'))|$($_.CommandLine)\" }")
    r = _sp.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True, timeout=240,
                creationflags=0x08000000)  # PC lento: listar processos chegou a levar > 60 s
    from datetime import datetime as _dt, timezone as _tz
    for linha in (r.stdout or "").splitlines():
        try:
            pid, criado, cmd = linha.split("|", 2)
            m = _re.search(r"remote-debugging-port=(\d+)", cmd)
            porta = int(m.group(1)) if m else None
            idade = (_dt.now(_tz.utc) - _dt.fromisoformat(criado.strip())).total_seconds()
        except (ValueError, AttributeError):
            continue
        if porta in minhas or idade < 180:
            continue
        _sp.run(["taskkill", "/PID", pid.strip(), "/T", "/F"], capture_output=True, creationflags=0x08000000)
        log(f"Chrome órfão do Fish fechado (porta {porta}, {idade / 60:.0f} min aberto)")


def soltar(email):
    with _geral:
        c = _contas.pop(email.lower(), None)
    if c:
        c.fechar()


def zelador(srv):
    """Enche as reservas e fecha conta ociosa; sem conta nenhuma por OCIOSO_S, encerra a fábrica."""
    vazio_desde = time.time()
    ult_varre = 0.0
    while True:
        time.sleep(5)
        # 21/11 dona ("fecha as abas Fish que não estão sendo usadas; elas não fecham"): Chrome que abriu DEPOIS do
        # "não abriu a porta em 45 s" (PC lento) ou que sobrou de uma fábrica anterior (que caiu/reiniciou) não estava
        # em _contas e ninguém fechava. A cada 5 min fecha todo Chrome da ponte do Fish que não é desta fábrica.
        # FISH_VARRE_ORFAOS=0 desliga.
        if time.time() - ult_varre > 300 and os.environ.get("FISH_VARRE_ORFAOS", "1") != "0":
            ult_varre = time.time()
            try:
                _varrer_orfaos()
            except Exception as e:  # noqa: BLE001
                log(f"varredura de órfãos falhou ({type(e).__name__})")
        for email, c in list(_contas.items()):
            if time.time() - c.uso > OCIOSO_S:
                soltar(email)
            else:
                c.encher()
        if _contas:
            vazio_desde = time.time()
        elif time.time() - vazio_desde > OCIOSO_S:
            log("fábrica ociosa: encerrando")
            srv.shutdown()
            return


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _resp(self, code, obj):
        b = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        try:
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)
        except (ConnectionError, BrokenPipeError):  # cliente já foi embora (ex.: _fabrica_no_ar com 3 s)
            pass

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        q = {k: v[0] for k, v in urllib.parse.parse_qs(u.query).items()}
        try:
            if u.path == "/estado":
                with _geral:
                    copia = list(_contas.items())  # outra linha pode estar abrindo/soltando conta agora
                return self._resp(200, {"contas": {e: {"reserva": len(c.reserva), "parada_s": int(time.time() - c.uso),
                                                       "aba_idade_s": int(time.time() - getattr(c, "desde", time.time())),
                                                       "ip_n": c.ip_n}
                                                   for e, c in copia}, "pid": os.getpid()})
            email = q.get("conta") or fa.CONTA_PADRAO
            if u.path == "/sessao":
                c = conta(email)
                c.uso = time.time()
                return self._resp(200, {"token": c.sessao["token"], "workspace": c.sessao["workspace"],
                                        "proxy": f"http://127.0.0.1:{c.porta_proxy}", "ip_n": c.ip_n})
            if u.path == "/token":
                return self._resp(200, {"token": conta(email).token()})
            if u.path == "/soltar":
                soltar(email)
                return self._resp(200, {"ok": True})
            if u.path == "/aquecer":
                # abre a conta e enche a reserva em segundo plano; responde na hora (quem pede não espera o Chrome)
                def _aq():
                    try:
                        conta(email).encher()
                    except Exception as e:  # noqa: BLE001
                        log(f"{email}: aquecer falhou ({str(e)[:120]})")
                threading.Thread(target=_aq, daemon=True).start()
                return self._resp(202, {"ok": True, "aquecendo": email})
            return self._resp(404, {"erro": "rota desconhecida"})
        except PermissionError as e:
            return self._resp(401, {"erro": str(e)})
        except SystemExit as e:  # checar_conta recusou (Kaggle / fora do pool)
            return self._resp(403, {"erro": str(e)})
        except (ConnectionError, BrokenPipeError):  # quem pediu desistiu antes da resposta: nada a fazer
            return None
        except Exception as e:  # noqa: BLE001
            log(f"erro {u.path}: {str(e)[:200]}")
            try:
                return self._resp(500, {"erro": str(e)[:300]})
            except (ConnectionError, BrokenPipeError):
                return None


ABERTOS = AQUI / "fabrica_abertos.json"  # Chromes que ESTA fábrica abriu (para limpar se ela morrer de repente)


def _anotar_aberto(porta, pid_chrome):
    try:
        d = json.loads(ABERTOS.read_text("utf-8")) if ABERTOS.exists() else {}
    except (OSError, ValueError):
        d = {}
    d[str(porta)] = {"pid": pid_chrome, "fabrica": os.getpid()}
    ABERTOS.write_text(json.dumps(d), "utf-8")


def _limpar_sobras():
    """Fábrica anterior morreu sem fechar: fecha SÓ os Chromes que ela anotou como seus (porta + pid do Chrome iguais
    aos anotados — nunca fecha o Chrome que a dona ou outro projeto abriu depois na mesma porta)."""
    import cofre
    try:
        d = json.loads(ABERTOS.read_text("utf-8")) if ABERTOS.exists() else {}
    except (OSError, ValueError):
        d = {}
    for porta, info in d.items():
        try:
            pids = [int(p) for p, _ in cofre._chrome_da_porta(int(porta))]
        except Exception:  # noqa: BLE001
            pids = []
        if info.get("pid") in pids:
            cofre._fechar_porta(int(porta))
            log(f"sobra da fábrica anterior fechada (porta {porta})")
    try:
        ABERTOS.unlink()
    except OSError:
        pass


def main():
    try:
        srv = ThreadingHTTPServer(("127.0.0.1", PORTA), H)
    except OSError:
        print(f"porta {PORTA} ocupada: outra fábrica já está no ar")
        return
    _limpar_sobras()
    log(f"fábrica no ar (pid {os.getpid()}, porta {PORTA})")
    threading.Thread(target=zelador, args=(srv,), daemon=True).start()
    try:
        srv.serve_forever()
    finally:
        for e in list(_contas):
            soltar(e)


if __name__ == "__main__":
    main()
