"""proxy_tiktok.py — IP fixo da Webshare para cada conta do TikTok (dono 19/10: "é só usar proxy da webshare"; escolheu
os grátis mesmo sabendo: IPs de datacenter EUA/GB/PT/DE, nenhum do Brasil).

O Chrome não aceita proxy com senha na linha de comando: este repassador escuta em 127.0.0.1:18201..18209 (+ 18220 para o
IP 10, porque a 18210 é do proxy_celular), uma porta por
IP fixo da Webshare (usuário "<conta>-N"), e põe a senha. As contas grátis da Webshare saem pelos MESMOS IPs (o "-N" é o
mesmo IP em qualquer conta, conferido 19/10), então quando a banda do mês de uma acaba (402) passa para a próxima sem a
conta do TikTok mudar de IP. As últimas RESERVA_GROQ linhas de secrets/proxies.txt ficam só para o Groq.
O Chrome usa um PAC (http://127.0.0.1:18200/<N>.pac) que manda SÓ os domínios do TikTok pelo proxy, sem cair para
direto se o proxy falhar: o mesmo perfil do cofre também sobe no YouTube, que continua saindo pela internet de casa.
Conta -> IP fica gravada em config/proxy_tiktok.json (conta nova vai para o IP com menos contas).

  pythonw proxy_tiktok.py            # o postar_tiktok_auto sobe sozinho (garantir()) se não estiver no ar
  python proxy_tiktok.py --uso       # bytes por IP hoje
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

PROXIES = Path(r"D:\postador-de-videos\secrets\proxies.txt")
MAPA = Path(r"D:\postador-de-videos\config\proxy_tiktok.json")
ESTADO = Path(r"D:\postador-de-videos\logs\proxy_tiktok_estado.json")
UPSTREAM = ("p.webshare.io", 80)
PORTA_PAC = 18200
IPS = range(1, 11)  # 12/11: são 10 IPs fixos — o "-10" responde 200 (64.137.96.74) com login que tem banda; o 403 de
# 19/10 era login SEM banda. "-11" = 407 (não existe). Ver docs\TIKTOK_IPS_COMPARTILHADOS.md
RESERVA_GROQ = 25
DOMINIOS = r"tiktok|ttwstatic|byte|muscdn|snssdk|ttlivecdn|ttdns|tiktokv"
DOMINIOS_IG = r"instagram|cdninstagram|facebook|fbcdn|fbsbx|meta\.com"
FLAGS_EXTRA = ["--force-webrtc-ip-handling-policy=disable_non_proxied_udp"]  # WebRTC não mostra o IP de casa

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
    # 12/11: o IP 10 iria para 18210, que é a porta SOCKS do proxy_celular — vai para 18220 (os 1..9 não mudam)
    return PORTA_PAC + n if n < 10 else PORTA_PAC + 10 + n


def flags(n, rede="tiktok"):
    return [f"--proxy-pac-url=http://127.0.0.1:{PORTA_PAC}/{'ig' if rede == 'instagram' else ''}{n}.pac", *FLAGS_EXTRA]


def ip_da_conta(conta):
    with _trava:
        m = json.loads(MAPA.read_text(encoding="utf-8")) if MAPA.exists() else {"contas": {}}
        if conta not in m["contas"]:
            uso = Counter(m["contas"].values())
            m["contas"][conta] = min(IPS, key=lambda n: (uso[n], n))
            MAPA.write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")
        return m["contas"][conta]


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


def pronto(n):
    """O IP n abre túnel até o TikTok agora? (só o CONNECT, sem baixar nada)"""
    try:
        s = socket.create_connection(("127.0.0.1", porta(n)), timeout=10)
        s.settimeout(40)
        s.sendall(b"CONNECT www.tiktok.com:443 HTTP/1.1\r\nHost: www.tiktok.com:443\r\n\r\n")
        resp = s.recv(200)
        s.close()
        return resp.split(b" ")[1:2] == [b"200"]
    except (OSError, IndexError):
        return False


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
    # 402 = banda acabou; o dono 19/10: cada conta renova a cada 30 dias (dia diferente em cada uma) -> testa de novo
    # em 24 h (só um CONNECT); 407 = senha recusada, idem
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
    srv.bind(("127.0.0.1", p))
    srv.listen(64)
    while True:
        c, _ = srv.accept()
        threading.Thread(target=alvo, args=(c,), daemon=True).start()


def _pac(cli):
    try:
        cli.settimeout(10)
        cab, _ = _cabeca(cli)
        m = re.match(rb"GET /(ig)?(\d+)\.pac", cab or b"")
        if not m or int(m.group(2)) not in IPS:
            cli.sendall(b"HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\n\r\n")
            return
        # 11/11 (dona: "Instagram e TikTok usem os proxies grátis"): /ig<N>.pac = mesmo IP fixo, domínios do Instagram/
        # Meta (o Gmail/Google seguem DIRECT — o criador lê o código no Gmail do perfil, que sempre saiu por casa)
        dom = DOMINIOS_IG if m.group(1) else DOMINIOS
        corpo = ("function FindProxyForURL(url, host) {\n"
                 f"  if (/{dom}/i.test(host)) return \"PROXY 127.0.0.1:{porta(int(m.group(2)))}\";\n"
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
    for n in IPS:
        threading.Thread(target=_servir, args=(porta(n), lambda c, n=n: _atender(c, n, pool)), daemon=True).start()
    threading.Thread(target=_gravar_estado, daemon=True).start()
    _servir(PORTA_PAC, _pac)


if __name__ == "__main__":
    if "--uso" in sys.argv:
        _ler_estado()
        print(json.dumps(_estado["uso"].get(str(date.today()), {}), indent=1))
        print("mortas:", {u[:5]: v for u, v in _estado["mortas"].items()})
    else:
        main()
