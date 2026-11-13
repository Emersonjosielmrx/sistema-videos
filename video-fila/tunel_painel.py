"""tunel_painel.py — deixa o painel :8790 (Central de Vídeos) acessível de qualquer lugar (dona 25/10/2026: "de qualquer
lugar da internet e não só nesse PC").

O painel continua no PC1 (ele lê os arquivos e processos daqui). Este script mantém um túnel SSH reverso até a
hermes-prod: lá, 127.0.0.1:8099 cai no 127.0.0.1:8790 deste PC, e o Traefik publica em
https://videos.opus-sem-limites.com.br (/opt/traefik-config/dynamic/videos.yml). Nenhuma porta da casa fica aberta.
Quem chega pelo túnel vem com X-Forwarded-For → o painel trata como "de fora" e pede a chave (estado\\painel_chave.txt).

Tarefa do Windows PainelTunel (ao ligar + a cada 5 min; só uma cópia roda, pela trava). Caiu a conexão: religa em 15 s.
Log em logs\\tunel_painel.log. Só biblioteca padrão.
"""
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
LOG = BASE / "logs" / "tunel_painel.log"
TRAVA = BASE / "estado" / "tunel_painel.lock"
SSH = r"C:\Program Files\Git\usr\bin\ssh.exe"
PORTA_VPS, PORTA_PAINEL = 8099, 8790
SEM_JANELA = 0x08000000


def log(m):
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        if LOG.exists() and LOG.stat().st_size > 500_000:
            LOG.write_text(LOG.read_text(encoding="utf-8", errors="replace")[-100_000:], encoding="utf-8")
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now():%d/%m %H:%M:%S}] {m}\n")
    except OSError:
        pass


def outra_viva():
    """Trava com o PID: se o dono da trava ainda existe, esta cópia sai."""
    try:
        pid = int(TRAVA.read_text().strip())
        r = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True,
                           creationflags=SEM_JANELA)
        return str(pid) in r.stdout and pid != os.getpid()
    except (OSError, ValueError):
        return False


def main():
    if outra_viva():
        return
    TRAVA.parent.mkdir(parents=True, exist_ok=True)
    TRAVA.write_text(str(os.getpid()))
    log("túnel iniciado")
    while True:
        t0 = time.time()
        p = subprocess.run([SSH, "-N", "-o", "BatchMode=yes", "-o", "ExitOnForwardFailure=yes", "-o", "ServerAliveInterval=20",
                            "-o", "ServerAliveCountMax=3", "-o", "ConnectTimeout=15", "-o", "LogLevel=ERROR",
                            "-R", f"127.0.0.1:{PORTA_VPS}:127.0.0.1:{PORTA_PAINEL}", "hermes-prod"],
                           capture_output=True, text=True, creationflags=SEM_JANELA)
        erro = (p.stderr or "").strip().splitlines()
        erro = [x for x in erro if "post-quantum" not in x and "store now" not in x and "openssh.com/pq" not in x]
        log(f"túnel caiu após {int(time.time() - t0)} s (código {p.returncode}) {' | '.join(erro)[-200:]}")
        if "remote port forwarding failed" in " ".join(erro).lower():
            # porta ainda presa por uma sessão velha do lado da VPS: ela expira sozinha (ServerAlive), espera mais
            time.sleep(60)
        time.sleep(15)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
