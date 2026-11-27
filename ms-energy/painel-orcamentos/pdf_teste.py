# pdf_teste.py — roda DENTRO do contêiner: gera o PDF híbrido de teste direto pelo motor (não grava no banco).
import asyncio, sys
sys.path.insert(0, "/app")
import motor
from playwright.async_api import async_playwright
d = {"cliente_nome": "Keyla Mayra dos Santos", "cliente_doc": "55019722200", "consumo": 500, "tipo": "hibrido",
     "baterias": [{"id": "basica5"}, {"id": "mb48314"}], "extras": [{"id": "ar12"}, {"id": "poste"}]}
html, r = motor.montar_html(d, {}, vendedor={"nome": "Vendedor Teste", "telefone": "(91) 98469-8653"}, num="MS2611-TESTE")
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--no-sandbox"]); pg = await b.new_page()
        await pg.set_content(html, wait_until="load")
        open("/app/dados/_prints/hibrido_teste.pdf", "wb").write(await pg.pdf(format="A4", print_background=True, prefer_css_page_size=True))
        await b.close()
asyncio.run(main()); print("pdf ok", r["paginas"])
