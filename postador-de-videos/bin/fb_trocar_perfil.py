"""Troca o perfil ativo (menu da foto -> 'Ver todos os perfis' -> <nome>) e lista as páginas desse perfil.
    python fb_trocar_perfil.py <conta> "<nome do perfil>" [--voltar "<nome>"]"""
import sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright
import fb_contas

conta, nome = sys.argv[1], sys.argv[2]
voltar = sys.argv[sys.argv.index("--voltar") + 1] if "--voltar" in sys.argv else None
LOG = Path(__file__).resolve().parent.parent / "logs"


def trocar(pg, alvo):
    pg.goto("https://www.facebook.com/", wait_until="domcontentloaded", timeout=45000)
    time.sleep(6)
    pg.click('[aria-label="Seu perfil"]')
    time.sleep(3)
    ver = pg.get_by_text("Ver todos os perfis", exact=False).first
    if ver.count():
        ver.click(); time.sleep(3)
    alvos = pg.get_by_text(alvo, exact=True)
    for i in range(alvos.count()):
        if alvos.nth(i).is_visible():
            alvos.nth(i).click(); break
    else:
        pg.screenshot(path=str(LOG / "fb_trocar_falhou.png"))
        raise SystemExit(f"'{alvo}' não visível no menu")
    time.sleep(10)
    print("trocado para", alvo, "->", pg.url)


porta, proc = fb_contas.abrir(conta)
try:
    with sync_playwright() as p:
        b = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
        ctx = b.contexts[0]
        pg = ctx.new_page()
        pg.set_viewport_size({"width": 1280, "height": 900})
        trocar(pg, nome)
        pg.screenshot(path=str(LOG / f"fb_perfil_{conta}_{nome.replace(' ', '_')}.png"))
        for t, h in fb_contas.listar_paginas(ctx):
            print("  pagina:", repr(t), h)
        pg2 = ctx.new_page()
        pg2.goto("https://www.facebook.com/pages/?category=your_pages", wait_until="domcontentloaded", timeout=45000)
        time.sleep(6)
        pg2.screenshot(path=str(LOG / f"fb_perfil_{conta}_{nome.replace(' ', '_')}_paginas.png"), full_page=True)
        pg2.close()
        if voltar:
            trocar(pg, voltar)
        pg.close()
finally:
    fb_contas.fechar(proc)
