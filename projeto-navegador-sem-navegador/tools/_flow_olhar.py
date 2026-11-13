import sys, time, subprocess
from filelock import FileLock
from playwright.sync_api import sync_playwright
trava = FileLock(r"D:\veo\beta\logs\.cdp_lock_9250", timeout=5); trava.acquire()
cap = subprocess.Popen([sys.executable, "-u", r"D:\projeto-navegador-sem-navegador\tools\capturar_cdp.py", "9250",
                        "--filtro", "batchexecute|aisandbox|upload", "--saida", r"D:\projeto-navegador-sem-navegador\capturas\flow_carga.jsonl", "--segundos", "40"])
time.sleep(4)
with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://127.0.0.1:9250")
    pg = [x for c in b.contexts for x in c.pages if "flow" in x.url][0]
    pg.reload(wait_until="domcontentloaded"); pg.wait_for_timeout(15000)
    pg.screenshot(path=r"D:\projeto-navegador-sem-navegador\capturas\telas\flow_seebotsia.png")
    print(pg.url); print((pg.evaluate("() => document.body.innerText") or "")[:1500])
cap.wait(); trava.release()
