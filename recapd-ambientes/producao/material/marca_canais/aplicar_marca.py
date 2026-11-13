"""Aplica banner e/ou foto de perfil no canal pelo YouTube Studio, tira a marca-d'água e publica.

Uso:  python aplicar_marca.py <email> <channel_id> <slug> banner,foto
Imagens nesta pasta: <slug>_banner.jpg (2560x1440, até 6 MB) e <slug>_perfil.png (até 4 MB).
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, r"D:\logins-google")
import cofre  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

MARCA = Path(__file__).resolve().parent
if len(sys.argv) != 5:
    sys.exit(__doc__)
email, cid, slug, oque = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4].split(",")

SECAO_JS = """e => { let x = e;
    for (let k = 0; k < 8 && x; k++) { x = x.parentElement;
      if (x && x.innerText && x.innerText.length > 40) return x.innerText.slice(0, 300); }
    return ''; }"""


def achar(pg, seletor, chave):
    for b in pg.locator(seletor).all():
        if b.is_visible() and chave in b.evaluate(SECAO_JS):
            return b
    return None


def enviar(pg, chave, arquivo, nome):
    b = achar(pg, "#upload-button", chave) or achar(pg, "ytcp-button:has-text('Alterar')", chave)
    if b is None:
        raise RuntimeError(f"botão de {nome} não encontrado")
    with pg.expect_file_chooser(timeout=20000) as fc:
        b.click()
    fc.value.set_files(str(arquivo))
    pronto = pg.locator("#done-button:visible")
    pronto.first.wait_for(timeout=60000)
    time.sleep(2)
    pronto.first.click()
    time.sleep(5)
    print(f"  {nome}: enviado", flush=True)


# Abrir o Chrome já na URL do Studio às vezes travava a página (botões nunca apareciam): abre vazio e navega depois.
porta, proc = cofre.abrir(email, visivel=True)
time.sleep(5)
with sync_playwright() as p:
    br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}", timeout=30000)
    try:
        pg = br.contexts[0].new_page()
        pg.goto(f"https://studio.youtube.com/channel/{cid}/editing/profile", wait_until="commit", timeout=60000)
        pg.locator("#upload-button, ytcp-button:has-text('Alterar')").first.wait_for(timeout=90000)
        time.sleep(6)
        d = pg.locator("#dismiss-button:visible")
        if d.count():
            d.first.click()
            time.sleep(2)
        if "banner" in oque:
            enviar(pg, "6 MB", MARCA / f"{slug}_banner.jpg", "banner")
        if "foto" in oque:
            enviar(pg, "98 x 98", MARCA / f"{slug}_perfil.png", "foto")
        rm = achar(pg, "ytcp-button:has-text('Remover')", "Tempo de exibição")
        if rm is not None:
            rm.click()
            time.sleep(3)
            print("  marca-d'água: removida", flush=True)
        pub = pg.locator("#publish-button")
        if pub.get_attribute("aria-disabled") != "true":
            pub.click()
            time.sleep(12)
        print("  publicado (botão Publicar desativado):", pub.get_attribute("aria-disabled") == "true", flush=True)
    finally:
        cofre.fechar(proc, br)
print("fim", slug)
