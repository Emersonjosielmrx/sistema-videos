#!/usr/bin/env python3
r"""Captura o catalogo de modelos do Gemini (hash + array de capacidade de cada modelo).

Navega, coleta todas as respostas batchexecute e salva a que contem a lista de modelos.
"""
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, r"D:\logins-google")
sys.path.insert(0, r"D:\gemini-argo")
import cofre
import gemini_argon as ga
from playwright.sync_api import sync_playwright

CONTA = sys.argv[1] if len(sys.argv) > 1 else "emersonjosiel2030"
SAIDA = Path(r"D:\gemini-argo\captura\catalogo.json")

porta, proc = cofre.abrir(CONTA, url="about:blank", visivel=False)
br = None
achados = []
try:
    with sync_playwright() as pw:
        br = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
        pg = br.contexts[0].new_page()

        def on_resp(resp):
            if "batchexecute" not in resp.url:
                return
            try:
                body = resp.text()
            except Exception:
                return
            if "Argon" in body or "Thinking" in body or "Flash-Lite" in body:
                achados.append({"url": resp.url, "body": body})

        pg.on("response", on_resp)
        pg.goto("https://gemini.google.com/app", wait_until="domcontentloaded", timeout=60000)
        time.sleep(6)
        ga._fechar_popup_idade(pg)
        # abrir o seletor de modelo forca o carregamento do catalogo
        ga._abrir_dropdown_modelo(pg)
        time.sleep(3)
        pg.screenshot(path=r"D:\gemini-argo\captura\dropdown.png")
        pg.close()
finally:
    cofre.fechar(proc, br, CONTA)

SAIDA.write_text(json.dumps(achados, ensure_ascii=False), encoding="utf-8")
print("respostas com modelos:", len(achados))
# extrair pares hash -> nome e tentar achar o array de capacidade perto de "Argon"
for a in achados:
    b = a["body"]
    for m in re.finditer(r'\\"([0-9a-f]{14,18})\\",\\"([^\\"]{2,40})\\"', b):
        print(m.group(1), "->", m.group(2))
    # contexto ao redor de Argon
    i = b.find("Argon")
    if i >= 0:
        print("--- contexto Argon ---")
        print(b[max(0, i-400):i+200])
print("salvo em", SAIDA)
