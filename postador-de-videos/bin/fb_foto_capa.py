"""Coloca foto de perfil e capa numa Página nova (perfil novo do FB). Troca para a Página ('Trocar agora'), envia as
imagens e salva. Prints em logs/fb_fc_<tag>_*.png.
    python fb_foto_capa.py <conta> <url_pagina> <foto.png> <capa.png> <tag>"""
import sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright
import fb_contas

LOG = Path(__file__).resolve().parent.parent / "logs"
conta, url, foto, capa, tag = sys.argv[1:6]


def vis(pg, loc):
    for i in range(loc.count()):
        if loc.nth(i).is_visible():
            return loc.nth(i)
    return None


def salvar(pg, nome):
    for _ in range(40):
        b = vis(pg, pg.get_by_role("button", name="Salvar", exact=True)) or vis(pg, pg.get_by_role("button", name="Salvar alterações"))
        if b and (b.get_attribute("aria-disabled") or "false") == "false":
            pg.screenshot(path=str(LOG / f"fb_fc_{tag}_{nome}_antes_salvar.png"))
            b.click(); time.sleep(8)
            return True
        time.sleep(2)
    pg.screenshot(path=str(LOG / f"fb_fc_{tag}_{nome}_sem_salvar.png"))
    return False


porta, proc = fb_contas.abrir(conta)
try:
    with sync_playwright() as p:
        b = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
        pg = b.contexts[0].new_page()
        pg.set_viewport_size({"width": 1366, "height": 900})
        # 20/11: entra como a Página pelo cookie i_user (as telas de troca travavam o clique)
        import re as _re, fb_entrar_como
        fb_entrar_como.entrar_como_cookie(b.contexts[0], (_re.search(r"id=(\d+)", url) or [None, None])[1])
        pg.goto(url, wait_until="domcontentloaded", timeout=90000)
        time.sleep(8)
        t = vis(pg, pg.get_by_role("button", name="Trocar agora")) or vis(pg, pg.get_by_text("Trocar agora", exact=True)) or vis(pg, pg.get_by_role("button", name="Alternar", exact=True)) or vis(pg, pg.get_by_text("Alternar", exact=True))
        if t:
            try:
                t.click(timeout=8000); time.sleep(4)
                c = vis(pg, pg.get_by_role("button", name="Trocar", exact=True))
                if c:
                    c.click(timeout=8000)
            except Exception:
                pass
            time.sleep(12)
            pg.goto(url, wait_until="domcontentloaded", timeout=90000)
            time.sleep(10)
        for nome_b in ("Usar Página", "Agora não", "Fechar", "OK"):
            u = vis(pg, pg.get_by_role("button", name=nome_b, exact=True))
            if u:
                try:
                    u.click(timeout=5000); time.sleep(3)
                except Exception:
                    pg.keyboard.press("Escape"); time.sleep(1)
        pg.screenshot(path=str(LOG / f"fb_fc_{tag}_1_como_pagina.png"))

        # FOTO DE PERFIL: clica na foto grande -> "Atualizar foto do perfil" -> "Carregar foto"
        f = vis(pg, pg.locator('[aria-label="Atualizar foto do perfil"], [aria-label="Update profile picture"]'))
        if not f:
            f = vis(pg, pg.locator("svg[aria-label] >> xpath=ancestor::a[1]").filter(has_text=""))
        if f:
            f.click(); time.sleep(4)
            up = vis(pg, pg.get_by_text("Carregar foto", exact=True)) or vis(pg, pg.get_by_text("Upload photo", exact=True))
            if up:
                with pg.expect_file_chooser(timeout=20000) as fc:
                    up.click()
                fc.value.set_files(str(Path(foto).resolve()))
                time.sleep(8)
                print("foto:", "salva" if salvar(pg, "foto") else "SEM BOTAO SALVAR")
            else:
                pg.screenshot(path=str(LOG / f"fb_fc_{tag}_foto_menu.png")); print("foto: sem 'Carregar foto'")
        else:
            print("foto: botão não achado")
        pg.keyboard.press("Escape"); time.sleep(2)
        pg.goto(url, wait_until="domcontentloaded", timeout=90000); time.sleep(10)

        # CAPA: "Adicionar foto da capa" / "Editar foto da capa" -> "Carregar foto"
        c = vis(pg, pg.get_by_role("button", name="Adicionar foto da capa")) or vis(pg, pg.get_by_text("Adicionar foto da capa")) \
            or vis(pg, pg.get_by_role("button", name="Editar foto da capa")) or vis(pg, pg.get_by_text("Editar foto da capa"))
        if c:
            c.click(); time.sleep(3)
            up = vis(pg, pg.get_by_text("Carregar foto", exact=True)) or vis(pg, pg.get_by_text("Upload photo", exact=True))
            if up:
                with pg.expect_file_chooser(timeout=20000) as fc:
                    up.click()
            else:
                with pg.expect_file_chooser(timeout=20000) as fc:
                    c.click()
            fc.value.set_files(str(Path(capa).resolve()))
            time.sleep(10)
            print("capa:", "salva" if salvar(pg, "capa") else "SEM BOTAO SALVAR")
        else:
            print("capa: botão não achado")
        pg.goto(url, wait_until="domcontentloaded", timeout=90000); time.sleep(10)
        pg.screenshot(path=str(LOG / f"fb_fc_{tag}_2_final.png"))
        pg.close()
finally:
    fb_contas.fechar(proc)
