# -*- coding: utf-8 -*-
"""_debug_hover.py - faz hover no card do avatar e no thumbnail pra ver se
aparece botao de troca (change/swap). Depois clica no thumbnail da imagem
Annie (1505,171) e verifica se o modal Choose Avatar abre."""
import asyncio, json, os, time, urllib.request, base64
import websockets

CDP_PORT = int(os.environ.get("HEYGEN_CDP_PORT", "9225"))


def flush(m):
    print("[" + time.strftime("%H:%M:%S") + "] " + str(m), flush=True)


async def main():
    tabs = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json/list").read())
    tab = next((t for t in tabs if 'app.heygen.com' in t.get('url', '') and t.get('type') == 'page'), tabs[0])
    async with websockets.connect(tab['webSocketDebuggerUrl'], max_size=200 * 1024 * 1024,
                                  ping_interval=None, ping_timeout=None) as ws:
        state = {"id": 0}

        async def cmd(method, params=None):
            state["id"] += 1
            mid = state["id"]
            await ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
            for _ in range(240):
                try:
                    d = json.loads(await asyncio.wait_for(ws.recv(), timeout=0.5))
                except asyncio.TimeoutError:
                    continue
                if d.get("id") == mid:
                    return d
            return {"error": "timeout"}

        async def js(expr):
            r = await cmd("Runtime.evaluate", {"expression": expr, "returnByValue": True})
            res = r.get("result", {})
            if "exceptionDetails" in res:
                return None
            return res.get("result", {}).get("value")

        async def move(x, y):
            await cmd("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": x, "y": y})

        async def click(x, y):
            await cmd("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": x, "y": y})
            await asyncio.sleep(0.05)
            await cmd("Input.dispatchMouseEvent", {"type": "mousePressed", "x": x, "y": y, "button": "left", "clickCount": 1})
            await asyncio.sleep(0.08)
            await cmd("Input.dispatchMouseEvent", {"type": "mouseReleased", "x": x, "y": y, "button": "left", "clickCount": 1})

        async def shot(name):
            s = await cmd("Page.captureScreenshot", {"format": "png"})
            data = s.get("result", {}).get("data")
            if data:
                p = "D:/roteador-heygen-api/_debug_" + name + ".png"
                with open(p, "wb") as f:
                    f.write(base64.b64decode(data))
                flush("screenshot: " + p)

        await cmd("Page.enable")
        await cmd("Runtime.enable")
        await cmd("Page.bringToFront")

        # 1) hover no card do avatar (1652,171) e ve botoes que aparecem
        flush("hover no card Annie (1652,171)")
        await move(1652, 171)
        await asyncio.sleep(1.2)
        # dump de botoes/elementos que apareceram na regiao do card apos hover
        hov = await js(
            '(function(){var out=[];var els=document.querySelectorAll("button,svg,div,span");'
            'for(var i=0;i<els.length;i++){var e=els[i];if(e.offsetParent===null)continue;'
            'var r=e.getBoundingClientRect();'
            'if(r.x<1470||r.x>1840||r.y<138||r.y>205||r.width<10||r.width>200)continue;'
            'var al=(e.getAttribute&&(e.getAttribute("aria-label")||e.getAttribute("title")))||"";'
            'var t=(e.textContent||"").trim().slice(0,18);'
            'out.push({tag:e.tagName,al:al,t:t,x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)});}'
            'return JSON.stringify(out.slice(0,25));})()')
        flush("=== elementos na regiao do card apos hover ===")
        try:
            for e in json.loads(hov or "[]"):
                flush("  <%s> al=%r t=%r @(%d,%d) %dx%d" % (e["tag"], e["al"], e["t"], e["x"], e["y"], e["w"], e["h"]))
        except Exception as ex:
            flush("parse err: " + str(ex))
        await shot("hover_card")

        # 2) clica no thumbnail da imagem Annie (centro do img 44x44 em 1483,149 -> 1505,171)
        flush("clicando no thumbnail da imagem Annie (1505,171)")
        await click(1505, 171)
        await asyncio.sleep(2.5)
        modal = await js(
            '(function(){var el=document.querySelectorAll("h1,h2,h3,div,span");'
            'for(var i=0;i<el.length;i++){var t=(el[i].textContent||"").trim();'
            'if(t==="Choose Avatar"&&el[i].offsetParent!==null)return true;}return false;})()')
        flush("modal Choose Avatar aberto? " + str(modal))
        await shot("thumb_click")


if __name__ == "__main__":
    asyncio.run(main())
