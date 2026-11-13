# -*- coding: utf-8 -*-
"""_debug_click_card.py - clica no card do avatar (Annie) no painel esquerdo
e verifica se o modal "Choose Avatar" abre. Testa mouse real (CDP)."""
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

        async def click(x, y):
            await cmd("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": x, "y": y})
            await asyncio.sleep(0.05)
            await cmd("Input.dispatchMouseEvent", {"type": "mousePressed", "x": x, "y": y, "button": "left", "clickCount": 1})
            await asyncio.sleep(0.08)
            await cmd("Input.dispatchMouseEvent", {"type": "mouseReleased", "x": x, "y": y, "button": "left", "clickCount": 1})

        await cmd("Page.enable")
        await cmd("Runtime.enable")
        await cmd("Page.bringToFront")

        # card da Annie: (1476,142) 352x58 -> centro ~ (1652, 171)
        flush("clicando no card do avatar (1652, 171)")
        await click(1652, 171)
        await asyncio.sleep(2.5)

        modal = await js(
            '(function(){var el=document.querySelectorAll("h1,h2,h3,div,span");'
            'for(var i=0;i<el.length;i++){var t=(el[i].textContent||"").trim();'
            'if(t==="Choose Avatar"&&el[i].offsetParent!==null)return true;}return false;})()')
        flush("modal Choose Avatar aberto? " + str(modal))

        if modal:
            # dump do search input e abas do modal
            search = await js(
                '(function(){var ins=document.querySelectorAll("input");'
                'for(var i=0;i<ins.length;i++){var r=ins[i].getBoundingClientRect();'
                'if((ins[i].placeholder||"").toLowerCase().indexOf("search")>=0&&ins[i].offsetParent!==null){'
                'return JSON.stringify({ph:ins[i].placeholder,x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width)});}}return null;})()')
            flush("search input: " + str(search))
            tabs_modal = await js(
                '(function(){var out=[];var el=document.querySelectorAll("div,button,span");'
                'for(var i=0;i<el.length;i++){var t=(el[i].textContent||"").trim();'
                'if((t==="My Avatars"||t==="Public Avatars"||t==="Photo Avatars")&&el[i].offsetParent!==null){'
                'var r=el[i].getBoundingClientRect();if(r.width<250)out.push(t+"@"+Math.round(r.x)+","+Math.round(r.y));}}'
                'return JSON.stringify(out);})()')
            flush("abas do modal: " + str(tabs_modal))

        # screenshot pra confirmar
        shot = await cmd("Page.captureScreenshot", {"format": "png"})
        data = shot.get("result", {}).get("data")
        if data:
            out = "D:/roteador-heygen-api/_debug_modal.png"
            with open(out, "wb") as f:
                f.write(base64.b64decode(data))
            flush("screenshot: " + out)


if __name__ == "__main__":
    asyncio.run(main())
