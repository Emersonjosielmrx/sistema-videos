"""Monta uma Página já criada: entra como ela, põe foto e capa e descobre o asset_id do Business Suite.
    python fb_montar_pagina.py <conta> "<Nome>" <profile_id> <foto> <capa>"""
import sys, time, re, collections, subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright
import fb_contas, fb_entrar_como
BIN = Path(__file__).resolve().parent
PY = sys.executable
conta, nome, pid, foto, capa = sys.argv[1:6]
url = f"https://www.facebook.com/profile.php?id={pid}"

porta, proc = fb_contas.abrir(conta)
try:
    with sync_playwright() as p:
        pg = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}").contexts[0].new_page()
        pg.set_viewport_size({"width": 1366, "height": 900})
        print("entrou como:", fb_entrar_como.entrar_como(pg, nome))
        pg.goto(url, wait_until="domcontentloaded", timeout=90000); time.sleep(8)
        ids = collections.Counter(re.findall(r'"delegate_page_id"\s*:\s*"?(\d{6,20})', pg.content()))
        print("asset_id:", ids.most_common(1)[0][0] if ids else None)
        pg.close()
    for scr, args in (("fb_foto_perfil.py", [conta, url, foto, nome.replace(" ", "_")]),
                      ("fb_foto_capa.py", [conta, url, foto, capa, nome.replace(" ", "_")])):
        r = subprocess.run([PY, str(BIN / scr)] + args, capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=str(BIN))
        print(scr, "->", (r.stdout.strip().splitlines() or ["?"])[-2:])
finally:
    fb_contas.fechar(proc)
