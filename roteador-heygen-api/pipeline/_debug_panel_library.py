# -*- coding: utf-8 -*-
"""_debug_panel_library.py - dumpa o avatar library (Avatar & Voice) do painel
DIREITO (x>1400). Lista imgs[alt] e textos pra ver se ha 'emerson' disponivel
como avatar de cena (a Annie atual e' uma das variantes da coluna)."""
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
        # garante que estamos no editor
        cur = await c.js("location.href") or ""
        if "create-v4" not in cur:
            flush("[nav] indo pro editor")
            await c.cmd("Page.navigate", {"url": "https://app.heygen.com/create-v4?panel=scene"})
            await asyncio.sleep(8)
        await asyncio.sleep(20)
        # dump imgs[alt] no painel direito inteiro
        imgs = await c.js(
            '(function(){var out=[];var e=document.querySelectorAll("img[alt]");'
            'for(var i=0;i<e.length;i++){if(e[i].offsetParent===null)continue;'
            'var a=(e[i].getAttribute("alt")||"").trim();'
            'var r=e[i].getBoundingClientRect();if(r.x<1400)continue;'
            'out.push({alt:a,x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)});}'
            'return JSON.stringify(out);})()')
        flush("=== IMGS[alt] painel direito (x>=1400) ===")
        for e in json.loads(imgs or "[]"):
            flush("  %r @(%d,%d) %dx%d" % (e["alt"], e["x"], e["y"], e["w"], e["h"]))
        # dump textos no painel direito (toda regiao)
        txts = await c.js(
            '(function(){var out=[];var w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT,null);'
            'var n;while(n=w.nextNode()){var t=(n.textContent||"").trim();if(!t||t.length>30)continue;'
            'var p=n.parentElement;if(!p||p.offsetParent===null)continue;'
            'var r=p.getBoundingClientRect();if(r.x<1400||r.x>1900)continue;'
            'if(r.y<100||r.y>900)continue;if(r.width<10)continue;'
            'out.push({t:t,x:Math.round(r.x),y:Math.round(r.y)});}'
            'return JSON.stringify(out.slice(0,40));})()')
        flush("=== TEXTOS painel direito (x>=1400) ===")
        for e in json.loads(txts or "[]"):
            flush("  %r @(%d,%d)" % (e["t"], e["x"], e["y"]))
        # screenshot
        s = await c.cmd("Page.captureScreenshot", {"format": "png"})
        data = s.get("result", {}).get("data")
        if data:
            import base64
            open("D:/roteador-heygen-api/_debug_panel.png", "wb").write(base64.b64decode(data))
            flush("screenshot: _debug_panel.png")
        c._stop = True
        await pump


if __name__ == "__main__":
    asyncio.run(main())