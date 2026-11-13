import json, collections
from datetime import datetime, timedelta
L = r"D:\video-fila\estado\avisos.jsonl"
cont = collections.Counter(); env = collections.Counter(); ult = {}
corte = (datetime.now() - timedelta(days=7)).isoformat()
for ln in open(L, encoding="utf-8"):
    try:
        d = json.loads(ln)
    except Exception:
        continue
    q = str(d.get("em") or "")
    if q and q < corte[:len(q)]:
        continue
    o = d.get("origem") or "?"
    cont[o] += 1
    if d.get("situacao") == "enviado":
        env[o] += 1
    ult[o] = (q, (d.get("texto") or d.get("msg") or "").replace("\n", " ")[:220])
print(json.dumps({"campos_exemplo": list(json.loads(open(L, encoding='utf-8').readline()).keys())}))
for o, n in cont.most_common():
    print(f"{n}\t{env[o]}\t{o}\t{ult[o][0][:16]}\t{ult[o][1]}")


