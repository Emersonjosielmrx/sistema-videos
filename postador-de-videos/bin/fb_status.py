"""Situação do Facebook num relance (20/11): Reels hoje x teto por Página, erros do dia, fila de criação, MS Energy.
    python fb_status.py"""
import json, sys
from datetime import datetime
from pathlib import Path

BIN = Path(__file__).resolve().parent
sys.path.insert(0, str(BIN))
import postar_facebook_paginas as p, fb_escada as e  # noqa: E402

if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
hoje = datetime.now().strftime("%Y-%m-%d")
r, c = p._ler(p.REG, {}), p._ler(p.CFG, {})
print(f"== {datetime.now():%d/%m %H:%M}")
for k, v in c["paginas"].items():
    erros = [m for q, m in (r.get("erros", {}).get(k) or {}).items() if q.startswith(hoje)]
    print(f"{v['nome']:26} hoje {p.hoje_na_pagina(r, k)}/{e.teto(k, v)}"
          + (" PAUSADA" if v.get("pausada") else "") + (f" | {len(erros)} erro(s): {erros[-1][:70]}" if erros else ""))
est = p._ler(BIN.parent / "logs" / "fb_fila_estado.json", {})
pags = est.get("paginas", {})
print(f"fila: {sum(1 for x in pags.values() if x.get('etapa') == 'pronta')} prontas, "
      f"{sum(1 for x in pags.values() if x.get('etapa') not in (None, 'pronta'))} pela metade | contas: "
      + "; ".join(f"{k}: {', '.join(f'{a}={b}' for a, b in v.items())}" for k, v in est.get("contas", {}).items()))
ms = p._ler(Path(r"D:\ms-energy\videos\postagem_log.json"), {})
fb_hoje = [k for k, x in ms.items() if str(x.get("fb", ""))[:10] == hoje]
print(f"MS energy (FB) hoje: {len(fb_hoje)} post(s)")
