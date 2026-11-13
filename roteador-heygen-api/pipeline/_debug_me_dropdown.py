# -*- coding: utf-8 -*-
"""_debug_me_dropdown.py - abre o dropdown Motion Engine e dumpa TODAS as
opcoes visiveis com coordenadas pra encontrar 'Avatar III'."""
import asyncio, json, os, urllib.request
os.environ["PYTHONUTF8"] = "1"
import websockets
from run_one import CDP, flush, CDP_PORT


async def main():
    tabs = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json/list").read())
    tab = next((t for t in tabs if 'app.heygen.com' in t.get('url', '') and t.get('type') == 'page'), tabs[0])
    async with websockets.connect(tab['webSocketDebuggerUrl'], max_size=200 * 1024 * 1024,
                                  ping_interval=None, ping_timeout=None) as ws:
        c = CDP(ws)
        pump = asyncio.create_task(c._pump())
        await c.cmd("Page.enable")
        await c.cmd("Runtime.enable")
        await c.cmd("Page.bringToFront")
        # garante editor
        cur = await c.js("location.href") or ""
        if "create-v4" not in cur:
            await c.cmd("Page.navigate", {"url": "https://app.heygen.com/create-v4?panel=scene"})
            await asyncio.sleep(8)
        await asyncio.sleep(25)
        # dump ANTES: botoes na area do motion engine (y 350-500, x 1400-1850)
        btns_before = await c.js(
            '(function(){var out=[];var els=document.querySelectorAll("button,div,span");'
            'for(var i=0;i<els.length;i++){if(els[i].offsetParent===null)continue;'
            'var t=(els[i].textContent||"").trim();if(!t||t.length>30)continue;'
            'var r=els[i].getBoundingClientRect();'
            'if(r.x<1400||r.x>1850||r.y<300||r.y>500)continue;'
            'if(r.width<10)continue;'
            'out.push({tag:els[i].tagName,t:t,x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width)});}'
            'return JSON.stringify(out.slice(0,30));})()')
        flush("=== ANTES do clique (motion engine area) ===")
        for e in json.loads(btns_before or "[]"):
            flush("  <%s> %r @(%d,%d) w=%d" % (e["tag"], e["t"], e["x"], e["y"], e["w"]))
        # clica no dropdown Avatar IV
        btn = await c.js(
            '(function(){var els=document.querySelectorAll("button");'
            'for(var i=0;i<els.length;i++){var t=(els[i].textContent||"").trim();'
            'if((t==="Avatar IV"||t==="Avatar V")&&els[i].offsetWidth>100){'
            'var r=els[i].getBoundingClientRect();'
            'return JSON.stringify({x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2)});}}return null;})()')
        flush("btn dropdown: " + str(btn))
        if btn:
            p = json.loads(btn)
            await c.click(p["x"], p["y"])
            await asyncio.sleep(2)
            # dump DEPOIS: tudo visivel no painel direito (y 350-700)
            btns_after = await c.js(
                '(function(){var out=[];var els=document.querySelectorAll("button,div,span,a,[role=button]");'
                'for(var i=0;i<els.length;i++){if(els[i].offsetParent===null)continue;'
                'var t=(els[i].textContent||"").trim();if(!t||t.length>40)continue;'
                'var r=els[i].getBoundingClientRect();'
                'if(r.x<1400||r.x>1850||r.y<350||r.y>750)continue;'
                'if(r.width<10)continue;'
                'out.push({tag:els[i].tagName,t:t,x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width)});}'
                'return JSON.stringify(out.slice(0,40));})()')
            flush("=== DEPOIS do clique (dropdown aberto) ===")
            for e in json.loads(btns_after or "[]"):
                flush("  <%s> %r @(%d,%d) w=%d" % (e["tag"], e["t"], e["x"], e["y"], e["w"]))
            s = await c.cmd("Page.captureScreenshot", {"format": "png"})
            data = s.get("result", {}).get("data")
            if data:
                import base64
                open("D:/roteador-heygen-api/_debug_me_dropdown.png", "wb").write(base64.b64decode(data))
                flush("screenshot: _debug_me_dropdown.png")
        c._stop = True
        await pump


if __name__ == "__main__":
    asyncio.run(main())