# -*- coding: utf-8 -*-
"""_debug_plan_modal.py - dumpa todos os elementos clicaveis perto do X
do modal 'Plans that fit your scale' (visualmente em ~(1315, 50))."""
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
        # dump todos elementos visiveis no canto superior-direito do modal
        # area: x 1280-1360, y 30-70
        els = await c.js(
            '(function(){var out=[];var nodes=document.querySelectorAll("*");'
            'for(var i=0;i<nodes.length;i++){var e=nodes[i];'
            'if(e.offsetParent===null)continue;'
            'var r=e.getBoundingClientRect();'
            'if(r.x<1100||r.x>1500||r.y<30||r.y>120)continue;'
            'if(r.width<5||r.width>50||r.height<5||r.height>50)continue;'
            'var al=e.getAttribute("aria-label")||"";'
            'var t=(e.textContent||"").trim().slice(0,15);'
            'out.push({tag:e.tagName,al:al,t:t,x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height),cls:(e.className||"").toString().slice(0,40)});}'
            'return JSON.stringify(out.slice(0,30));})()')
        flush("=== CANDIDATOS X (x 1280-1360 y 30-90) ===")
        for e in json.loads(els or "[]"):
            flush("  <%s> al=%r t=%r @(%d,%d) %dx%d cls=%r" % (
                e["tag"], e["al"], e["t"], e["x"], e["y"], e["w"], e["h"], e["cls"]))
        # tambem dump botoes/clickables grandes do centro do modal pra entender
        btns = await c.js(
            '(function(){var out=[];var b=document.querySelectorAll("button,a,[role=button]");'
            'for(var i=0;i<b.length;i++){if(b[i].offsetParent===null)continue;'
            'var t=(b[i].textContent||"").trim();if(!t||t.length>30)continue;'
            'var r=b[i].getBoundingClientRect();'
            'if(r.x<400||r.x>1500||r.y<50||r.y>900)continue;'
            'if(r.width<10)continue;'
            'out.push({tag:b[i].tagName,t:t,x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width)});}'
            'return JSON.stringify(out.slice(0,30));})()')
        flush("=== BOTOES no modal (x 400-1500) ===")
        for e in json.loads(btns or "[]"):
            flush("  <%s> %r @(%d,%d) w=%d" % (e["tag"], e["t"], e["x"], e["y"], e["w"]))
        c._stop = True
        await pump


if __name__ == "__main__":
    asyncio.run(main())