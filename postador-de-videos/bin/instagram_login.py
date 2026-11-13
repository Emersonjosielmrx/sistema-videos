# -*- coding: utf-8 -*-
"""Loga contas do Instagram (usuário + senha) num Chrome próprio do cofre (D:/logins-google/cofre, entrada "ig_<usuário>"),
para o postar_insta_auto.py postar pelo navegador nas contas sem token. Uma conta por vez; senha só por variável de
ambiente (IG_SENHA), nunca em arquivo. Desafio do Instagram (código, "foi você?") = o dono resolve na janela
(IG_ESPERA segundos, padrão 180).

  set IG_SENHA=...  &&  python bin/instagram_login.py recenas.ia fakenews.ia4 ...
"""
import json
import os
import sys
import time

sys.path.insert(0, r"D:\logins-google")
import cofre  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

FORM = "https://www.instagram.com/api/v1/accounts/edit/web_form_data/"
PRINTS = r"C:\Users\Haylla\AppData\Local\Temp\q_veo"


def chave(usuario):
    return f"ig_{usuario.strip().lower()}"


def usuario_logado(pg):
    """@ da sessão, perguntado ao próprio Instagram (cookie sozinho não prova login)."""
    try:
        r = pg.evaluate(f"async () => (await fetch('{FORM}', {{credentials: 'include', "
                        "headers: {'X-IG-App-ID': '936619743392459'}})).text()")
        return (json.loads(r).get("form_data") or {}).get("username")
    except Exception:  # noqa: BLE001
        return None


def logar(p, usuario, senha):
    k = chave(usuario)
    try:
        cofre.conta(k)
    except KeyError:
        cofre.registrar(k, usos={"instagram": usuario}, tipo="instagram")
    porta, proc = cofre.abrir(k, "about:blank", visivel=True)
    br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
    try:
        pg = br.contexts[0].new_page()
        pg.goto("https://www.instagram.com/", wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(4000)
        u = usuario_logado(pg)
        if u:
            return f"já estava logado: @{u}"
        pg.goto("https://www.instagram.com/accounts/login/", wait_until="domcontentloaded", timeout=60000)
        campo = pg.locator("input[name=username], input[name=email], input[autocomplete*=username]").first
        for _ in range(15):
            for t in ("Permitir todos os cookies", "Allow all cookies", "Recusar cookies opcionais"):
                b = pg.get_by_role("button", name=t)
                if b.count() and b.first.is_visible():
                    b.first.click()
            if campo.count() and campo.is_visible():
                break
            pg.wait_for_timeout(2000)
        else:
            pg.screenshot(path=rf"{PRINTS}\ig_{usuario}_tela.png")
            return f"não achei o campo de usuário (ver ig_{usuario}_tela.png)"
        campo.fill(usuario)
        if senha:
            pg.locator("input[name=password], input[type=password]").first.fill(senha)
            pg.keyboard.press("Enter")
        else:  # sem IG_SENHA: o dono digita a senha na janela (usuário já preenchido) e o script espera o login
            pg.locator("input[name=password], input[type=password]").first.click()
        fim = time.time() + int(os.environ.get("IG_ESPERA", "180"))
        while time.time() < fim:
            pg.wait_for_timeout(3000)
            for t in ("Agora não", "Not now", "Agora nao"):
                b = pg.get_by_role("button", name=t)
                try:
                    if b.count() and b.first.is_visible():
                        b.first.click()
                except Exception:  # noqa: BLE001
                    pass
            try:
                txt = pg.inner_text("body", timeout=2000).lower()
            except Exception:  # noqa: BLE001
                txt = ""
            if any(s in txt for s in ("senha incorreta", "incorrect password", "sua senha está incorreta",
                                      "estão incorretas", "login information you entered is incorrect")):
                pg.screenshot(path=rf"{PRINTS}\ig_{usuario}_senha.png")
                return "SENHA INCORRETA (o Instagram recusou)"
            u = usuario_logado(pg)
            if u:
                return f"LOGADO: @{u}"
        pg.screenshot(path=rf"{PRINTS}\ig_{usuario}_falhou.png")
        return f"não logou (desafio do Instagram? ver ig_{usuario}_falhou.png)"
    finally:
        cofre.fechar(proc, br, k)


if __name__ == "__main__":
    if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    senha = os.environ.get("IG_SENHA")  # vazio = o dono digita na janela
    with sync_playwright() as p:
        for nome in sys.argv[1:]:
            try:
                print(f"{nome}: {logar(p, nome, senha)}", flush=True)
            except Exception as ex:  # noqa: BLE001
                print(f"{nome}: ERRO {type(ex).__name__}: {str(ex)[:160]}", flush=True)
