"""Só a FOTO de perfil da Página (já trocado para a Página). Clica na foto grande -> menu -> 'Escolher foto do perfil'
/'Atualizar foto do perfil' -> 'Carregar foto' -> Salvar.  python fb_foto_perfil.py <conta> <url> <foto.png> <tag>"""
import sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright
import fb_contas
LOG = Path(__file__).resolve().parent.parent / "logs"
conta, url, foto, tag = sys.argv[1:5]


def vis(loc):
    for i in range(loc.count()):
        if loc.nth(i).is_visible():
            return loc.nth(i)
    return None


porta, proc = fb_contas.abrir(conta)
try:
    with sync_playwright() as p:
        b = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
        pg = b.contexts[0].new_page()
        pg.set_viewport_size({"width": 1366, "height": 900})
        pg.goto(url, wait_until="domcontentloaded", timeout=90000)
        time.sleep(10)
        t = vis(pg.get_by_role("button", name="Trocar agora")) or vis(pg.get_by_role("button", name="Alternar", exact=True)) or vis(pg.get_by_text("Alternar", exact=True))
        if t:
            t.click(); time.sleep(4)
            c = vis(pg.get_by_role("button", name="Trocar", exact=True))
            if c: c.click()
            time.sleep(12); pg.goto(url, wait_until="domcontentloaded", timeout=90000); time.sleep(10)
        for nome_b in ("Usar Página", "Agora não"):
            u = vis(pg.get_by_role("button", name=nome_b, exact=True))
            if u: u.click(); time.sleep(3)
        pg.mouse.wheel(0, -2000); time.sleep(2)
        # botão câmera da foto: aria-label com "foto do perfil"
        alvo = vis(pg.locator('[aria-label*="foto do perfil" i], [aria-label*="profile picture" i]'))
        if not alvo:
            # clica no centro da foto grande (círculo à esquerda do nome)
            nome = vis(pg.get_by_role("heading", level=1))
            bb = nome.bounding_box()
            pg.mouse.click(bb["x"] - 110, bb["y"] + 40)
        else:
            print("achou:", alvo.get_attribute("aria-label")); alvo.click()
        time.sleep(4)
        pg.screenshot(path=str(LOG / f"fb_fp_{tag}_menu.png"))
        for t_ in ("Escolher foto do perfil", "Atualizar foto do perfil", "Choose profile picture"):
            m = vis(pg.get_by_text(t_, exact=True))
            if m:
                m.click(); time.sleep(4); break
        up = vis(pg.get_by_text("Carregar foto", exact=True)) or vis(pg.get_by_text("Upload photo", exact=True))
        if not up:
            pg.screenshot(path=str(LOG / f"fb_fp_{tag}_sem_carregar.png")); print("sem 'Carregar foto'"); sys.exit(2)
        with pg.expect_file_chooser(timeout=20000) as fc:
            up.click()
        fc.value.set_files(str(Path(foto).resolve()))
        time.sleep(10)
        for _ in range(30):
            s = vis(pg.get_by_role("button", name="Salvar", exact=True))
            if s and (s.get_attribute("aria-disabled") or "false") == "false":
                s.click(); print("foto salva"); break
            time.sleep(2)
        else:
            pg.screenshot(path=str(LOG / f"fb_fp_{tag}_sem_salvar.png")); print("sem Salvar")
        time.sleep(10)
        pg.goto(url, wait_until="domcontentloaded", timeout=90000); time.sleep(10)
        pg.screenshot(path=str(LOG / f"fb_fp_{tag}_final.png"))
        pg.close()
finally:
    fb_contas.fechar(proc)
