r"""ponte_proxy_fixo.py — repassador local SEM senha para UM proxy fixo da Webshare (06/11/2026).

Dona 06/11: "crie os tokens dessas contas já usando proxies". Regra do banimento 02/11: cada conta Kaggle fala com o
Kaggle (e com o Google, no login) só pelo IP fixo dela. O Chrome não aceita proxy com senha: este processo escuta em
127.0.0.1:<porta> e repassa TUDO (sem PAC, sem cair para direto) para http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80.

    python ponte_proxy_fixo.py <N> <porta>      # ex.: 2 18302

27/11 CADEADO (D:\sistema\comum\cadeado_pagos.py): IP pago so para o Kaggle (ou N liberado pelo dono). Recusado =
a ponte sobe pelo FAILBACK gratis (proxies_gratis.saida: GitHub -> Webshare gratis), nunca pela casa.
PONTE_QUEM=<texto> diz quem pediu (senao le a linha de comando do processo pai). CADEADO_PAGOS=0 desliga.
"""
import base64
import socket
import sys
import threading
from pathlib import Path

PROXIES = Path(r"D:\postador-de-videos\secrets\proxies.txt")
# 27/11 cadeado: a linha paga (rnprmtfo) saiu do proxies.txt (rodizio) e mora so aqui; proxies.txt fica de reserva
PAGO = Path(r"D:\postador-de-videos\secrets\proxy_pago_kaggle.txt")
UP = ("p.webshare.io", 80)
# 11/11 (dona: login do Google da verse8 dava "Request canceled" / ERR_TIMED_OUT): o proxy direto responde em 0,4–0,8 s,
# mas pela ponte o Google levava 12–17 s ou caía — o Chrome abre ~38 conexões ao mesmo tempo e a Webshare engasga com
# tantos túneis CONNECT simultâneos do mesmo usuário. Limita os túneis ABRINDO ao mesmo tempo (os já abertos não contam
# como espera) e liga TCP_NODELAY (TLS em pacotes pequenos). PONTE_MAX_ABRINDO muda.
import os  # noqa: E402
ABRINDO = threading.BoundedSemaphore(int(os.environ.get("PONTE_MAX_ABRINDO", "12")))


def credencial(n):
    for l in [*(PAGO.read_text(encoding="utf-8").splitlines() if PAGO.exists() else []),
              *PROXIES.read_text(encoding="utf-8").splitlines()]:
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
        # 25/11: cabeçalho do cliente sem prazo + vaga presa = com o Chrome do FB abrindo dezenas de conexões, as 12 vagas
        # ficavam presas e a ponte parava de atender (2-3x/dia em 23-24/11). Prazo para o cabeçalho; PONTE_ESPERA_CAB_S muda.
        cli.settimeout(float(os.environ.get("PONTE_ESPERA_CAB_S", "20")))
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
        if auth:  # 27/11: proxy publico do failback nao tem senha
            linhas.insert(1, b"Proxy-Authorization: Basic " + auth.encode())
        with ABRINDO:  # só a abertura do túnel (CONNECT até a 1ª resposta) entra na fila
            up = socket.create_connection(UP, timeout=15)
            up.settimeout(float(os.environ.get("PONTE_ESPERA_200_S", "8")))  # 25/11: nada dentro da vaga sem prazo
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


def _cadeado(n):
    """27/11 (dono): IP pago so para o Kaggle; o resto sai pelo FAILBACK gratis (GitHub -> Webshare gratis).
    Devolve (auth, upstream, rotulo). Ponte ja aberta antes de 27/11 nao passa por aqui (continua ate fechar)."""
    sys.path.insert(0, r"D:\sistema\comum")
    try:
        import cadeado_pagos
    except Exception:  # noqa: BLE001  sem o cadeado = comportamento antigo
        return credencial(n), UP, f"rnprmtfo-{n}"
    pai = os.environ.get("PONTE_QUEM") or _quem_chamou()
    if cadeado_pagos.liberar(n, pai, levantar=False):
        return credencial(n), UP, f"rnprmtfo-{n}"
    import proxies_gratis
    url, origem = proxies_gratis.saida(f"ponte {n} (cadeado: {pai})", chave=f"ponte-{n}")
    if not url:
        raise SystemExit(f"[CADEADO IP PAGO] rnprmtfo-{n} recusado e sem proxy gratis agora - nao abro pela casa")
    resto = url.split("//", 1)[1]
    cred, hp = (resto.rsplit("@", 1) + [None])[:2] if "@" in resto else (None, resto)
    host, porta_up = hp.rsplit(":", 1)
    auth = base64.b64encode(cred.encode()).decode() if cred else None
    print(f"[PROXY GRATIS - EM TESTE] ponte {n}: IP pago recusado pelo cadeado -> {origem} {host}:{porta_up}", flush=True)
    return auth, (host, int(porta_up)), f"{origem} {host}"


def _quem_chamou():
    """Linha de comando do processo PAI (quem pediu a ponte) - o cadeado decide por ela."""
    try:
        import subprocess as _sp
        r = _sp.run(["powershell", "-NoProfile", "-Command",
                     f"(Get-CimInstance Win32_Process -Filter \"ProcessId={os.getppid()}\").CommandLine"],
                    capture_output=True, text=True, timeout=15, creationflags=0x08000000)
        return (r.stdout or "").strip() or "?"
    except Exception:  # noqa: BLE001
        return "?"


def main():
    global UP
    n, porta = int(sys.argv[1]), int(sys.argv[2])
    auth, UP, rotulo = _cadeado(n)
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("127.0.0.1", porta))
    s.listen(64)
    print(f"ponte {rotulo} em 127.0.0.1:{porta}", flush=True)
    while True:
        c, _ = s.accept()
        threading.Thread(target=atender, args=(c, auth), daemon=True).start()


if __name__ == "__main__":
    main()
