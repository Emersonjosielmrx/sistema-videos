r"""instagram_local.py — loga as contas do Instagram NESTE PC, no Chrome do cofre (D:\logins-google\cofre, perfil
ig_<conta>), uma por vez, com fila e estado como o netbooks\tiktok_notebooks.py.

O Instagram web (teste 24/10) NÃO tem "Continuar com Google" — só usuário/senha ou Facebook. 1º tenta SEM SENHA:
"Esqueceu a senha" -> "Enviar link de login" -> lê o link no Gmail da conta Google do cofre (as mesmas do Groq/Gemini)
e abre neste perfil. Não deu (--sem-senha para aqui): abre a janela NA
TELA, preenche o usuário e espera a dona digitar a senha (senha nunca passa por aqui; começou a digitar = o prazo
estica). Depois disso é sozinho: "Agora não", e o CÓDIGO de segurança — lê o e-mail mascarado na tela
(e****1@gmail.com), acha a conta Google do cofre que bate, pega o código no Gmail dela e digita.
Logado = confirmado pela API do próprio Instagram (cookie sozinho não prova).

    python bin\instagram_local.py --conferir   # confere TODAS em segundos (sem janela de espera) e marca as logadas
    python bin\instagram_local.py              # a próxima conta da fila
    python bin\instagram_local.py --todas      # todas da fila, uma depois da outra
    python bin\instagram_local.py --fila       # mostra quem falta
    python bin\instagram_local.py recenas.ia   # só essa conta
"""
import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, r"D:\logins-google")

ROOT = Path(__file__).resolve().parent.parent
REUSO = ROOT / "config" / "reuso_plataformas.json"
ESTADO = ROOT / "config" / "instagram_local.json"
PRINTS = ROOT / "logs" / "instagram_tela"
FORM = "https://www.instagram.com/api/v1/accounts/edit/web_form_data/"
ESPERA_SENHA_S = 300
ESPERA_DIGITANDO_S = 600
COOKIES = ("Permitir todos os cookies", "Allow all cookies", "Recusar cookies opcionais", "Decline optional cookies")
DEPOIS = ("Agora não", "Not now", "Agora nao", "Salvar informações", "Save info", "Save Info")
SENHA_ERRADA = ("senha incorreta", "incorrect password", "estão incorretas", "login information you entered is incorrect",
                "sorry, your password was incorrect")


def _ler(arq):
    try:
        return json.loads(arq.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _gravar_res(usuario, res):
    est = _ler(ESTADO)
    est.setdefault(usuario, {}).update({"resultado": res, "t": time.time()})
    ESTADO.write_text(json.dumps(est, ensure_ascii=False, indent=2), encoding="utf-8")


def _contas():
    return list(((_ler(REUSO).get("instagram") or {}).get("contas") or {}).items())


def _chave(usuario, r):
    return (r.get("cofre") or f"ig_{usuario}").lower()


def fila():
    est, out = _ler(ESTADO), []
    for usuario, r in _contas():
        ult = est.get(usuario) or {}
        res = str(ult.get("resultado", ""))
        if res.startswith("logado"):
            continue
        if res == "whatsapp" and "--whatsapp" not in sys.argv:
            continue  # só com a dona e o celular: python bin\instagram_local.py --whatsapp
        espera = 6 * 3600 if res == "senha_incorreta" else 0 if res in ("conferido_sem_login", "whatsapp") else 3600
        if time.time() - ult.get("t", 0) < espera:
            continue
        out.append((usuario, r))
    return out


def _print(pg, usuario, etapa):
    try:
        PRINTS.mkdir(parents=True, exist_ok=True)
        pg.screenshot(path=str(PRINTS / f"{usuario}_{time.strftime('%H-%M-%S')}_{etapa}.png"), timeout=20000)
    except Exception:  # noqa: BLE001
        pass
    for velho in sorted(PRINTS.glob("*.png"), key=lambda x: x.stat().st_mtime)[:-300]:
        velho.unlink(missing_ok=True)


def _usuario_logado(pg):
    try:
        r = pg.evaluate(f"async () => (await fetch('{FORM}', {{credentials: 'include', "
                        "headers: {'X-IG-App-ID': '936619743392459'}})).text()")
        return (json.loads(r).get("form_data") or {}).get("username")
    except Exception:  # noqa: BLE001
        return None


def _clicar(pg, textos):
    for t in textos:
        try:
            b = pg.get_by_role("button", name=t)
            if b.count() and b.first.is_visible() and b.first.is_enabled():
                b.first.click()
                pg.wait_for_timeout(1200)
                return True
        except Exception:  # noqa: BLE001
            pass
    return False


def _texto(pg):
    try:
        return pg.inner_text("body", timeout=3000)
    except Exception:  # noqa: BLE001
        return ""


def _avisar(texto):
    try:
        sys.path.insert(0, r"D:\video-fila")
        import avisos
        avisos.enviar(texto, "instagram login", importante=True)
    except Exception:  # noqa: BLE001
        print("aviso não saiu:", texto)


# ─────────────────────────── código por e-mail ────────────────────────────
def _emails_da_mascara(txt, usuario=None):
    """'e*****1@gmail.com' na tela -> e-mails do cofre que batem. O já vinculado à conta (instagram_local.json) vem
    primeiro."""
    import cofre
    vinculado = ((_ler(ESTADO).get(usuario) or {}).get("email") or "") if usuario else ""
    inteiros = [e for e in re.findall(r"[\w.+-]+@[\w.-]+\.\w+", txt.lower()) if e in cofre._ler()["contas"]]
    if inteiros:  # o Instagram às vezes mostra o e-mail sem máscara
        return inteiros[:1]
    for m in re.finditer(r"([\w.+-]\*+[\w.+-]*|[\w.+-]*\*+[\w.+-])@([\w.-]+\.\w+)", txt):
        local, dom = m.group(1), m.group(2).lower()
        padrao = re.compile("^" + "".join(".*" if c == "*" else re.escape(c) for c in re.sub(r"\*+", "*", local)) + "$",
                            re.I)
        achados = [e for e in cofre._ler()["contas"] if e.endswith("@" + dom) and padrao.match(e.split("@")[0])]
        return sorted(achados, key=lambda e: e != vinculado)
    return []


def _vincular(usuario, email):
    est = _ler(ESTADO)
    est.setdefault(usuario, {})["email"] = email
    ESTADO.write_text(json.dumps(est, ensure_ascii=False, indent=2), encoding="utf-8")


def _email_da_mascara(txt):
    achados = _emails_da_mascara(txt)
    return achados[0] if len(achados) == 1 else None


_GMAIL = {}  # email -> (br, proc, aba): o Gmail fica ABERTO durante o login (dona 24/10: abrir/fechar gerava código novo)
BUSCA_IG = "https://mail.google.com/mail/u/0/#search/in%3Aanywhere+from%3Ainstagram+newer_than%3A1h"  # spam também


def _gmail(p, email):
    """Aba do Gmail da conta Google do cofre, aberta NA TELA e reaproveitada até o fim do login."""
    import cofre
    if email in _GMAIL:
        return _GMAIL[email][2]
    porta, proc = cofre.abrir(email, "about:blank", visivel=True)
    br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
    g = br.contexts[0].new_page()
    _GMAIL[email] = (br, proc, g)
    return g


def _fechar_gmails():
    import cofre
    for email, (br, proc, _) in list(_GMAIL.items()):
        cofre.fechar(proc, br, email)
    _GMAIL.clear()


def _abrir_ultimo_ig(g):
    """Busca os e-mails do Instagram da última hora (recarrega a busca) e abre o mais novo. False se não há."""
    try:  # o Gmail às vezes não termina de carregar em 90 s: basta começar a navegar e esperar a lista
        g.goto(BUSCA_IG, wait_until="commit", timeout=60000)
    except Exception:  # noqa: BLE001
        pass
    linhas = g.locator("tr.zA")
    try:
        linhas.first.wait_for(timeout=60000)
    except Exception:  # noqa: BLE001
        return False
    linhas.first.click()
    g.wait_for_timeout(5000)
    return True


def _codigos_gmail(p, email, antes=()):
    """Códigos de 6 dígitos do e-mail mais novo do Instagram, no Gmail (aberto) da conta do cofre."""
    g = _gmail(p, email)
    if not _abrir_ultimo_ig(g):
        return []
    cods = re.findall(r"\b\d{6}\b", " ".join(g.locator("div.a3s").all_inner_texts()))
    return [c for c in cods if c not in antes]


def _links_gmail(p, email, antes=()):
    """Links do Instagram (login/redefinição) do e-mail mais novo do Instagram, no Gmail (aberto) do cofre."""
    from urllib.parse import parse_qs, urlparse
    g = _gmail(p, email)
    if not _abrir_ultimo_ig(g):
        return []
    hrefs = g.locator("div.a3s a").evaluate_all("as => as.map(a => a.href)")
    out = []
    for h in hrefs:
        if "google.com/url" in h:
            h = (parse_qs(urlparse(h).query).get("q") or [h])[0]
        if "instagram.com" in h and re.search(r"login|reset|uidb36|/_n/|token", h, re.I) and h not in antes:
            out.append(h)
    return out


def _por_link(p, pg, usuario):
    """Sem senha: 'Esqueceu a senha' -> 'Enviar link de login' -> abre o link do Gmail do cofre neste perfil."""
    pg.goto("https://www.instagram.com/accounts/password/reset/", wait_until="domcontentloaded", timeout=90000)
    pg.wait_for_timeout(4000)
    _clicar(pg, COOKIES)
    campo = pg.locator("input[name=cppEmailOrUsername], input[name=email], input[type=text]").first
    try:
        campo.wait_for(timeout=20000)
    except Exception:  # noqa: BLE001
        _print(pg, usuario, "link_sem_campo")
        return ""
    campo.fill(usuario)
    if not _clicar(pg, ("Enviar link de login", "Send login link", "Enviar link", "Send link", "Continuar", "Continue")):
        pg.keyboard.press("Enter")
    pg.wait_for_timeout(6000)
    _print(pg, usuario, "link_pedido")
    if re.search(r"não sou um robô|not a robot|confirmar que é você|confirm it'?s you", _texto(pg), re.I):
        # reCAPTCHA: quem marca é a dona; depois o script segue sozinho (link + Gmail)
        pg.bring_to_front()
        print("   reCAPTCHA na tela: marque 'Não sou um robô' e Avançar (espero 5 min)", flush=True)
        _avisar(f"Instagram {usuario}: marque o 'Não sou um robô' na janela aberta no PC1 e clique Avançar. "
                "O resto é sozinho.")
        fim = time.time() + 300
        while time.time() < fim and re.search(r"não sou um robô|not a robot", _texto(pg), re.I):
            pg.wait_for_timeout(3000)
        pg.wait_for_timeout(5000)
        _print(pg, usuario, "link_pos_captcha")
    email = _email_da_mascara(_texto(pg))
    if not email:
        print("   link: e-mail da tela não bate com nenhuma conta do cofre", flush=True)
        return ""
    print(f"   link de login foi pro {email}: lendo o Gmail", flush=True)
    fim = time.time() + 240
    while time.time() < fim:
        time.sleep(15)
        links = _links_gmail(p, email)
        if links:
            pg.goto(links[0], wait_until="domcontentloaded", timeout=90000)
            pg.wait_for_timeout(6000)
            _clicar(pg, ("Entrar", "Log in", "Continuar", "Continue", "Fazer login como", *DEPOIS))
            pg.goto("https://www.instagram.com/", wait_until="domcontentloaded", timeout=90000)
            pg.wait_for_timeout(5000)
            _print(pg, usuario, "link_aberto")
            u = _usuario_logado(pg)
            if u:
                _vincular(usuario, email)
            return f"logado @{u}" if u else ""
    return ""


SELFIE = Path(r"D:\fotos para videos\fotos\fotos base so suar se for criar uma foto nova"
              r"\Screenshot_20250710_020236_Photos.jpg")  # dona 24/10: foto dela só de rosto, pra selfie de verificação


def _selfie(pg, usuario):
    """'Carregar uma selfie de verificação': manda a foto de rosto da dona e Envia. True se enviou."""
    if not re.search(r"selfie", _texto(pg), re.I):
        return False
    try:
        entrada = pg.locator("input[type=file]")
        if entrada.count():
            entrada.first.set_input_files(str(SELFIE))
        else:
            with pg.expect_file_chooser(timeout=15000) as fc:
                pg.get_by_text(re.compile(r"Carregar uma foto|Upload a photo", re.I)).first.click()
            fc.value.set_files(str(SELFIE))
        pg.wait_for_timeout(4000)
        _clicar(pg, ("Enviar", "Submit", "Continuar", "Continue"))
        pg.wait_for_timeout(6000)
        _print(pg, usuario, "selfie_enviada")
        return True
    except Exception as e:  # noqa: BLE001
        print(f"   selfie: falhou ({type(e).__name__}: {str(e)[:80]})", flush=True)
        _print(pg, usuario, "selfie_falhou")
        return False


def _campo_codigo(pg):
    c = pg.locator("input[name=security_code], input[name=verificationCode], input[name=email_code], input[name=code], "
                   "input[autocomplete=one-time-code], input[inputmode=numeric], input[aria-label*=ódigo], "
                   "input[aria-label*=ode]")
    try:
        for i in range(c.count()):
            if c.nth(i).is_visible():
                return c.nth(i)
        if re.search(r"insira o código|enter the code|código de confirmação|confirmation code|verifique seu e-?mail|"
                     r"check your email", _texto(pg), re.I):
            t = pg.locator("input:not([type=hidden]):not([type=checkbox]):not([type=radio]):not([type=file]):visible, "
                           "textarea:visible, [contenteditable=true]:visible, [role=textbox]:visible")
            if t.count():
                return t.first
            # tela de conta suspensa (24/10): o campo não é <input>; clica no rótulo e digita pelo teclado
            t = pg.get_by_text(re.compile(r"^\s*(Código de 6 dígitos|6-digit code|Código)\s*$", re.I))
            if t.count() and t.first.is_visible():
                return t.first
    except Exception:  # noqa: BLE001
        pass
    return None


def _resolver_codigo(p, pg, usuario):
    """Desafio com código: escolhe e-mail, pede o código, lê no Gmail certo e digita. True se digitou."""
    txt = _texto(pg)
    try:  # tela de escolha (SMS / e-mail): fica com o e-mail
        op = pg.get_by_text(re.compile(r"e-?mail", re.I)).locator("xpath=ancestor-or-self::label").first
        if op.count() and op.is_visible():
            op.click()
    except Exception:  # noqa: BLE001
        pass
    emails = _emails_da_mascara(txt, usuario)
    if not emails and _clicar(pg, ("Tentar outra forma", "Try another way")):
        # código foi pro WhatsApp/SMS: troca pra e-mail
        pg.wait_for_timeout(3000)
        try:
            pg.get_by_text(re.compile(r"e-?mail", re.I)).first.click(timeout=8000)
            pg.wait_for_timeout(1500)
            _clicar(pg, ("Continuar", "Continue", "Enviar código", "Send code"))
            pg.wait_for_timeout(5000)
        except Exception:  # noqa: BLE001
            pass
        _print(pg, usuario, "outra_forma")
        emails = _emails_da_mascara(_texto(pg), usuario)
    if not emails:
        _print(pg, usuario, "codigo_sem_email")
        return False
    print(f"   código vai pra {', '.join(emails)}: lendo o Gmail", flush=True)
    if not _campo_codigo(pg):  # ainda na escolha: pede o envio
        _clicar(pg, ("Enviar código de segurança", "Send security code", "Enviar código", "Send code", "Continuar",
                     "Continue"))
    inicio, fim, reenviou = time.time(), time.time() + 360, False
    while time.time() < fim:
        time.sleep(15)
        if not reenviou and time.time() - inicio > 120:  # 24/10: código que não chega em 2 min — pede outro
            reenviou = _clicar(pg, ("Não recebi o código", "Solicitar novo código", "Receber um novo código",
                                    "Didn't get the code", "Resend code"))
            if reenviou:
                print("   código não chegou em 2 min: pedi outro", flush=True)
        for email in emails:
            try:
                novos = _codigos_gmail(p, email)  # newer_than:1h; o mais novo vem primeiro
            except Exception as e:  # noqa: BLE001
                print(f"   gmail {email}: {type(e).__name__}", flush=True)
                continue
            if not novos:
                continue
            pg.bring_to_front()
            pg.wait_for_timeout(1000)
            campo = _campo_codigo(pg)  # 02/11: procurar DEPOIS de voltar pra aba (com o Gmail na frente o campo sumia)
            if not campo:
                return False
            try:
                campo.click(timeout=10000)
            except Exception:  # noqa: BLE001 — 02/11 21:41: click de 30 s estourou com o campo na tela; foco e digita
                try:
                    campo.focus(timeout=5000)
                except Exception:  # noqa: BLE001
                    _print(pg, usuario, "codigo_sem_foco")
                    return False
            pg.keyboard.press("Control+A")  # 25/10: sem limpar, cada tentativa colava o código atrás do anterior
            pg.keyboard.press("Backspace")
            pg.keyboard.type(novos[0], delay=120)
            pg.wait_for_timeout(800)
            if not _clicar(pg, ("Avançar", "Confirmar", "Confirm", "Enviar", "Submit", "Continuar", "Continue", "Próximo",
                                "Next")):
                pg.keyboard.press("Enter")
            pg.wait_for_timeout(8000)
            _print(pg, usuario, "codigo_digitado")
            if not _campo_codigo(pg):
                _vincular(usuario, email)
                print(f"   código aceito: {usuario} vinculada a {email}", flush=True)
                return True
    return False


def _desafio(pg):
    u = pg.url.lower()
    return "challenge" in u or "two_factor" in u or "auth_platform" in u or _campo_codigo(pg) is not None


# ─────────────────────────── login ─────────────────────────────────────────
def conferir(p, usuario, r):
    """Só olha (sem janela de espera): '@usuario', 'suspensa' (accounts/suspended, "confirme que é humano") ou ''."""
    import cofre
    chave = _chave(usuario, r)
    try:
        cofre.conta(chave)
    except KeyError:
        return ""
    porta, proc = cofre.abrir(chave, "about:blank")
    br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
    try:
        pg = br.contexts[0].new_page()
        pg.goto("https://www.instagram.com/", wait_until="domcontentloaded", timeout=90000)
        pg.wait_for_timeout(5000)
        u = _usuario_logado(pg)
        if u:
            return f"@{u}"
        return "suspensa" if "accounts/suspended" in pg.url or "humano" in _texto(pg).lower() else ""
    finally:
        cofre.fechar(proc, br, chave)


def logar(p, usuario, r):
    import cofre
    chave = _chave(usuario, r)
    try:
        cofre.conta(chave)
    except KeyError:
        cofre.registrar(chave, usos={"instagram": usuario}, tipo="instagram")
    porta, proc = cofre.abrir(chave, "about:blank", visivel=True)
    br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
    try:
        pg = br.contexts[0].new_page()
        pg.goto("https://www.instagram.com/", wait_until="domcontentloaded", timeout=90000)
        pg.wait_for_timeout(5000)
        u = _usuario_logado(pg)
        if u:
            return f"logado @{u}"
        res = ""
        if not os.environ.get("IG_SENHA"):  # sem senha na variável: tenta o link por e-mail
            try:
                res = _por_link(p, pg, usuario)
            except Exception as e:  # noqa: BLE001
                print(f"   link: falhou ({type(e).__name__}: {str(e)[:80]})", flush=True)
        if res:
            return res
        if "--sem-senha" in sys.argv:
            return "sem_login"
        pg.goto("https://www.instagram.com/accounts/login/", wait_until="domcontentloaded", timeout=90000)
        pg.bring_to_front()
        campo = pg.locator("input[name=username], input[name=email], input[autocomplete*=username]").first
        for _ in range(15):
            _clicar(pg, COOKIES)
            if campo.count() and campo.is_visible():
                break
            pg.wait_for_timeout(2000)
        else:
            _print(pg, usuario, "sem_campo")
            if _selfie(pg, usuario):  # conta em verificação de identidade: o Instagram analisa (horas/dias)
                return "selfie_enviada"
            if _campo_codigo(pg) and _resolver_codigo(p, pg, usuario):  # checkpoint de código antes do login
                pg.goto("https://www.instagram.com/", wait_until="domcontentloaded", timeout=90000)
                pg.wait_for_timeout(5000)
                u = _usuario_logado(pg)
                if u:
                    return f"logado @{u}"
                if _selfie(pg, usuario):
                    return "selfie_enviada"
                _print(pg, usuario, "pos_codigo")
                return "sem_login"
            return "erro: campo de usuário não apareceu"
        campo.fill(usuario)
        senha = pg.locator("input[name=password], input[name=pass], input[type=password]").first
        senha.click()
        _print(pg, usuario, "1_usuario")
        if os.environ.get("IG_SENHA"):  # a senha vem só da variável de ambiente, nunca de arquivo/log
            senha.fill(os.environ["IG_SENHA"])
            pg.keyboard.press("Enter")
            print("   senha digitada", flush=True)
        else:
            print(f"   janela aberta: digite a SENHA de {usuario} e Enter", flush=True)
            _avisar(f"Instagram {usuario}: janela aberta NO PC1 com o usuário preenchido — digite a senha. "
                    "O resto (código do e-mail) é sozinho.")
        inicio, fim, tentou_codigo = time.time(), time.time() + ESPERA_SENHA_S, False
        while time.time() < fim:
            pg.wait_for_timeout(3000)
            try:  # começou a digitar: dá mais tempo
                if senha.count() and senha.input_value(timeout=1000):
                    fim = max(fim, inicio + ESPERA_DIGITANDO_S)
            except Exception:  # noqa: BLE001
                pass
            _clicar(pg, DEPOIS)
            txt = _texto(pg).lower()
            if any(s in txt for s in SENHA_ERRADA):
                _print(pg, usuario, "senha_incorreta")
                return "senha_incorreta"
            u = _usuario_logado(pg)
            if u:
                _print(pg, usuario, "2_logado")
                return f"logado @{u}"
            if _selfie(pg, usuario):
                return "selfie_enviada"
            if _desafio(pg) and not tentou_codigo:
                tentou_codigo = True
                fim = max(fim, time.time() + 300)
                _print(pg, usuario, "desafio")
                if not _resolver_codigo(p, pg, usuario):
                    if re.search(r"whatsapp|sms|celular|número|phone", _texto(pg), re.I):
                        return "whatsapp"  # código no celular da dona: fica pro fim (dona 24/10)
                    _avisar(f"Instagram {usuario}: pediu verificação que não consegui sozinho. A janela está aberta "
                            "no PC1 — resolva lá (espero 5 min).")
        _print(pg, usuario, "3_sem_login")
        return "sem_login"
    finally:
        _fechar_gmails()
        cofre.fechar(proc, br, chave)


def main(a):
    from playwright.sync_api import sync_playwright
    if "--fila" in a:
        f = fila()
        est = _ler(ESTADO)
        for usuario, _ in f:
            print(f"  {usuario}  (último: {(est.get(usuario) or {}).get('resultado', '-')})")
        print(f"Total: {len(f)} na fila.")
        return
    with sync_playwright() as p:
        if "--conferir" in a:
            for usuario, r in _contas():
                try:
                    ok = conferir(p, usuario, r)
                except Exception as e:  # noqa: BLE001
                    print(f"  {usuario}: erro {type(e).__name__}: {str(e)[:80]}")
                    continue
                _gravar_res(usuario, f"logado {ok}" if ok.startswith("@") else ok or "conferido_sem_login")
                print(f"  {usuario}: {ok.upper() if ok == 'suspensa' else ok or 'NÃO logado'}", flush=True)
            return
        nomes = [x for x in a if not x.startswith("--")]
        if nomes:
            todas = dict(_contas())
            alvos = [(n, todas.get(n, {})) for n in nomes]  # fora do reuso: perfil ig_<conta> do cofre
        else:
            alvos = fila() if "--todas" in a else fila()[:1]
        if not alvos:
            print("Nada a logar.")
            return
        for usuario, r in alvos:
            print(f"\n== {usuario}", flush=True)
            try:
                res = logar(p, usuario, r)
            except Exception as e:  # noqa: BLE001
                res = f"erro: {type(e).__name__}: {str(e)[:100]}"
            _gravar_res(usuario, res)
            print(f"   {res}", flush=True)
            if res == "senha_incorreta":
                _avisar(f"Instagram {usuario}: a senha digitada foi recusada.")


if __name__ == "__main__":
    if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main(sys.argv[1:])
