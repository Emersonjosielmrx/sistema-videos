"""sonda_studio_lenta.py - abre um perfil no Studio do canal, espera bem mais e registra para onde o Google mandou
(prints em postador-de-videos/logs/yt_web). Nao envia nada. Uso: sonda_studio_lenta.py <pasta> <UC...> <porta>"""
import sys
import time

sys.path.insert(0, r"D:\postador-de-videos\bin")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import youtube_web_poster as W  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

pasta, uc, porta = sys.argv[1], sys.argv[2], int(sys.argv[3])
proc = W.abrir_chrome(pasta, porta)
with sync_playwright() as p:
    br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
    pg = br.contexts[0].new_page()
    pg.goto(f"https://studio.youtube.com/channel/{uc}", wait_until="domcontentloaded", timeout=90000)
    for i in range(6):
        time.sleep(5)
        print(f"{(i + 1) * 5:3}s {pg.url[:150]}", flush=True)
    print("print:", W._shot(pg, "sonda_lenta"))
    try:
        print("texto:", pg.locator("body").inner_text(timeout=5000)[:400].replace("\n", " | "))
    except Exception as ex:  # noqa: BLE001
        print("texto: erro", ex)
    pg.close()
    W.soltar(br, proc)
W.fechar_chrome(proc)
