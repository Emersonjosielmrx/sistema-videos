#!/usr/bin/env python3
r"""og_manter.py — mantém o Opus do Genspark NO AR para o seletor do Claude Code (molde do argon_manter.py).

Caminho: Claude Code -> proxy da VPS (:20133, modelo "genspark-opus-5-5") -> túnel ssh -R 20165 -> genspark_http.py
(PC, :20165) -> pool de contas do Genspark (genspark.py). A porta 20165 da VPS é fechada para fora por
fechar-20165.service (o sshd de lá tem GatewayPorts yes e o front não tem chave).

A cada passada (tarefa OpusGratisManter: a cada 5 min e ao entrar no Windows):
  1. :20165 local não responde -> sobe genspark_http.py escondido (logs genspark_http.out/err.log).
  2. a VPS não alcança a :20165 -> recria o túnel (ssh -N -R, sem janela).

    python og_manter.py            # uma passada
    python og_manter.py --status   # só mostra
"""
import sys as _sys
_sys.path.append(r"D:\hipercool-materiais\comum")
import sem_janela  # noqa: E402,F401 — nenhum processo filho abre janela na tela
import json
import os
import subprocess
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

SSH_EXE = r"C:\Program Files\Git\usr\bin\ssh.exe" if os.path.exists(r"C:\Program Files\Git\usr\bin\ssh.exe") else "ssh"
AQUI = Path(__file__).resolve().parent
PYW = Path(r"C:\Users\SEU_USUARIO\AppData\Local\Programs\Python\Python313\pythonw.exe")
PORTA = 20165
VPS = "hermes-bloqueio"
ESTADO = AQUI / "og_manter.json"
OUT, ERR = AQUI / "genspark_http.out.log", AQUI / "genspark_http.err.log"
SEM_JANELA, DETACHED = 0x08000000, 0x00000008


def log(m):
    print(f"[{datetime.now():%d/%m %H:%M:%S}] {m}", flush=True)


def front_vivo():
    """3 tentativas: com o PC a 100% de CPU uma resposta pode levar ~20 s (lição do argon_manter)."""
    for i in range(3):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{PORTA}/v1/models", timeout=20) as r:
                if b"genspark" in r.read():
                    return True
        except Exception:  # noqa: BLE001
            pass
        if i < 2:
            time.sleep(10)
    return False


def subir_front():
    with OUT.open("a", encoding="utf-8") as o, ERR.open("a", encoding="utf-8") as e:
        p = subprocess.Popen([str(PYW), "-X", "utf8", str(AQUI / "genspark_http.py")], cwd=str(AQUI),
                             stdout=o, stderr=e, creationflags=SEM_JANELA | DETACHED)
    for _ in range(45):
        time.sleep(2)
        if p.poll() is not None:
            return None
        if front_vivo():
            return p.pid
    return p.pid


def tunel_ativo():
    """True/False pelo que a VPS enxerga; None = ssh falhou (não dá para saber)."""
    try:
        r = subprocess.run([SSH_EXE, "-n", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "-o", "LogLevel=ERROR", VPS,
                            f"curl -s --max-time 15 http://127.0.0.1:{PORTA}/v1/models"],
                           capture_output=True, text=True, timeout=45, creationflags=SEM_JANELA)
        if r.returncode == 255:
            return None
        return "genspark" in r.stdout
    except Exception:  # noqa: BLE001
        return None


def _tuneis_vivos():
    """PIDs dos ssh.exe vivos que fazem ESTE túnel (-R 127.0.0.1:20165). 31/10 (achado pelo genspark-ajudante,
    corrigido pelo pc1): o PID salvo no og_manter.json ficava velho (7928 salvo x 9476 real) e o taskkill podia matar
    outro processo que herdasse o número. Agora só se mata o que for, de fato, o ssh deste túnel."""
    r = subprocess.run(["powershell", "-NoProfile", "-Command",
                        "Get-CimInstance Win32_Process -Filter \"Name='ssh.exe'\" | "
                        f"Where-Object {{ $_.CommandLine -match '-R 127.0.0.1:{PORTA}:' }} | "
                        "ForEach-Object { $_.ProcessId }"],
                       capture_output=True, text=True, timeout=30, creationflags=SEM_JANELA)
    return [int(x) for x in r.stdout.split() if x.strip().isdigit()]


def subir_tunel(est):
    for pid in _tuneis_vivos():  # ssh antigo vivo mas sem entregar nada: derruba (só o deste túnel) antes de recriar
        subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True, creationflags=SEM_JANELA)
    p = subprocess.Popen([SSH_EXE, "-N", "-o", "BatchMode=yes", "-o", "ServerAliveInterval=30", "-o", "ServerAliveCountMax=3",
                          "-o", "ExitOnForwardFailure=yes", "-o", "LogLevel=ERROR",
                          "-R", f"127.0.0.1:{PORTA}:127.0.0.1:{PORTA}", VPS],
                         creationflags=SEM_JANELA | DETACHED, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(6)
    return p.pid if p.poll() is None else None  # morreu na hora (porta da VPS ocupada, ssh recusado): não é túnel


def main():
    try:
        est = json.loads(ESTADO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        est = {}
    if "--status" in sys.argv:
        print(json.dumps({**est, "front": front_vivo(), "tunel": tunel_ativo()}, ensure_ascii=False, indent=1))
        return
    feitos = []
    vivo = front_vivo()
    if not vivo:
        est["front_pid"] = subir_front()
        vivo = bool(est["front_pid"])
        feitos.append(f"front :{PORTA} {'subiu (pid ' + str(est['front_pid']) + ')' if est['front_pid'] else 'NÃO subiu (ver genspark_http.err.log)'}")
    # 31/10: o teste do túnel passa PELO front (curl na VPS -> túnel -> front). Com o front fora/lento ele dá False e o
    # túnel saudável era derrubado, cortando os pedidos em andamento. Só confere o túnel com o front respondendo.
    t = tunel_ativo() if vivo else None
    if t is False:
        t = (time.sleep(20), tunel_ativo())[1]  # confirma antes de mexer: uma falha só não derruba o túnel
    if t is False:
        est["tunel_pid"] = subir_tunel(est)
        feitos.append(f"túnel {'restaurado' if tunel_ativo() else 'NÃO voltou'} (pid {est['tunel_pid']})")
    elif t is None:
        feitos.append("VPS não respondeu ao ssh (túnel não conferido)")
    est.update(em=datetime.now().isoformat(timespec="seconds"), ultimo=feitos or ["ok"])
    ESTADO.write_text(json.dumps(est, ensure_ascii=False, indent=1), encoding="utf-8")
    log(" | ".join(feitos) if feitos else f"ok (front :{PORTA} vivo, túnel na VPS)")


if __name__ == "__main__":
    main()
