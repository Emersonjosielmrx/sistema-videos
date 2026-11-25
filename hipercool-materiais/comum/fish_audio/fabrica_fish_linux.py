#!/usr/bin/env python3
r"""fabrica_fish_linux.py — a fábrica de tokens do Fish NAS MÁQUINAS (notebooks Linux), mesma API da fabrica_fish.py do PC1.

25/11 dona ("todos sejam workers e montadores"; "não é pra ter diferença entre criar e relogar"): cada máquina gera Fish
com AS CONTAS DELA (sessoes_remotas\donos.json: 1 conta = 1 máquina). O Chrome da conta (chrome_conta.py --proxy-fish=N)
e a ponte do IP fixo (ponte_proxy_fixo.py N 18500+N) rodam AQUI — nunca pelo IP de casa.

    GET /estado            -> contas abertas
    GET /sessao?conta=E    -> {"token", "workspace", "proxy": "http://127.0.0.1:18500+N", "ip_n"}
    GET /token?conta=E     -> {"token": <reCAPTCHA Enterprise>}
    GET /soltar?conta=E    -> fecha o Chrome da conta

Contas: ~/postador-worker/fish_contas.json  {email: {"ip_n": N, "perfil": "..."}} (o PC1 escreve ao entregar a conta).
Sem dependências (só a biblioteca padrão): CDP por websocket feito à mão.
    python3 fabrica_fish_linux.py            # porta 9397 (FISH_FABRICA_PORTA)
"""
import base64
import json
import os
import socket
import struct
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE = Path.home() / "postador-worker"
CONTAS = BASE / "fish_contas.json"
LOG = BASE / "fabrica_fish_linux.log"
PORTA = int(os.environ.get("FISH_FABRICA_PORTA", "9397"))
SITEKEY = "6LfR4RwqAAAAAEvptRw9zohw7HeDU6NCqtAnJk1i"
OCIOSA_S = int(os.environ.get("FISH_OCIOSA_S", "900"))  # conta sem uso por 15 min = fecha o Chrome

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
_JS_SESSAO = """JSON.stringify({token: localStorage.getItem('token'),
  workspace: localStorage.getItem('active_workspace_id') || localStorage.getItem('active_team_id'),
  url: location.href})"""


def log(m):
    try:
        with LOG.open("a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%d/%m %H:%M:%S')}] {m}\n")
    except OSError:
        pass


# ------------------------------------------------------------------ websocket mínimo (cliente, texto)
class WS:
    def __init__(self, url, timeout=60):
        u = urllib.parse.urlparse(url)
        self.s = socket.create_connection((u.hostname, u.port), timeout=timeout)
        chave = base64.b64encode(os.urandom(16)).decode()
        self.s.sendall((f"GET {u.path} HTTP/1.1\r\nHost: {u.hostname}:{u.port}\r\nUpgrade: websocket\r\n"
                        f"Connection: Upgrade\r\nSec-WebSocket-Key: {chave}\r\nSec-WebSocket-Version: 13\r\n\r\n").encode())
        cab = b""
        while b"\r\n\r\n" not in cab:
            d = self.s.recv(4096)
            if not d:
                raise ConnectionError("websocket fechou no aperto de mão")
            cab += d
        if b" 101 " not in cab.split(b"\r\n", 1)[0]:
            raise ConnectionError(f"websocket recusado: {cab[:80]!r}")
        self.buf = cab.split(b"\r\n\r\n", 1)[1]
        self.n = 0

    def _ler(self, k):
        while len(self.buf) < k:
            d = self.s.recv(65536)
            if not d:
                raise ConnectionError("websocket fechou")
            self.buf += d
        r, self.buf = self.buf[:k], self.buf[k:]
        return r

    def enviar(self, txt):
        d = txt.encode()
        cab = bytearray([0x81])
        if len(d) < 126:
            cab.append(0x80 | len(d))
        elif len(d) < 65536:
            cab.append(0x80 | 126)
            cab += struct.pack(">H", len(d))
        else:
            cab.append(0x80 | 127)
            cab += struct.pack(">Q", len(d))
        m = os.urandom(4)
        self.s.sendall(bytes(cab) + m + bytes(b ^ m[i % 4] for i, b in enumerate(d)))

    def receber(self):
        partes = b""
        while True:
            b1, b2 = self._ler(2)
            k = b2 & 0x7F
            if k == 126:
                k = struct.unpack(">H", self._ler(2))[0]
            elif k == 127:
                k = struct.unpack(">Q", self._ler(8))[0]
            d = self._ler(k)
            op = b1 & 0x0F
            if op == 8:
                raise ConnectionError("websocket fechado pelo Chrome")
            if op in (9, 10):
                continue
            partes += d
            if b1 & 0x80:
                return partes.decode("utf-8", "replace")

    def cmd(self, metodo, params=None, timeout=90):
        self.n += 1
        meu = self.n
        self.s.settimeout(timeout)
        self.enviar(json.dumps({"id": meu, "method": metodo, "params": params or {}}))
        fim = time.time() + timeout
        while time.time() < fim:
            r = json.loads(self.receber())
            if r.get("id") == meu:
                if "error" in r:
                    raise RuntimeError(f"{metodo}: {r['error']}")
                return r.get("result", {})
        raise TimeoutError(metodo)

    def js(self, expr, timeout=90):
        r = self.cmd("Runtime.evaluate", {"expression": expr, "awaitPromise": True, "returnByValue": True},
                     timeout=timeout)
        if r.get("exceptionDetails"):
            raise RuntimeError(str(r["exceptionDetails"].get("exception", {}).get("description") or r)[:200])
        return r.get("result", {}).get("value")

    def fechar(self):
        try:
            self.s.close()
        except OSError:
            pass


# ------------------------------------------------------------------ conta
def _contas():
    try:
        return json.loads(CONTAS.read_text("utf-8"))
    except (OSError, ValueError):
        return {}


class Conta:
    def __init__(self, email):
        cfg = _contas().get(email)
        if not cfg:
            raise SystemExit(f"{email} não é desta máquina (fish_contas.json) — 1 conta = 1 máquina")
        self.email = email
        self.ip_n = int(cfg["ip_n"])
        self.perfil = cfg.get("perfil") or email.split("@")[0]
        self.porta_proxy = 18500 + self.ip_n
        # 25/11: porta da FAIXA EXTRA do chrome_conta (9461-9479, trava própria por porta) — a 9460 é "uma conta por vez"
        # da postagem e a 96xx caía na trava dela (a 2ª conta esperava 15 min). Faixa = posição da conta nesta máquina.
        minhas = sorted(_contas())
        self.porta = int(cfg.get("porta_cdp") or (9461 + (minhas.index(email) if email in minhas else 0) % 19))
        self.trava = threading.Lock()
        self.uso = time.time()
        self.ws = None
        self.sessao = None
        self._ponte()
        self._abrir()

    def _ponte(self):
        try:
            socket.create_connection(("127.0.0.1", self.porta_proxy), timeout=3).close()
        except OSError:
            subprocess.Popen([sys.executable, str(BASE / "ponte_proxy_fixo.py"), str(self.ip_n), str(self.porta_proxy)],
                             cwd=str(BASE), stdout=open(f"/tmp/ponte{self.ip_n}.log", "a"),
                             stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True)
            time.sleep(3)

    def _abrir(self):
        r = subprocess.run([sys.executable, str(BASE / "chrome_conta.py"), "abrir", self.perfil, str(self.porta),
                            "about:blank", f"--proxy-fish={self.ip_n}"], capture_output=True, text=True, timeout=600)
        if f"PROXY_OK {self.ip_n}" not in r.stdout and "ja estava aberto" not in r.stdout:
            raise RuntimeError(f"Chrome da conta não abriu pelo IP {self.ip_n}: {(r.stdout + r.stderr)[-200:]}")
        alvo = None
        for _ in range(30):
            try:
                abas = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{self.porta}/json", timeout=5).read())
                alvo = next((a for a in abas if a.get("type") == "page"), None)
                if alvo:
                    break
            except Exception:  # noqa: BLE001
                pass
            time.sleep(1)
        if not alvo:
            raise RuntimeError("sem aba no Chrome")
        self.ws = WS(alvo["webSocketDebuggerUrl"])
        self.ws.cmd("Page.enable")
        self.ws.cmd("Page.navigate", {"url": "https://fish.audio/pt/app/text-to-speech/"}, timeout=120)
        for _ in range(60):
            time.sleep(2)
            try:
                if self.ws.js("document.readyState", timeout=20) in ("interactive", "complete"):
                    break
            except Exception:  # noqa: BLE001
                pass
        time.sleep(5)
        ses = json.loads(self.ws.js(_JS_SESSAO, timeout=30) or "{}")
        if not ses.get("token") or "/auth" in (ses.get("url") or ""):
            raise PermissionError(f"{self.email}: Chrome desta máquina sem login no Fish (rodar logar_fish_remoto)")
        self.sessao = ses
        if not self.ws.js(_JS_CARREGAR, timeout=90):
            raise RuntimeError("reCAPTCHA não carregou")
        log(f"{self.email}: pronta (IP {self.ip_n}, CDP {self.porta})")

    def token(self):
        with self.trava:
            self.uso = time.time()
            for i in range(2):
                try:
                    return self.ws.js(_JS_TOKEN, timeout=90)
                except Exception as e:  # noqa: BLE001 — página recarregou / ws caiu: reabre 1 vez
                    log(f"{self.email}: token falhou ({str(e)[:120]}) — reabrindo")
                    if i:
                        raise
                    self.fechar(chrome=False)
                    self._abrir()

    def fechar(self, chrome=True):
        if self.ws:
            self.ws.fechar()
            self.ws = None
        if chrome:
            subprocess.run([sys.executable, str(BASE / "chrome_conta.py"), "fechar", str(self.porta)],
                           capture_output=True, timeout=60)


_contas_abertas, _geral = {}, threading.Lock()
_abrindo = {}


def conta(email):
    email = email.lower()
    with _geral:
        c = _contas_abertas.get(email)
        if c:
            return c
        t = _abrindo.setdefault(email, threading.Lock())
    with t:
        with _geral:
            if email in _contas_abertas:
                return _contas_abertas[email]
        c = Conta(email)
        with _geral:
            _contas_abertas[email] = c
        return c


def soltar(email):
    with _geral:
        c = _contas_abertas.pop(email.lower(), None)
    if c:
        c.fechar()


def _faxina():
    while True:
        time.sleep(60)
        with _geral:
            velhas = [e for e, c in _contas_abertas.items() if time.time() - c.uso > OCIOSA_S]
        for e in velhas:
            log(f"{e}: {OCIOSA_S // 60} min sem uso — fecho o Chrome")
            soltar(e)


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _resp(self, cod, obj):
        d = json.dumps(obj).encode()
        self.send_response(cod)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(d)))
        self.end_headers()
        self.wfile.write(d)

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        q = {k: v[0] for k, v in urllib.parse.parse_qs(u.query).items()}
        try:
            if u.path == "/estado":
                with _geral:
                    cp = list(_contas_abertas.items())
                return self._resp(200, {"contas": {e: {"ip_n": c.ip_n, "parada_s": int(time.time() - c.uso)}
                                                   for e, c in cp}, "minhas": list(_contas()), "pid": os.getpid()})
            email = (q.get("conta") or "").lower()
            if not email:
                return self._resp(400, {"erro": "falta ?conta="})
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
            return self._resp(404, {"erro": "rota desconhecida"})
        except PermissionError as e:
            return self._resp(401, {"erro": str(e)})
        except SystemExit as e:
            return self._resp(403, {"erro": str(e)})
        except (ConnectionError, BrokenPipeError):
            return None
        except Exception as e:  # noqa: BLE001
            log(f"erro {u.path}: {str(e)[:200]}")
            try:
                return self._resp(500, {"erro": str(e)[:300]})
            except (ConnectionError, BrokenPipeError):
                return None


if __name__ == "__main__":
    threading.Thread(target=_faxina, daemon=True).start()
    log(f"fábrica no ar em 127.0.0.1:{PORTA} (contas desta máquina: {list(_contas())})")
    ThreadingHTTPServer(("127.0.0.1", PORTA), H).serve_forever()
