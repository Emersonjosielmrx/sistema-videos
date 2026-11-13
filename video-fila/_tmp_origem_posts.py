import json, collections, glob, os, re
from datetime import datetime, timedelta
corte = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
# catálogo: o que saiu do YouTube e foi pra TikTok/Insta
cat = r"D:\postador-de-videos\estado\catalogo.json"
origem = collections.Counter()
try:
    c = json.load(open(cat, encoding="utf-8"))
    itens = c.values() if isinstance(c, dict) else c
    for v in itens:
        if not isinstance(v, dict):
            continue
        for plat in ("tiktok", "instagram"):
            p = (v.get("postado") or {}).get(plat) or v.get(plat)
            if p and str(p.get("em", p) if isinstance(p, dict) else p)[:10] >= corte:
                origem[(plat, v.get("projeto") or v.get("origem") or v.get("tipo") or "?")] += 1
except Exception as e:
    print("catalogo:", e)
for (plat, o), n in sorted(origem.items()):
    print(f"{plat:10} {o:25} {n}")
print("total", sum(origem.values()))
