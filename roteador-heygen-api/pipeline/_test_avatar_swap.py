# -*- coding: utf-8 -*-
"""_test_avatar_swap.py - testa SO o ensure_avatar_emerson() do run_one.py,
reutilizando a classe CDP real (nao reimplementa). Valida o fluxo inteiro:
hover no thumbnail -> abre modal -> aba My Avatars -> busca emerson -> clica
card -> fecha -> verifica current_avatar()."""
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
        atual = await c.current_avatar()
        flush("[test] avatar atual = '" + str(atual) + "'")
        ok = await c.ensure_avatar_emerson()
        flush("[test] ensure_avatar_emerson -> " + str(ok))
        final = await c.current_avatar()
        flush("[test] avatar final = '" + str(final) + "'")
        c._stop = True
        await pump
        flush("[test] RESULTADO: " + ("SUCESSO" if (ok and final.startswith("emerson")) else "FALHA"))


if __name__ == "__main__":
    asyncio.run(main())
