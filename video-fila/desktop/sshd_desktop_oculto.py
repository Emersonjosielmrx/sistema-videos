"""01/11 dona ("aparece toda hora o PowerShell no desktop"): o sshd do usuário roda na sessão da tela, então cada
comando que chega por ssh abre uma janela de console na frente dela. Este sobe o sshd (porta 2223, mesmo Emerson, mesma
chave) numa ÁREA DE TRABALHO INVISÍVEL do Windows (CreateDesktop "sshd_oculto"): os consoles dos comandos nascem lá e
nunca aparecem. Não precisa de administrador. A 2222 (tarefa SSHD-Usuario) segue de reserva.
Tarefa SSHD-Oculto (no logon e a cada 5 min, pythonw): se já está rodando, sai."""
import ctypes
import subprocess
import sys
import time
from ctypes import wintypes
from pathlib import Path

D = Path(r"D:\ferramentas\sshd-usuario")
CFG = D / "sshd_config_2223"
SSHD = r"C:\Program Files\OpenSSH\sshd.exe"
LOG = D / "sshd_oculto.log"
NO_WIN = 0x08000000


def log(m):
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S')} {m}\n")


def rodando():
    r = subprocess.run(["powershell", "-NoProfile", "-Command",
                        "Get-CimInstance Win32_Process -Filter \"Name='sshd.exe'\" | Where-Object { $_.CommandLine "
                        "-like '*sshd_config_2223*' } | Measure-Object | Select-Object -ExpandProperty Count"],
                       capture_output=True, text=True, creationflags=NO_WIN, timeout=60)
    return (r.stdout or "0").strip() not in ("", "0")


def config():
    linhas = []
    for l in (D / "sshd_config").read_text(encoding="utf-8", errors="replace").splitlines():
        if l.strip().lower().startswith(("port ", "pidfile ")):
            continue
        linhas.append(l)
    CFG.write_text("Port 2223\nPidFile " + str(D / "sshd_2223.pid").replace("\\", "/") + "\n" + "\n".join(linhas) + "\n",
                   encoding="ascii", errors="replace")


class STARTUPINFO(ctypes.Structure):
    _fields_ = [("cb", wintypes.DWORD), ("lpReserved", wintypes.LPWSTR), ("lpDesktop", wintypes.LPWSTR),
                ("lpTitle", wintypes.LPWSTR), ("dwX", wintypes.DWORD), ("dwY", wintypes.DWORD),
                ("dwXSize", wintypes.DWORD), ("dwYSize", wintypes.DWORD), ("dwXCountChars", wintypes.DWORD),
                ("dwYCountChars", wintypes.DWORD), ("dwFillAttribute", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
                ("wShowWindow", wintypes.WORD), ("cbReserved2", wintypes.WORD), ("lpReserved2", ctypes.c_void_p),
                ("hStdInput", wintypes.HANDLE), ("hStdOutput", wintypes.HANDLE), ("hStdError", wintypes.HANDLE)]


class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [("hProcess", wintypes.HANDLE), ("hThread", wintypes.HANDLE), ("dwProcessId", wintypes.DWORD),
                ("dwThreadId", wintypes.DWORD)]


def main():
    if rodando():
        return
    config()
    u32, k32 = ctypes.WinDLL("user32", use_last_error=True), ctypes.WinDLL("kernel32", use_last_error=True)
    u32.CreateDesktopW.restype = wintypes.HANDLE
    hdesk = u32.CreateDesktopW("sshd_oculto", None, None, 0, 0x10000000, None)  # GENERIC_ALL
    if not hdesk:
        log(f"CreateDesktop falhou {ctypes.get_last_error()}")
        sys.exit(1)
    si = STARTUPINFO()
    si.cb = ctypes.sizeof(si)
    si.lpDesktop = "WinSta0\\sshd_oculto"
    si.dwFlags = 0x1  # STARTF_USESHOWWINDOW
    si.wShowWindow = 0  # SW_HIDE
    pi = PROCESS_INFORMATION()
    cmd = f'"{SSHD}" -D -f "{CFG}" -E "{D / "sshd_2223.log"}"'
    ok = k32.CreateProcessW(SSHD, ctypes.create_unicode_buffer(cmd), None, None, False, 0, None, str(D),
                            ctypes.byref(si), ctypes.byref(pi))
    if not ok:
        log(f"CreateProcess falhou {ctypes.get_last_error()}")
        sys.exit(1)
    log(f"sshd 2223 na área invisível (pid {pi.dwProcessId})")
    k32.WaitForSingleObject(pi.hProcess, 0xFFFFFFFF)  # segura a área de trabalho aberta enquanto o sshd vive
    log("sshd 2223 saiu")


if __name__ == "__main__":
    main()
