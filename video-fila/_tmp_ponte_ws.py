"""Ponte local sem senha para o IP fixo N do Webshare GRÁTIS (usuário '<conta>-N' = mesmo IP N em qualquer conta
grátis). Escolhe uma conta grátis que responde agora. 10/11: conferir banimento das contas Kaggle ws-N, cada uma pela
saída fixa dela.   python _tmp_ponte_ws.py <N> <porta>"""
import base64, socket, sys, threading, urllib.request
from pathlib import Path
PROXIES = Path(r"D:\postador-de-videos\secrets\proxies.txt")
UP = ("p.webshare.io", 80)
n, porta = int(sys.argv[1]), int(sys.argv[2])
cred = None
for l in PROXIES.read_text(encoding="utf-8").splitlines():
    l = l.strip()
    if "-rotate:" not in l or "rnprmtfo" in l:
        continue
    u, resto = l.split("//", 1)[-1].split("-rotate:", 1)
    senha = resto.split("@", 1)[0]
    url = f"http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80"
    try:
        op = urllib.request.build_opener(urllib.request.ProxyHandler({"http": url}))
        op.open("http://example.com", timeout=12).read(10)
        cred = base64.b64encode(f"{u}-{n}:{senha}".encode()).decode()
        break
    except Exception:
        continue
if not cred:
    raise SystemExit("nenhuma conta grátis respondeu pro IP %d" % n)


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
                s.close()
            except OSError:
                pass


def cliente(c):
    try:
        cab = b""
        while b"\r\n\r\n" not in cab:
            d = c.recv(65536)
            if not d:
                c.close(); return
            cab += d
        topo, resto = cab.split(b"\r\n\r\n", 1)
        linhas = topo.split(b"\r\n")
        linhas = [x for x in linhas if not x.lower().startswith(b"proxy-authorization")]
        linhas.insert(1, b"Proxy-Authorization: Basic " + cred.encode())
        up = socket.create_connection(UP, timeout=30)
        up.sendall(b"\r\n".join(linhas) + b"\r\n\r\n" + resto)
        threading.Thread(target=pipe, args=(up, c), daemon=True).start()
        pipe(c, up)
    except OSError:
        try:
            c.close()
        except OSError:
            pass


s = socket.socket(); s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(("127.0.0.1", porta)); s.listen(50)
while True:
    c, _ = s.accept()
    threading.Thread(target=cliente, args=(c,), daemon=True).start()
