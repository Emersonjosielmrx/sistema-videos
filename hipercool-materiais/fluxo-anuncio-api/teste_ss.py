"""Render direto no Shotstack (sandbox): python teste_ss.py <edicao.json> [stage|v1]"""
import json, sys, time, urllib.request, urllib.error
CH = open(r"D:\hipercool-materiais\fluxo-anuncio-api\shotstack_chaves.txt").read().split()
AMB = sys.argv[2] if len(sys.argv) > 2 else "stage"
K = CH[0] if AMB == "stage" else CH[1]
def chama(m, u, c=None):
    r = urllib.request.Request(u, method=m, data=json.dumps(c).encode() if c else None, headers={"x-api-key": K, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(r, timeout=60) as x: return x.status, json.loads(x.read())
    except urllib.error.HTTPError as e: return e.code, json.loads(e.read() or b"{}")
st, r = chama("POST", f"https://api.shotstack.io/edit/{AMB}/render", json.load(open(sys.argv[1], encoding="utf-8")))
print("criar:", st, json.dumps(r, ensure_ascii=False)[:600], flush=True)
rid = (r.get("response") or {}).get("id")
if not rid: sys.exit(1)
for i in range(120):
    time.sleep(6)
    st, r = chama("GET", f"https://api.shotstack.io/edit/{AMB}/render/{rid}")
    x = r.get("response") or {}
    print(i, x.get("status"), x.get("error", "")[:300] if x.get("error") else "", flush=True)
    if x.get("status") in ("done", "failed"):
        print(json.dumps({k: x.get(k) for k in ("status", "url", "poster", "duration", "error", "credits")}, ensure_ascii=False)); break
