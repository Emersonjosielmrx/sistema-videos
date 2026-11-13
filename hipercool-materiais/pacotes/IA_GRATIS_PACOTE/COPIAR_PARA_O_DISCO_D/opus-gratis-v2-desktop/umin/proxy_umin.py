# -*- coding: utf-8 -*-
r"""proxy_umin.py — IP da Webshare SÓ para o 1min.ai, para contornar o IP_LOCKED (31/10) na criação de contas.

Em 31/10 ~15h52 o 1min bloqueou o IP de casa por 24 h depois de 3 cadastros seguidos
(POST api.1min.ai/auth/oauth -> 400 IP_LOCKED). A dona pediu para usar o proxy da Webshare que já temos
(as mesmas credenciais do TikTok em D:\postador-de-videos\secrets\proxies.txt) para poder continuar.

Este módulo é GÊMEO do D:\postador-de-videos\bin\proxy_tiktok.py, mas:
  - portas próprias (PAC 18210, IPs 18211..18219) para NÃO colidir com o repassador do TikTok (18200/18201..18209),
    que é produção e não pode ser tocado;
  - o PAC manda pelo proxy SÓ os domínios do 1min (1min.ai / api.1min.ai). O login do Google (accounts.google.com)
    e todo o resto continuam saindo pela internet de CASA — assim o Google vê o IP confiável de sempre e só o 1min
    vê o IP da Webshare. É isso que troca o IP só onde o 1min bloqueou, sem quebrar o OAuth do Google.

O Chrome não aceita proxy com senha na linha de comando: o repassador escuta em 127.0.0.1:18211..18219, uma porta por
IP fixo da Webshare (usuário "<conta>-N"), e põe a senha (Basic). As contas grátis saem pelos MESMOS IPs fixos (o "-N"
é o mesmo IP em qualquer conta), então quando a banda do mês de uma acaba (402) passa para a próxima sem mudar de IP.
As últimas RESERVA_GROQ linhas de proxies.txt ficam para o Groq (igual ao proxy_tiktok).

  pythonw proxy_umin.py            # sobe o repassador (garantir() sobe sozinho se não estiver no ar)
  python proxy_umin.py --teste     # testa cada IP (CONNECT api.1min.ai:443) e diz quais respondem
  python proxy_umin.py --uso       # bytes por IP hoje
"""
import base64
import json
import re
import socket
import subprocess
import sys
import threading
import time
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path

PROXIES = Path(r"D:\postador-de-videos\secrets\proxies.txt")   # mesmas credenciais Webshare do TikTok
ESTADO = Path(__file__).resolve().parent / "proxy_umin_estado.json"
MAPA = Path(__file__).resolve().parent / "proxy_umin_mapa.json"       # conta -> IP fixo (espalha entre os 9)
UPSTREAM = ("p.webshare.io", 80)
PORTA_PAC = 18250                 # 18250 PAC, 18251..18259 um por IP (TikTok usa 18200/18201..18209; 18210 é um ssh)
IPS = range(1, 10)                # "-10" deu 403 no TikTok em 19/10: 9 IPs fixos
RESERVA_GROQ = 25                 # últimas linhas de proxies.txt são do Groq
DOMINIOS = r"1min\.ai"            # só o 1min pelo proxy; resto (Google etc.) DIRECT
FLAGS_EXTRA = ["--force-webrtc-ip-handling-policy=disable_non_proxied_udp"]  # WebRTC não vaza o IP de casa

_trava = threading.Lock()
_vez = Counter()
_estado = {"mortas": {}, "uso": {}}


def credenciais():
    out = []
    for linha in PROXIES.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^(?:https?://)?([^:\s]+)-rotate:([^@\s]+)@p\.webshare\.io:80$", linha.strip())
        if m:
            out.append(m.groups())
    return out[:max(0, len(out) - RESERVA_GROQ)]


def porta(n):
    return PORTA_PAC + n


def flags(n):
    """Flags do Chrome: PAC que manda só o 1min pelo IP n; o resto sai direto."""
    return [f"--proxy-pac-url=http://127.0.0.1:{PORTA_PAC}/{n}.pac", *FLAGS_EXTRA]


def _no_ar(p, timeout=2):
    try:
        socket.create_connection(("127.0.0.1", p), timeout=timeout).close()
        return True
    except OSError:
        return False


def garantir():
    """Sobe o repassador em segundo plano se não estiver no ar. True = no ar."""
    if _no_ar(PORTA_PAC):
        return True
    pyw = Path(sys.executable).with_name("pythonw.exe")
    subprocess.Popen([str(pyw if pyw.exists() else sys.executable), str(Path(__file__).resolve())],
                     creationflags=0x00000008 | 0x00000200, close_fds=True)  # DETACHED_PROCESS | NEW_PROCESS_GROUP
    for _ in range(20):
        time.sleep(0.5)
        if _no_ar(PORTA_PAC):
            return True
    return False


def pronto(n, alvo="api.1min.ai"):
    """O IP n abre túnel até o 1min agora? (só o CONNECT, sem baixar nada)"""
    try:
        s = socket.create_connection(("127.0.0.1", porta(n)), timeout=10)
        s.settimeout(40)
        s.sendall(f"CONNECT {alvo}:443 HTTP/1.1\r\nHost: {alvo}:443\r\n\r\n".encode())
        resp = s.recv(200)
        s.close()
        return resp.split(b" ")[1:2] == [b"200"]
    except (OSError, IndexError):
        return False


def ip_da_conta(conta):
    """IP fixo (1..9) desta conta, espalhando as contas entre os IPs (nova vai para o IP com menos contas)."""
    with _trava:
        m = json.loads(MAPA.read_text(encoding="utf-8")) if MAPA.exists() else {"contas": {}}
        if conta not in m["contas"]:
            uso = Counter(m["contas"].values())
            m["contas"][conta] = min(IPS, key=lambda n: (uso[n], n))
            MAPA.write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")
        return m["contas"][conta]


def escolher_ip(conta=None):
    """Garante o repassador no ar e devolve um IP que abre túnel até o 1min agora; None se nenhum.
    Com `conta`, prefere o IP fixo dela (se estiver com túnel); senão o 1º IP que responder."""
    if not garantir():
        return None
    if conta is not None:
        pref = ip_da_conta(conta)
        if pronto(pref):
            return pref
    for n in IPS:
        if pronto(n):
            return n
    return None


# ---------------- repassador ----------------

def _ler_estado():
    try:
        _estado.update(json.loads(ESTADO.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        pass


def _gravar_estado():
    while True:
        time.sleep(30)
        with _trava:
            _estado["uso"] = {d: v for d, v in _estado["uso"].items() if d >= str(date.today() - timedelta(days=40))}
            dados = json.dumps(_estado, ensure_ascii=False, indent=1)
        try:
            ESTADO.write_text(dados, encoding="utf-8")
        except OSError:
            pass


def _somar(n, user, nbytes):
    with _trava:
        dia = _estado["uso"].setdefault(str(date.today()), {})
        dia[f"ip{n}"] = dia.get(f"ip{n}", 0) + nbytes
        dia[user] = dia.get(user, 0) + nbytes


def _morta(user, status):
    # 402 = banda do mês acabou; 407 = senha recusada. Testa de novo em 24 h.
    ate = datetime.now() + timedelta(hours=24)
    with _trava:
        _estado["mortas"][user] = {"ate": ate.isoformat(timespec="minutes"), "status": status}


def _proxima(n, pool):
    agora = datetime.now().isoformat(timespec="minutes")
    with _trava:
        for _ in range(len(pool)):
            user, senha = pool[_vez[n] % len(pool)]
            _vez[n] += 1
            if _estado["mortas"].get(user, {}).get("ate", "") <= agora:
                return user, senha
    return None


def _cabeca(sock):
    buf = b""
    while b"\r\n\r\n" not in buf:
        c = sock.recv(4096)
        if not c or len(buf) > 65536:
            return None, b""
        buf += c
    i = buf.index(b"\r\n\r\n") + 4
    return buf[:i], buf[i:]


def _pipe(cli, up, n, user):
    def ida(src, dst):
        tot = 0
        try:
            while True:
                d = src.recv(65536)
                if not d:
                    break
                dst.sendall(d)
                tot += len(d)
        except OSError:
            pass
        finally:
            _somar(n, user, tot)
            for s in (src, dst):
                try:
                    s.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
    cli.settimeout(None)
    up.settimeout(None)
    t = threading.Thread(target=ida, args=(cli, up), daemon=True)
    t.start()
    ida(up, cli)
    t.join()


def _atender(cli, n, pool):
    up = None
    try:
        cli.settimeout(60)
        cab, resto = _cabeca(cli)
        if not cab:
            return
        linhas = [x for x in cab.decode("latin-1").split("\r\n") if x]
        tunel = linhas[0].upper().startswith("CONNECT ")
        for _ in range(8):
            cred = _proxima(n, pool)
            if not cred:
                break
            user, senha = cred
            try:
                up = socket.create_connection(UPSTREAM, timeout=20)
            except OSError:
                time.sleep(1)
                continue
            auth = base64.b64encode(f"{user}-{n}:{senha}".encode()).decode()
            novo = [linhas[0], f"Proxy-Authorization: Basic {auth}"] + [
                x for x in linhas[1:] if not x.lower().startswith("proxy-authorization")]
            up.sendall(("\r\n".join(novo) + "\r\n\r\n").encode("latin-1") + resto)
            if tunel:
                resp, extra = _cabeca(up)
                status = int(resp.split()[1]) if resp else 0
                if status in (402, 407):
                    _morta(user, status)
                    up.close()
                    up = None
                    continue
                cli.sendall((resp or b"HTTP/1.1 502 Bad Gateway\r\n\r\n") + extra)
                if status != 200:
                    return
            _pipe(cli, up, n, user)
            return
        cli.sendall(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
    except OSError:
        pass
    finally:
        for s in (cli, up):
            if s:
                try:
                    s.close()
                except OSError:
                    pass


def _servir(p, alvo):
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", p))
    srv.listen(64)
    while True:
        c, _ = srv.accept()
        threading.Thread(target=alvo, args=(c,), daemon=True).start()


def _pac(cli):
    try:
        cli.settimeout(10)
        cab, _ = _cabeca(cli)
        m = re.match(rb"GET /(\d+)\.pac", cab or b"")
        if not m or int(m.group(1)) not in IPS:
            cli.sendall(b"HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\n\r\n")
            return
        corpo = ("function FindProxyForURL(url, host) {\n"
                 f"  if (/{DOMINIOS}/i.test(host)) return \"PROXY 127.0.0.1:{porta(int(m.group(1)))}\";\n"
                 "  return \"DIRECT\";\n}\n").encode()
        cli.sendall(b"HTTP/1.1 200 OK\r\nContent-Type: application/x-ns-proxy-autoconfig\r\nContent-Length: "
                    + str(len(corpo)).encode() + b"\r\n\r\n" + corpo)
    except OSError:
        pass
    finally:
        cli.close()


def main():
    _ler_estado()
    pool = credenciais()
    if not pool:
        print("proxies.txt sem credenciais Webshare utilizáveis", file=sys.stderr)
        return
    for n in IPS:
        threading.Thread(target=_servir, args=(porta(n), lambda c, n=n: _atender(c, n, pool)), daemon=True).start()
    threading.Thread(target=_gravar_estado, daemon=True).start()
    _servir(PORTA_PAC, _pac)


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # sob pythonw (repassador) stdout é None
    except (AttributeError, ValueError):
        pass
    if "--uso" in sys.argv:
        _ler_estado()
        print(json.dumps(_estado["uso"].get(str(date.today()), {}), indent=1))
        print("mortas:", {u[:5]: v for u, v in _estado["mortas"].items()})
    elif "--teste" in sys.argv:
        print("garantindo repassador...", "no ar" if garantir() else "FALHOU")
        for n in IPS:
            print(f"  IP {n}: {'OK (túnel até api.1min.ai)' if pronto(n) else 'sem túnel'}")
    else:
        main()
