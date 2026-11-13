"""Manda um pedido para a Rendi e acompanha: python teste_rendi.py <pedido.json>"""
import json, sys, time, urllib.request, urllib.error
K = open(r"D:\hipercool-materiais\fluxo-anuncio-api\rendi_chave.txt").read().split()[0]


def chama(m, u, c=None):
    r = urllib.request.Request(u, method=m, data=json.dumps(c).encode() if c else None, headers={"X-API-KEY": K, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(r, timeout=60) as x:
            return x.status, json.loads(x.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


st, r = chama("POST", "https://api.rendi.dev/v1/run-ffmpeg-command", json.load(open(sys.argv[1], encoding="utf-8")))
print("criar:", st, json.dumps(r)[:800], flush=True)
cid = r.get("command_id")
if not cid:
    sys.exit(1)
for i in range(100):
    time.sleep(6)
    st, r = chama("GET", f"https://api.rendi.dev/v1/commands/{cid}")
    print(i, r.get("status"), flush=True)
    if r.get("status") in ("SUCCESS", "FAILED"):
        print(json.dumps(r, ensure_ascii=False)[:3000])
        break
