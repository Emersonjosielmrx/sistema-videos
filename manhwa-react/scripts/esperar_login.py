"""esperar_login.py - SOMENTE LEITURA. Espera o login do Google aparecer no Chrome do perfil (porta CDP).
Olha so se os cookies de sessao EXISTEM (nao le o valor). Uso: esperar_login.py <porta> <minutos>"""
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
porta, minutos = int(sys.argv[1]), float(sys.argv[2])
fim = time.time() + minutos * 60
with sync_playwright() as p:
    br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
    ctx = br.contexts[0]
    while time.time() < fim:
        nomes = {c["name"] for c in ctx.cookies(["https://www.youtube.com", "https://accounts.google.com"])}
        urls = [pg.url[:80] for pg in ctx.pages]
        if {"SID", "__Secure-1PSID"} & nomes and any("youtube.com" in u for u in urls):
            print("LOGADO", urls, flush=True)
            break
        time.sleep(10)
    else:
        print("AINDA NAO", sorted(n for n in nomes if "SID" in n), urls, flush=True)
    br.close()  # so desconecta: o Chrome continua aberto para ela
