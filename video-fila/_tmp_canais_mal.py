import json, sys
from datetime import datetime, timedelta
sys.path.insert(0, r"D:\postador-de-videos\bin")
import politica
H = r"D:\postador-de-videos\painel\historico.jsonl"
ini, fim = {}, {}
corte = (datetime.now() - timedelta(days=7)).isoformat()
for l in open(H, encoding="utf-8"):
    try:
        r = json.loads(l)
    except ValueError:
        continue
    s, ts = r.get("slug"), r.get("ts") or ""
    if ts < corte:
        continue
    ini.setdefault(s, r)
    fim[s] = r
# token vivo por slug (canais.json liga slug -> creds)
c = json.load(open(r"D:\postador-de-videos\config\canais.json", encoding="utf-8"))
it = c.get("canais", c) if isinstance(c, dict) else c
it = list(it.values()) if isinstance(it, dict) else it
creds = {x["id"]: x for x in politica.carregar_creds()}
linhas = []
for s in fim:
    a, b = ini[s], fim[s]
    dias = max(1, (datetime.fromisoformat(b["ts"]) - datetime.fromisoformat(a["ts"])).days)
    ganho = (b.get("views", 0) - a.get("views", 0)) / dias
    vids = max(1, b.get("videos", 0) - a.get("videos", 0))
    ch = next((x for x in it if x.get("slug") == s), {})
    tok = any((creds.get(i) or {}).get("refresh_token") for i in ch.get("creds") or [])
    linhas.append((ganho, s, ch.get("nome"), b.get("views", 0), b.get("videos", 0) - a.get("videos", 0), tok))
for g, s, n, v, nv, tok in sorted(linhas):
    print(f"{g:8.0f} views/dia | {s:22} | {str(n)[:24]:24} | total {v:7} | +{nv} vídeos em 7 d | token {'sim' if tok else 'NAO'}")
