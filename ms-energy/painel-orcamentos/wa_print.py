# roda DENTRO do contêiner: prints da tela Meu WhatsApp como o vendedor luiz (só leitura)
import asyncio, os
from playwright.async_api import async_playwright
B = "http://127.0.0.1:8101"; OUT = "/app/dados/_prints"; os.makedirs(OUT, exist_ok=True)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--no-sandbox"])
        for nome, vp in (("pc", {"width": 1440, "height": 900}), ("cel", {"width": 390, "height": 844})):
            ctx = await b.new_context(viewport=vp, is_mobile=nome == "cel", has_touch=nome == "cel")
            pg = await ctx.new_page()
            await pg.goto(B + "/"); await pg.wait_for_timeout(1200)
            await pg.fill("input[name=usuario]", "luiz"); await pg.fill("input[name=senha]", "1234"); await pg.click("button.pri")
            await pg.wait_for_timeout(1500); await pg.goto(B + "/#/whatsapp"); await pg.wait_for_timeout(9000)
            await pg.screenshot(path=f"{OUT}/wa_{nome}_1.png")
            its = await pg.query_selector_all(".wa-it")
            if len(its) > 5:
                await its[5].click(); await pg.wait_for_timeout(5000)
                await pg.screenshot(path=f"{OUT}/wa_{nome}_2.png")
            await ctx.close()
        await b.close()
    print("ok", sorted(os.listdir(OUT)))
asyncio.run(main())
