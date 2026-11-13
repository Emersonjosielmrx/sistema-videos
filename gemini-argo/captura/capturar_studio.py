"""Abre o Studio de 1 canal UMA vez: salva cookies .youtube.com e as chamadas youtubei que a aba Analytics faz."""
import gzip
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, r"D:\logins-google")
sys.path.insert(0, r"D:\postador-de-videos\bin\netbooks")
import cofre
import chrome_conta
from playwright.sync_api import sync_playwright

email, cid = sys.argv[1], sys.argv[2]
SAIDA = Path(r"D:\gemini-argo\captura")
COOKIES = Path(r"D:\gemini-argo\cookies_youtube")
COOKIES.mkdir(exist_ok=True)

chrome_conta._liberar_ram()
porta, proc = cofre.abrir(email, url="about:blank", visivel=False)
br = None
chamadas = []
try:
    with sync_playwright() as pw:
        br = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
        ctx = br.contexts[0]
        pg = ctx.new_page()

        def on_req(req):
            if req.method == "POST" and "studio.youtube.com/youtubei" in req.url:
                corpo = req.post_data_buffer or b""
                if corpo[:2] == b"\x1f\x8b":
                    corpo = gzip.decompress(corpo)
                chamadas.append({"url": req.url, "headers": dict(req.headers), "post": corpo.decode("utf-8", "replace")})

        ctx.on("request", on_req)
        for url in [f"analytics/{a}/period-default" for a in ("tab-overview", "tab-reach_viewers", "tab-interest_viewers")] + ["videos/upload"]:
            try:
                pg.goto(f"https://studio.youtube.com/channel/{cid}/{url}", wait_until="domcontentloaded", timeout=90000)
            except Exception as e:  # Studio às vezes troca de rota sozinho no meio
                print("  aviso:", str(e).splitlines()[0][:120])
            time.sleep(12)
        todos = ctx.new_cdp_session(pg).send("Network.getAllCookies")["cookies"]
        pg.close()
finally:
    cofre.fechar(proc, br, email)

ck = {c["name"]: c["value"] for c in todos if c.get("domain", "").endswith("youtube.com")}
(COOKIES / f"{email.split('@')[0]}.json").write_text(json.dumps(ck, indent=1), "utf-8")
(SAIDA / "studio_chamadas.json").write_text(json.dumps(chamadas, ensure_ascii=False, indent=1), "utf-8")
print(f"cookies: {len(ck)} ({'SAPISID' in ck and 'ok' or 'SEM SAPISID'}) | chamadas youtubei: {len(chamadas)}")
for c in chamadas:
    print(" ", c["url"].split("?")[0].replace("https://studio.youtube.com/youtubei/v1/", ""))
