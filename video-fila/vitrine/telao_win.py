"""telao_win.py — o PC2 (Windows) como TELÃO do painel, igual aos notebooks (dona 23/10/2026: "você pode usar o PC2 como
usa os outros 2 notebooks como tela"). Só o painel: vídeo continua só no Acer (o X200MA de reserva).

Roda na sessão da tela (tarefa PC2_Telao, ao entrar no Windows; instalada pelo vitrine.py --instalar-pc2 no PC1).
Serve C:\\vitrine em 127.0.0.1:8791 (o PC1 manda o painel.json a cada rodada) e mantém um Chrome em tela cheia com
perfil próprio, prioridade baixa (o PC2 renderiza o anime) e poucas abas de processo. Fechou: reabre em até 1 min.
Pra tirar da tela sem desinstalar: criar C:\\vitrine\\desligado.txt (fecha e não reabre); apagar o arquivo = volta.
Login na máquina (C:\\vitrine\\login.txt, posto pelo PC1): fecha na hora e volta quando o arquivo sai.
Só biblioteca padrão.
"""
import ctypes
import http.server
import json
import os
import socketserver
import subprocess
import threading
import time
from pathlib import Path

PASTA = Path(r"C:\vitrine")
# 27/10 (dona): o MESMO telão roda no PC2 e no desktop. maquina.txt diz quem é (posto pelo vitrine.py --instalar-*).
MAQUINA = ((PASTA / "maquina.txt").read_text("utf-8").strip() if (PASTA / "maquina.txt").exists() else "pc2")
SAUDE_CSV = PASTA / "saude.csv"  # 1 linha por minuto, 24 h por dia (mesmo com o telão fora da tela)
_saude = {"cpu": None, "ram": None}
PORTA = 8791
PERFIL = PASTA / "perfil_chrome"
DESLIGADO = PASTA / "desligado.txt"
LOGIN = PASTA / "login.txt"
LOG = PASTA / "telao.log"
CHROMES = [Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
           Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe")]
URL = f"http://127.0.0.1:{PORTA}/moldura_{MAQUINA}.html"  # pc2: 20% da esquerda preto (falha no monitor, 23/10)
ABAIXO_DO_NORMAL = 0x00004000


def log(m):
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%d/%m %H:%M:%S')}] {m}\n")
        if LOG.stat().st_size > 1_000_000:
            LOG.write_text(LOG.read_text(encoding="utf-8")[-200_000:], encoding="utf-8")
    except OSError:
        pass


PC1_IP = "100.118.234.102"  # Tailscale (vigia_mutuo.VIGIADAS)


def pc1_conectado():
    """28/10 (dona: o telão dizia PC2/notebook 'desconectado' com tudo trabalhando — era só o painel.json atrasado):
    True se esta máquina alcança o PC1 pela Tailscale (painel 8790 ou ping)."""
    import socket
    # 30/10 (dona: "sem conexão aparece toda hora; só deve aparecer se a perda for real"): o PC1 não tem ssh (22
    # fechada) e, sobrecarregado, a 8790 passava dos 3 s — o PC1 estava lá. 8790 com 8 s; senão ping (Tailscale).
    try:
        with socket.create_connection((PC1_IP, 8790), timeout=8):
            return True
    except OSError:
        pass
    try:  # bytes: o ping em português (cp850) quebrava a leitura como texto
        r = subprocess.run(["ping", "-n", "2", "-w", "3000", PC1_IP], capture_output=True, timeout=15,
                           creationflags=0x08000000)
        return b"TTL=" in r.stdout
    except Exception:  # noqa: BLE001
        return False


class Pagina(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=str(PASTA), **k)

    def do_GET(self):
        if self.path.startswith("/pc1"):  # 28/10 (dona): "sem sinal" só se NÃO houver conexão de verdade com o PC1
            corpo = json.dumps({"conectado": pc1_conectado()}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(corpo)))
            self.end_headers()
            self.wfile.write(corpo)
            return
        if self.path.startswith("/saude.json"):  # medidor CPU/RAM da própria máquina (canto do telão)
            corpo = json.dumps(_saude).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(corpo)))
            self.end_headers()
            self.wfile.write(corpo)
            return
        if self.path.startswith("/pedido"):  # botões "Abrir/Ver" do painel: vídeo é só no Acer
            corpo = "Vídeo só no telão do Acer".encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(corpo)))
            self.end_headers()
            self.wfile.write(corpo)
            return
        if self.path.startswith(("/perfil_chrome", "/telao")):
            self.send_error(404)
            return
        super().do_GET()

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, *a):
        pass


class _FT(ctypes.Structure):
    _fields_ = [("lo", ctypes.c_uint32), ("hi", ctypes.c_uint32)]


class _MEM(ctypes.Structure):
    _fields_ = [("len", ctypes.c_uint32), ("carga", ctypes.c_uint32), ("total", ctypes.c_uint64),
                ("livre", ctypes.c_uint64), ("pf_t", ctypes.c_uint64), ("pf_l", ctypes.c_uint64),
                ("v_t", ctypes.c_uint64), ("v_l", ctypes.c_uint64), ("ext", ctypes.c_uint64)]


def _tempos():
    i, k, u = _FT(), _FT(), _FT()
    ctypes.windll.kernel32.GetSystemTimes(ctypes.byref(i), ctypes.byref(k), ctypes.byref(u))
    v = [(x.hi << 32) | x.lo for x in (i, k, u)]
    return v[0], v[1] + v[2]  # ocioso, total (o kernel já inclui o ocioso)


def _ram():
    m = _MEM()
    m.len = ctypes.sizeof(_MEM)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    return m.carga, round(m.livre / 2 ** 30, 1)


def _contar():
    """Quantos ffmpeg / python / chrome rodando (o trabalho de verdade: render = ffmpeg)."""
    r = subprocess.run(["tasklist", "/FO", "CSV", "/NH"], capture_output=True, text=True, timeout=60,
                       creationflags=0x08000000)
    nomes = [ln.split('","')[0].strip('"').lower() for ln in r.stdout.splitlines() if ln]
    return {n: sum(1 for x in nomes if x == f"{n}.exe") for n in ("ffmpeg", "python", "pythonw", "chrome", "obs64")}


def _camera_em_uso():
    """Desktop (dona 27/10): telão só quando ele trabalha = câmera/microfone livres e sem OBS. Mesma regra do
    maquinas.py: ConsentStore com LastUsedTimeStop = 0 enquanto o app usa."""
    import winreg
    base = r"Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore"

    def varrer(ch):
        try:
            k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, ch)
        except OSError:
            return False
        try:
            try:
                if winreg.QueryValueEx(k, "LastUsedTimeStop")[0] == 0 and winreg.QueryValueEx(k, "LastUsedTimeStart")[0]:
                    return True
            except OSError:
                pass
            i = 0
            while True:
                try:
                    sub = winreg.EnumKey(k, i)
                except OSError:
                    return False
                if varrer(ch + "\\" + sub):
                    return True
                i += 1
        finally:
            winreg.CloseKey(k)
    return any(varrer(f"{base}\\{c}") for c in ("webcam", "microphone"))


def saude():
    """CPU/RAM ao vivo (a cada 5 s, pro medidor na tela) + 1 linha por minuto em saude.csv (análise de 24 h no PC1)."""
    oc0, to0 = _tempos()
    ultimo = 0.0
    while True:
        time.sleep(5)
        try:
            oc1, to1 = _tempos()
            cpu = round(100 * (1 - (oc1 - oc0) / max(to1 - to0, 1)))
            oc0, to0 = oc1, to1
            ram, livre = _ram()
            _saude.update(cpu=cpu, ram=ram, livre=livre, maquina=MAQUINA, em=time.strftime("%H:%M:%S"))
            if time.time() - ultimo >= 60:
                ultimo = time.time()
                n = _contar()
                cam = int(MAQUINA == "desktop" and (_camera_em_uso() or n["obs64"] > 0))
                _saude.update(ffmpeg=n["ffmpeg"], camera=cam)
                novo = not SAUDE_CSV.exists()
                with open(SAUDE_CSV, "a", encoding="utf-8") as f:
                    if novo:
                        f.write("quando,cpu,ram_pct,ram_livre_gb,ffmpeg,python,pythonw,chrome,camera,telao\n")
                    f.write(f"{time.strftime('%Y-%m-%d %H:%M')},{cpu},{ram},{livre},{n['ffmpeg']},{n['python']},"
                            f"{n['pythonw']},{n['chrome']},{cam},{int(not _saude.get('parado', False))}\n")
                if SAUDE_CSV.stat().st_size > 5_000_000:  # ~35 dias: guarda o fim
                    SAUDE_CSV.write_text(SAUDE_CSV.read_text("utf-8")[-2_500_000:].split("\n", 1)[1], "utf-8")
        except Exception as e:  # noqa: BLE001 — o medidor nunca derruba o telão
            log(f"saude: {type(e).__name__}: {e}")


def servidor():
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("127.0.0.1", PORTA), Pagina) as s:
        s.serve_forever()


def _chrome_aberto():
    r = subprocess.run(["powershell", "-NoProfile", "-Command",
                        "Get-CimInstance Win32_Process -Filter \"Name='chrome.exe'\" | Where-Object { $_.CommandLine -like "
                        f"'*{PERFIL}*' }} | Select-Object -ExpandProperty ProcessId"],
                       capture_output=True, text=True, timeout=60, creationflags=0x08000000)
    return [int(x) for x in r.stdout.split() if x.strip().isdigit()]


def _abrir():
    exe = next((c for c in CHROMES if c.exists()), None)
    if not exe:
        log("sem Chrome no PC2")
        return
    subprocess.Popen([str(exe), f"--user-data-dir={PERFIL}", "--kiosk", f"--app={URL}", "--no-first-run",
                      "--no-default-browser-check", "--disable-extensions", "--disable-sync", "--mute-audio",
                      "--disable-features=Translate,MediaRouter,OptimizationHints", "--renderer-process-limit=1",
                      "--disable-background-networking", "--lang=pt-BR", "--password-store=basic"],
                     creationflags=ABAIXO_DO_NORMAL | 0x00000008)  # DETACHED_PROCESS
    log("telão aberto")


def _em_login():
    """Dona 26/10: "o painel deve ficar desativado quando for fazer logins". O PC1 (vitrine.py, pela vez da máquina) e o
    login_em_lote criam C:\\vitrine\\login.txt; velho de 40 min não vale (o PC1 caiu no meio e não apagou)."""
    try:
        return time.time() - LOGIN.stat().st_mtime < 40 * 60
    except OSError:
        return False


def main():
    PASTA.mkdir(parents=True, exist_ok=True)
    threading.Thread(target=servidor, daemon=True).start()
    threading.Thread(target=saude, daemon=True).start()
    log(f"telao_win iniciado ({MAQUINA})")
    parado, ultimo = None, 0.0
    while True:
        try:
            parar = DESLIGADO.exists() or _em_login() or bool(_saude.get("camera"))
            _saude["parado"] = parar
            # o PowerShell do PC2 é lento: confere o Chrome só quando muda o estado ou a cada 1 min
            if parar != parado or time.time() - ultimo >= 60:
                if parar != parado:
                    log("telão fora da tela (login/desligado)" if parar else "telão de volta")
                parado, ultimo = parar, time.time()
                pids = _chrome_aberto()
                if parar:
                    for p in pids:
                        subprocess.run(["taskkill", "/PID", str(p), "/T", "/F"], capture_output=True,
                                       creationflags=0x08000000)
                elif not pids and (PASTA / "painel.html").exists():
                    _abrir()
        except Exception as e:  # noqa: BLE001 — o laço nunca morre
            log(f"erro: {type(e).__name__}: {e}")
        time.sleep(5)


if __name__ == "__main__":
    if os.name == "nt":
        main()
