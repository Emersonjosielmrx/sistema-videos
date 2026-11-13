#!/usr/bin/env python3
r"""Teste do protocolo HTTP puro (sem navegador) do Gemini Argon."""
import json
import re
import sys
from pathlib import Path
import requests

CONTA = sys.argv[1] if len(sys.argv) > 1 else "emersonjosiel2030"
PERGUNTA = sys.argv[2] if len(sys.argv) > 2 else "Responda apenas: FUNCIONOU HTTP"
ARGON = "95a4c0abcba24364"

cookies = json.load(open(rf"D:\gemini-argo\captura\cookies_{CONTA}.json", encoding="utf-8"))

s = requests.Session()
s.cookies.update(cookies)
s.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/156.0.0.0 Safari/537.36",
})

# 1) GET a pagina pra pegar at (SNlM0e), bl (cfb2h), f.sid (FdrFJe)
r = s.get("https://gemini.google.com/app")
print("GET /app status", r.status_code, "len", len(r.text))
html = r.text
def pega(chave):
    m = re.search(r'"%s":"([^"]+)"' % chave, html)
    return m.group(1) if m else None
at = pega("SNlM0e")
bl = pega("cfb2h")
fsid = pega("FdrFJe")
print("at:", (at or "")[:30], "| bl:", bl, "| f.sid:", fsid)
if not at:
    print("!!! SNlM0e nao encontrado — cookies invalidos ou pagina de login")
    Path(r"D:\gemini-argo\captura\get_app.html").write_text(html, encoding="utf-8")
    sys.exit(1)

# 2) Montar f.req minimo
inner = [[PERGUNTA, 0, None, None, None, None, 0], ["pt"], None]
freq = json.dumps([None, json.dumps(inner, ensure_ascii=False)], ensure_ascii=False)

model_header = json.dumps([1, None, None, None, ARGON])

url = ("https://gemini.google.com/_/BardChatUi/data/"
       "assistant.lamda.BardFrontendService/StreamGenerate"
       f"?bl={bl}&f.sid={fsid}&hl=pt&_reqid=100000&rt=c")

headers = {
    "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
    "x-same-domain": "1",
    "x-goog-ext-525001261-jspb": model_header,
    "Origin": "https://gemini.google.com",
    "Referer": "https://gemini.google.com/",
}

r2 = s.post(url, data={"f.req": freq, "at": at}, headers=headers)
print("POST StreamGenerate status", r2.status_code, "len", len(r2.text))
body = r2.text
Path(r"D:\gemini-argo\captura\resp_http.txt").write_text(body, encoding="utf-8")
print(body[:1500])

# 3) Parsear a resposta
def parse(body):
    for linha in body.split("\n"):
        linha = linha.strip()
        if not linha.startswith("[["):
            continue
        try:
            arr = json.loads(linha)
        except Exception:
            continue
        for item in arr:
            if item and item[0] == "wrb.fr" and len(item) > 2 and item[2]:
                try:
                    data = json.loads(item[2])
                except Exception:
                    continue
                if isinstance(data, list) and len(data) > 4 and data[4]:
                    cand = data[4][0]
                    if len(cand) > 1 and cand[1]:
                        return cand[1][0]
    return None

texto = parse(body)
print("\n=== RESPOSTA PARSEADA ===")
print(repr(texto))
