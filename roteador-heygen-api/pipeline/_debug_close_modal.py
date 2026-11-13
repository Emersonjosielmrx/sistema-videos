# -*- coding: utf-8 -*-
"""_debug_close_modal.py - dumpa TUDO no canto superior direito do modal
e tambem todos os botoes com aria-label='close' para encontrar o X real."""
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
        # achar TODOS elementos com aria-label 'Close'
        closes = await c.js(
            '(function(){var out=[];var b=document.querySelectorAll("*");'
            'for(var i=0;i<b.length;i++){var e=b[i];'
            'if(e.offsetParent===null)continue;'
            'var al=(e.getAttribute("aria-label")||"").toLowerCase();'
            'if(al!=="close"&&al!=="fechar"&&al!=="close dialog"&&al!=="dismiss")continue;'
            'var r=e.getBoundingClientRect();'
            'out.push({tag:e.tagName,al:al,x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height),cls:(e.className||"").toString().slice(0,60)});}'
            'return JSON.stringify(out);})()')
        flush("=== TODOS aria-label close ===")
        for e in json.loads(closes or "[]"):
            flush("  <%s> %r @(%d,%d) %dx%d cls=%r" % (
                e["tag"], e["al"], e["x"], e["y"], e["w"], e["h"], e["cls"]))
        # tambem elementos com class dialog-close ou modal-close
        closes2 = await c.js(
            '(function(){var out=[];var b=document.querySelectorAll("*");'
            'for(var i=0;i<b.length;i++){var e=b[i];'
            'if(e.offsetParent===null)continue;'
            'var cls=(e.className||"").toString().toLowerCase();'
            'if(cls.indexOf("dialog-close")<0&&cls.indexOf("modal-close")<0)continue;'
            'var r=e.getBoundingClientRect();'
            'out.push({tag:e.tagName,cls:cls.slice(0,40),x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)});}'
            'return JSON.stringify(out);})()')
        flush("=== TODOS class~dialog-close ===")
        for e in json.loads(closes2 or "[]"):
            flush("  <%s> cls=%r @(%d,%d) %dx%d" % (
                e["tag"], e["cls"], e["x"], e["y"], e["w"], e["h"]))
        # tenta clicar no X e ver se fecha
        btn = await c.js(
            '(function(){var b=document.querySelectorAll("button,svg,[role=button]");'
            'for(var i=0;i<b.length;i++){if(b[i].offsetParent===null)continue;'
            'var al=(b[i].getAttribute("aria-label")||"").toLowerCase();'
            'var cls=(b[i].className||"").toString().toLowerCase();'
            'var r=b[i].getBoundingClientRect();'
            'if((al.indexOf("close")>=0||cls.indexOf("dialog-close")>=0||cls.indexOf("modal-close")>=0)'
            '&&r.width<=50&&r.height<=50&&r.x>1300&&r.x<1450&&r.y>30&&r.y<200)'
            'return JSON.stringify({x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2),tag:b[i].tagName,al:al,cls:cls.slice(0,40)});}return null;})()')
        flush("seletor X: " + str(btn))
        if btn:
            p = json.loads(btn)
            await c.click(p["x"], p["y"])
            await asyncio.sleep(2)
            still = await c.js(
                '(function(){var t=document.body.innerText||"";'
                'if(t.indexOf("Plans that fit your scale")>=0)return "plans";return "closed";})()')
            flush("apos clique: " + still)
        c._stop = True
        await pump


if __name__ == "__main__":
    asyncio.run(main())