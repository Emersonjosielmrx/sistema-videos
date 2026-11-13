# -*- coding: utf-8 -*-
"""_debug_avatar.py - inspeciona a toolbar direita do editor HeyGen.
Dumpa todos os elementos clicaveis com coords na regiao x>1700 (toolbar direita)
e salva um screenshot pra ver onde esta o icone Avatar."""
import asyncio, json, os, sys, time, urllib.request, base64
import websockets

CDP_PORT = int(os.environ.get("HEYGEN_CDP_PORT", "9225"))


def flush(m):
    print("[" + time.strftime("%H:%M:%S") + "] " + str(m), flush=True)


async def main():
    tabs = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json/list").read())
    tab = next((t for t in tabs if 'app.heygen.com' in t.get('url', '') and t.get('type') == 'page'), tabs[0])
    flush("tab url: " + tab.get('url', '')[:70])
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

        await cmd("Page.enable")
        await cmd("Runtime.enable")

        url = await js("location.href") or ""
        flush("location: " + url[:70])

        # 1) dump de TODOS elementos com texto curto na regiao toolbar direita (x>1700)
        dump = await js(
            '(function(){var out=[];var els=document.querySelectorAll("div,button,a,span,svg");'
            'for(var i=0;i<els.length;i++){var e=els[i];if(e.offsetParent===null)continue;'
            'var r=e.getBoundingClientRect();'
            'if(r.x<1700||r.width===0||r.width>200)continue;'
            'if(r.y>200)continue;'
            'var t=(e.textContent||"").trim().slice(0,25);'
            'var al=(e.getAttribute&&e.getAttribute("aria-label"))||"";'
            'out.push({tag:e.tagName,t:t,al:al,x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)});}'
            'return JSON.stringify(out);})()')
        flush("=== elementos toolbar direita (x>1700, y<200) ===")
        try:
            for e in json.loads(dump or "[]"):
                flush("  <%s> t=%r al=%r  @(%d,%d) %dx%d" % (e["tag"], e["t"], e["al"], e["x"], e["y"], e["w"], e["h"]))
        except Exception as ex:
            flush("parse err: " + str(ex) + " raw=" + str(dump)[:200])

        # 2) dump de TODOS elementos que contem texto "Avatar" (qualquer regiao)
        dump2 = await js(
            '(function(){var out=[];var els=document.querySelectorAll("div,button,a,span");'
            'for(var i=0;i<els.length;i++){var e=els[i];if(e.offsetParent===null)continue;'
            'var t=(e.textContent||"").trim();'
            'if(t!=="Avatar")continue;'
            'var r=e.getBoundingClientRect();'
            'out.push({tag:e.tagName,x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)});}'
            'return JSON.stringify(out);})()')
        flush('=== elementos com textContent EXATO "Avatar" ===')
        try:
            for e in json.loads(dump2 or "[]"):
                flush("  <%s> @(%d,%d) %dx%d" % (e["tag"], e["x"], e["y"], e["w"], e["h"]))
        except Exception as ex:
            flush("parse2 err: " + str(ex))

        # 3) screenshot
        shot = await cmd("Page.captureScreenshot", {"format": "png"})
        data = shot.get("result", {}).get("data")
        if data:
            out = "D:/roteador-heygen-api/_debug_editor.png"
            with open(out, "wb") as f:
                f.write(base64.b64decode(data))
            flush("screenshot salvo: " + out)
        else:
            flush("sem screenshot")


if __name__ == "__main__":
    asyncio.run(main())
