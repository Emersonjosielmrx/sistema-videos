"""instagram_notebooks.py — loga os Instagrams (perfis ig_* do mapa) nos NOTEBOOKS (x200ma, acer).

Dona 24/10 à noite: "mesma senha, documentada; código no e-mail como no TikTok; monitore com prints". O Instagram web
não tem login pelo Google: usuário + senha (IG_SENHA, variável de usuário do Windows — nunca em arquivo) no Chrome do
notebook (perfil ig_<usuario> pelo chrome_conta, que já fecha o que não precisa antes de abrir). Desafio de código: a
leitura do Gmail é a do instagram_local (Chrome do cofre NO PC1). Logado = o próprio Instagram devolve o @ (web_form_data).
Prints: logs/tiktok_tela/<notebook>_ig_<usuario>_<hh-mm-ss>_<etapa>.png + tela inteira a cada minuto.

    python bin\\netbooks\\instagram_notebooks.py [x200ma|acer]     # uma rodada (até 40 min) nesse(s) notebook(s)
    python bin\\netbooks\\instagram_notebooks.py --fila
"""
import json
import os
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import maquina_remota as mr  # noqa: E402
import instagram_local as il  # noqa: E402
import tiktok_notebooks as tn  # noqa: E402

ESTADO = mr.ROOT / "config" / "instagram_notebooks.json"
_CODIGOS_ORIG = il._codigos_gmail
NOTEBOOKS = ("x200ma", "acer")


def _senha():
    if os.environ.get("IG_SENHA"):
        return os.environ["IG_SENHA"]
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
        return winreg.QueryValueEx(k, "IG_SENHA")[0]


def _ler():
    try:
        return json.loads(ESTADO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _usados():
    return set(_ler().get("_codigos_usados") or [])


def _usar(cod):
    est = _ler()
    est["_codigos_usados"] = sorted(set(est.get("_codigos_usados") or []) | {cod})[-500:]
    ESTADO.write_text(json.dumps(est, ensure_ascii=False, indent=2), encoding="utf-8")


def _gravar(perfil, nome, res):
    est = _ler()
    est.setdefault(perfil, {})[nome] = {"resultado": res, "t": time.time()}
    ESTADO.write_text(json.dumps(est, ensure_ascii=False, indent=2), encoding="utf-8")


def _marcar(perfil, nome, logado):
    pol = mr._politica()
    lg = mr._logins()
    lg.setdefault(perfil, {}).setdefault(nome, {})["instagram"] = bool(logado)
    pol.gravar_json(mr.LOGINS, lg)


def fila(so=()):
    lg, est, out = mr._logins(), _ler(), []
    for perfil, info in sorted(mr._mapa_perfis().items()):
        if not perfil.startswith("ig_") or not info.get("instagram"):
            continue
        for nome in NOTEBOOKS:
            if so and nome not in so:
                continue
            if ((lg.get(perfil) or {}).get(nome) or {}).get("instagram"):
                continue
            ult = (est.get(perfil) or {}).get(nome) or {}
            res = str(ult.get("resultado", ""))
            espera = 6 * 3600 if res in ("senha_incorreta", "whatsapp", "selfie_enviada", "captcha") else 3600 if res else 0
            if time.time() - ult.get("t", 0) < espera:
                continue
            out.append((perfil, info["instagram"][0], nome))
    return out


def _logar(p, perfil, usuario, nome):
    r = mr.Remoto(nome)
    try:
        r.ceder_veo()
        porta = r.abrir(perfil, "https://www.instagram.com/accounts/login/", sem_espera=True)
        try:  # 25/10: no Acer, carregando o Instagram, a ligação passou de 3 min — 5 min e mais uma tentativa
            br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}", timeout=300000)
        except Exception:  # noqa: BLE001
            time.sleep(20)
            br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}", timeout=300000)
        ctx = br.contexts[0]
        pg = next((x for x in ctx.pages if "instagram.com" in x.url), None) or ctx.new_page()
        pg.set_viewport_size({"width": 1280, "height": 1000})
        pg.goto("https://www.instagram.com/", wait_until="domcontentloaded", timeout=120000)
        pg.wait_for_timeout(8000)
        u = il._usuario_logado(pg)
        if u:
            return f"logado @{u}"
        pg.goto("https://www.instagram.com/accounts/login/", wait_until="domcontentloaded", timeout=120000)
        pg.bring_to_front()
        pg.wait_for_timeout(4000)
        if "app para tablet" in il._texto(pg).lower() or "abrir instagram" in il._texto(pg).lower():
            # 25/10 x200ma (tela de toque): o Instagram mostra a versão "para tablet", com campo escondido na página
            for t in ("Entrar", "Log in"):
                lk = pg.get_by_role("link", name=t, exact=True)
                if lk.count():
                    lk.first.click()
                    pg.wait_for_timeout(6000)
                    break
        campo = pg.locator("input[name=username]:visible, input[name=email]:visible, "
                           "input[autocomplete*=username]:visible").first
        for _ in range(20):
            il._clicar(pg, il.COOKIES)
            if campo.count() and campo.is_visible():
                break
            try:  # 25/10 x200ma: página "para tablet" (Abrir Instagram / Entrar ou Cadastre-se) — clica em Entrar
                for t in ("Entrar", "Log in", "Log In"):
                    lk = pg.get_by_role("link", name=t, exact=True)
                    if not lk.count():
                        lk = pg.get_by_role("button", name=t, exact=True)
                    if lk.count() and lk.first.is_visible():
                        lk.first.click()
                        break
            except Exception:  # noqa: BLE001
                pass
            pg.wait_for_timeout(3000)
        else:
            tn._passo(pg, perfil, nome, "sem_campo")
            if il._campo_codigo(pg) and il._resolver_codigo(p, pg, usuario):
                pg.goto("https://www.instagram.com/", wait_until="domcontentloaded", timeout=120000)
                pg.wait_for_timeout(8000)
                u = il._usuario_logado(pg)
                if u:
                    return f"logado @{u}"
            return "erro: campo de usuário não apareceu"
        tn._passo(pg, perfil, nome, "1_login")
        campo.fill(usuario)
        senha = pg.locator("input[name=password]:visible, input[name=pass]:visible, input[type=password]:visible").first
        senha.fill(_senha())
        # 25/10: o x200ma digitou o código que o Acer tinha recebido minutos antes (mesma conta): os códigos que JÁ estão
        # no e-mail da conta antes de entrar não valem
        email = (il._ler(il.ESTADO).get(usuario) or {}).get("email")
        velhos = set(_usados())
        if email:
            try:
                velhos |= set(_CODIGOS_ORIG(p, email))
            except Exception:  # noqa: BLE001
                pass

        def _filtrado(p_, e_, antes=()):
            # 25/10: o 914298 (já recusado) foi digitado de novo — código oferecido uma vez não volta nunca
            novos = _CODIGOS_ORIG(p_, e_, tuple(velhos | _usados()) + tuple(antes))
            if novos:
                _usar(novos[0])
            return novos
        il._codigos_gmail = _filtrado
        pg.keyboard.press("Enter")
        tn._passo(pg, perfil, nome, "2_senha_enviada")
        fim, tentou = time.time() + 360, False
        while time.time() < fim:
            pg.wait_for_timeout(4000)
            il._clicar(pg, il.DEPOIS)
            txt = il._texto(pg).lower()
            if any(s in txt for s in il.SENHA_ERRADA):
                tn._passo(pg, perfil, nome, "senha_incorreta")
                return "senha_incorreta"
            # 25/10 recenas.ia no Acer: a Meta mostrou "Não sou um robô" (reCAPTCHA) — não é coisa pra robô resolver;
            # anota e segue (a dona marca depois)
            if "não sou um robô" in txt or "recaptcha" in txt or "você é humano" in txt or any("recaptcha" in f.url for f in pg.frames):
                tn._passo(pg, perfil, nome, "captcha")
                return "captcha"
            u = il._usuario_logado(pg)
            if u:
                time.sleep(40)  # o Chrome grava os cookies no disco (~30 s) antes de fechar
                tn._passo(pg, perfil, nome, "3_logado")
                return f"logado @{u}"
            if il._selfie(pg, usuario):
                return "selfie_enviada"
            if il._desafio(pg) and not tentou:
                tentou = True
                fim = max(fim, time.time() + 420)
                tn._passo(pg, perfil, nome, "4_pediu_codigo")
                if il._resolver_codigo(p, pg, usuario):
                    tn._passo(pg, perfil, nome, "5_codigo_digitado")
                elif __import__("re").search(r"whatsapp|sms|celular|número|phone", il._texto(pg), 2):
                    tn._passo(pg, perfil, nome, "whatsapp")
                    return "whatsapp"
        tn._passo(pg, perfil, nome, "6_sem_login")
        return "sem_login"
    finally:
        il._codigos_gmail = _CODIGOS_ORIG
        il._fechar_gmails()
        r.fechar()


def logar(perfil, usuario, nome):
    from playwright.sync_api import sync_playwright
    parar = threading.Event()
    threading.Thread(target=tn._prints_tela, args=(perfil, nome, parar), daemon=True).start()
    try:
        with sync_playwright() as p:
            return _logar(p, perfil, usuario, nome)
    finally:
        parar.set()


def main(a):
    so = [n for n in NOTEBOOKS if n in a]
    if "--fila" in a:
        for perfil, usuario, nome in fila(so):
            print(f"{usuario} no {nome}")
        return
    fim, feitos = time.time() + 40 * 60, set()
    # a mesma conta nos 2 notebooks ao mesmo tempo misturava os códigos do e-mail: o Acer anda a fila de trás pra frente
    for perfil, usuario, nome in (fila(so)[::-1] if so == ["acer"] else fila(so)):
        if time.time() > fim:
            break
        if (perfil, nome) in feitos or not tn.Remoto_livre(nome):
            continue
        feitos.add((perfil, nome))
        vez = f"login instagram {usuario}"
        mr.ocupar(nome, vez, 20)
        try:
            res = logar(perfil, usuario, nome)
        except Exception as e:  # noqa: BLE001
            res = f"erro: {type(e).__name__}: {str(e)[:100]}"
        finally:
            mr.liberar(nome, quem=vez)
        if res.startswith("logado"):
            _marcar(perfil, nome, True)
        _gravar(perfil, nome, res)
        mr.log(f"instagram {usuario} no {nome}: {res}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main(sys.argv[1:])
