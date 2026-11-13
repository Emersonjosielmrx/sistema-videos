"""ExploraÃ§Ã£o rÃ¡pida (28/10): bimodalidade dos Shorts de parceiro por hora, data, duraÃ§Ã£o, impressÃµes."""
import json, statistics, sys
from collections import defaultdict
from datetime import datetime, timezone, timedelta
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
views = {vid: m["views"] for vid, m in med.items() if m.get("views") is not None}
for vid, m in ms.items():
    if isinstance(m, dict) and vid not in views and m.get("views") is not None and 40 <= (m.get("idade_h") or 0) <= 120:
        views[vid] = m["views"]
L = []
BR = timezone(timedelta(hours=-3))
for vid, v in views.items():
    r = led.get(vid) or {}
    if r.get("projeto") != "parceiro":
        continue
    f = {}
    try:
        f = json.loads((Path(r["caminho"]).parent / "postar.json").read_text(encoding="utf-8"))
    except Exception:
        pass
    pa = r.get("publish_at") or r.get("ts")
    try:
        dt = datetime.fromisoformat(pa.replace("Z", "+00:00")).astimezone(BR)
    except Exception:
        dt = None
    st = ms.get(vid) if isinstance(ms.get(vid), dict) else {}
    L.append(dict(vid=vid, v=float(v), canal=r.get("canal_id"), hora=dt.hour if dt else None,
                  dia=dt.strftime("%m-%d") if dt else "?", dur=f.get("duracao") or f.get("duracao_s"),
                  imp=st.get("impressoes"), ctr=st.get("ctr"), ret=st.get("ret30"), cont=st.get("continuaram"),
                  chaves=sorted(f.keys()), fonte=f.get("fonte"), cat=f.get("categoria"), rev=str(f.get("revisao"))[:20], obra=bool(f.get("obra"))))
print("n", len(L))
hist = defaultdict(int)
for x in L:
    b = 0 if x["v"] == 0 else 1 if x["v"] < 10 else 2 if x["v"] < 100 else 3 if x["v"] < 500 else 4 if x["v"] < 2000 else 5
    hist[b] += 1
print("faixas 0|1-9|10-99|100-499|500-1999|2000+:", [hist[i] for i in range(6)])
def tab(k):
    g = defaultdict(list)
    for x in L:
        g[x[k]].append(x["v"])
    print(f"\npor {k}: n | mediana | %>=500")
    for kk in sorted(g, key=lambda z: str(z)):
        l = g[kk]
        print(f"  {str(kk):<10} {len(l):>3} | {statistics.median(l):>6.0f} | {sum(v>=500 for v in l)/len(l):.0%}")
tab("fonte"); tab("cat"); tab("obra"); tab("rev")
print("\nchaves da ficha:", L[0]["chaves"])
com = [x for x in L if x["imp"] is not None]
print("\ncom impressÃµes:", len(com))
for x in sorted(com, key=lambda x: -x["v"])[:6] + sorted(com, key=lambda x: x["v"])[:6]:
    print(f"  {x['v']:>6.0f} imp {x['imp']} ctr {x['ctr']} ret30 {x['ret']} cont {x['cont']} {x['canal']}")
# canais bimodais: quantos com >=500 e <=10 no mesmo canal
g = defaultdict(list)
for x in L:
    g[x["canal"]].append(x["v"])
print("\nmesmo canal: alto(>=500)/baixo(<=10)")
for c, l in sorted(g.items()):
    a = sum(v >= 500 for v in l); b = sum(v <= 10 for v in l)
    if a and b:
        print(f"  {c:<30} alto {a} baixo {b} de {len(l)}")


print("\n=== reuso da mesma fonte ===")
from collections import Counter
cnt = Counter(x["fonte"] for x in L if x["fonte"])
for nome, cond in (("fonte usada 1 vez", lambda x: cnt[x["fonte"]] == 1), ("fonte usada 2+ vezes", lambda x: cnt[x["fonte"]] >= 2)):
    l = [x["v"] for x in L if x["fonte"] and cond(x)]
    print(f"  {nome:<22} n {len(l):>3} | mediana {statistics.median(l):>6.0f} | >=500 {sum(v>=500 for v in l)/len(l):.0%} | <=10 {sum(v<=10 for v in l)/len(l):.0%}")
