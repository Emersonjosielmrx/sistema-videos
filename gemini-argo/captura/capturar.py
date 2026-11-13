#!/usr/bin/env python3
r"""Captura o protocolo HTTP real do Gemini.

Abre o cofre, navega, manda uma pergunta com o modelo padrao e salva TUDO
(qualquer POST com corpo: url, headers, post body; e as respostas) em
captura/protocolo.json para eu reconstruir o cliente HTTP.
"""
import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import unquote

sys.path.insert(0, r"D:\logins-google")
sys.path.insert(0, r"D:\gemini-argo")
import cofre
import gemini_argon as ga
from playwright.sync_api import sync_playwright

CONTA = sys.argv[1] if len(sys.argv) > 1 else "emersonjosiel2030"
PERGUNTA = "Responda apenas com a palavra: FUNCIONOU"
SAIDA = Path(r"D:\gemini-argo\captura\protocolo.json")

dados = {"conta": CONTA, "pergunta": PERGUNTA, "requests": [], "page_tokens": {}}

porta, proc = cofre.abrir(CONTA, url="about:blank", visivel=False)
br = None
try:
    with sync_playwright() as pw:
        br = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
        pg = br.contexts[0].new_page()

        capturados = []

        def on_req(req):
            if req.method != "POST":
                return
            try:
                post = req.post_data
            except Exception:
                post = None
            if not post:
                return
            capturados.append({
                "url": req.url,
                "method": req.method,
                "headers": dict(req.headers),
                "post": post[:8000],
                "has_pergunta": "FUNCIONOU" in unquote(post),
            })

        pg.on("request", on_req)

        respostas = []

        def on_resp(resp):
            url = resp.url
            if "batchexecute" in url or "StreamGenerate" in url or "GenerateContent" in url:
                try:
                    body = resp.text()
                except Exception:
                    return
                if "wrb.fr" in body:
                    respostas.append({"url": url, "status": resp.status, "body": body[:20000]})

        pg.on("response", on_resp)

        pg.goto("https://gemini.google.com/app", wait_until="domcontentloaded", timeout=60000)
        time.sleep(5)
        ga._fechar_popup_idade(pg)

        html = pg.content()
        for nome, chave in [("at", "SNlM0e"), ("f_sid", "FdrFJe"), ("bl", "cfb2h"),
                             ("f_req_id", "qwAQke")]:
            m = re.search(r'"%s":"([^"]+)"' % chave, html)
            if m:
                dados["page_tokens"][nome] = m.group(1)

        # Garantir que nenhum menu esta aberto
        pg.keyboard.press("Escape")
        time.sleep(1)
        capturados.clear()
        respostas.clear()

        enviado = ga._enviar_pergunta(pg, PERGUNTA)
        dados["enviado"] = enviado
        time.sleep(18)

        pg.screenshot(path=r"D:\gemini-argo\captura\estado.png")

        dados["requests"] = capturados
        dados["respostas"] = respostas

        pg.close()
finally:
    cofre.fechar(proc, br, CONTA)

SAIDA.parent.mkdir(exist_ok=True)
SAIDA.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")

print("tokens:", dados["page_tokens"])
print("enviado:", dados.get("enviado"))
print("POSTs capturados:", len(dados["requests"]))
for r in dados["requests"]:
    marca = " <<< PERGUNTA" if r["has_pergunta"] else ""
    print(f"  {r['url'][:120]}{marca}")
print("respostas wrb.fr:", len(dados.get("respostas", [])))
print("salvo em", SAIDA)
