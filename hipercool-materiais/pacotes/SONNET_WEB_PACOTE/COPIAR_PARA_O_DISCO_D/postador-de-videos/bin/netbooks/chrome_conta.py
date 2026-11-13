#!/usr/bin/env python3
"""chrome_conta.py — roda NO X200MA (~/postador-worker/). Abre e fecha o Chrome de UMA conta por vez, perfil próprio
por conta (~/postador-worker/perfis/<perfil>), com a porta de controle (CDP) só em 127.0.0.1. Quem comanda é o PC1
(D:\\postador-de-videos\\bin\\maquina_remota.py) por um túnel ssh: aqui não há regra de postagem, só o navegador.
Dono 22/10/2026: "usa o X200MA pra postagens, com pouca CPU, usando mais o navegador". Só biblioteca padrão.

    python3 chrome_conta.py abrir  <perfil> <porta> [url]   # imprime PRONTO quando a porta responde
    python3 chrome_conta.py logar  <perfil> <porta> [url]   # igual, mas é pra dona entrar na conta na tela
    python3 chrome_conta.py fechar <porta>                  # fecha (SIGTERM = Chrome grava os cookies) e limpa a entrada
    python3 chrome_conta.py estado
    python3 chrome_conta.py liberar                         # fecha o que não precisa e limpa a RAM (Linux e Windows)
    python3 chrome_conta.py janelas | login_janela <perfil> <x> <y> <url> | fechar_janela <perfil>   # login em lote (Linux)
"""
import json
import os
import shutil
import signal
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

WIN = os.name == "nt"  # 23/10: também roda no DESKTOP (Windows), com a regra de não usar com OBS/câmera/microfone
BASE = Path("C:/postador-worker") if WIN else Path.home() / "postador-worker"
PERFIS = BASE / "perfis"
ENTRADA = BASE / "entrada"
OCUPADO = BASE / "ocupado"
LOG = BASE / "chrome.log"
RAM_MINIMA_MB = 550          # abaixo disso não abre (o notebook tem 1,8 GB)
CACHE_MAX_MB = 250           # perfil passou disso: limpa só o cache (o login fica)
# leve: sem extensões, sem tradução/sync/atualização de componente, poucos processos de página, sem som.
# --password-store=basic: sem chaveiro do GNOME (aberto pelo ssh ele pediria senha na tela e travaria o Chrome).
LEVE = ["--no-first-run", "--no-default-browser-check", "--password-store=basic", "--disable-extensions",
        "--disable-component-update", "--disable-sync", "--disable-features=Translate,MediaRouter,OptimizationHints",
        "--renderer-process-limit=2", "--mute-audio", "--disable-background-timer-throttling",
        "--disable-renderer-backgrounding", "--disable-backgrounding-occluded-windows", "--window-size=1280,900",
        "--remote-allow-origins=*",
        # 23/10: o Studio abria em INGLÊS nos notebooks ("1,433" views) e os textos lidos não batiam com os do PC1
        "--lang=pt-BR", "--accept-lang=pt-BR,pt"]


def log(m):
    BASE.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(time.strftime("%d/%m %H:%M:%S ") + m + "\n")


def _ambiente():
    """Variáveis da sessão gráfica (o ssh não tem): Chrome abre na tela do notebook."""
    env = dict(os.environ)
    if WIN:
        return env
    try:
        r = subprocess.run(["systemctl", "--user", "show-environment"], capture_output=True, text=True, timeout=10)
        for linha in r.stdout.splitlines():
            k, _, v = linha.partition("=")
            if k in ("DISPLAY", "WAYLAND_DISPLAY", "XAUTHORITY", "DBUS_SESSION_BUS_ADDRESS", "XDG_RUNTIME_DIR",
                     "XDG_SESSION_TYPE"):
                env[k] = v
    except (OSError, subprocess.TimeoutExpired):
        pass
    uid = os.getuid()
    env.setdefault("DISPLAY", ":0")
    env.setdefault("XDG_RUNTIME_DIR", f"/run/user/{uid}")
    env.setdefault("DBUS_SESSION_BUS_ADDRESS", f"unix:path=/run/user/{uid}/bus")
    return env


def _cdp_vivo(porta):
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{porta}/json/version", timeout=3)
        return True
    except Exception:  # noqa: BLE001
        return False


def _ram_livre_mb():
    if WIN:
        import ctypes

        class M(ctypes.Structure):
            _fields_ = [("l", ctypes.c_ulong), ("c", ctypes.c_ulong), ("t", ctypes.c_ulonglong),
                        ("a", ctypes.c_ulonglong), ("x", ctypes.c_ulonglong * 5)]
        m = M()
        m.l = ctypes.sizeof(M)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
        return int(m.a // (1024 * 1024))
    try:
        for linha in open("/proc/meminfo", encoding="utf-8"):
            if linha.startswith("MemAvailable:"):
                return int(linha.split()[1]) // 1024
    except OSError:
        pass
    return 9999


def _ps(cmd, timeout=60):
    r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", cmd],
                       capture_output=True, text=True, timeout=timeout, creationflags=0x08000000)
    return (r.stdout or "").strip()


def _imagem_win(pid):
    """Caminho do executável do processo, ou "" se não existe. ctypes: o PowerShell do PC2 leva ~1 min pra abrir e 10
    deles juntos (TikTok em lote, 26/10) deixavam a CPU em 100%."""
    import ctypes
    k = ctypes.WinDLL("kernel32")
    try:
        h = k.OpenProcess(0x1000, False, int(pid))  # PROCESS_QUERY_LIMITED_INFORMATION
    except (ValueError, TypeError):
        return ""
    if not h:
        return ""
    try:
        cod = ctypes.c_ulong()
        if not k.GetExitCodeProcess(h, ctypes.byref(cod)) or cod.value != 259:  # STILL_ACTIVE
            return ""
        buf, n = ctypes.create_unicode_buffer(1024), ctypes.c_ulong(1024)
        return buf.value if k.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(n)) else "?"
    finally:
        k.CloseHandle(h)


def _pid_da_porta(porta):
    """PID que escuta na porta de controle (o Chrome principal), pelo netstat — sem WMI/PowerShell."""
    r = subprocess.run(["netstat", "-ano", "-p", "TCP"], capture_output=True, timeout=30, creationflags=0x08000000)
    for linha in (r.stdout or b"").decode("oem", errors="replace").splitlines():
        c = linha.split()
        if len(c) >= 5 and c[1].endswith(f":{int(porta)}") and c[3].upper() in ("LISTENING", "ESCUTANDO"):
            return int(c[4])
    return 0


def _pid_vivo(pid):
    if WIN:
        return bool(_imagem_win(pid))
    try:
        os.kill(int(pid), 0)
        return True
    except (OSError, ValueError):
        return False


def _ocupante():
    """{'pid', 'porta', 'perfil', 'desde'} de quem está com o Chrome aberto, ou None (trava órfã é solta)."""
    try:
        d = json.loads(OCUPADO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    # revisão 23/10: o PID tem que ser MESMO o Chrome do postador (depois de reiniciar, o número pode ser de outro
    # programa — ex.: o player do telão) e postagem não passa de 50 min (o PC1 morto por prazo deixava o Chrome
    # aberto e o notebook "ocupado" por 3 h)
    limite = 3 * 3600 if d.get("login") else 50 * 60
    nosso = _e_nosso(d.get("pid"), d.get("porta"))
    if nosso and time.time() - d.get("desde", 0) < limite:
        return d
    if nosso:
        _matar(d.get("pid"))
    OCUPADO.unlink(missing_ok=True)
    return None


def _e_nosso(pid, porta=None):
    if WIN:  # 26/10: sem PowerShell — Chrome nosso = é o que escuta na porta de controle; janela de login (porta 0) ou
        # o próprio chrome_conta (python, enquanto abre) = pelo nome do executável
        img = _imagem_win(pid).lower()
        if not img:
            return False
        if img.endswith("chrome.exe") and porta and int(porta):
            return _pid_da_porta(porta) == int(pid)
        return img.endswith(("chrome.exe", "python.exe", "pythonw.exe"))
    try:
        cmd = Path(f"/proc/{int(pid)}/cmdline").read_bytes().decode("utf-8", "replace")
    except (OSError, ValueError, TypeError):
        return False
    return "postador-worker" in cmd or "chrome_conta.py" in cmd


def _matar(pid):
    if WIN:  # taskkill sem /F pede pro Chrome fechar (grava os cookies); se não fechar, força
        subprocess.run(["taskkill", "/PID", str(pid), "/T"], capture_output=True, creationflags=0x08000000)
        # 26/10 PC2: pelo ssh o pedido não alcança a janela da tela (outra sessão) e a espera passava do prazo do ssh
        # (60 s) antes do /F — o Chrome ficava aberto. O pedido roda NA sessão da tela, por tarefa, como no _lancar.
        tn = f"PostadorFechar{int(pid)}"  # 26/10: um por Chrome (vários fechando juntos no lote do TikTok)
        if _pid_vivo(pid):
            subprocess.run(["schtasks", "/create", "/tn", tn, "/tr", f"taskkill /PID {int(pid)} /T",
                            "/sc", "once", "/st", "00:00", "/it", "/f"], capture_output=True, timeout=60,
                           creationflags=0x08000000)
            subprocess.run(["schtasks", "/run", "/tn", tn], capture_output=True, timeout=60, creationflags=0x08000000)
        for _ in range(12):
            if not _pid_vivo(pid):
                break
            time.sleep(1)
        else:
            subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, creationflags=0x08000000)
        subprocess.run(["schtasks", "/delete", "/tn", tn, "/f"], capture_output=True, timeout=60, creationflags=0x08000000)
        return
    try:
        os.killpg(int(pid), signal.SIGTERM)
    except (OSError, ValueError, TypeError):
        return
    for _ in range(40):
        if not _pid_vivo(pid):
            return
        time.sleep(0.5)
    try:
        os.killpg(int(pid), signal.SIGKILL)
    except (OSError, ValueError):
        pass


def _tamanho_mb(p):
    t = 0
    for raiz, _, arqs in os.walk(p):
        for a in arqs:
            try:
                t += os.path.getsize(os.path.join(raiz, a))
            except OSError:
                pass
    return t / 1e6


def _limpar_cache(perfil):
    pasta = PERFIS / perfil
    if not pasta.is_dir() or _tamanho_mb(pasta) < CACHE_MAX_MB:
        return
    for sub in ("Default/Cache", "Default/Code Cache", "Default/GPUCache", "Default/Service Worker/CacheStorage",
                "GrShaderCache", "ShaderCache", "component_crx_cache"):
        shutil.rmtree(pasta / sub, ignore_errors=True)
    log(f"cache de {perfil} limpo (login mantido)")


def _chrome():
    """google-chrome do sistema; senão o extraído sem sudo em ~/.local/chrome (maquina_remota.py preparar-chrome)."""
    if WIN:
        c = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
        return [str(c)] if c.exists() else None
    for c in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):
        if shutil.which(c):
            return [c]
    local = Path.home() / ".local" / "chrome" / "opt" / "google" / "chrome" / "chrome"
    if local.exists():
        return [str(local)] + ([] if _userns_ok() else ["--no-sandbox"])
    return None


def _userns_ok():
    try:
        return Path("/proc/sys/kernel/apparmor_restrict_unprivileged_userns").read_text().strip() != "1"
    except OSError:
        return True


APPS_BLOQUEADOS = ("bytedance", "snssdk1233", "snssdk1180", "snssdk1128", "tiktok", "musically", "intent", "youtube", "vnd.youtube",
                   "instagram", "fb", "market", "googlechrome")


SUPERFLUOS = ("mintUpdate", "mintreport-tray", "blueman-applet", "update-notifier", "gnome-software",
             "snap-store", "evolution-alarm-notify", "tracker-miner-fs-3", "deja-dup-monitor", "orca", "zeitgeist")


SUPERFLUOS_WIN = ("OneDrive.exe", "Teams.exe", "ms-teams.exe", "PhoneExperienceHost.exe", "YourPhone.exe",
                  "GameBar.exe", "Widgets.exe", "SkypeApp.exe", "Cortana.exe")


def _enxugar_win():
    """Devolve ao sistema a memória parada de cada processo (EmptyWorkingSet, o mesmo que o Wise Memory Optimizer faz):
    nada fecha, o que precisar volta da memória sozinho."""
    import ctypes
    from ctypes import wintypes
    k = ctypes.WinDLL("kernel32")
    pids, n = (wintypes.DWORD * 4096)(), wintypes.DWORD()
    k.K32EnumProcesses(pids, ctypes.sizeof(pids), ctypes.byref(n))
    for pid in pids[:n.value // 4]:
        h = k.OpenProcess(0x0100 | 0x0400, False, pid)  # SET_QUOTA | QUERY_INFORMATION
        if h:
            k.K32EmptyWorkingSet(h)
            k.CloseHandle(h)


def _liberar_ram():
    """Dona 23/10: antes de cada ação, libera o máximo — fecha (sinal normal) bandeja/atualização do Mint/Ubuntu.
    O navegador pessoal da dona e o sistema não são tocados. No DESKTOP não fecha nada (é onde a dona trabalha).
    26/10 (dona: "o mesmo passo dos notebooks... sempre"): no Windows também — fecha os apps de bandeja que não servem
    pra ação (não no DESKTOP) e enxuga a memória de todos. Nunca toca em python/pythonw (PC2 é do hipercool)."""
    if WIN:
        antes = _ram_livre_mb()
        if not os.environ.get("COMPUTERNAME", "").upper().startswith("DESKTOP"):
            for nome in SUPERFLUOS_WIN:
                subprocess.run(["taskkill", "/IM", nome, "/F"], capture_output=True, creationflags=0x08000000)
        try:
            _enxugar_win()
        except (OSError, AttributeError) as e:
            log(f"enxugar memória falhou: {e}")
        log(f"limpeza antes de abrir: RAM livre {antes} → {_ram_livre_mb()} MB")
        return
    for nome in SUPERFLUOS:
        subprocess.run(["pkill", "-x", nome[:15]], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # 24/10 (dona: "toda janela aberta: fechar o que não precisa + limpeza de RAM, assim não trava"): devolve o cache
    # de disco ao sistema (só se o sudo não pedir senha; sem ele segue só com o fechamento acima)
    antes = _ram_livre_mb()
    subprocess.run("sync; sudo -n sh -c 'echo 1 > /proc/sys/vm/drop_caches'", shell=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
    log(f"limpeza antes de abrir: RAM livre {antes} → {_ram_livre_mb()} MB")


def _sem_abrir_app(perfil):
    """Dona 23/10: o TikTok abria "Abrir xdg-open?" (quer abrir o aplicativo) e travava o login até alguém clicar
    Cancelar. Esses links de aplicativo ficam BLOQUEADOS no perfil (protocol_handler.excluded_schemes = true: o Chrome
    nem pergunta). Só mexe nos Preferences com o Chrome fechado."""
    pref = PERFIS / perfil / "Default" / "Preferences"
    try:
        d = json.loads(pref.read_text(encoding="utf-8")) if pref.exists() else {}
        ex = d.setdefault("protocol_handler", {}).setdefault("excluded_schemes", {})
        if all(ex.get(s) is True for s in APPS_BLOQUEADOS):
            return
        ex.update({s: True for s in APPS_BLOQUEADOS})
        pref.parent.mkdir(parents=True, exist_ok=True)
        pref.write_text(json.dumps(d), encoding="utf-8")
    except (OSError, ValueError) as e:
        log(f"preferências de {perfil}: não deu pra bloquear apps ({e})")


def _gravando():
    """DESKTOP (dona 22/10 e 23/10): só trabalha se o OBS estiver fechado e nenhum app estiver usando microfone ou
    câmera (Meet, Zoom...). Lido do registro do Windows (CapabilityAccessManager: LastUsedTimeStop = 0 = em uso)."""
    if not WIN or not os.environ.get("COMPUTERNAME", "").upper().startswith("DESKTOP"):  # só o desktop grava/faz chamada
        return ""
    ps = ("$u = @(Get-Process | Where-Object { $_.ProcessName -match '^(obs64|obs32|obs)$' } | ForEach-Object { 'OBS' });"
          r"$cap = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore';"
          "$u += @(foreach ($k in 'microphone','webcam') { Get-ChildItem \"$cap\\$k\" -Recurse -ErrorAction SilentlyContinue"
          " | Where-Object { $_.GetValue('LastUsedTimeStop') -eq 0 -and $_.GetValue('LastUsedTimeStart') }"
          " | ForEach-Object { $k } });"
          "($u | Select-Object -Unique) -join ','")
    try:
        return _ps(ps, 30)
    except subprocess.TimeoutExpired:
        return ""


def _lancar(cmd):
    """Abre o Chrome e devolve o PID. No DESKTOP vai por uma tarefa do Windows (abre na sessão da tela da dona e
    sobrevive ao fim do ssh)."""
    if not WIN:
        return subprocess.Popen(cmd, env=_ambiente(), start_new_session=True, stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL).pid
    args = subprocess.list2cmdline(cmd[1:]).replace("'", "''")
    sem_cmdlets = BASE / "sem_cmdlets_tarefa"  # 26/10: já falhou aqui (PC2) — não gasta 1 min de PowerShell de novo
    saida = "" if sem_cmdlets.exists() else _ps(
        "$ErrorActionPreference = 'Stop';"
        f"$a = New-ScheduledTaskAction -Execute '{cmd[0]}' -Argument '{args}';"
        "$p = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive;"
        "Register-ScheduledTask -TaskName PostadorChrome -Action $a -Principal $p -Force | Out-Null;"
        "Start-ScheduledTask -TaskName PostadorChrome; 'TAREFA_OK'", 60)
    if "TAREFA_OK" not in saida:
        if not sem_cmdlets.exists():  # registra a falha (no PC2: WMI quebrado, "Classe inválida") uma vez
            sem_cmdlets.write_text("cmdlets de tarefa falham aqui: vai direto pelo schtasks", encoding="utf-8")
        # 23/10: no PC2 os cmdlets de tarefa dão "Classe inválida" (WMI quebrado) — plano B pelo schtasks.exe com um
        # .bat (o /tr do schtasks não cabe a linha inteira do Chrome); /it = abre na sessão da tela, sem senha
        # 26/10: nome por porta — vários Chrome abrindo juntos (TikTok em lote) não sobrescrevem o .bat um do outro
        porta = next((x.split("=", 1)[1] for x in cmd if x.startswith("--remote-debugging-port=")), "")
        # 12/11 desktop: a "PostadorChrome" antiga ficou presa no perfil da conta_exemplo e o ssh não tem
        # permissão de sobrescrever ("Acesso negado") — toda conta abria a maite. Nome novo = tarefa nossa.
        tn = f"PostadorChromeB{porta if porta != '9460' else ''}"
        bat = BASE / f"abrir_chrome{porta if porta != '9460' else ''}.bat"
        bat.write_text("@echo off\r\nstart \"\" " + subprocess.list2cmdline(cmd) + "\r\n", encoding="utf-8")
        subprocess.run(["schtasks", "/create", "/tn", tn, "/tr", f'"{bat}"', "/sc", "once",
                        "/st", "00:00", "/it", "/f"], capture_output=True, timeout=60)
        subprocess.run(["schtasks", "/run", "/tn", tn], capture_output=True, timeout=60)
    porta = next((x.split("=", 1)[1] for x in cmd if x.startswith("--remote-debugging-port=")), "")
    if porta:  # 26/10: o PID pela porta (netstat), sem PowerShell/WMI
        for _ in range(90):
            pid = _pid_da_porta(porta)
            if pid:
                return pid
            time.sleep(1)
        return 0
    marca = [x for x in cmd if x.startswith("--user-data-dir=")][0].split("=", 1)[1].replace("'", "''")
    for _ in range(30):
        pid = _ps("Get-CimInstance Win32_Process -Filter \"Name='chrome.exe'\" | Where-Object { $_.CommandLine -like '*"
                  + marca + "*' -and $_.CommandLine -notlike '*--type=*' } | Select-Object -First 1 -ExpandProperty ProcessId",
                  30)
        if pid.isdigit():
            return int(pid)
        time.sleep(1)
    return 0


def logar(perfil, url):
    """Janela pra dona ENTRAR na conta: Chrome SEM a porta de controle (com ela ligada o Google recusa o login —
    "este navegador ou app pode não ser seguro"). Mesmo perfil e mesmas opções do abrir, então o login vale depois."""
    perfil = "".join(c for c in perfil if c.isalnum() or c in "._-") or "sem_nome"
    d = _ocupante()
    if d:
        print(f"OCUPADO por {d.get('perfil')}: espere a postagem terminar")
        return 3
    chrome = _chrome()
    if not chrome:
        print("SEM_CHROME")
        return 5
    # dona 23/10 ("loguei mas estava rodando um vídeo"): marca o login ANTES de tudo (o telão para em ~2 s) e fecha o
    # navegador do telão (vídeo/painel) pra janela dela abrir com a RAM livre; o vídeo interrompido volta depois
    OCUPADO.write_text(json.dumps({"pid": os.getpid(), "porta": 0, "perfil": perfil, "desde": time.time(), "login": True}),
                       encoding="utf-8")
    if not WIN:
        subprocess.run(["pkill", "-f", "[v]itrine/perfil_"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    (PERFIS / perfil).mkdir(parents=True, exist_ok=True)
    _sem_abrir_app(perfil)
    _liberar_ram()
    leve = [x for x in LEVE if not x.startswith("--remote-allow-origins")]
    if not WIN:
        leve.append("--ozone-platform=x11")  # janela X11 (Xwayland no GNOME): aceita o e-mail digitado pelo teclado.py
    pid = _lancar([*chrome, f"--user-data-dir={PERFIS / perfil}", *leve, url])
    OCUPADO.write_text(json.dumps({"pid": pid, "porta": 0, "perfil": perfil, "desde": time.time(), "login": True}),
                       encoding="utf-8")
    log(f"janela de login de {perfil} aberta (sem porta de controle)")
    print("PRONTO_LOGIN", flush=True)
    return 0


def _principais_login():
    """{perfil: pid} dos Chrome de LOGIN EM LOTE (perfil do postador, sem porta de controle) — Linux."""
    out = {}
    for d in Path("/proc").iterdir():
        if not d.name.isdigit():
            continue
        try:
            a = (d / "cmdline").read_bytes().decode("utf-8", "replace").split("\0")
        except OSError:
            continue
        if len([x for x in a if x]) == 1:  # Chrome 157 no Mint (STI) grava a linha de comando inteira num campo só
            a = a[0].split(" ")
        if not a or "chrome" not in a[0] or any(x.startswith(("--type=", "--remote-debugging-port")) for x in a):
            continue
        dd = next((x.split("=", 1)[1] for x in a if x.startswith("--user-data-dir=")), "")
        if str(PERFIS) in dd:
            out[Path(dd).name] = int(d.name)
    return out


def janelas():
    """26/10 login em lote (Linux): "#|<hora>" e uma linha "perfil|pid|título" por janela de login aberta."""
    env, titulos = _ambiente(), {}
    r = subprocess.run(["xprop", "-root", "_NET_CLIENT_LIST"], capture_output=True, text=True, env=env, timeout=15)
    for wid in r.stdout.split("#")[-1].replace(",", " ").split():
        w = subprocess.run(["xprop", "-id", wid, "_NET_WM_PID", "_NET_WM_NAME"], capture_output=True, text=True,
                           env=env, timeout=15).stdout
        pid = next((x.split("=")[-1].strip() for x in w.splitlines() if x.startswith("_NET_WM_PID")), "")
        nome = next((x.split("=", 1)[-1].strip().strip('"') for x in w.splitlines() if x.startswith("_NET_WM_NAME")), "")
        if pid.isdigit() and (int(pid) not in titulos or "youtube" in nome.lower()):
            titulos[int(pid)] = nome
    print(f"#|{int(time.time())}")
    for perfil, pid in _principais_login().items():
        print(f"{perfil}|{pid}|{titulos.get(pid, '')}")
    return 0


def login_janela(perfil, x, y, url):
    """26/10 login em lote (Linux): mais uma janela de login (sem porta de controle, sem marcar OCUPADO — quem segura
    a máquina é a vez do PC1). Antes: telão fechado e RAM limpa; sem RAM, não abre."""
    perfil = "".join(c for c in perfil if c.isalnum() or c in "._-") or "sem_nome"
    chrome = _chrome()
    if not chrome:
        print("SEM_CHROME")
        return 5
    subprocess.run(["pkill", "-f", "[v]itrine/perfil_"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    _liberar_ram()
    livre = _ram_livre_mb()
    if livre < RAM_MINIMA_MB + 250:  # a janela come ~250 MB e a conferência precisa de RAM_MINIMA depois
        print(f"POUCA_RAM {livre} MB livres")
        return 4
    (PERFIS / perfil).mkdir(parents=True, exist_ok=True)
    _sem_abrir_app(perfil)
    leve = [x for x in LEVE if not x.startswith(("--remote-allow-origins", "--window-size"))]
    pid = _lancar([*chrome, f"--user-data-dir={PERFIS / perfil}", *leve, "--ozone-platform=x11",
                   "--window-size=1000,700", f"--window-position={int(x)},{int(y)}", url])
    log(f"login em lote: janela de {perfil} aberta (pid {pid}, RAM livre {livre} MB)")
    print(f"PRONTO_LOGIN {pid}", flush=True)
    return 0


def fechar_janela(perfil):
    """26/10 login em lote (Linux): fecha a janela de login do perfil com SIGTERM (o Chrome grava os cookies)."""
    pid = _principais_login().get(perfil)
    if pid:
        _matar(pid)
        log(f"login em lote: janela de {perfil} fechada")
    print("FECHADO")
    return 0


def som(acao):
    """Dona 26/10: som desligado durante os logins. "mudo" guarda como estava; "volta" só desmuta se estava ligado."""
    antes = BASE / "som_antes"
    env = _ambiente()
    if acao == "mudo":
        r = subprocess.run(["pactl", "get-sink-mute", "@DEFAULT_SINK@"], capture_output=True, text=True, env=env,
                           timeout=15)
        if r.returncode == 0 and not antes.exists():
            antes.write_text("sim" if "sim" in r.stdout.lower() or "yes" in r.stdout.lower() else "nao")
        subprocess.run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "1"], capture_output=True, env=env, timeout=15)
    else:
        if antes.exists() and antes.read_text().strip() == "nao":
            subprocess.run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "0"], capture_output=True, env=env, timeout=15)
        antes.unlink(missing_ok=True)
    print("SOM", acao)
    return 0


def _fechar_orfaos(porta):
    """23/10: janela deixada aberta pra dona (código do TikTok) perdia o registro quando outra conta abria; o Chrome
    velho ficava preso na porta e o novo abria sem controle (x200ma com 3 perdidos na 9460). Fecha os que sobraram."""
    if WIN:  # 26/10 PC2: Chrome que demorou a subir ficava órfão na porta e o próximo falhava ("não abriu a porta")
        for _ in range(3):
            pid = _pid_da_porta(porta)
            if not pid:
                return
            log(f"Chrome perdido na porta {porta} fechado (pid {pid})")
            _matar(pid)
        return
    r = subprocess.run(["pgrep", "-f", "--", f"--remote-debugging-port={porta}"], capture_output=True, text=True)
    for pid in r.stdout.split():
        try:
            cmd = Path(f"/proc/{pid}/cmdline").read_bytes().decode(errors="replace")
        except OSError:
            continue
        if "--type=" in cmd or "chrome" not in cmd:  # só o processo principal; os filhos saem junto
            continue
        log(f"Chrome perdido na porta {porta} fechado (pid {pid})")
        try:
            os.kill(int(pid), signal.SIGTERM)
        except OSError:
            pass
    time.sleep(3)


def _soltar_da_fabrica(perfil):
    """02/11: a fábrica de tokens (nsn services/veo_flow/fabrica_tokens.py, porta 9399) pode estar com o Chrome QUENTE
    desse perfil; dois Chromes no mesmo perfil não sobem (o 2º não abre a porta de controle). Pede pra ela soltar."""
    try:
        r = urllib.request.urlopen(f"http://127.0.0.1:9399/estado", timeout=3)
        if perfil.lower() in json.loads(r.read()).get("contas", {}):
            urllib.request.urlopen(f"http://127.0.0.1:9399/soltar?perfil={perfil.lower()}", timeout=30)
            time.sleep(3)
            log(f"{perfil}: soltei o Chrome quente da fábrica de tokens")
    except Exception:  # noqa: BLE001 — fábrica fora do ar = nada a soltar
        pass


def _alguem_conectado(porta):
    """Há conexão TCP estabelecida na porta de controle do Chrome (alguém usando, pelo túnel ou local)? Na dúvida, True."""
    try:
        porta = int(porta)
        if WIN:
            r = subprocess.run(["netstat", "-ano", "-p", "TCP"], capture_output=True, text=True, timeout=30)
            return any(f":{porta} " in l and "ESTABLISHED" in l for l in r.stdout.splitlines())
        r = subprocess.run(["ss", "-tnH", "state", "established", f"( sport = :{porta} )"], capture_output=True,
                           text=True, timeout=30)
        return bool(r.stdout.strip()) if r.returncode == 0 else True
    except Exception:  # noqa: BLE001
        return True


def _proxy_pronto(n):
    """04/11: o PC1 abre um túnel SSH REVERSO das portas do proxy_tiktok (18200 = PAC, 18200+n = IP Webshare n da conta)
    antes de pedir o Chrome. Aqui confere que os dois respondem ANTES de abrir — senão o Chrome cairia no DIRECT (IP de
    casa). Falhou = não abre (falha fechado)."""
    import socket
    import urllib.request
    try:
        pac = urllib.request.urlopen(f"http://127.0.0.1:18200/{int(n)}.pac", timeout=8).read().decode("utf-8", "replace")
        if f"PROXY 127.0.0.1:{18200 + int(n)}" not in pac:
            return False
        socket.create_connection(("127.0.0.1", 18200 + int(n)), timeout=8).close()
        return True
    except Exception:  # noqa: BLE001
        return False


def abrir(perfil, porta, url="about:blank", espera_trava_s=900, proxy_n=None):
    perfil = "".join(c for c in perfil if c.isalnum() or c in "._-") or "sem_nome"
    if proxy_n is not None and not _proxy_pronto(proxy_n):
        print(f"SEM_PROXY {proxy_n}: o túnel do proxy do PC1 não responde aqui — não abro (nunca pelo IP de casa)")
        return 6
    g = _gravando()
    if g:  # desktop gravando/em chamada: não usa (o PC1 tenta o próximo)
        print(f"OCUPADO gravando ({g})")
        return 3
    porta = int(porta)
    fim = time.time() + espera_trava_s
    while True:  # uma conta por vez: o notebook não aguenta dois Chromes
        d = _ocupante()
        if not d:
            break
        # 23/10: janela de LOGIN esquecida aberta (a da ing ficou das 02:25 às 07h) travava o notebook a noite toda.
        # Passou de 45 min = a dona já terminou: fecha normal (SIGTERM grava o login) e libera.
        if d.get("login") and time.time() - d.get("desde", 0) > 45 * 60:
            log(f"janela de login de {d.get('perfil')} aberta há {int((time.time() - d['desde']) // 60)} min — fechada")
            _matar(d.get("pid"))
            OCUPADO.unlink(missing_ok=True)
            continue
        if d.get("login") and d.get("perfil") == perfil and _cdp_vivo(porta) and proxy_n is None:
            # só a janela de LOGIN é reaproveitada (a conferência logo depois do login). Dois trabalhos da mesma conta
            # dividindo o Chrome = o primeiro a terminar fechava o do outro no meio (revisão 23/10)
            print(f"PRONTO (ja estava aberto) HOME={Path.home()}", flush=True)
            return 0
        # 04/11: quem abriu morreu sem "fechar" (conferir_logins parado, túnel órfão) e o notebook ficava OCUPADO pra
        # sempre — o Veo das solares não achava máquina das 05:48 às 06:10. Ocupante com 40+ min e NINGUÉM conectado na
        # porta de controle = abandonado: fecha e segue.
        if not d.get("login") and time.time() - d.get("desde", 0) > 40 * 60 and not _alguem_conectado(d.get("porta")):
            log(f"ocupante abandonado: {d.get('perfil')} na porta {d.get('porta')} há "
                f"{int((time.time() - d.get('desde', 0)) // 60)} min sem conexão — fechado")
            _matar(d.get("pid"))
            OCUPADO.unlink(missing_ok=True)
            continue
        if time.time() > fim:
            print(f"OCUPADO por {d.get('perfil')} desde {time.strftime('%H:%M', time.localtime(d.get('desde', 0)))}")
            return 3
        time.sleep(10)
    # marca ocupado ANTES de medir a RAM: o telão (vitrine/player.py) vê e fecha o painel em ~5 s, liberando memória
    # 24/10 (dona: vídeo tocando no acer quando a janela de login abria): login marcado já aqui, e o navegador do
    # telão fecha antes do Chrome subir (antes só o `logar` fazia isso; o email_login entra por este `abrir`)
    login = any(s in url for s in ("accounts.google", "instagram.com/accounts", "tiktok.com/login"))
    OCUPADO.write_text(json.dumps({"pid": os.getpid(), "porta": porta, "perfil": perfil, "desde": time.time(),
                                   "login": login}), encoding="utf-8")
    if login and not WIN:
        subprocess.run(["pkill", "-f", "[v]itrine/perfil_"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    livre = _ram_livre_mb()
    for _ in range(25):
        if livre >= RAM_MINIMA_MB:
            break
        time.sleep(1)
        livre = _ram_livre_mb()
    if livre < RAM_MINIMA_MB:
        OCUPADO.unlink(missing_ok=True)
        print(f"POUCA_RAM {livre} MB livres")
        return 4
    (PERFIS / perfil).mkdir(parents=True, exist_ok=True)
    _sem_abrir_app(perfil)
    _liberar_ram()
    ENTRADA.mkdir(parents=True, exist_ok=True)
    _soltar_da_fabrica(perfil)
    _fechar_orfaos(porta)
    chrome = _chrome()
    if not chrome:
        OCUPADO.unlink(missing_ok=True)
        print("SEM_CHROME: nesta máquina não há Chrome (rode no PC1: maquina_remota.py preparar-chrome <máquina>)")
        return 5
    # dona 23/10: a postagem NÃO aparece na tela (o telão continua com o painel). X11 (Xwayland no GNOME) aceita
    # posicionar a janela fora da área visível; tamanho normal, pro Studio/TikTok montarem a página igual.
    login = any(s in url for s in ("accounts.google", "instagram.com/accounts", "tiktok.com/login"))
    fora = [] if login else (["--window-position=-3000,0"] if WIN else
                             ["--ozone-platform=x11", "--window-position=-3000,0"])  # login: a dona precisa ver
    px = ([f"--proxy-pac-url=http://127.0.0.1:18200/{int(proxy_n)}.pac",
           "--force-webrtc-ip-handling-policy=disable_non_proxied_udp"] if proxy_n is not None else [])
    cmd = [*chrome, f"--user-data-dir={PERFIS / perfil}", f"--remote-debugging-port={porta}", *LEVE, *px, *fora, url]
    pid = _lancar(cmd)
    OCUPADO.write_text(json.dumps({"pid": pid, "porta": porta, "perfil": perfil, "desde": time.time(), "login": login}),
                       encoding="utf-8")
    for _ in range(120):  # Celeron: o Chrome leva até ~30 s pra subir com a máquina ocupada
        if _cdp_vivo(porta):
            log(f"abriu {perfil} na porta {porta} (RAM livre antes: {livre} MB)"
                + (f" pelo proxy {proxy_n}" if proxy_n is not None else ""))
            if proxy_n is not None:
                print(f"PROXY_OK {int(proxy_n)}", flush=True)
            print(f"PRONTO HOME={BASE.parent if WIN else Path.home()}", flush=True)
            return 0
        if not WIN and pid and not _pid_vivo(pid):
            break
        time.sleep(0.5)
    _matar(pid or (_pid_da_porta(porta) if WIN else 0))  # 26/10: sem PID (subiu tarde) = acha pela porta
    OCUPADO.unlink(missing_ok=True)
    print("FALHOU: o Chrome não abriu a porta de controle")
    return 2


def fechar(porta):
    d = _ocupante()
    if d and int(d.get("porta", 0)) == int(porta):
        _matar(d["pid"])
        OCUPADO.unlink(missing_ok=True)
        _limpar_cache(d.get("perfil", ""))
        log(f"fechou {d.get('perfil')} (porta {porta})")
        # vídeo/capa mandados pelo PC1 só serviam pra ESTE envio (que acabou). 02/11: só os com mais de 1 h — com vários
        # Chromes de imagem e a fábrica de tokens, apagar tudo levava as referências de OUTRO pedido no meio (FileNotFound)
        for a in ENTRADA.glob("*"):
            try:
                st = a.stat()  # vídeo grande (> 20 MB) é do envio que acabou: sai já (disco dos notebooks)
                if st.st_size > 20_000_000 or time.time() - st.st_mtime > 3600:
                    a.unlink()
            except OSError:
                pass
    elif not _ocupante():  # ninguém usando: sobra de envio interrompido
        for a in ENTRADA.glob("*"):
            try:
                a.unlink()
            except OSError:
                pass
    print("FECHADO")
    return 0


def estado():
    d = _ocupante()
    perfis = sorted(p.name for p in PERFIS.iterdir() if p.is_dir()) if PERFIS.is_dir() else []
    print(json.dumps({"aberto": d, "perfis": perfis, "ram_livre_mb": _ram_livre_mb(), "chrome": (_chrome() or [None])[0],
                      "entrada": [a.name for a in ENTRADA.glob("*")] if ENTRADA.is_dir() else []},
                     ensure_ascii=False))
    return 0


def main(a):
    sem_espera = "--sem-espera" in a  # ocupado = responde OCUPADO na hora (o PC1 tenta o outro notebook)
    proxy_n = next((x.split("=", 1)[1] for x in a if x.startswith("--proxy-n=")), None)  # 04/11: Chrome pelo proxy
    a = [x for x in a if x != "--sem-espera" and not x.startswith("--proxy-n=")]
    # 26/10 (dona: TikTok "vários de uma vez" no PC2): portas 9461–9479 = Chrome EXTRA, com ocupante e entrada próprios;
    # a 9460 segue "uma conta por vez" (postagem, Veo, conferência)
    p = a[2] if len(a) >= 3 and a[0] == "abrir" else a[1] if len(a) >= 2 and a[0] == "fechar" else ""
    if str(p).isdigit() and 9461 <= int(p) <= 9479:
        global OCUPADO, ENTRADA
        OCUPADO, ENTRADA = BASE / f"ocupado_{p}", BASE / f"entrada_{p}"
    if len(a) >= 3 and a[0] == "logar":
        return logar(a[1], a[3] if len(a) > 3 else "https://accounts.google.com")
    if len(a) >= 3 and a[0] == "abrir":
        return abrir(a[1], a[2], a[3] if len(a) > 3 else "about:blank", espera_trava_s=0 if sem_espera else 900,
                     proxy_n=proxy_n)
    if len(a) >= 2 and a[0] == "fechar":
        return fechar(a[1])
    if a and a[0] == "estado":
        return estado()
    if a and a[0] == "liberar":
        _liberar_ram()
        print(f"RAM_LIVRE {_ram_livre_mb()}")
        return 0
    if a and a[0] == "janelas":
        return janelas()
    if len(a) >= 5 and a[0] == "login_janela":
        return login_janela(a[1], a[2], a[3], a[4])
    if len(a) >= 2 and a[0] == "fechar_janela":
        return fechar_janela(a[1])
    if len(a) >= 2 and a[0] == "som" and not WIN:
        return som(a[1])
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
