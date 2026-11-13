"""ponte_proxy_fixo.py — repassador local SEM senha para UM proxy fixo da Webshare (06/11/2026).

Dona 06/11: "crie os tokens dessas contas já usando proxies". Regra do banimento 02/11: cada conta Kaggle fala com o
Kaggle (e com o Google, no login) só pelo IP fixo dela. O Chrome não aceita proxy com senha: este processo escuta em
127.0.0.1:<porta> e repassa TUDO (sem PAC, sem cair para direto) para http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80.

    python ponte_proxy_fixo.py <N> <porta>      # ex.: 2 18302
"""
import base64
import socket
import sys
import threading
from pathlib import Path

PROXIES = Path(r"D:\postador-de-videos\secrets\proxies.txt")
UP = ("p.webshare.io", 80)
# 11/11 (dona: login do Google da verse8 dava "Request canceled" / ERR_TIMED_OUT): o proxy direto responde em 0,4–0,8 s,
# mas pela ponte o Google levava 12–17 s ou caía — o Chrome abre ~38 conexões ao mesmo tempo e a Webshare engasga com
# tantos túneis CONNECT simultâneos do mesmo usuário. Limita os túneis ABRINDO ao mesmo tempo (os já abertos não contam
# como espera) e liga TCP_NODELAY (TLS em pacotes pequenos). PONTE_MAX_ABRINDO muda.
import os  # noqa: E402
ABRINDO = threading.BoundedSemaphore(int(os.environ.get("PONTE_MAX_ABRINDO", "12")))


def credencial(n):
    for l in PROXIES.read_text(encoding="utf-8").splitlines():
        l = l.strip()
        if "rnprmtfo-rotate:" in l and "p.webshare.io" in l:
            senha = l.split("rnprmtfo-rotate:", 1)[1].split("@", 1)[0]
            return base64.b64encode(f"rnprmtfo-{n}:{senha}".encode()).decode()
    raise SystemExit("sem rnprmtfo em proxies.txt")


def pipe(a, b):
    try:
        while True:
            d = a.recv(65536)
            if not d:
                break
            b.sendall(d)
    except OSError:
        pass
    finally:
        for s in (a, b):
            try:
                s.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass


def atender(cli, auth):
    try:
        cab = b""
        while b"\r\n\r\n" not in cab:
            d = cli.recv(65536)
            if not d:
                cli.close()
                return
            cab += d
        topo, resto = cab.split(b"\r\n\r\n", 1)
        linhas = topo.split(b"\r\n")
        linhas = [l for l in linhas if not l.lower().startswith(b"proxy-authorization")]
        linhas.insert(1, b"Proxy-Authorization: Basic " + auth.encode())
        with ABRINDO:  # só a abertura do túnel (CONNECT até a 1ª resposta) entra na fila
            up = socket.create_connection(UP, timeout=30)
            for s_ in (up, cli):
                s_.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            up.sendall(b"\r\n".join(linhas) + b"\r\n\r\n" + resto)
            if linhas[0].upper().startswith(b"CONNECT"):
                # 11/11 tarde: túnel da Webshare que não responde em 8 s prendia a vaga 40 s e travava a fila inteira
                # (login do Google caía em ERR_TIMED_OUT) — desiste rápido; o Chrome tenta de novo noutra conexão
                up.settimeout(float(os.environ.get("PONTE_ESPERA_200_S", "8")))
                resp = b""
                while b"\r\n\r\n" not in resp:  # espera o "200 Connection established" antes de soltar a vaga
                    d = up.recv(4096)
                    if not d:
                        break
                    resp += d
                cli.sendall(resp)
        up.settimeout(None)
        cli.settimeout(None)
        threading.Thread(target=pipe, args=(cli, up), daemon=True).start()
        pipe(up, cli)
    except OSError:
        try:
            cli.close()
        except OSError:
            pass


def main():
    n, porta = int(sys.argv[1]), int(sys.argv[2])
    auth = credencial(n)
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("127.0.0.1", porta))
    s.listen(64)
    print(f"ponte rnprmtfo-{n} em 127.0.0.1:{porta}", flush=True)
    while True:
        c, _ = s.accept()
        threading.Thread(target=atender, args=(c, auth), daemon=True).start()


if __name__ == "__main__":
    main()
