#!/usr/bin/env python3
r"""Captura o StreamGenerate do Gemini web com o Argon em cada nível de raciocínio (Baixo, Médio, Alto), para achar
o campo que leva o nível (o gemini_http só mandava o hash do modelo). Salva em captura/nivel_raciocinio.json.
    python -X utf8 capturar_nivel.py <conta>
"""
import json
import sys
import time
from pathlib import Path
from urllib.parse import parse_qs

sys.path.insert(0, r"D:\logins-google")
sys.path.insert(0, r"D:\gemini-argo")
import cofre
import gemini_argon as ga
from playwright.sync_api import sync_playwright

CONTA = sys.argv[1]
SAIDA = Path(__file__).with_name("nivel_raciocinio.json")
NIVEIS = {"Baixo": ["text=Baixo", "text=Low"], "Médio": ["text=Médio", "text=Medium"], "Alto": ["text=Alto", "text=High"]}


def nivel(pg, nome):
    if not ga._abrir_dropdown_modelo(pg):
        return False
    for sel in ['text=Nível de raciocínio', 'text=Reasoning level', 'button:has-text("raciocínio")']:
        try:
            el = pg.locator(sel).first
            if el.is_visible(timeout=3000):
                el.click()
                time.sleep(1.5)
                break
        except Exception:  # noqa: BLE001
            continue
    for sel in NIVEIS[nome]:
        try:
            el = pg.locator(sel).first
            if el.is_visible(timeout=3000):
                el.click()
                time.sleep(1)
                pg.keyboard.press("Escape")
                return True
        except Exception:  # noqa: BLE001
            continue
    pg.keyboard.press("Escape")
    return False


resultado = {}
porta, proc = cofre.abrir(CONTA, url="about:blank", visivel=False)
br = None
try:
    with sync_playwright() as pw:
        br = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
        pg = br.contexts[0].new_page()
        pegos, posts = [], []
        pg.on("request", lambda r: posts.append(r.url[:110]) if r.method == "POST" else None)
        pg.on("request", lambda r: pegos.append(r) if "StreamGenerate" in r.url and r.method == "POST" else None)
        sessao = []  # 27/10: o app novo manda a pergunta por geminiweb-pa.../v1/processSession
        pg.on("request", lambda r: sessao.append({"url": r.url, "headers": dict(r.headers),
                                                  "post": (r.post_data_buffer or b"").decode("utf-8", "replace")[:20000]})
              if "processSession" in r.url and r.method == "POST" else None)
        for nome in NIVEIS:
            pg.goto("https://gemini.google.com/app", wait_until="domcontentloaded", timeout=60000)
            time.sleep(5)
            ga._fechar_popup_idade(pg)
            argon = ga._selecionar_argon(pg)
            ok = nivel(pg, nome)
            rotulo = pg.locator('button[aria-label*="seletor de modo"]').first.get_attribute("aria-label") or ""
            pegos.clear()
            posts.clear()
            sessao.clear()
            enviou = ga._enviar_pergunta(pg, f"Responda só: nivel {nome}")
            time.sleep(20)
            print(nome, "enviou", enviou, "POSTs:", posts[:6], flush=True)
            pg.screenshot(path=str(SAIDA.with_name(f"_nivel_{nome}.png")))
            if not pegos:
                resultado[nome] = {"erro": "sem StreamGenerate", "argon": argon, "nivel_ok": ok, "rotulo": rotulo,
                                   "sessao": list(sessao)}
                continue
            r = pegos[-1]
            inner = json.loads(json.loads(parse_qs(r.post_data)["f.req"][0])[1])
            resultado[nome] = {"argon": argon, "nivel_ok": ok, "rotulo": rotulo,
                               "jspb": r.headers.get("x-goog-ext-525001261-jspb"),
                               "inner": {i: x for i, x in enumerate(inner) if x is not None and i not in (0, 3)}}
            print(nome, "argon", argon, "nivel", ok, rotulo[-40:], flush=True)
        pg.close()
finally:
    cofre.fechar(proc, br, CONTA)

SAIDA.write_text(json.dumps(resultado, ensure_ascii=False, indent=1), encoding="utf-8")
# o que muda entre os níveis
ns = [n for n in NIVEIS if "inner" in resultado.get(n, {})]
if len(ns) > 1:
    chaves = set().union(*(resultado[n]["inner"] for n in ns))
    for k in sorted(chaves):
        vals = [json.dumps(resultado[n]["inner"].get(k)) for n in ns]
        if len(set(vals)) > 1:
            print("corpo campo", k, dict(zip(ns, vals)))
    js = [json.loads(resultado[n]["jspb"] or "[]") for n in ns]
    for i in range(max(map(len, js))):
        vals = [json.dumps(j[i] if i < len(j) else None) for j in js]
        if len(set(vals)) > 1 and i not in (16, 19):
            print("cabeçalho pos", i, dict(zip(ns, vals)))
