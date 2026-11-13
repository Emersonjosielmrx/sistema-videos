# -*- coding: utf-8 -*-
"""watch_download.py - espera 'Scene rendered' e baixa o MP4. Nao mexe em nada
mais (o render ja foi disparado). Roda em background e escreve log."""
import asyncio, json, os, time, uuid, subprocess
os.environ["PYTHONUTF8"] = "1"
import urllib.request
import websockets
from pathlib import Path

CDP_PORT = 9225
OUT = Path("D:/roteador-heygen-api/videos/api_jobs")
TAG = os.environ.get("TAG", "paste3000")
MAX_WAIT = int(os.environ.get("MAX_WAIT", "3000"))  # segundos


def flush(m):
    try:
        print("[" + time.strftime("%H:%M:%S") + "] " + str(m), flush=True)
    except UnicodeEncodeError:
        print("[" + time.strftime("%H:%M:%S") + "] " + str(m).encode("ascii", "replace").decode("ascii"), flush=True)


async def main():
    OUT.mkdir(parents=True, exist_ok=True)
    tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:{}/json/list".format(CDP_PORT)).read())
    tab = next((t for t in tabs if "app.heygen.com" in t.get("url", "") and t.get("type") == "page"), tabs[0])
    cid = [0]
    async with websockets.connect(tab["webSocketDebuggerUrl"], max_size=200 * 1024 * 1024,
                                   ping_interval=None, ping_timeout=None) as ws:
        async def send(m, p=None, t=15):
            cid[0] += 1; myid = cid[0]
            await ws.send(json.dumps({"id": myid, "method": m, "params": p or {}}))
            s = time.time()
            while time.time() - s < t:
                d = json.loads(await ws.recv())
                if d.get("id") == myid:
                    return d
            return None

        async def js(e, t=15):
            r = await send("Runtime.evaluate", {"expression": e, "returnByValue": True}, t)
            if r and "result" in r and "result" in r["result"]:
                return r["result"]["result"].get("value")
            return None

        await send("Runtime.enable")
        flush("=== WATCH: esperando Scene rendered (max " + str(MAX_WAIT) + "s) ===")
        el = None
        for i in range(MAX_WAIT // 10):
            s = await js('(function(){var els=document.querySelectorAll("*");for(var i=0;i<els.length;i++){var t=(els[i].textContent||"").trim();if(t==="Scene rendered")return "done";}return "";})()')
            if s == "done":
                el = i * 10
                break
            if i > 0 and i % 6 == 0:
                flush("[render] " + str(i * 10) + "s...")
            await asyncio.sleep(10)
        if el is None:
            flush("[ERRO] timeout render"); return
        flush("[render] OK apos " + str(el) + "s (" + str(round(el / 60, 1)) + " min)")

        # play + pega src
        await js('(function(){var v=document.querySelector("video");if(v)v.play();return "p";})()')
        await asyncio.sleep(3)
        info = await js('(function(){var v=document.querySelector("video");return v?JSON.stringify({src:v.src||v.currentSrc,dur:v.duration}):null;})()')
        if not info:
            flush("[dl] sem video"); return
        d = json.loads(info); src = d.get("src"); dur = d.get("dur", 0)
        flush("[dl] video " + str(round(dur, 1)) + "s (" + str(round(dur / 60, 2)) + " min) src=" + str(src)[:60])
        if not src or src.startswith("blob:"):
            flush("[dl] URL invalida (blob)"); return
        try:
            req = urllib.request.Request(src, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=1200) as r:
                body = r.read()
            mb = len(body) / (1024 * 1024)
            p = OUT / (TAG + "_" + str(round(dur)) + "s_" + uuid.uuid4().hex[:4] + ".mp4")
            p.write_bytes(body)
            flush("[OK] " + p.name + " (" + str(round(mb, 1)) + "MB)")
            flush("=== SUCESSO ===")
        except Exception as e:
            flush("[dl ERRO] " + str(e))


if __name__ == "__main__":
    asyncio.run(main())
