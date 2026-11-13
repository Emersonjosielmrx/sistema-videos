#!/usr/bin/env python3
r"""argon_manter.py — mantém o Argon NO AR sozinho (dona 29/10: "ele tem que iniciar só").

O Argon é: gemini_http_proxy.py (PC1, :20141, sem navegador) + túnel reverso ssh -R 20141 -> VPS hermes-bloqueio +
o proxy da VPS (:20133, node) que o pipeline chama. Em 28/10 20:46 o proxy e o túnel morreram no PC1 e nada relançava:
o :20133 passou a responder 502 e todas as linhas caíram no Gemini 3.8 em silêncio.

A cada passada (tarefa ArgonManter: a cada 5 min e ao iniciar o Windows):
  1. :20141 local não responde -> sobe gemini_http_proxy.py escondido (logs em gemini_http_proxy.out/err.log).
  2. VPS sem a porta 20141 escutando -> recria o túnel (ssh -N -R, sem janela) e guarda o PID.
  3. Registra em argon_manter.json; avisa no Telegram (portão avisos.py) só quando teve de relançar.

    python argon_manter.py            # uma passada
    python argon_manter.py --status   # só mostra
"""
import sys as _sys
_sys.path.insert(0, r"D:\hipercool-materiais\comum")
import sem_janela  # noqa: E402,F401 — regra da dona: nenhum processo filho abre janela na tela
import json
import os
import socket
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

SSH_EXE = r"C:\Program Files\Git\usr\bin\ssh.exe" if __import__("os").path.exists(r"C:\Program Files\Git\usr\bin\ssh.exe") else "ssh"  # 29/10 (Fable): sob tarefa agendada o "ssh" do PATH e o OpenSSH do Windows, que trava ate o timeout

AQUI = Path(__file__).resolve().parent
PY = Path(sys.executable)
PYW = PY.with_name("pythonw.exe") if PY.with_name("pythonw.exe").exists() else PY
PORTA = 20141
VPS = "hermes-bloqueio"
ESTADO = AQUI / "argon_manter.json"
OUT, ERR = AQUI / "gemini_http_proxy.out.log", AQUI / "gemini_http_proxy.err.log"
SEM_JANELA, DETACHED = 0x08000000, 0x00000008


def log(m):
    print(f"[{datetime.now():%d/%m %H:%M:%S}] {m}", flush=True)


def _estado():
    try:
        return json.loads(ESTADO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _gravar(d):
    ESTADO.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")


def proxy_local_ativo(timeout=8):
    """29/10 (Fable): GET /health com prazo, não só a porta aberta (um proxy travado passava como vivo)."""
    try:
        import urllib.request
        with urllib.request.urlopen(f"http://127.0.0.1:{PORTA}/health", timeout=timeout) as r:
            return b'"ok"' in r.read()
    except Exception:  # noqa: BLE001
        return False


def proxy_vivo_de_verdade():
    """30/10: 3 tentativas em ~1 min antes de dar o proxy por morto. Com o PC a 100% de CPU (várias sessões) o /health
    chegou a levar 25 s; com 1 tentativa de 8 s o manter matou um proxy SÃO às 11:2x e subiu outro que levou 15 min."""
    for i in range(3):
        if proxy_local_ativo(timeout=20):
            return True
        if i < 2:
            time.sleep(10)
    return False


def _pids_proxy():
    """{pid: segundos de vida} de todo gemini_http_proxy.py desta porta (não só o pid guardado no estado)."""
    cmd = ("Get-CimInstance Win32_Process -Filter \"Name like 'python%'\" | "
           "Where-Object { $_.CommandLine -match 'gemini_http_proxy\\.py' } | "
           "ForEach-Object { '{0} {1}' -f $_.ProcessId, [int]((Get-Date) - $_.CreationDate).TotalSeconds }")
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True, timeout=90,
                           creationflags=SEM_JANELA)
    except Exception:  # noqa: BLE001
        return {}
    pids = {}
    for linha in r.stdout.split("\n"):
        p = linha.split()
        if len(p) == 2 and p[0].isdigit() and p[1].lstrip("-").isdigit():
            pids[int(p[0])] = int(p[1])
    return pids


SUBINDO_S = 300  # proxy com menos de 5 min de vida ainda pode estar subindo (import lento com o PC carregado)


def _matar(pid):
    subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True, creationflags=SEM_JANELA)


def _girar_err_log():
    """O err.log nunca girava (160 KB/dia de tracebacks). Só dá para girar com o proxy parado (Windows prende o arquivo)."""
    try:
        if ERR.exists() and ERR.stat().st_size > 5_000_000:
            velho = ERR.with_suffix(".log.1")
            velho.unlink(missing_ok=True)
            ERR.rename(velho)
    except OSError:
        pass


def vps_20133_ok():
    """O proxy node da VPS (:20133, antigravity-cc-proxy.service) responde? None = VPS fora. 29/10 (Fable): o manter
    só olhava o túnel; o :20133 é o que o pipeline chama."""
    try:
        r = subprocess.run([SSH_EXE, "-n", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "-o", "LogLevel=ERROR", VPS,
                            "curl -s -o /dev/null -w '%{http_code}' --max-time 8 http://127.0.0.1:20133/v1/models || echo falhou"],
                           capture_output=True, text=True, timeout=40, creationflags=SEM_JANELA)
        c = r.stdout.strip()
        return c.startswith(("2", "4"))  # 401/404 também significa "o node está de pé"
    except Exception:  # noqa: BLE001
        return None


def reiniciar_20133():
    r = subprocess.run([SSH_EXE, "-n", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "-o", "LogLevel=ERROR", VPS,
                        "sudo -n systemctl restart antigravity-cc-proxy.service 2>&1 || systemctl restart antigravity-cc-proxy.service 2>&1; sleep 3; "
                        "curl -s -o /dev/null -w '%{http_code}' --max-time 8 http://127.0.0.1:20133/v1/models"],
                       capture_output=True, text=True, timeout=60, creationflags=SEM_JANELA)
    return r.stdout.strip()[-3:]


def subir_proxy():
    _girar_err_log()
    with OUT.open("a", encoding="utf-8") as o, ERR.open("a", encoding="utf-8") as e:
        p = subprocess.Popen([str(PYW), "-X", "utf8", str(AQUI / "gemini_http_proxy.py"), "--porta", str(PORTA)],
                             cwd=str(AQUI), stdout=o, stderr=e, creationflags=SEM_JANELA | DETACHED)
    for _ in range(60):  # 30/10: até 2 min (com o PC carregado só o "import requests" levou 15 s)
        time.sleep(2)
        if p.poll() is not None:
            return None  # saiu (porta já ocupada: o proxy novo agora recusa dividir a porta)
        if proxy_local_ativo():
            return p.pid
    return p.pid  # ainda subindo: a próxima passada vê (e não sobe outro em cima, ver SUBINDO_S)


def cuidar_do_proxy(est, feitos):
    """Proxy :20141 respondendo? Senão: espera o que está subindo, derruba os presos/duplicados e sobe UM."""
    if proxy_vivo_de_verdade():
        pids = _pids_proxy()
        if len(pids) > 1:  # 30/10: sobra de antes da porta exclusiva; fica o que tem a porta
            dono = _dono_da_porta()
            for pid in pids:
                if dono and pid != dono:
                    _matar(pid)
                    feitos.append(f"proxy duplicado {pid} derrubado (fica o {dono})")
            est["proxy_pid"] = dono or est.get("proxy_pid")
        return
    pids = _pids_proxy()
    subindo = [pid for pid, vida in pids.items() if vida < SUBINDO_S]
    if subindo:
        log(f"proxy {subindo} ainda subindo; não subo outro")
        return
    for pid in pids:
        _matar(pid)
    if pids:
        feitos.append(f"proxy preso derrubado ({', '.join(map(str, pids))})")
    pid = subir_proxy()
    feitos.append(f"proxy :{PORTA} {'subiu (pid ' + str(pid) + ')' if pid else 'NÃO subiu (ver gemini_http_proxy.err.log)'}")
    est["proxy_pid"] = pid


def _dono_da_porta():
    try:
        r = subprocess.run(["netstat", "-ano", "-p", "TCP"], capture_output=True, text=True, timeout=30,
                           creationflags=SEM_JANELA)
        for linha in r.stdout.split("\n"):
            p = linha.split()
            if len(p) == 5 and p[1] == f"127.0.0.1:{PORTA}" and p[3] in ("LISTENING", "ESCUTANDO"):
                return int(p[4])
    except Exception:  # noqa: BLE001
        pass
    return None


def tunnel_ativo():
    try:
        # 29/10 (sessão PRODUTOS): a porta escutava na VPS mas o túnel não entregava nada ("Argon proxy unreachable:
        # socket hang up" em argon-pro/argon-gemini/gweb com 28 contas prontas) -> confere a resposta, não só a porta
        r = subprocess.run([SSH_EXE, "-n", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "-o", "LogLevel=ERROR", VPS,
                            f"curl -s --max-time 10 http://127.0.0.1:{PORTA}/health"], capture_output=True, text=True,
                           timeout=40, creationflags=SEM_JANELA)
        if r.returncode == 255:
            return None  # ssh falhou: não deu para saber
        return '"ok"' in r.stdout
    except Exception:  # noqa: BLE001
        return None  # não deu para saber (VPS fora/ssh falhou)


def _pid_vivo(pid):
    try:
        import ctypes
        k = ctypes.windll.kernel32
        h = k.OpenProcess(0x1000, False, int(pid))
        if not h:
            return False
        code = ctypes.c_ulong()
        ok = k.GetExitCodeProcess(h, ctypes.byref(code))
        k.CloseHandle(h)
        return bool(ok) and code.value == 259
    except Exception:  # noqa: BLE001
        return False


def subir_tunnel(est):
    pid = est.get("tunnel_pid")
    if pid and _pid_vivo(pid):  # ssh vivo mas a VPS não escuta: ele está preso — derruba e recria
        subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True, creationflags=SEM_JANELA)
    p = subprocess.Popen([SSH_EXE, "-N", "-o", "BatchMode=yes", "-o", "ServerAliveInterval=30", "-o", "ServerAliveCountMax=3",
                          "-o", "ExitOnForwardFailure=yes", "-o", "LogLevel=ERROR",
                          # 127.0.0.1, não localhost: o proxy escuta só em IPv4 e "localhost" ia para ::1 (29/10)
                          "-R", f"{PORTA}:127.0.0.1:{PORTA}", VPS], creationflags=SEM_JANELA | DETACHED,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(6)
    return p.pid


def _avisar(texto):
    try:
        sys.path.insert(0, r"D:\video-fila")
        import avisos
        avisos.enviar(texto, origem="argon", importante=False, chave="<SEGREDO_REMOVIDO>" + texto[:40])
    except Exception:  # noqa: BLE001
        pass


def main():
    est = _estado()
    if "--status" in sys.argv:
        print(json.dumps({**est, "proxy_local": proxy_local_ativo(), "tunnel": tunnel_ativo()}, ensure_ascii=False, indent=1))
        return
    feitos = []
    cuidar_do_proxy(est, feitos)
    t = tunnel_ativo()
    if t is False:
        est["tunnel_pid"] = subir_tunnel(est)
        t2 = tunnel_ativo()
        feitos.append(f"túnel {'restaurado' if t2 else 'NÃO voltou'} (pid {est['tunnel_pid']})")
    elif t is None:
        feitos.append("VPS não respondeu ao ssh (túnel não conferido)")
    if t is not None:
        ok20133 = vps_20133_ok()
        if ok20133 is False:
            feitos.append(f"VPS :20133 mudo -> reiniciado (agora {reiniciar_20133()})")
        est["vps_20133"] = ok20133
    est.update({"em": datetime.now().isoformat(timespec="seconds"), "proxy_local": proxy_local_ativo(),
                "tunnel": tunnel_ativo() if feitos else t, "ultimo": feitos or ["ok"]})
    _gravar(est)
    log(" | ".join(feitos) if feitos else f"ok (proxy :{PORTA} vivo, túnel na VPS)")
    if feitos and any("subiu" in f or "restaurado" in f or "NÃO" in f for f in feitos):
        _avisar("🔌 Argon: " + " | ".join(feitos))


if __name__ == "__main__":
    main()
