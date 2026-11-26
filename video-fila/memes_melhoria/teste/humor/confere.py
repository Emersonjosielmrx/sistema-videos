# -*- coding: utf-8 -*-
import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
B = Path(r"D:\recapd-ambientes\producao\bin")
for n in ("humor_narrador.py", "humor_narradores.json", "anime_script.py", "anime_script.py.antes_humor_26nov"):
    p = B / n
    print(f"{n:38} {'existe' if p.exists() else 'NAO existe':10} {p.stat().st_size if p.exists() else ''}")
t = (B / "anime_script.py").read_text(encoding="utf-8")
print("anime_script tem humor_narrador.polir:", "humor_narrador.polir" in t)
