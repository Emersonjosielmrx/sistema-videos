# -*- coding: utf-8 -*-
"""Loga o TikTok pelo "Continuar com Google" usando o Google que já está logado no perfil do cofre da conta
(D:/logins-google/cofre): o TikTok fica no MESMO Chrome do YouTube. Só serve pra TikTok criado com esse Google: se o
Google abriria um cadastro novo (pede data de nascimento), para e avisa — nunca cria conta.

  python bin/tiktok_login_google.py emersonjosiel2027 emersonjosiel2029 ...
"""
import json
import os
import re
import sys
import time

sys.path.insert(0, r"D:\logins-google")
import cofre  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

INFO = "https://www.tiktok.com/passport/web/account/info/?aid=1459"


def _sessao(ctx):
    return any(c["name"] == "sessionid" and c["value"] for c in ctx.cookies("https://www.tiktok.com"))


def _ir(pg, url):
    """Navega tolerando o redirecionamento do próprio TikTok logo depois do login (net::ERR_ABORTED)."""
    try:
        pg.goto(url, wait_until="domcontentloaded", timeout=60000)
    except Exception:  # noqa: BLE001
        pg.wait_for_timeout(4000)


def _usuario(pg):
    try:
        r = pg.evaluate(f"async () => (await fetch('{INFO}', {{credentials: 'include'}})).text()")
        return (json.loads(r).get("data") or {}).get("username")
    except Exception:  # noqa: BLE001
        return None


def _codigos_gmail(ctx):
    """Códigos de 6 dígitos nos e-mails do TikTok da última hora (o Gmail da conta está logado no mesmo perfil)."""
    g = ctx.new_page()
    try:
        g.goto("https://mail.google.com/mail/u/0/#search/from%3Atiktok+newer_than%3A1h",
               wait_until="domcontentloaded", timeout=60000)
        g.wait_for_timeout(6000)
        linhas = g.locator("tr.zA")
        return [m for i in range(min(linhas.count(), 5))
                for m in re.findall(r"\b\d{6}\b", linhas.nth(i).inner_text())]
    except Exception:  # noqa: BLE001
        return []
    finally:
        g.close()


def _verificar_por_email(ctx, pg, apelido):
    """19/10: depois do Google o TikTok pede "Verifique se é você" (código no e-mail). Pede o código, lê no Gmail e
    digita. True se digitou um código novo."""
    antes = set(_codigos_gmail(ctx))
    pg.get_by_text("E-mail", exact=True).first.click()
    pg.wait_for_timeout(4000)
    for t in ("Enviar código", "Enviar", "Send code"):
        b = pg.get_by_role("button", name=t)
        if b.count() and b.first.is_visible() and b.first.is_enabled():
            b.first.click()
            break
    pg.screenshot(path=rf"C:\Users\Haylla\AppData\Local\Temp\q_veo\tk_{apelido}_codigo.png")
    for _ in range(12):
        pg.wait_for_timeout(10000)
        novos = [c for c in _codigos_gmail(ctx) if c not in antes]
        if novos:
            campo = pg.locator("input:visible").first
            campo.click()
            pg.keyboard.type(novos[0], delay=120)
            pg.wait_for_timeout(1500)
            for t in ("Verificar", "Avançar", "Next", "Confirmar"):
                b = pg.get_by_role("button", name=t)
                if b.count() and b.first.is_visible() and b.first.is_enabled():
                    b.first.click()
                    break
            return True
    return False


def _criar_conta(pg, apelido):
    """Dono 19/10 ("pode criar as contas"): TK_CRIAR=1 completa o cadastro que o Google abriu — data de nascimento de
    adulto fixa e o nome de usuário que o próprio TikTok sugere."""
    for campo, valor in (("Mês", "Março"), ("Dia", "15"), ("Ano", "1995")):
        pg.get_by_text(campo, exact=True).first.click()
        pg.wait_for_timeout(800)
        pg.get_by_text(valor, exact=True).last.click()
        pg.wait_for_timeout(800)
    pg.screenshot(path=rf"C:\Users\Haylla\AppData\Local\Temp\q_veo\tk_{apelido}_criar1.png")
    pg.get_by_role("button", name=re.compile("Seguinte|Avançar|Próximo|Next")).first.click()
    pg.wait_for_timeout(6000)
    pg.screenshot(path=rf"C:\Users\Haylla\AppData\Local\Temp\q_veo\tk_{apelido}_criar2.png")
    for t in ("Inscrever-se", "Registar", "Registrar", "Cadastrar", "Sign up", "Ignorar", "Pular", "Skip"):
        b = pg.get_by_role("button", name=t)
        if b.count() and b.first.is_visible() and b.first.is_enabled():
            b.first.click()
            break


def logar(p, nome):
    email, e = cofre.conta(nome)
    if e.get("google") != "vivo":
        return f"Google {e.get('google')} no cofre: logar o Google antes (python D:\\logins-google\\cofre.py logar {e['apelido']})"
    porta, proc = cofre.abrir(email, "about:blank", visivel=True)
    br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
    try:
        ctx = br.contexts[0]
        pg = ctx.new_page()
        if _sessao(ctx):
            _ir(pg, "https://www.tiktok.com/")
            return f"já estava logado: @{_usuario(pg)}"
        pg.goto("https://www.tiktok.com/login", wait_until="domcontentloaded", timeout=60000)
        pg.get_by_text("Continuar com Google").first.wait_for(timeout=30000)
        with ctx.expect_page(timeout=30000) as nova:
            pg.get_by_text("Continuar com Google").first.click()
        pop = nova.value
        pop.wait_for_load_state("domcontentloaded")
        conta = pop.locator(f'[data-identifier="{email}"]')
        try:
            conta.first.wait_for(timeout=15000)
            conta.first.click()
        except Exception:  # noqa: BLE001
            if not pop.is_closed():
                pop.screenshot(path=rf"C:\Users\Haylla\AppData\Local\Temp\q_veo\tk_{e['apelido']}_popup.png")
                return f"o Google não mostrou a conta {email} no popup (ver tk_{e['apelido']}_popup.png)"
        espera = int(os.environ.get("TK_ESPERA", "45"))  # com o dono no PC: tempo pra ele resolver o captcha
        fim = time.time() + espera
        verificou = criou = False
        while time.time() < fim and not _sessao(ctx):
            if not verificou and pg.get_by_text(re.compile(r"Verifi(que se é|ca que és)")).count():
                verificou = True
                if not _verificar_por_email(ctx, pg, e["apelido"]):
                    pg.screenshot(path=rf"C:\Users\Haylla\AppData\Local\Temp\q_veo\tk_{e['apelido']}_falhou.png")
                    return "pediu código por e-mail e o código não chegou no Gmail em 2 min"
                fim = max(fim, time.time() + 30)
            if not pop.is_closed():  # tela de consentimento ("Continuar") na 1ª vez
                for t in ("Continuar", "Continue", "Permitir", "Allow"):
                    try:
                        b = pop.get_by_role("button", name=t)
                        if b.count() and b.first.is_visible():
                            b.first.click()
                            break
                    except Exception:  # noqa: BLE001
                        pass
            try:
                txt = pg.inner_text("body", timeout=2000).lower()
                if ("nascimento" in txt or "birthday" in txt) and not criou:
                    pg.screenshot(path=rf"C:\Users\Haylla\AppData\Local\Temp\q_veo\tk_{e['apelido']}_cadastro.png")
                    if os.environ.get("TK_CRIAR") != "1":
                        return "SEM CONTA: o TikTok abriu cadastro novo com esse Google (não criei nada)"
                    criou = True
                    _criar_conta(pg, e["apelido"])
                    fim = max(fim, time.time() + 60)
            except Exception:  # noqa: BLE001
                pass
            time.sleep(2)
        if not _sessao(ctx):
            pg.screenshot(path=rf"C:\Users\Haylla\AppData\Local\Temp\q_veo\tk_{e['apelido']}_falhou.png")
            return f"não logou em {espera} s (captcha? ver tk_{e['apelido']}_falhou.png)"
        _ir(pg, "https://www.tiktok.com/")
        return f"LOGADO: @{_usuario(pg)}"
    finally:
        cofre.fechar(proc, br, email)  # só fecha se fomos nós que abrimos (grava os cookies)


if __name__ == "__main__":
    if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    with sync_playwright() as p:
        for nome in sys.argv[1:]:
            try:
                print(f"{nome}: {logar(p, nome)}", flush=True)
            except Exception as ex:  # noqa: BLE001
                print(f"{nome}: ERRO {type(ex).__name__}: {str(ex)[:160]}", flush=True)
