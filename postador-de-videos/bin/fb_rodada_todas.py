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
# 23/11: antes de disparar, conserta sozinho (ponte caída, trava morta) e pula a conta que já tem rodada no ar
# (dona: "quero poder fechar o chat e saber que tudo vai receber postagem"). FB_SEM_SAUDE=1 pula esta etapa.
if os.environ.get("FB_SEM_SAUDE") != "1":
    try:
        sys.path.insert(0, str(BIN))
        import fb_saude
        prontas = fb_saude.conferir()
        contas = [c for c in contas if prontas.get(c, True)]
    except Exception as e:  # noqa: BLE001
        print(f"[saude] falhou ({e}); sigo com todas", flush=True)
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

# 24/11 (noite, criacao.2): a criação de Página perdia a vez porque a tarefa de 50 min caía com a conta postando
# (9x em 4 dias). Logo que a rodada da conta termina, dispara o criador SÓ dela, solto (não segura a próxima rodada).
# O próprio fb_criar_fila respeita limite do dia (3), intervalo de 3 h, trava da conta e bloqueio — nada sobe aqui.
# FB_SEM_CRIAR_APOS=1 desliga.
if os.environ.get("FB_SEM_CRIAR_APOS") != "1":
    for c in procs:
        try:
            subprocess.Popen([PY, "-u", str(BIN / "fb_criar_fila.py"), "--conta", c], cwd=str(BIN),
                             stdout=open(BIN.parent / "logs" / f"fb_criar_{c}.log", "a", encoding="utf-8"),
                             stderr=subprocess.STDOUT, env=dict(os.environ, PYTHONUTF8="1"),
                             creationflags=0x08000000 | 0x01000000, close_fds=True)
            print(f"[criar] {c}: criador disparado após a rodada", flush=True)
        except Exception as e:  # noqa: BLE001
            print(f"[criar] {c}: não disparou ({e})", flush=True)
