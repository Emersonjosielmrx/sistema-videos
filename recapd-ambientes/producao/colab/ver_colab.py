"""Lê a aba da Colab já aberta (Chrome do cofre da 649): saída das células e print. Não mexe em nada.

  python ver_colab.py
"""
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright

PORTA = 9719  # cofre: emersonjosiel649
PRINTS = Path(__file__).resolve().parent / "prints"

with sync_playwright() as p:
    br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{PORTA}")
    for pg in br.contexts[0].pages:
        if "colab.research" in pg.url and "/drive/" in pg.url:
            for i, saida in enumerate(pg.locator(".output, colab-static-output-renderer, .output_area").all()):
                try:
                    txt = saida.inner_text(timeout=5000).strip()
                except Exception:
                    continue
                if txt:
                    print(f"--- saída {i} ---\n{txt[-3000:]}")
            for fr in pg.frames[1:]:  # saídas grandes/erros ficam em iframe
                try:
                    txt = fr.locator("body").inner_text(timeout=3000).strip()
                except Exception:
                    continue
                if txt:
                    print(f"--- iframe ---\n{txt[-3000:]}")
            PRINTS.mkdir(exist_ok=True)
            try:
                pg.screenshot(path=str(PRINTS / f"{datetime.now():%H%M%S}_ver.png"), timeout=15000)
            except Exception:
                pass
