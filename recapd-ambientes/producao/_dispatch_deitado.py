import sys, time, json
# stdout/stderr em UTF-8: a resposta do worker pode ter caracteres como '→'
# que quebravam a impressao no cp1252 do Windows (UnicodeEncodeError).
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
sys.path.insert(0, "bin")
import anime_worker_client as wc
HOST, PORT = "100.125.7.77", 8772
cand = {
    "url": "https://www.youtube.com/watch?v=Jx4UTsdeam0",
    "title": "He Was Born With Zero Magic But Became Strongest",
    "id": "Jx4UTsdeam0",
}
payload = {
    "video_url": cand["url"],
    "titulo": cand["title"],
    "modo": "deitado",
    "work_dir": "",
}
t0 = time.time()
print(f"[{time.strftime('%H:%M:%S')}] DISPARANDO deitado 100min -> worker {HOST}:{PORT}", flush=True)
res = wc.run_anime(HOST, PORT, payload, timeout=36000)
dt = time.time() - t0
print(f"[{time.strftime('%H:%M:%S')}] RESPOSTA apos {dt/60:.1f}min:", flush=True)
print(json.dumps(res, ensure_ascii=False, indent=2), flush=True)
