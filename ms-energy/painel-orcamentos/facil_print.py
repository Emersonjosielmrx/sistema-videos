# roda DENTRO do contêiner: percorre o Orçamento fácil como o vendedor luiz (não gera proposta) e tira prints
import asyncio, os
from playwright.async_api import async_playwright
B = "http://127.0.0.1:8101"; OUT = "/app/dados/_prints"; os.makedirs(OUT, exist_ok=True)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--no-sandbox"])
        for nome, vp in (("pc", {"width": 1366, "height": 900}), ("cel", {"width": 390, "height": 844})):
            ctx = await b.new_context(viewport=vp, is_mobile=nome == "cel", has_touch=nome == "cel")
            pg = await ctx.new_page()
            await pg.goto(B + "/"); await pg.wait_for_timeout(1200)
            await pg.fill("input[name=usuario]", "luiz"); await pg.fill("input[name=senha]", "1234"); await pg.click("button.pri")
            await pg.wait_for_timeout(1500); await pg.goto(B + "/#/facil"); await pg.wait_for_timeout(1500)
            async def txt(v):
                await pg.fill("#fIn", v); await pg.click("#fForm button.pri"); await pg.wait_for_timeout(500)
            async def bt(t):
                await pg.click(f".qbt:has-text('{t}')"); await pg.wait_for_timeout(500)
            await txt("Maria da Silva Souza"); await txt("91984698653")
            await pg.screenshot(path=f"{OUT}/facil_{nome}_1.png")
            await txt("Capitão Poço"); await bt("Pelo valor da conta"); await txt("650"); await bt("Telha de barro")
            await bt("Mostrar as duas"); await pg.click("[data-p='ar12']"); await pg.wait_for_timeout(300)
            await pg.screenshot(path=f"{OUT}/facil_{nome}_2.png")
            await pg.click("#fCont"); await pg.wait_for_timeout(500); await bt("Não"); await pg.wait_for_timeout(2500)
            await pg.screenshot(path=f"{OUT}/facil_{nome}_3.png", full_page=nome == "pc")
            await ctx.close()
        await b.close()
    print("ok", sorted(os.listdir(OUT)))
asyncio.run(main())
