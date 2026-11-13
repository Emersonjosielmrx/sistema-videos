"""Diagnóstico de ALCANCE dos Shorts de parceiro (22/10, prioridade 1 da lista do recap): views na 1ª leitura (48-96 h,
medidas_48h do notificar_telegram + metricas_studio do metricas_rede, incluindo o lote) cruzadas com canal, nicho,
parceiro de origem, narrador, duração e título (postar.json da ficha, achada pelo caminho do ledger)."""
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

if sys.stdout:  # pythonw (tarefa agendada) não tem stdout

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
POST = Path(r"D:\postador-de-videos")
med = json.load(open(POST / "config" / "telegram_estado.json", encoding="utf-8")).get("medidas_48h") or {}
ms = json.load(open(POST / "_analise" / "metricas_studio.json", encoding="utf-8"))
led = {}
for ln in (POST / "logs" / "uploads_ledger.jsonl").read_text("utf-8").splitlines():
    try:
        r = json.loads(ln)
    except ValueError:
        continue
    if r.get("video_id"):
        led[r["video_id"]] = r
# views: 1ª leitura (48-96 h); o metricas_studio completa o que o telegram não mediu
views = {vid: (m["views"], m.get("canal")) for vid, m in med.items() if m.get("views") is not None}
for vid, m in ms.items():
    if isinstance(m, dict) and vid not in views and m.get("views") is not None and 40 <= (m.get("idade_h") or 0) <= 120:
        views[vid] = (m["views"], m.get("canal_slug"))
linhas = []
for vid, (v, canal) in views.items():
    r = led.get(vid) or {}
    if r.get("projeto") != "parceiro":
        continue
    ficha = {}
    try:
        ficha = json.loads((Path(r["caminho"]).parent / "postar.json").read_text(encoding="utf-8"))
    except (KeyError, OSError, ValueError, TypeError):
        pass
    linhas.append({"vid": vid, "views": float(v), "canal": canal or r.get("canal"), "nicho": ficha.get("midia") or "?",
                   "parceiro": ficha.get("parceiro") or "?", "narrador": ficha.get("narrador") or "(sem clone)",
                   "estilo": ficha.get("estilo_titulo") or "?", "titulo": ficha.get("titulo") or "",
                   "idioma": ficha.get("idioma") or "?"})
print(f"Shorts de PARCEIRO com views de 48-96 h: {len(linhas)}")
if not linhas:
    sys.exit()
vs = sorted(x["views"] for x in linhas)
print(f"  mediana {statistics.median(vs):.0f} | média {statistics.mean(vs):.0f} | zero {sum(v == 0 for v in vs)} "
      f"| >=100 {sum(v >= 100 for v in vs)} | >=5000 {sum(v >= 5000 for v in vs)} | máx {vs[-1]:.0f}")


def tabela(campo, minimo=2):
    g = defaultdict(list)
    for x in linhas:
        g[x[campo]].append(x["views"])
    print(f"\npor {campo} (n >= {minimo}): n | mediana | média | % zero | >=5000")
    for k, lst in sorted(g.items(), key=lambda kv: -statistics.mean(kv[1])):
        if len(lst) >= minimo:
            print(f"  {str(k)[:30]:<30} {len(lst):>3} | {statistics.median(lst):>6.0f} | {statistics.mean(lst):>7.0f} | "
                  f"{sum(v == 0 for v in lst) / len(lst):>4.0%} | {sum(v >= 5000 for v in lst)}")


for c in ("canal", "nicho", "parceiro", "narrador", "estilo", "idioma"):
    tabela(c)
print("\nos 8 melhores:")
for x in sorted(linhas, key=lambda x: -x["views"])[:8]:
    print(f"  {x['views']:>7.0f}  {x['canal']:<22} {x['nicho']:<12} {x['parceiro']:<16} {x['titulo'][:60]}")
