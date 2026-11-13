"""Mini proxy forwarder: escuta em portas locais sem auth e encaminha pro Webshare com auth."""
import socket, threading, base64, sys

# 6 novos (vivos) + 19 antigos (em descanso; voltam no reset de banda ~dia 1-2).
# Os 19 só estouraram a cota do mês (402), não morreram. NÃO apagar.
PROXIES = [
    ("lkuysmxy-rotate", "vizwqulapsqu"),
    ("bnqtrnqo-rotate", "sk8rkkv132ju"),
    ("ihozoiok-rotate", "ex024mppry8q"),
    ("xrrymngm-rotate", "glt6y6pcttjb"),
    ("krptizvy-rotate", "49cxrrreyai5"),
    ("yzohhgdp-rotate", "lm0bpp78gd0z"),
    ("rtvgarrj-rotate", "lm01alulir0q"),
    ("dnqirzkr-rotate", "chzafg7c61vh"),
    ("gniprpsk-rotate", "nfe3v5p8ljh7"),
    ("orlhwzjj-rotate", "9npj7i4fr2qn"),
    ("zukrbczt-rotate", "lthv78w8ar6o"),
    ("xmclwhdf-rotate", "slgbxf0pirf2"),
    ("ujwgoped-rotate", "51tl7ogtsedj"),
    ("nduqzpyq-rotate", "3n43tqu33zop"),
    ("umsobndd-rotate", "9s801aw7inuh"),
    ("yegnulof-rotate", "vrr51m5335le"),
    ("ujqhbjhm-rotate", "bbzznuytyq7f"),
    ("xqthonfl-rotate", "atviwiojz5lo"),
    ("uiwltwjb-rotate", "ndj2ml3tp60x"),
    ("lulnoqml-rotate", "wkecio9ce6vt"),
    ("rdiwjxyb-rotate", "95xr5tvqhjwa"),
    ("cnvpknrz-rotate", "esdfw6zokuuc"),
    ("kvevteie-rotate", "lubw6c2yhkcu"),
    ("rvdvcyks-rotate", "hbq4fxkq9tzf"),
    ("vbpfwwjl-rotate", "shgzyp5jgyr4"),
]

UPSTREAM = "p.webshare.io"
UPSTREAM_PORT = 80
BASE_LOCAL_PORT = 18100

def forward(src, dst):
    try:
        while True:
            data = src.recv(65536)
            if not data:
                break
            dst.sendall(data)
    except:
        pass
    finally:
        src.close()
        dst.close()

def handle_client(client_sock, user, passwd):
    try:
        request = b""
        while b"\r\n\r\n" not in request:
            chunk = client_sock.recv(4096)
            if not chunk:
                client_sock.close()
                return
            request += chunk

        upstream = socket.create_connection((UPSTREAM, UPSTREAM_PORT), timeout=10)
        creds = base64.b64encode(f"{user}:{passwd}".encode()).decode()
        header_end = request.find(b"\r\n\r\n")
        headers = request[:header_end].decode()
        lines = headers.split("\r\n")
        lines.insert(1, f"Proxy-Authorization: Basic {creds}")
        modified = "\r\n".join(lines).encode() + b"\r\n\r\n" + request[header_end+4:]
        upstream.sendall(modified)

        t1 = threading.Thread(target=forward, args=(client_sock, upstream), daemon=True)
        t2 = threading.Thread(target=forward, args=(upstream, client_sock), daemon=True)
        t1.start()
        t2.start()
        t1.join()
        t2.join()
    except:
        client_sock.close()

def run_proxy(local_port, user, passwd):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", local_port))
    server.listen(5)
    while True:
        client, _ = server.accept()
        threading.Thread(target=handle_client, args=(client, user, passwd), daemon=True).start()

if __name__ == "__main__":
    print(f"Iniciando {len(PROXIES)} proxy forwarders (portas {BASE_LOCAL_PORT}-{BASE_LOCAL_PORT+len(PROXIES)-1})...")
    for i, (user, passwd) in enumerate(PROXIES):
        port = BASE_LOCAL_PORT + i
        t = threading.Thread(target=run_proxy, args=(port, user, passwd), daemon=True)
        t.start()
        print(f"  Porta {port} -> {user}@{UPSTREAM}:{UPSTREAM_PORT}")
    print("Todos ativos. Ctrl+C pra parar.")
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        pass
