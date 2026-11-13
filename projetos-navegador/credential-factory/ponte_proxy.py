r"""Ponte local -> Webshare com usuario/senha (o Chrome nao aceita proxy com senha na linha de comando).

  python ponte_proxy.py <usuario-webshare-N> <senha> <porta_local>
  ex.: python ponte_proxy.py rnprmtfo-5 SENHA 18815

Cada conta usa SEMPRE a mesma ponte/IP (regra: nunca 2 contas no mesmo IP). Fica no ar ate ser encerrada.
"""
import base64
import socket
import sys
import threading

usuario, senha, porta = sys.argv[1], sys.argv[2], int(sys.argv[3])
AUTH = base64.b64encode(f"{usuario}:{senha}".encode()).decode()


def _pipe(a, b):
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
                s.close()
            except OSError:
                pass


def _atender(c):
    try:
        req = c.recv(65536)
        if not req:
            c.close()
            return
        r = socket.create_connection(("p.webshare.io", 80), timeout=15)
        i = req.find(b"\r\n")
        r.sendall(req[:i + 2] + f"Proxy-Authorization: Basic {AUTH}\r\n".encode() + req[i + 2:])
        threading.Thread(target=_pipe, args=(c, r), daemon=True).start()
        threading.Thread(target=_pipe, args=(r, c), daemon=True).start()
    except OSError:
        c.close()


srv = socket.socket()
srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
srv.bind(("127.0.0.1", porta))
srv.listen(50)
print(f"ponte {usuario} em 127.0.0.1:{porta}", flush=True)
while True:
    threading.Thread(target=_atender, args=(srv.accept()[0],), daemon=True).start()
