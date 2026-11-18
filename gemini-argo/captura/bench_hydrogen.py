"""17/11: Gemini 4 Hydrogen (ag-hydrogen) na mesma bancada de código real do Argon/Gemini (hibridos_real.py)."""
import json
import sys

import hibridos_real as hr

hb = hr.hb
MODELO = sys.argv[1] if len(sys.argv) > 1 else "ag-hydrogen"
feito = json.loads(hb.PLACAR.read_text("utf-8")) if hb.PLACAR.exists() else {}
for t in hr.TAREFAS:
    if t not in feito.get(MODELO, {}):
        hb.rodar(MODELO, t)
placar = json.loads(hb.PLACAR.read_text("utf-8"))
for m in (MODELO, "gemini-4-argon", "agy/gemini-3.8-flash-high", "hx-maos-gemini"):
    d = placar.get(m, {})
    print(f"{m:30} {sum(x['ok'] for x in d.values()):>2}/{sum(x['total'] for x in d.values()):<2} "
          f"{sum(x['tempo'] for x in d.values()):>5}s  " + "  ".join(f"{t}:{x['ok']}/{x['total']}" for t, x in d.items()))
