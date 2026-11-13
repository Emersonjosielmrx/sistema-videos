# -*- coding: utf-8 -*-
"""_debug_panel.py - inspeciona o painel esquerdo "Avatar & Voice" do editor HeyGen.
O objetivo e achar o CARD do avatar (thumbnail Annie) que, ao clicar, abre o
modal "Choose Avatar". O icone "Avatar" da toolbar direita so alterna o painel."""
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

        await cmd("Page.enable")
        await cmd("Runtime.enable")

        # 1) TODAS as imagens (thumbnails) no painel esquerdo (x 1430-1840, y 120-500)
        imgs = await js(
            '(function(){var out=[];var els=document.querySelectorAll("img");'
            'for(var i=0;i<els.length;i++){var e=els[i];if(e.offsetParent===null)continue;'
            'var r=e.getBoundingClientRect();'
            'if(r.x<1430||r.x>1840||r.y<120||r.y>500||r.width<20)continue;'
            'out.push({alt:(e.getAttribute("alt")||""),x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)});}'
            'return JSON.stringify(out);})()')
        flush("=== IMAGENS no painel esquerdo (thumbnails) ===")
        try:
            for e in json.loads(imgs or "[]"):
                flush("  IMG alt=%r @(%d,%d) %dx%d" % (e["alt"], e["x"], e["y"], e["w"], e["h"]))
        except Exception as ex:
            flush("parse imgs err: " + str(ex) + " raw=" + str(imgs)[:200])

        # 2) botoes/elementos clicaveis no painel esquerdo com aria-label ou title
        clickables = await js(
            '(function(){var out=[];var els=document.querySelectorAll("button,[role=button],svg,div");'
            'for(var i=0;i<els.length;i++){var e=els[i];if(e.offsetParent===null)continue;'
            'var r=e.getBoundingClientRect();'
            'if(r.x<1430||r.x>1840||r.y<120||r.y>450||r.width<10||r.width>380)continue;'
            'var al=(e.getAttribute&&(e.getAttribute("aria-label")||e.getAttribute("title")))||"";'
            'var t=(e.textContent||"").trim().slice(0,20);'
            'if(!al&&!t)continue;'
            'out.push({tag:e.tagName,al:al,t:t,x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)});}'
            'return JSON.stringify(out.slice(0,40));})()')
        flush("=== CLICAVEIS no painel esquerdo (aria-label/title/texto) ===")
        try:
            for e in json.loads(clickables or "[]"):
                flush("  <%s> al=%r t=%r @(%d,%d) %dx%d" % (e["tag"], e["al"], e["t"], e["x"], e["y"], e["w"], e["h"]))
        except Exception as ex:
            flush("parse clickables err: " + str(ex))


if __name__ == "__main__":
    asyncio.run(main())
