"""Cria uma Página nova no perfil (facebook.com/pages/creation). Volta ao perfil pessoal antes (só o perfil cria Página).
Prints em logs/fb_criar_<tag>_*.png.  python fb_criar_pagina.py <conta> "<perfil pessoal>" "<Nome da Página>" "<categoria>" "<bio>" <tag>"""
import sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright
import fb_contas, fb_entrar_como
LOG = Path(__file__).resolve().parent.parent / "logs"
conta, perfil, nome, categoria, bio, tag = sys.argv[1:7]


def vis(loc):
    for i in range(loc.count()):
        if loc.nth(i).is_visible():
            return loc.nth(i)
    return None


porta, proc = fb_contas.abrir(conta)
try:
    with sync_playwright() as p:
        pg = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}").contexts[0].new_page()
        pg.set_viewport_size({"width": 1366, "height": 900})
        print("perfil pessoal:", fb_entrar_como.entrar_como(pg, perfil))
        pg.goto("https://www.facebook.com/pages/creation/", wait_until="domcontentloaded", timeout=90000)
        time.sleep(10)
        pg.screenshot(path=str(LOG / f"fb_criar_{tag}_0.png"))
        campos = pg.locator("input[type=text], input:not([type]), textarea")
        print("campos:", campos.count(), [campos.nth(i).get_attribute("aria-label") for i in range(campos.count())])
        nome_in = vis(pg.locator('input[aria-label*="Nome da Página" i], input[aria-label*="Page name" i]')) or vis(campos)
        nome_in.click(); nome_in.fill(nome); time.sleep(2)
        cat_in = vis(pg.locator('input[aria-label*="Categoria" i], input[aria-label*="Category" i]'))
        cat_in.click(); cat_in.fill(categoria); time.sleep(4)
        op = vis(pg.locator("[role=option]"))
        if op:
            print("categoria:", op.inner_text()[:60]); op.click(); time.sleep(2)
        bio_in = vis(pg.locator('textarea[aria-label*="Bio" i], textarea'))
        if bio_in:
            bio_in.click(); bio_in.fill(bio); time.sleep(1)
        pg.screenshot(path=str(LOG / f"fb_criar_{tag}_1_preenchido.png"))
        b = vis(pg.get_by_role("button", name="Criar Página")) or vis(pg.get_by_role("button", name="Create Page"))
        if not b:
            print("sem botão Criar Página"); sys.exit(2)
        b.click(); time.sleep(15)
        pg.screenshot(path=str(LOG / f"fb_criar_{tag}_2_criada.png"))
        # passos seguintes (foto, capa, WhatsApp, convidar amigos): pular
        for _ in range(6):
            s = vis(pg.get_by_role("button", name="Avançar")) or vis(pg.get_by_role("button", name="Ignorar")) \
                or vis(pg.get_by_role("button", name="Pular")) or vis(pg.get_by_role("button", name="Concluir"))
            if not s:
                break
            s.click(); time.sleep(5)
        time.sleep(5)
        print("url:", pg.url)
        pg.screenshot(path=str(LOG / f"fb_criar_{tag}_3_fim.png"))
        pg.close()
finally:
    fb_contas.fechar(proc)
