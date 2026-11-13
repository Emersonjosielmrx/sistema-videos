r"""
Kaggle: cria contas e captura API token (username + key) em cada conta Google do cofre.

Passos: kaggle.com -> "Register with Google" -> consent -> perfil criado automaticamente.
API token: kaggle.com/settings -> seção API -> Create New Token -> baixa kaggle.json com
{"username": "...", "key": "..."}.

CLI:
  python kaggle_contas.py criar <conta>
  python kaggle_contas.py criar_massa <conta1> <conta2> ...
  python kaggle_contas.py criar_massa --vivas            # todas as contas com Google vivo
  python kaggle_contas.py salvar <conta> <username> <key> # credencial criada à mão
  python kaggle_contas.py listar
"""
import json
import random
import re
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, r"D:\logins-google")
import cofre

DIR = Path(__file__).resolve().parent
REGISTRO = DIR / "kaggle_contas.json"
KAGGLE_URL = "https://www.kaggle.com"
SETTINGS_URL = "https://www.kaggle.com/settings"
SIGNUP_URL = "https://www.kaggle.com/account/login?phase=startRegisterTab"
VALIDACAO_URL = "https://www.kaggle.com/api/v1/competitions/list"


def _ler(arq, padrao):
    return json.loads(arq.read_text(encoding="utf-8")) if arq.exists() else padrao


def _gravar(arq, dados, indent=2):
    arq.parent.mkdir(parents=True, exist_ok=True)
    tmp = arq.with_suffix(".tmp")
    tmp.write_text(json.dumps(dados, indent=indent, ensure_ascii=True) + "\n", encoding="utf-8")
    tmp.replace(arq)


def _contas_vivas():
    """Retorna lista de (email, apelido) com Google vivo no cofre."""
    reg = cofre._ler()
    resultado = []
    for email, info in reg["contas"].items():
        google_vivo = info.get("google") == "vivo" or info.get("servicos", {}).get("google") == "vivo"
        if google_vivo:
            apelido = email.split("@")[0]
            resultado.append((email, apelido))
    return resultado


def validar_chave(username, key, timeout=15):
    """Valida a API key batendo no endpoint Kaggle real."""
    if not username or not key:
        return {"valida": False, "motivo": "username ou key vazio"}

    url = f"{VALIDACAO_URL}?page=1"
    import base64
    cred = base64.b64encode(f"{username}:{key}".encode()).decode()
    try:
        req = urllib.request.Request(url, headers={
            "Authorization": f"Basic {cred}",
            "User-Agent": "kaggle-api/1.6",  # com UA de navegador a API devolve 404 até pra chave boa
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return {"valida": True}
    except urllib.error.HTTPError as e:
        if e.code == 401:
            return {"valida": False, "motivo": "credencial invalida (401)"}
        if e.code == 403:
            return {"valida": False, "motivo": "acesso negado (403)"}
        return {"valida": False, "motivo": f"HTTP {e.code}"}
    except Exception as e:
        return {"valida": False, "motivo": str(e)}


def salvar(conta, username, key):
    """Salva credencial (criada pelo robô ou à mão)."""
    validacao = validar_chave(username, key)
    reg = _ler(REGISTRO, {})
    reg[conta] = {
        "username": username,
        "key": key,
        "valida": validacao["valida"],
        "criado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    _gravar(REGISTRO, reg)
    return {"conta": conta, "username": username, "valida": validacao["valida"], "final": key[-4:]}


def _no_kaggle(url):
    from urllib.parse import urlparse
    return urlparse(url).netloc.endswith("kaggle.com")


def _esperar_url(page, teste, seg=40):
    fim = time.time() + seg
    while time.time() < fim:
        try:
            if teste(page.url):
                return True
        except Exception:
            pass
        page.wait_for_timeout(1000)
    return False


def _print(page, motivo):
    p = DIR / f"_debug_kaggle_{datetime.now():%H%M%S}_{motivo}.png"
    try:
        page.screenshot(path=str(p))
    except Exception:
        pass
    return str(p)


def _login_google(page, conta):
    """Faz o fluxo de login/consent do Google. Retorna True se voltou ao Kaggle."""
    _esperar_url(page, lambda u: "accounts.google.com" in u or _no_kaggle(u), 30)
    page.wait_for_timeout(3000)

    if _no_kaggle(page.url):
        return True

    if "accounts.google.com" not in page.url:
        return False

    # Se pedir login (input de email), a sessão morreu
    if page.locator('input[type="email"]').count():
        return False

    # Escolher a conta certa se vier o seletor
    if "accountchooser" in page.url or "selectaccount" in page.url.lower():
        escolha = page.locator(f'[data-email*="{conta}" i], [data-identifier*="{conta}" i]')
        if not escolha.count():  # tela nova do Google (23/10) não tem data-email: clica no texto do e-mail
            escolha = page.get_by_text(conta, exact=True)
        if escolha.count():
            escolha.first.click()
            page.wait_for_timeout(3000)

    # Consentimento: clicar em Continuar/Continue/Permitir/Allow repetidamente
    fim = time.time() + 40
    while time.time() < fim and "accounts.google.com" in page.url:
        for txt in ("Continuar", "Continue", "Permitir", "Allow"):
            b = page.get_by_role("button", name=txt, exact=True)
            try:
                if b.count() and b.first.is_visible():
                    b.first.click()
                    page.wait_for_timeout(4000)
                    break
            except Exception:
                pass
        page.wait_for_timeout(1500)

    return _esperar_url(page, _no_kaggle, 30)


def _logar_kaggle(page, email):
    """Vai ao Kaggle, faz login com Google se necessário. Retorna True se logou."""
    apelido = email.split("@")[0]

    # Ir direto pra página de login (com returnUrl pro settings, assim se logar cai lá)
    login_url = "https://www.kaggle.com/account/login?returnUrl=%2Fsettings"
    print(f"[{apelido}] Abrindo Kaggle login...", flush=True)
    page.goto(login_url, timeout=45000, wait_until="domcontentloaded")
    time.sleep(5)

    # Se já chegou no settings, já está logado
    if "/settings" in page.url and "login" not in page.url:
        print(f"[{apelido}] Ja logado no Kaggle", flush=True)
        return True

    # Se redirecionou pro Google (consent direto)
    if "accounts.google.com" in page.url:
        ok = _login_google(page, email)
        if ok and _no_kaggle(page.url) and "login" not in page.url:
            return True

    # Captcha?
    captcha = page.locator('iframe[src*="recaptcha"], iframe[src*="turnstile"], iframe[src*="challenges"]').all()
    # o reCAPTCHA invisível sempre carrega no login; só desiste se aparecer de verdade
    if any(c.is_visible() and (c.bounding_box() or {}).get("height", 0) > 60 for c in captcha):
        _print(page, f"{apelido}_captcha")
        return False

    # Clicar no botão "Sign in with Google" / "Register with Google"
    google_btn = None
    for seletor in (
        'button:has-text("Google")',
        'a:has-text("Google")',
        '[data-testid*="google" i]',
        'span:has-text("Google")',
        '.google-button',
        '[aria-label*="Google" i]',
    ):
        loc = page.locator(seletor).first
        try:
            if loc.count() and loc.is_visible():
                google_btn = loc
                break
        except Exception:
            pass

    if not google_btn:
        # Tentar aba de registro
        for txt in ("Register", "Registrar", "Sign up"):
            tab = page.locator(f'a:has-text("{txt}"), button:has-text("{txt}")').first
            try:
                if tab.count() and tab.is_visible():
                    tab.click(timeout=5000)
                    time.sleep(3)
                    break
            except Exception:
                pass

        for seletor in ('button:has-text("Google")', 'a:has-text("Google")', 'span:has-text("Google")'):
            loc = page.locator(seletor).first
            try:
                if loc.count() and loc.is_visible():
                    google_btn = loc
                    break
            except Exception:
                pass

    if not google_btn:
        print(f"[{apelido}] Botao Google nao encontrado na tela de login", flush=True)
        _print(page, f"{apelido}_no_google")
        return False

    print(f"[{apelido}] Clicando em Sign in with Google...", flush=True)
    google_btn.click(timeout=10000)
    time.sleep(3)

    ok = _login_google(page, email)
    if not ok:
        _print(page, f"{apelido}_login_fail")
        return False

    time.sleep(5)

    # Kaggle pode pedir pra completar perfil (username)
    if _no_kaggle(page.url):
        username_input = page.locator('input[name="userName"], input[name="username"], #username')
        if username_input.count():
            print(f"[{apelido}] Completando perfil...", flush=True)
            base = email.split("@")[0].replace(".", "").replace("-", "").replace("_", "")[:20]

            def trocar_usuario(nome):
                # o usuário sugerido vem do nome completo: abrir o "Edit"; o campo do usuário é o último texto visível
                try:
                    page.get_by_text("Edit", exact=True).first.click(timeout=5000)
                    time.sleep(1)
                except Exception:
                    pass
                campo = page.locator('input[name="username"][type="text"]').first
                if not campo.count() or not campo.is_visible():
                    vis = [i for i in page.locator('input[type="text"], input:not([type])').all() if i.is_visible()]
                    campo = vis[-1] if len(vis) >= 2 else None
                if campo:
                    campo.fill(nome)
                    campo.press("Tab")  # o Kaggle só confere o nome quando o campo perde o foco

            time.sleep(3)
            if "no more than 20" in page.inner_text("body") or not username_input.first.is_visible():
                trocar_usuario(base)
                time.sleep(2)
            _print(page, f"{apelido}_cadastro")

            # cadastro em etapas (23/10): Next -> Privacy and Terms (I Agree) -> ...; caixa de newsletter fica sem marcar
            for _ in range(8):
                if not _no_kaggle(page.url) or "/account/" not in page.url:
                    break
                # "already taken" só aparece DEPOIS do Next (o servidor confere): trocar por nome com números e repetir
                if "already taken" in page.inner_text("body"):
                    base = base[:16] + str(random.randint(1000, 9999))
                    print(f"[{apelido}] usuario em uso, tentando {base}", flush=True)
                    trocar_usuario(base)
                    time.sleep(2)
                clicou = False
                for txt in ("I Agree", "Next", "Register", "Create Account", "Submit", "Done"):
                    btn = page.get_by_role("button", name=txt, exact=True)
                    try:
                        if btn.count() and btn.first.is_visible():
                            btn.first.click(timeout=5000)
                            clicou = True
                            break
                    except Exception:
                        pass
                time.sleep(4)
                if not clicou:
                    _print(page, f"{apelido}_cadastro_parado")
                    break

    # Verificar se login deu certo: estamos no settings ou ao menos não no login
    if _no_kaggle(page.url) and "login" not in page.url:
        print(f"[{apelido}] Login OK ({page.url[:90]})", flush=True)
        _print(page, f"{apelido}_pos_login")
        return True

    return False


def criar(conta_nome):
    """Cria conta Kaggle + API token para a conta Google especificada."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return {"sucesso": False, "erro": "Playwright nao instalado"}

    email, info = cofre.conta(conta_nome)
    reg = _ler(REGISTRO, {})

    # Pular se já tem credencial válida
    anterior = reg.get(email)
    if anterior and anterior.get("valida"):
        return {"sucesso": False, "pulada": True, "erro": "ja tem conta valida",
                "username": anterior.get("username")}

    print(f"[{email.split('@')[0]}] Abrindo Chrome do cofre...", flush=True)
    porta, proc = cofre.abrir(email, url="about:blank", visivel=True)

    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else context.new_page()

            # 1. Tentar logar com Google no Kaggle
            ja_logado = _logar_kaggle(page, email)
            if not ja_logado:
                foto = _print(page, "login_fail")
                cofre.fechar(proc, browser, nome=email)
                return {"sucesso": False, "erro": "nao conseguiu logar no Kaggle", "print": foto}

            # 3. Ir para settings e pegar/criar API token
            print(f"[{email.split('@')[0]}] Indo para Settings (API)...", flush=True)
            page.goto(SETTINGS_URL, timeout=45000, wait_until="domcontentloaded")
            time.sleep(5)

            url_agora = page.url
            print(f"[{email.split('@')[0]}] URL apos settings: {url_agora}", flush=True)

            if "login" in url_agora.lower() and "kaggle" not in url_agora.split("login")[0][-10:]:
                # Pode ter sido redirecionado para Google login (consent)
                if "accounts.google.com" in url_agora:
                    ok = _login_google(page, email)
                    if ok:
                        page.goto(SETTINGS_URL, timeout=45000, wait_until="domcontentloaded")
                        time.sleep(5)
                        url_agora = page.url
                        print(f"[{email.split('@')[0]}] URL apos re-settings: {url_agora}", flush=True)

            if "account/login" in url_agora:
                foto = _print(page, "settings_redirect")
                cofre.fechar(proc, browser, nome=email)
                return {"sucesso": False, "erro": f"nao conseguiu logar no Kaggle (redirecionou: {url_agora})",
                        "print": foto}

            # Scroll até a seção API
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)

            # Procurar seção de API e botão Create New Token
            # No Kaggle: Settings -> Account -> API section -> "Create New API Token"
            # Isso baixa um kaggle.json

            # Configurar download path
            download_dir = DIR / "_kaggle_downloads"
            download_dir.mkdir(exist_ok=True)

            # No Kaggle, o botão fica na seção API e baixa um arquivo
            # Primeiro verificar se já existe token (seria "Expire API Token" visível)
            expire_btn = page.locator('button:has-text("Expire API Token"), a:has-text("Expire API Token")')

            # Clicar em "Create New API Token"
            create_btn = page.locator(
                'button:has-text("Create New API Token"), '
                'button:has-text("Create New Token"), '
                'a:has-text("Create New API Token"), '
                'a:has-text("Create New Token")'
            ).first

            if not create_btn.count():
                # Pode estar em /settings/account ou dentro de uma aba
                # Tentar clicar na aba "Account" se existir
                for tab_text in ("API Tokens", "Account", "Conta", "API"):
                    tab = page.locator(f'a:has-text("{tab_text}"), button:has-text("{tab_text}"), '
                                       f'[role="tab"]:has-text("{tab_text}")').first
                    if not tab.count():
                        tab = page.get_by_text(tab_text, exact=True).first
                    try:
                        if tab.count() and tab.is_visible():
                            tab.click(timeout=5000)
                            time.sleep(3)
                            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                            time.sleep(2)
                            break
                    except Exception:
                        pass

                create_btn = page.locator(
                    'button:has-text("Create Legacy API Key"), '
                    'button:has-text("Create New API Token"), '
                    'button:has-text("Create New Token"), '
                    'a:has-text("Create New API Token"), '
                    'a:has-text("Create New Token")'
                ).first

            if not create_btn.count():
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                foto = _print(page, "no_api_btn")
                botoes = [t.strip() for t in page.locator("button, a").all_inner_texts() if t.strip()][:80]
                cofre.fechar(proc, browser, nome=email)
                return {"sucesso": False, "erro": "botao 'Create New API Token' nao encontrado",
                        "print": foto, "botoes": botoes}

            # Interceptar download do kaggle.json
            username = None
            key = None

            try:
                with page.expect_download(timeout=30000) as download_info:
                    create_btn.click(timeout=10000)
                    page.wait_for_timeout(2500)
                    # chave legada (23/10) pede confirmação numa janela antes de baixar
                    dlg = page.locator('[role="dialog"]')
                    if dlg.count():
                        for txt in ("Continue", "Create", "Confirm", "Yes", "OK"):
                            b = dlg.get_by_role("button", name=txt, exact=True)
                            if b.count() and b.first.is_visible():
                                b.first.click(timeout=5000)
                                break
            except Exception as e:  # noqa: BLE001
                foto = _print(page, "sem_download")
                cofre.fechar(proc, browser, nome=email)
                return {"sucesso": False, "erro": f"download do kaggle.json não veio: {type(e).__name__}", "print": foto}

            download = download_info.value
            save_path = download_dir / f"kaggle_{email.split('@')[0]}.json"
            download.save_as(str(save_path))

            # Ler o kaggle.json
            try:
                dados = json.loads(save_path.read_text(encoding="utf-8"))
                username = dados.get("username", "")
                key = dados.get("key", "")
            except Exception as e:
                cofre.fechar(proc, browser, nome=email)
                return {"sucesso": False, "erro": f"falha ao ler kaggle.json: {e}"}
            finally:
                save_path.unlink(missing_ok=True)

            cofre.fechar(proc, browser, nome=email)

            if username and key:
                print(f"[{email.split('@')[0]}] Credencial capturada: {username} ...{key[-4:]}")
                resultado = salvar(email, username, key)
                resultado["sucesso"] = resultado["valida"]
                if not resultado["valida"]:
                    resultado["erro"] = "credencial capturada mas reprovada na validacao"
                return resultado
            else:
                return {"sucesso": False, "erro": "username ou key nao encontrados no kaggle.json"}

    except Exception as e:
        try:
            page.screenshot(path=str(DIR / f"_debug_kaggle_{email.split('@')[0]}.png"))
        except Exception:
            pass
        try:
            cofre.fechar(proc, browser, nome=email)
        except Exception:
            pass
        return {"sucesso": False, "erro": str(e)[:300]}


def criar_massa(*contas, vivas=False):
    """Cria contas Kaggle para várias contas Google. vivas = todas com Google vivo."""
    if vivas:
        lista = [email for email, _ in _contas_vivas()]
        print(f"[Fabrica] Modo --vivas: {len(lista)} contas")
    else:
        lista = list(contas)

    if not lista:
        return {"erro": "nenhuma conta especificada"}

    print(f"[Fabrica] Criando contas Kaggle para {len(lista)} conta(s) -- {datetime.now():%H:%M:%S}")

    log = DIR / f"kaggle_massa_log_{datetime.now():%Y%m%d_%H%M%S}.txt"
    resultados = []

    for i, conta in enumerate(lista, 1):
        print(f"\n[{i}/{len(lista)}] {conta}")
        r = criar(conta)
        r["conta"] = conta
        resultados.append(r)

        situacao = "OK" if r.get("sucesso") else ("PULADA" if r.get("pulada") else "FALHA")
        linha = f"{datetime.now():%H:%M:%S} | {conta:30} | {situacao} | {r.get('username', r.get('erro', ''))}\n"
        with open(log, "a", encoding="utf-8") as f:
            f.write(linha)

        print(f"  -> {situacao} {r.get('username', r.get('erro', ''))}")
        if r.get("pulada"):
            continue

        if not r.get("sucesso"):
            erro = r.get("erro", "")
            if "sessao Google expirada" in erro or "login Google falhou" in erro:
                print(f"  [Fabrica] Sessao expirada, pulando. Depois: python D:\\logins-google\\cofre.py logar {conta}")
            elif "CAPTCHA detectado" in erro:
                print(f"\n[Fabrica] CAPTCHA detectado! Resolver manualmente e retomar depois.")
                print(f"[Fabrica] Parando na conta {i}/{len(lista)}")
                break

        # Pausa entre contas
        if i < len(lista):
            time.sleep(20)

    sucesso_count = sum(1 for r in resultados if r.get("sucesso"))
    print(f"\n[Fabrica] Concluido: {sucesso_count}/{len(resultados)} contas criadas")
    print(f"[Fabrica] Log: {log}")

    # Gravar saida resumida
    saida = DIR / "kaggle_massa_saida.txt"
    linhas_saida = []
    for r in resultados:
        sit = "OK" if r.get("sucesso") else ("PULADA" if r.get("pulada") else "FALHA")
        linhas_saida.append(f"{r['conta']:30} | {sit:6} | {r.get('username', r.get('erro', ''))}")
    saida.write_text("\n".join(linhas_saida) + "\n", encoding="utf-8")

    return {"total": len(resultados), "sucesso": sucesso_count, "log": str(log)}


def listar():
    """Lista contas no registro local."""
    reg = _ler(REGISTRO, {})
    if not reg:
        print("Nenhuma conta Kaggle no registro local")
        return {"total": 0, "contas": []}

    print(f"{'Conta':<35} {'Username':<25} {'Valida':<8} {'Criado em'}")
    print("-" * 90)

    for conta, info in sorted(reg.items()):
        username = info.get("username", "???")
        valida = "OK" if info.get("valida") else "X"
        criado = info.get("criado_em", "")[:16].replace("T", " ")
        print(f"{conta:<35} {username:<25} {valida:<8} {criado}")

    total_validas = sum(1 for info in reg.values() if info.get("valida"))
    print(f"\nTotal: {len(reg)} contas | {total_validas} validas")

    return {"total": len(reg), "validas": total_validas}


if __name__ == "__main__":
    args = sys.argv[1:]

    if not args:
        print(__doc__)
        sys.exit(0)

    if args[0] == "listar":
        listar()

    elif args[0] == "criar" and len(args) >= 2:
        r = criar(args[1])
        print(json.dumps(r, indent=2, ensure_ascii=True))

    elif args[0] == "criar_massa":
        if "--vivas" in args:
            r = criar_massa(vivas=True)
        else:
            contas = [a for a in args[1:] if not a.startswith("--")]
            r = criar_massa(*contas)
        print(json.dumps(r, indent=2, ensure_ascii=True))

    elif args[0] == "salvar" and len(args) >= 4:
        r = salvar(args[1], args[2], args[3])
        print(json.dumps(r, indent=2, ensure_ascii=True))

    else:
        print(__doc__)
        sys.exit(1)
