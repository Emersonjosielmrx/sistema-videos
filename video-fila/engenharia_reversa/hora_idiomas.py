"""hora_idiomas.py — Fable 29/10 (ER_04 tarefa 1): a que hora LOCAL do país os canais de língua recebem os Shorts?
Lê só o ledger (publish_at em UTC) e converte pro fuso de cada idioma; cruza com views de 48 h (medidas_48h).
python D:\video-fila\engenharia_reversa\hora_idiomas.py
"""
import json
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

if sys.stdout:  # pythonw (tarefa agendada) não tem stdout

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
POST = Path(r"D:\postador-de-videos")
FUSO = {"inovare_ita": ("it", 1), "inovare_ind": ("id", 7), "inovare_ru": ("ru", 3), "inovare_thai": ("th", 7),
        "inovare_hindi": ("hi", 5.5), "inovare_viet": ("vi", 7), "inovare_french": ("fr", 1), "inovare_eng": ("en", -5)}
med = json.load(open(POST / "config" / "telegram_estado.json", encoding="utf-8")).get("medidas_48h") or {}
slug_por_canal = {}
for ln in (POST / "logs" / "uploads_ledger.jsonl").read_text("utf-8").splitlines():
    try:
        r = json.loads(ln)
    except ValueError:
        continue
    vid, pub = r.get("video_id"), r.get("publish_at")
    if not vid or not pub:
        continue
    m = med.get(vid) or {}
    canal = m.get("canal") or r.get("canal_slug") or r.get("canal")
    if canal not in FUSO:
        continue
    idioma, off = FUSO[canal]
    try:
        dt = datetime.fromisoformat(pub.replace("Z", "+00:00")).astimezone(timezone(timedelta(hours=off)))
    except ValueError:
        continue
    slug_por_canal.setdefault(canal, []).append((dt, m.get("views"), r.get("projeto"), r.get("tipo")))

print("canal | idioma | n | hora local (mediana) | distribuição das horas | views 48 h mediana | % zero | dias da semana")
for canal, lst in sorted(slug_por_canal.items()):
    horas = [d.hour for d, *_ in lst]
    vs = [v for _, v, *_ in lst if v is not None]
    hc = Counter(horas)
    dias = Counter(d.strftime("%a") for d, *_ in lst)
    print(f"  {canal:<14} {FUSO[canal][0]:<3} {len(lst):>3} | {statistics.median(horas):>4.0f} h | "
          f"{' '.join(f'{h}h:{n}' for h, n in sorted(hc.items()))} | "
          f"{statistics.median(vs) if vs else float('nan'):>5.0f} | {sum(v == 0 for v in vs) / len(vs) if vs else 0:>4.0%} | "
          f"{' '.join(f'{k}:{n}' for k, n in dias.most_common())}")
# views por faixa de hora local (todos os idiomas mortos juntos)
print("\nhora LOCAL x views (it/id/ru/th/hi juntos, só com views):")
g = defaultdict(list)
for canal, lst in slug_por_canal.items():
    if FUSO[canal][0] in ("it", "id", "ru", "th", "hi"):
        for d, v, *_ in lst:
            if v is not None:
                g[(d.hour // 3) * 3].append(v)
for h in sorted(g):
    vs = g[h]
    print(f"  {h:>2}–{h + 2:>2} h  n={len(vs):>3}  mediana {statistics.median(vs):>4.0f}  >=100: {sum(v >= 100 for v in vs)}")
