# D:\sistema\catalogo\maquinas.py  (copia mestre: /mnt/win-bootcamp/claude-central/sistema/maquinas.py)
# OBRA etapa 3 - confere o ssh config DESTA maquina contra a lista unica maquinas.json.
#   python maquinas.py --conferir     -> linhas para a ronda ("!!" se algum host esta diferente)
import json, os, re, sys
from pathlib import Path
if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = Path(__file__).resolve().parent
M = json.loads((AQUI / "maquinas.json").read_text(encoding="utf-8"))["maquinas"]
cfg = Path(os.path.expanduser("~")) / ".ssh" / "config"
h, cur = {}, None
for l in cfg.read_text(encoding="utf-8", errors="ignore").splitlines():
    l = l.strip()
    if not l or l.startswith("#"):
        continue
    k, _, v = l.partition(" ")
    if k.lower() == "host":
        cur = v.split(); [h.setdefault(n, {}) for n in cur]
    elif cur:
        for n in cur:
            h[n].setdefault(k.lower(), v.strip())
dif = []
for n, m in M.items():
    if n not in h:
        continue
    d = h[n]
    for campo, val in (("hostname", m["hostname"]), ("user", m["user"]), ("port", str(m["port"]))):
        atual = d.get(campo, "22" if campo == "port" else None)
        if val and atual and str(atual) != str(val):
            dif.append(f"{n}: {campo} {atual} (deveria ser {val})")
print(f"[MAQUINAS] {len(M)} na lista unica | ssh config desta maquina: {len([n for n in M if n in h])} conferidas | diferentes: {len(dif)}")
for x in dif:
    print("  !! ssh config diferente da lista unica: " + x)
