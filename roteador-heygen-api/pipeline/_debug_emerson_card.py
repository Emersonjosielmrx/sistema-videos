# -*- coding: utf-8 -*-
"""_debug_emerson_card.py - abre o modal Choose Avatar (hover+click thumbnail),
digita 'emerson' no search, espera resultado e dumpa a posicao REAL dos cards
'emerson' (img alt + texto)."""
import asyncio, json, os, urllib.request
os.environ["PYTHONUTF8"] = "1"
import websockets
from run_one import CDP, flush, CDP_PORT

TARGET = "emerson"


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
        # 1) abre modal via thumbnail (hover + click)
        thumb = await c.js(
            '(function(){var els=document.querySelectorAll("img[alt]");'
            'for(var i=0;i<els.length;i++){var e=els[i];if(e.offsetParent===null)continue;'
            'var r=e.getBoundingClientRect();'
            'if(r.x>1200&&r.y<300&&r.width>=30&&r.width<=80){'
            'return JSON.stringify({ix:Math.round(r.x+r.width/2),iy:Math.round(r.y+r.height/2),'
            'cx:Math.round(r.x+r.width/2+150),cy:Math.round(r.y+r.height/2)});}}return null;})()')
        if not thumb:
            flush("thumbnail nao encontrado"); c._stop = True; await pump; return
        tp = json.loads(thumb)
        await c.cmd("Input.dispatchMouseEvent", {"type":"mouseMoved","x":tp["cx"],"y":tp["cy"]})
        await asyncio.sleep(1.2)
        await c.click(tp["ix"], tp["iy"])
        await asyncio.sleep(2.5)
        modal = await c.js(
            '(function(){var el=document.querySelectorAll("h1,h2,h3,div,span");'
            'for(var i=0;i<el.length;i++){var t=(el[i].textContent||"").trim();'
            'if(t==="Choose Avatar"&&el[i].offsetParent!==null)return true;}return false;})()')
        flush("modal aberto? " + str(modal))
        if not modal:
            c._stop = True; await pump; return
        # 2) digita emerson no search (native setter)
        await c.js(
            '(function(){var ins=document.querySelectorAll("input");'
            'for(var i=0;i<ins.length;i++){'
            'if((ins[i].placeholder||"").toLowerCase()==="search"&&ins[i].offsetParent!==null){'
            'var ns=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,"value").set;'
            'ns.call(ins[i],"' + TARGET + '");'
            'ins[i].dispatchEvent(new Event("input",{bubbles:true}));'
            'ins[i].dispatchEvent(new Event("change",{bubbles:true}));}}return 1;})()')
        await asyncio.sleep(2.5)
        # 3) dumpa imgs alt~emerson
        imgs = await c.js(
            '(function(){var out=[];var e=document.querySelectorAll("img[alt]");'
            'for(var i=0;i<e.length;i++){if(e[i].offsetParent===null)continue;'
            'var a=(e[i].getAttribute("alt")||"").toLowerCase();'
            'if(a.indexOf("emerson")<0)continue;var r=e[i].getBoundingClientRect();'
            'out.push({alt:a,x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)});}'
            'return JSON.stringify(out);})()')
        flush("=== IMGS alt~emerson ===")
        for e in json.loads(imgs or "[]"):
            flush("  IMG alt=%r @(%d,%d) %dx%d centro(%d,%d)" % (
                e["alt"], e["x"], e["y"], e["w"], e["h"],
                e["x"]+e["w"]//2, e["y"]+e["h"]//2))
        # 4) dumpa textos 'emerson' (x>400)
        txts = await c.js(
            '(function(){var out=[];var w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT,null);'
            'var n;while(n=w.nextNode()){var t=(n.textContent||"").trim().toLowerCase();'
            'if(t.indexOf("emerson")<0)continue;var p=n.parentElement;'
            'if(!p||p.offsetParent===null)continue;var r=p.getBoundingClientRect();'
            'if(r.x<400)continue;'
            'out.push({t:t.slice(0,20),x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)});}'
            'return JSON.stringify(out.slice(0,10));})()')
        flush("=== TEXTOS 'emerson' (x>400) ===")
        for e in json.loads(txts or "[]"):
            flush("  txt=%r @(%d,%d) %dx%d" % (e["t"], e["x"], e["y"], e["w"], e["h"]))
        # 5) CLICA na miniatura emerson e observa o que acontece
        card = await c.js(
            '(function(){var e=document.querySelectorAll("img[alt]");'
            'for(var i=0;i<e.length;i++){if(e[i].offsetParent===null)continue;'
            'var a=(e[i].getAttribute("alt")||"").toLowerCase();'
            'if(a.indexOf("emerson")<0)continue;var r=e[i].getBoundingClientRect();'
            'if(r.x>400&&r.y>300&&r.y<700&&r.width>=40)'
            'return JSON.stringify({x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2)});}return null;})()')
        flush("card p/ clicar: " + str(card))
        if card:
            p = json.loads(card)
            flush("clicando miniatura emerson (%d,%d)" % (p["x"], p["y"]))
            await c.click(p["x"], p["y"])
            await asyncio.sleep(3)
            # modal ainda aberto?
            still = await c.js(
                '(function(){var el=document.querySelectorAll("h1,h2,h3,div,span");'
                'for(var i=0;i<el.length;i++){var t=(el[i].textContent||"").trim();'
                'if(t==="Choose Avatar"&&el[i].offsetParent!==null)return true;}return false;})()')
            flush("modal ainda aberto apos clique? " + str(still))
            # botoes visiveis no modal (Select/Confirm/Add etc)?
            btns = await c.js(
                '(function(){var out=[];var b=document.querySelectorAll("button");'
                'for(var i=0;i<b.length;i++){if(b[i].offsetParent===null)continue;'
                'var t=(b[i].textContent||"").trim();if(!t||t.length>20)continue;'
                'var r=b[i].getBoundingClientRect();if(r.y<200||r.y>750)continue;'
                'out.push(t+"@"+Math.round(r.x)+","+Math.round(r.y));}return JSON.stringify(out.slice(0,20));})()')
            flush("botoes no modal: " + str(btns))
            # dump botoes/interativos amplos (toda regiao do modal detalhe)
            btns2 = await c.js(
                '(function(){var out=[];var els=document.querySelectorAll("button,div,span,a,[role=button]");'
                'for(var i=0;i<els.length;i++){if(els[i].offsetParent===null)continue;'
                'var t=(els[i].textContent||"").trim();if(!t||t.length>25)continue;'
                'var r=els[i].getBoundingClientRect();if(r.y<200||r.y>800||r.x<400||r.x>1000)continue;'
                'if(r.width<10||r.width>400)continue;'
                'out.push({tag:els[i].tagName,t:t.slice(0,20),x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width)});}'
                'return JSON.stringify(out.slice(0,30));})()')
            flush("=== INTERATIVOS no modal detalhe ===")
            for e in json.loads(btns2 or "[]"):
                flush("  <%s> %r @(%d,%d) w=%d" % (e["tag"], e["t"], e["x"], e["y"], e["w"]))
            # textos/titulos uteis
            titles = await c.js(
                '(function(){var out=[];var els=document.querySelectorAll("h1,h2,h3,h4,div,span");'
                'for(var i=0;i<els.length;i++){if(els[i].offsetParent===null)continue;'
                'if(els[i].children.length>2)continue;'
                'var t=(els[i].textContent||"").trim();if(!t||t.length>25)continue;'
                'var r=els[i].getBoundingClientRect();if(r.y<200||r.y>900)continue;'
                'out.push({tag:els[i].tagName,t:t,x:Math.round(r.x),y:Math.round(r.y)});}'
                'return JSON.stringify(out.slice(0,40));})()')
            flush("=== TEXTOS no modal detalhe ===")
            for e in json.loads(titles or "[]"):
                flush("  <%s> %r @(%d,%d)" % (e["tag"], e["t"], e["x"], e["y"]))
            # dump botoes amplos (area do modal, x 400-1400, y 100-800)
            btns3 = await c.js(
                '(function(){var out=[];var els=document.querySelectorAll("button,a,[role=button],div,span");'
                'for(var i=0;i<els.length;i++){if(els[i].offsetParent===null)continue;'
                'var r=els[i].getBoundingClientRect();'
                'if(r.x<400||r.x>1400||r.y<100||r.y>800)continue;'
                'if(r.width<10||r.width>400||r.height<10)continue;'
                'var al=(els[i].getAttribute&&(els[i].getAttribute("aria-label")||els[i].getAttribute("title")))||"";'
                'var t=(els[i].textContent||"").trim().slice(0,30);'
                'if(!al&&!t)continue;'
                'out.push({tag:els[i].tagName,al:al,t:t,x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)});}'
                'return JSON.stringify(out.slice(0,40));})()')
            flush("=== BOTOES/CLICAVEIS AMPLOS no modal detalhe ===")
            for e in json.loads(btns3 or "[]"):
                flush("  <%s> al=%r t=%r @(%d,%d) %dx%d" % (e["tag"], e["al"], e["t"], e["x"], e["y"], e["w"], e["h"]))
            # screenshot
            s = await c.cmd("Page.captureScreenshot", {"format": "png"})
            data = s.get("result", {}).get("data")
            if data:
                import base64
                open("D:/roteador-heygen-api/_debug_now.png", "wb").write(base64.b64decode(data))
                flush("screenshot: _debug_now.png")
            cur = await c.current_avatar()
            flush("current_avatar apos clique: '" + str(cur) + "'")
            # TENTA clicar no proprio FOTO grande (centro ~791,340) pra ver se seleciona
            flush("clicando na foto do emerson (~791,340)")
            await c.click(791, 340)
            await asyncio.sleep(2.5)
            modal_after_photo = await c.js(
                '(function(){var el=document.querySelectorAll("h1,h2,h3,div,span");'
                'for(var i=0;i<el.length;i++){var t=(el[i].textContent||"").trim();'
                'if(t==="Choose Avatar"&&el[i].offsetParent!==null)return true;}return false;})()')
            flush("modal 'Choose Avatar' ainda aberto? " + str(modal_after_photo))
            cur2 = await c.current_avatar()
            flush("current_avatar apos foto: '" + str(cur2) + "'")
            s2 = await c.cmd("Page.captureScreenshot", {"format": "png"})
            data2 = s2.get("result", {}).get("data")
            if data2:
                import base64
                open("D:/roteador-heygen-api/_debug_now.png", "wb").write(base64.b64decode(data2))
                flush("screenshot: _debug_now.png")
        c._stop = True
        await pump


if __name__ == "__main__":
    asyncio.run(main())
