"""launch_daemon.py — Lanca auto_producer.py totalmente destacado.

Cria um processo Windows sem console, sem ligacao com o shell pai.
Sobrevive ao fechamento do Claude Code, do bash, e ate reboot (se tarefa agendada).

Uso:
    python launch_daemon.py [--max N] [--generos g1,g2]
"""
import os
import sys
import subprocess
from pathlib import Path

# Tudo relativo a ESTA pista (prod/beta/teste) — sem depender de outro projeto.
PROJECT = Path(__file__).resolve().parent
SCRIPT = PROJECT / "auto_producer.py"

# pythonw do venv da propria pista; env HEF_PYTHONW pode sobrepor.
_env_pw = os.environ.get("HEF_PYTHONW")
_local_pw = PROJECT / "venv" / "Scripts" / "pythonw.exe"
if _env_pw and Path(_env_pw).exists():
    PYTHONW = Path(_env_pw)
elif _local_pw.exists():
    PYTHONW = _local_pw
else:
    # fallback: pythonw ao lado do python atual, senao o proprio python
    _cand = Path(sys.executable).with_name("pythonw.exe")
    PYTHONW = _cand if _cand.exists() else Path(sys.executable)

if not PYTHONW.exists():
    print(f"pythonw nao encontrado: {PYTHONW}")
    sys.exit(1)

cmd = [str(PYTHONW), str(SCRIPT)] + sys.argv[1:]
print(f"Lancando: {' '.join(cmd)}")

DETACHED_PROCESS = 0x00000008
CREATE_NEW_PROCESS_GROUP = 0x00000200
CREATE_NO_WINDOW = 0x08000000

proc = subprocess.Popen(
    cmd,
    creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW,
    close_fds=True,
    stdin=subprocess.DEVNULL,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)
print(f"Daemon PID: {proc.pid}")
print("Para parar: taskkill /PID {pid} /F")