# -*- coding: utf-8 -*-
"""_debug_modal_open.py - clica no thumbnail Annie (1505,171) que ABRE o modal
de avatares, e entao inspeciona: titulo real do modal, search input, abas,
e a posicao do card emerson apos busca."""
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

        flush("clicando no thumbnail Annie (1505,171) p/ abrir modal")
        await click(1505, 171)
        await asyncio.sleep(2.5)

        # 1) todos os inputs visiveis (search)
        ins = await js(
            '(function(){var out=[];var e=document.querySelectorAll("input,textarea");'
            'for(var i=0;i<e.length;i++){if(e[i].offsetParent===null)continue;'
            'var r=e[i].getBoundingClientRect();'
            'out.push({ph:(e[i].placeholder||""),type:e[i].type,x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width)});}'
            'return JSON.stringify(out);})()')
        flush("=== INPUTS visiveis ===")
        try:
            for e in json.loads(ins or "[]"):
                flush("  input ph=%r type=%s @(%d,%d) w=%d" % (e["ph"], e["type"], e["x"], e["y"], e["w"]))
        except Exception as ex:
            flush("parse err: " + str(ex))

        # 2) textos grandes/titulos no topo do modal (y 80-260, centro da tela)
        titles = await js(
            '(function(){var out=[];var e=document.querySelectorAll("h1,h2,h3,h4,div,span,button");'
            'for(var i=0;i<e.length;i++){if(e[i].offsetParent===null)continue;'
            'if(e[i].children.length>2)continue;'
            'var t=(e[i].textContent||"").trim();if(!t||t.length>30)continue;'
            'var r=e[i].getBoundingClientRect();'
            'if(r.x<300||r.x>1400||r.y<70||r.y>270)continue;'
            'out.push({tag:e[i].tagName,t:t,x:Math.round(r.x),y:Math.round(r.y)});}'
            'return JSON.stringify(out.slice(0,30));})()')
        flush("=== TEXTOS no topo do modal (possíveis titulo/abas) ===")
        try:
            for e in json.loads(titles or "[]"):
                flush("  <%s> %r @(%d,%d)" % (e["tag"], e["t"], e["x"], e["y"]))
        except Exception as ex:
            flush("parse titles err: " + str(ex))


if __name__ == "__main__":
    asyncio.run(main())
