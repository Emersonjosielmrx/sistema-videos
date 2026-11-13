"""
browser.py — Lançamento do Chrome headless com fingerprint + proxy in-process.

Features:
    - Proxy embutido (não depende de processo separado)
    - Health check dinâmico: testa quais proxies estão vivos antes de cada lote
    - Rotação de proxy: se uma conta falha 2x, troca pra outro
    - Chrome CDP com retry de porta (até 24s)
"""
import subprocess
import random
import socket
import time
import threading
import base64
import sys

from .config import BASE_DIR
sys.path.append(str(BASE_DIR / "shared"))
from google_session import PORT_MAP, get_profile_dir

from .config import CHROME_PATH
from .logger import log


# ============================================================
# PROXY IN-PROCESS
# ============================================================

# NOTA: os 19 "antigos" NÃO morreram — só estouraram a cota de banda do mês
# (Webshare responde 402). A cota reseta ~dia 1-2 do mês e eles voltam sozinhos.
# Ficam aqui "de molho" de propósito: o health_check_proxies() testa cada um e
# usa só os que respondem 200 (pula os 402). NÃO apagar os antigos.
PROXIES = [
    # --- 10 NOVOS (adicionados 2026-07-13, cortesia de Haylla) ---
    ("wwkgwons-rotate", "0hkpc1me94dy"),
    ("xkcqqygv-rotate", "lguvilxmo74v"),
    ("nsxkwvho-rotate", "r9n8vxyvfscr"),
    ("fqghtzop-rotate", "sqsb0npns8x0"),
    ("jbdnkkdj-rotate", "ou64qj0e9c2s"),
    ("pxfuwvtt-rotate", "gycya66lok8h"),
    ("ihbrskce-rotate", "516f3c0oydvx"),
    ("dbjihjwv-rotate", "atz38c3f12zp"),
    ("vexijkef-rotate", "uv14qoxappg7"),
    ("howlovqv-rotate", "lr5e1xslx6cb"),
    # --- 6 VIVOS (adicionados 2026-07-12, ainda com cota) ---
    ("lkuysmxy-rotate", "vizwqulapsqu"),
    ("bnqtrnqo-rotate", "sk8rkkv132ju"),
    ("ihozoiok-rotate", "ex024mppry8q"),
    ("xrrymngm-rotate", "glt6y6pcttjb"),
    ("krptizvy-rotate", "49cxrrreyai5"),
    ("yzohhgdp-rotate", "lm0bpp78gd0z"),
    # --- 19 ANTIGOS (em descanso; voltam no reset de banda dia 1-2) ---
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

_proxy_started = False
_proxy_lock = threading.Lock()
_healthy_proxies = []
_last_health_check = 0
HEALTH_CHECK_INTERVAL = 300  # re-testa a cada 5min
_runtime_blacklist = {}  # idx -> timestamp quando foi blacklistado
RUNTIME_BLACKLIST_DURATION = 120  # 2 min de blacklist por falha em runtime

# ------------------------------------------------------------
# DIAGNÓSTICO DE PROXY (pra o monitor/humano entender POR QUE parou)
# ------------------------------------------------------------
# _proxy_status guarda o motivo da última checagem. Valores possíveis:
#   "ok"              -> pelo menos 1 proxy vivo
#   "quota_esgotada"  -> Webshare respondeu 402 (cota de banda acabou;
#                        NÃO adianta reiniciar, precisa upgrade/reset da conta Webshare)
#   "todos_mortos"    -> proxies não respondem por outro motivo (rede, timeout)
_proxy_status = "ok"


# ============================================================
# FINGERPRINT
# ============================================================

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
]

VIEWPORTS = [
    {"width": 1920, "height": 1080},
    {"width": 1366, "height": 768},
    {"width": 1536, "height": 864},
    {"width": 1440, "height": 900},
    {"width": 1280, "height": 720},
    {"width": 1600, "height": 900},
]


# ============================================================
# PROXY FORWARDING
# ============================================================

def _forward(src, dst):
    try:
        while True:
            data = src.recv(65536)
            if not data:
                break
            dst.sendall(data)
    except:
        pass
    finally:
        try: src.close()
        except: pass
        try: dst.close()
        except: pass


def _handle_client(client_sock, user, passwd):
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

        t1 = threading.Thread(target=_forward, args=(client_sock, upstream), daemon=True)
        t2 = threading.Thread(target=_forward, args=(upstream, client_sock), daemon=True)
        t1.start()
        t2.start()
        t1.join()
        t2.join()
    except:
        try: client_sock.close()
        except: pass


def _run_proxy(local_port, user, passwd):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server.bind(("127.0.0.1", local_port))
        server.listen(5)
    except OSError:
        return
    while True:
        try:
            client, _ = server.accept()
            threading.Thread(target=_handle_client, args=(client, user, passwd), daemon=True).start()
        except:
            pass


def _test_proxy(idx, timeout=5):
    """
    Testa se o proxy idx funciona (faz um CONNECT de teste no upstream).

    Retorna uma tupla (vivo, motivo):
        (True,  "ok")             -> proxy respondeu 200, está funcionando
        (False, "quota_esgotada") -> Webshare respondeu 402 (cota de banda acabou)
        (False, "erro")           -> timeout, conexão recusada, ou outra resposta

    O motivo "quota_esgotada" é o que diferencia "acabou o plano do Webshare"
    (precisa pagar/resetar) de "proxy caiu por rede" (só esperar).
    """
    user, passwd = PROXIES[idx]
    sock = None
    try:
        sock = socket.create_connection((UPSTREAM, UPSTREAM_PORT), timeout=timeout)
        sock.settimeout(timeout)
        creds = base64.b64encode(f"{user}:{passwd}".encode()).decode()
        req = (
            f"CONNECT www.youtube.com:443 HTTP/1.1\r\n"
            f"Host: www.youtube.com:443\r\n"
            f"Proxy-Authorization: Basic {creds}\r\n"
            f"\r\n"
        )
        sock.sendall(req.encode())
        resp = sock.recv(1024).decode(errors="ignore")
        if "200" in resp:
            return True, "ok"
        if "402" in resp or "bandwidthlimit" in resp.lower():
            return False, "quota_esgotada"
        return False, "erro"
    except Exception:
        return False, "erro"
    finally:
        if sock:
            try: sock.close()
            except: pass


def _run_health_check_inner():
    """
    Roda o health check real (pode ser interrompido por timeout).

    Além de montar a lista de proxies vivos, define _proxy_status pra que o
    monitor/humano saiba POR QUE não há proxy: cota esgotada (402) x rede caiu.
    """
    global _healthy_proxies, _last_health_check, _proxy_status
    healthy = []
    quota_hits = 0
    for idx in range(len(PROXIES)):
        vivo, motivo = _test_proxy(idx)
        if vivo:
            healthy.append(idx)
        elif motivo == "quota_esgotada":
            quota_hits += 1

    _last_health_check = time.time()

    if healthy:
        _healthy_proxies = healthy
        _proxy_status = "ok"
        log(f"PROXY HEALTH: {len(healthy)}/{len(PROXIES)} vivos — {healthy}")
    elif quota_hits > 0:
        # A MAIORIA dos proxies respondeu 402 = cota de banda do Webshare acabou.
        # Reiniciar o bot NÃO resolve. Precisa upgrade/reset da conta Webshare.
        _proxy_status = "quota_esgotada"
        log(f"PROXY HEALTH: COTA WEBSHARE ESGOTADA (402 em {quota_hits} proxies)! "
            f"Precisa upgrade/reset da conta Webshare — reiniciar NAO resolve.")
    else:
        _proxy_status = "todos_mortos"
        log("PROXY HEALTH: TODOS mortos (rede/timeout)! Mantendo lista anterior.")


def health_check_proxies():
    """Testa todos os proxies com timeout total de 45s para não travar o bot."""
    global _last_health_check
    now = time.time()
    if now - _last_health_check < HEALTH_CHECK_INTERVAL:
        return

    _last_health_check = now
    t = threading.Thread(target=_run_health_check_inner, daemon=True)
    t.start()
    t.join(timeout=45)
    if t.is_alive():
        log("PROXY HEALTH: timeout 45s — mantendo lista anterior")


def ensure_proxy():
    """Inicia o proxy local in-process e faz health check."""
    global _proxy_started
    with _proxy_lock:
        if not _proxy_started:
            for idx in range(len(PROXIES)):
                user, passwd = PROXIES[idx]
                port = BASE_LOCAL_PORT + idx
                threading.Thread(target=_run_proxy, args=(port, user, passwd), daemon=True).start()
            _proxy_started = True
            time.sleep(1)
            start_continuous_health_check()
    health_check_proxies()


def get_proxy_port(account, attempt=0):
    """Retorna porta de proxy pra uma conta. Rotaciona em caso de retry. Evita blacklistados."""
    now = time.time()
    available = [
        idx for idx in _healthy_proxies
        if idx not in _runtime_blacklist or now - _runtime_blacklist[idx] > RUNTIME_BLACKLIST_DURATION
    ]
    if not available:
        available = _healthy_proxies if _healthy_proxies else [0]
    acc_list = list(PORT_MAP.keys())
    acc_idx = acc_list.index(account) if account in acc_list else 0
    proxy_idx = available[(acc_idx + attempt) % len(available)]
    return BASE_LOCAL_PORT + proxy_idx


def blacklist_proxy_runtime(port):
    """Marca um proxy como temporariamente ruim (falhou em runtime)."""
    idx = port - BASE_LOCAL_PORT
    _runtime_blacklist[idx] = time.time()
    log(f"PROXY BLACKLIST: idx={idx} (port={port}) por {RUNTIME_BLACKLIST_DURATION}s")


def start_continuous_health_check():
    """Inicia thread de health check contínuo em background."""
    def _loop():
        while True:
            time.sleep(HEALTH_CHECK_INTERVAL)
            try:
                _run_health_check_inner()
                now = time.time()
                expired = [k for k, v in _runtime_blacklist.items() if now - v > RUNTIME_BLACKLIST_DURATION]
                for k in expired:
                    del _runtime_blacklist[k]
            except Exception:
                pass
    t = threading.Thread(target=_loop, daemon=True)
    t.start()


# ============================================================
# CHROME LAUNCH
# ============================================================

def launch_chrome(account, cfg, attempt=0):
    """
    Abre o Chrome headless com o perfil da conta.
    attempt > 0 rotaciona pra um proxy diferente.
    Retorna (proc, port) ou (None, None) se não conseguir.
    """
    ensure_proxy()

    if not _healthy_proxies and attempt == 0:
        return None, None

    port = PORT_MAP.get(account)
    if not port:
        return None, None

    profile_dir = get_profile_dir(account)
    local_proxy_port = get_proxy_port(account, attempt)

    use_fingerprint = cfg.get("fingerprint", True)
    ua = random.choice(USER_AGENTS) if use_fingerprint else USER_AGENTS[0]
    vp = random.choice(VIEWPORTS) if use_fingerprint else VIEWPORTS[0]

    chrome_args = [
        CHROME_PATH,
        f"--user-data-dir={profile_dir}",
        f"--remote-debugging-port={port}",
        "--headless=new",
        "--no-first-run",
        "--disable-gpu",
        "--mute-audio",
        f"--proxy-server=http://127.0.0.1:{local_proxy_port}",
        "--disable-software-rasterizer",
        "--disable-dev-shm-usage",
        "--disable-extensions",
        "--disable-background-networking",
        "--disable-default-apps",
        "--disable-sync",
        "--disable-translate",
        "--no-sandbox",
        f"--window-size={vp['width']},{vp['height']}",
        f"--user-agent={ua}",
        "about:blank",
    ]

    proc = subprocess.Popen(
        chrome_args,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    for _ in range(12):
        time.sleep(2)
        try:
            s = socket.create_connection(("127.0.0.1", port), timeout=2)
            s.close()
            return proc, port
        except (ConnectionRefusedError, OSError):
            continue

    kill_chrome(proc)
    return None, None


def kill_chrome(proc):
    """Mata o processo do Chrome e filhos de forma agressiva."""
    if proc is None:
        return
    pid = proc.pid
    try:
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(pid)],
            capture_output=True, timeout=5,
        )
    except Exception:
        pass
    try:
        proc.wait(timeout=3)
    except Exception:
        try: proc.kill()
        except: pass
