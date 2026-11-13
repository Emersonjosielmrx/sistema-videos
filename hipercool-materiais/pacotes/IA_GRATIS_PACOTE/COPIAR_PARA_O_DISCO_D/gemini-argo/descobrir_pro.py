#!/usr/bin/env python3
r"""Testa as contas Google vivas do cofre e adiciona em contas_argon.json as que têm o 4 Argon (Pro).

Uma conta por vez, Chrome sem janela. Resultado de cada conta fica em descobrir_pro.json (retomável).
    python -I D:\gemini-argo\descobrir_pro.py
"""
import json
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, r"D:\gemini-argo")
import gemini_argon as ga
from gemini_argon import cofre

RESULTADO = Path(r"D:\gemini-argo\descobrir_pro.json")


def _liberar_ram():
    try:
        sys.path.insert(0, r"D:\logins-google")
        import chrome_conta
        chrome_conta._liberar_ram()
    except Exception:
        pass


def testar(email):
    from playwright.sync_api import sync_playwright
    porta, proc = cofre.abrir(email, url="about:blank", visivel=False)
    br = None
    try:
        with sync_playwright() as pw:
            br = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
            pg = br.contexts[0].new_page()
            pg.goto("https://gemini.google.com/app", wait_until="domcontentloaded", timeout=60000)
            time.sleep(5)
            if "accounts.google.com" in pg.url:
                return "deslogada"
            ga._fechar_popup_idade(pg)
            if not ga._selecionar_argon(pg):
                return "sem_argon"
            time.sleep(2)
            rotulo = pg.locator('button[aria-label*="seletor de modo"]').first.get_attribute("aria-label") or ""
            pg.close()
            return "pro" if "argon" in rotulo.lower() else f"sem_argon ({rotulo[-40:]})"
    finally:
        cofre.fechar(proc, br, email)


def main():
    feitos = json.loads(RESULTADO.read_text(encoding="utf-8")) if RESULTADO.exists() else {}
    ja_na_lista = {c["email"] for c in ga._ler_contas()["contas"]}
    reg = cofre._ler()["contas"]
    alvos = [e for e, d in sorted(reg.items())
             if d.get("google") == "vivo" and e.endswith("@gmail.com")
             and e not in ja_na_lista and e not in feitos]
    print(f"{len(alvos)} contas para testar")
    for email in alvos:
        _liberar_ram()
        try:
            r = testar(email)
        except Exception as e:
            r = f"erro: {str(e)[:120]}"
        feitos[email] = {"resultado": r, "quando": datetime.now().isoformat(timespec="minutes")}
        RESULTADO.write_text(json.dumps(feitos, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{email:42} {r}", flush=True)
        if r == "pro":
            ga.adicionar_conta(email)
    pro = [e for e, v in feitos.items() if v["resultado"] == "pro"]
    print(f"\nPro novas: {len(pro)} -> {pro}")


if __name__ == "__main__":
    main()
