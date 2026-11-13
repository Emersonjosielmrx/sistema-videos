# -*- coding: utf-8 -*-
import asyncio, json, os, urllib.request, base64
import websockets
CDP_PORT = int(os.environ.get("HEYGEN_CDP_PORT", "9225"))
async def main():
    tabs = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json/list").read())
    tab = next((t for t in tabs if 'app.heygen.com' in t.get('url','') and t.get('type')=='page'), tabs[0])
    async with websockets.connect(tab['webSocketDebuggerUrl'], max_size=200*1024*1024, ping_interval=None, ping_timeout=None) as ws:
        st={"id":0}
        async def cmd(m,p=None):
            st["id"]+=1; mid=st["id"]
            await ws.send(json.dumps({"id":mid,"method":m,"params":p or {}}))
            for _ in range(120):
                try: d=json.loads(await asyncio.wait_for(ws.recv(),0.5))
                except: continue
                if d.get("id")==mid: return d
        await cmd("Page.enable")
        s=await cmd("Page.captureScreenshot",{"format":"png"})
        data=s.get("result",{}).get("data")
        if data:
            open("D:/roteador-heygen-api/_debug_now.png","wb").write(base64.b64decode(data))
            print("saved _debug_now.png")
asyncio.run(main())
