r"""
Abre a Colab da emersonjosiel649 (Chrome do cofre), roda o notebook colab_recap.ipynb do Drive dela ("Executar
tudo") e passa pelos avisos (notebook de fora, acesso ao Drive). Deixa a aba aberta: a Colab só roda com ela aberta.

  python abrir_colab.py          # abre e roda; prints em colab\prints\
  python abrir_colab.py --ver    # só abre e tira print (não roda)
Plano: producao/COLAB_RECAP_LONGO.md
"""
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, r"D:\logins-google")
import cofre
from playwright.sync_api import sync_playwright

CONTA = "emersonjosiel649"
EMAIL = "emersonjosiel649@gmail.com"
RCLONE = r"D:\tools\rclone.exe"
PRINTS = Path(__file__).resolve().parent / "prints"
CLIQUES = ("Executar mesmo assim", "Run anyway", "Conectar ao Google Drive", "Connect to Google Drive",
           "Continuar", "Continue", "Permitir", "Allow", "Selecionar tudo", "Select all")


def _print(page, nome):
    PRINTS.mkdir(exist_ok=True)
    try:
        page.screenshot(path=str(PRINTS / f"{datetime.now():%H%M%S}_{nome}.png"))
    except Exception:
        pass


def _id_notebook():
    r = subprocess.run([RCLONE, "lsjson", "manhwa-drive:colab_recap/colab_recap.ipynb"], capture_output=True, text=True,
                       check=True)
    return json.loads(r.stdout)[0]["ID"]


def _clicar_avisos(ctx, segundos):
    """Clica nos avisos da Colab e nas janelas do Google (escolher conta, permitir Drive) por `segundos`."""
    fim = time.time() + segundos
    while time.time() < fim:
        for pg in list(ctx.pages):
            try:
                if "accountchooser" in pg.url or "selectaccount" in pg.url.lower():
                    e = pg.get_by_text(EMAIL, exact=True)
                    if e.count() and e.first.is_visible():
                        e.first.click()
                        continue
                if "accounts.google.com" in pg.url:
                    cx = pg.locator('input[type="checkbox"]:not(:checked)')
                    for i in range(cx.count()):
                        try:
                            cx.nth(i).check(timeout=2000)
                        except Exception:
                            pass
                for txt in CLIQUES:
                    b = pg.get_by_role("button", name=txt, exact=True)
                    if b.count() and b.first.is_visible() and b.first.is_enabled():
                        b.first.click(timeout=3000)
                        pg.wait_for_timeout(1500)
                        break
            except Exception:
                pass
        time.sleep(2)


def abrir(rodar=True):
    import cliente
    cliente.gravar_token()
    url = f"https://colab.research.google.com/drive/{_id_notebook()}"
    porta, _proc = cofre.abrir(CONTA, url="about:blank", visivel=True)
    p = sync_playwright().start()
    br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
    ctx = br.contexts[0]
    for velha in ctx.pages:  # uma sessão só
        if "colab.research" in velha.url:
            velha.close(run_before_unload=False)
    page = ctx.new_page()
    page.goto(url, timeout=90000)
    page.wait_for_timeout(15000)
    _print(page, "aberto")
    if not rodar:
        return
    page.locator("body").click()
    page.keyboard.press("Control+F9")
    _clicar_avisos(ctx, 240)
    _print(page, "rodando")
    print("Colab rodando; aba fica aberta. Conferir: python cliente.py vivo", flush=True)
    # sem fechar o Chrome nem o playwright: a sessão da Colab depende da aba aberta


if __name__ == "__main__":
    abrir(rodar="--ver" not in sys.argv)
