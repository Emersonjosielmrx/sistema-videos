# -*- coding: utf-8 -*-
"""_test_full_swap.py - troca emerson->annie (via library), confirma que
current_avatar le 'annie', depois roda ensure_avatar_emerson() e valida
o swap automatico de volta pra emerson."""
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
        # garante editor - navega com cache-buster pra forcar projeto NOVO (pode
# voltar pro avatar default 'annie')
        import time as _t
        url = "https://app.heygen.com/create-v4?panel=scene&_=" + str(int(_t.time()))
        await c.cmd("Page.navigate", {"url": url})
        await asyncio.sleep(10)
        await asyncio.sleep(30)
        # dump imgs[alt] da library pra escolher um avatar diferente p/ swap-out
        imgs = await c.js(
            '(function(){var out=[];var e=document.querySelectorAll("img[alt]");'
            'for(var i=0;i<e.length;i++){if(e[i].offsetParent===null)continue;'
            'var a=(e[i].getAttribute("alt")||"").trim();'
            'var r=e[i].getBoundingClientRect();'
            'if(!a||r.x<1400)continue;'
            'out.push({alt:a,x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)});}'
            'return JSON.stringify(out);})()')
        flush("=== TODOS IMGS[alt] no painel direito ===")
        for e in json.loads(imgs or "[]"):
            flush("  %r @(%d,%d) %dx%d" % (e["alt"], e["x"], e["y"], e["w"], e["h"]))
        # tenta achar um avatar 'annie' (library) pra fazer o swap-out manual
        annie = await c.js(
            '(function(){var e=document.querySelectorAll("img[alt]");'
            'for(var i=0;i<e.length;i++){if(e[i].offsetParent===null)continue;'
            'var a=(e[i].getAttribute("alt")||"").toLowerCase();'
            'var r=e[i].getBoundingClientRect();'
            'if(a.indexOf("annie")>=0&&r.y>250){'
            'return JSON.stringify({x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2)});}}return null;})()')
        flush("annie library p/ clicar: " + str(annie))
        if annie:
            p = json.loads(annie)
            await c.click(p["x"], p["y"])
            await asyncio.sleep(3)
        cur2 = await c.current_avatar()
        flush("apos swap-out manual: avatar = '" + str(cur2) + "'")
        if cur2.startswith("emerson"):
            # forca troca pra annie usando a mesma logica do ensure_avatar_emerson,
            # mas com TARGET='annie'
            flush("[test] forcando troca pra annie via modal...")
            ok_annie = await c.ensure_avatar_target("annie")
            flush("ensure_avatar_target(annie) -> " + str(ok_annie))
            cur2 = await c.current_avatar()
            flush("apos ensure annie: avatar = '" + str(cur2) + "'")
        # agora roda o swap automatico emerson
        ok = await c.ensure_avatar_emerson()
        flush("ensure_avatar_emerson -> " + str(ok))
        final = await c.current_avatar()
        flush("avatar final = '" + str(final) + "'")
        # screenshot final
        s = await c.cmd("Page.captureScreenshot", {"format": "png"})
        data = s.get("result", {}).get("data")
        if data:
            import base64
            open("D:/roteador-heygen-api/_test_full_swap.png", "wb").write(base64.b64decode(data))
            flush("screenshot: _test_full_swap.png")
        flush("RESULTADO: " + ("SUCESSO" if (ok and final.startswith("emerson")) else "FALHA"))
        c._stop = True
        await pump


if __name__ == "__main__":
    asyncio.run(main())