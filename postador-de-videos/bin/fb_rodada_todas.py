"""Rodada da hora em TODAS as contas que têm Páginas ativas (21/11). Um processo por conta, em paralelo, cada um no
Chrome e na saída dela; espera todos e junta a saída no log da tarefa. A conta msenergypara fica de fora (a Página
MS energy posta pelo postar_ms_energy, com os vídeos do Instagram).
    python fb_rodada_todas.py
"""
import json, os, subprocess, sys
from pathlib import Path

BIN = Path(__file__).resolve().parent
CFG = BIN.parent / "config" / "facebook_paginas.json"
PY = r"D:\hipercool-videos\venv\Scripts\python.exe"
if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

cfg = json.loads(CFG.read_text(encoding="utf-8"))
contas = sorted({p["conta"] for p in cfg["paginas"].values() if not p.get("pausada")} - {"msenergypara"})
print("contas na rodada:", contas, flush=True)
procs = {}
for c in contas:
    procs[c] = subprocess.Popen([PY, "-u", str(BIN / "postar_facebook_paginas.py"), "--horario", "--conta", c],
                                cwd=str(BIN), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                encoding="utf-8", errors="replace", env=dict(os.environ, PYTHONUTF8="1"),
                                creationflags=0x08000000)
for c, p in procs.items():
    try:
        out, _ = p.communicate(timeout=3300)
    except subprocess.TimeoutExpired:
        subprocess.run(["taskkill", "/PID", str(p.pid), "/T", "/F"], capture_output=True)
        out = "(rodada passou de 55 min — encerrada)"
    linhas = [l for l in out.splitlines() if not l.startswith("catalogo:")]
    print(f"--- {c} ---", flush=True)
    print("\n".join(linhas[-25:]), flush=True)
