"""Manda um pedido ao Very Good FFmpeg e acompanha: python teste_vgf.py <pedido.json>"""
import json, sys, time, urllib.request, urllib.error
K = open(r"D:\hipercool-materiais\fluxo-anuncio-api\vgf_chave.txt").read().split()[0]


def chama(m, u, c=None):
    r = urllib.request.Request(u, method=m, data=json.dumps(c).encode() if c else None,
                               headers={"Authorization": "Bearer " + K, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(r, timeout=60) as x:
            return x.status, json.loads(x.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


st, r = chama("POST", "https://verygoodffmpeg.com/api/ffmpeg", json.load(open(sys.argv[1], encoding="utf-8")))
d = r.get("data") or {}
print("criar:", st, d.get("id"), d.get("status"), json.dumps(r)[:300] if st >= 300 else "", flush=True)
if not d.get("id"):
    sys.exit(1)
for i in range(100):
    time.sleep(6)
    st, r = chama("GET", f"https://verygoodffmpeg.com/api/jobs/{d['id']}")
    d = r.get("data") or {}
    print(i, d.get("status"), flush=True)
    if d.get("status") in ("succeeded", "failed", "error", "timed_out"):
        print(json.dumps({k: d.get(k) for k in ("status", "error_message", "output_files", "total_input_bytes", "total_output_bytes", "started_at", "finished_at")}, ensure_ascii=False)[:3000])
        break
