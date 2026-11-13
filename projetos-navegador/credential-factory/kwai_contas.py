r"""
Kwai: cria/loga conta nas contas Google do cofre (login "Continue com o Google").
Alvo padrao: as contas que tem cookies de TikTok (as mesmas do postador de TikTok).

Passos: www.kwai.com -> Fazer login -> Continue com o Google -> popup OAuth (escolhe a conta, Continuar)
-> volta logado no Kwai. Primeira vez = cria a conta.

CLI:
  python kwai_contas.py logar <conta>
  python kwai_contas.py criar_massa <c1> <c2> ...
  python kwai_contas.py criar_massa --tiktok     # todas as contas com cookies de TikTok + Google vivo
  python kwai_contas.py criar_massa --instagram  # contas Google que tem um Instagram ligado (configs do postador)
  python kwai_contas.py criar_massa --todas      # TODAS as contas Google vivas do cofre (a frota inteira)
  python kwai_contas.py listar
  python kwai_contas.py assistido <c1> <c2> ...  # Google deslogado: digita o e-mail, a dona digita a senha
"""
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, r"D:\logins-google")
import cofre

DIR = Path(__file__).resolve().parent
REGISTRO = DIR / "kwai_contas.json"
KWAI_URL = "https://www.kwai.com"
# Com FedCM o Google abre a escolha de conta em janela nativa do Chrome (fora do Playwright); sem ele, vira popup.
# So vale o ultimo --disable-features, por isso repete a lista do cofre (+ Translate, que faz a barra de traducao).
SEM_FEDCM = tuple(f + ",FedCm,Translate" for f in cofre.FLAGS if f.startswith("--disable-features="))
# O Kwai enche a tela de popups: pedido de notificacao (Chrome) e barra de traducao. --disable-notifications
# corta o pedido de notificacao; o "Instale o app" (PWA, no DOM) e fechado por _fechar_popups.
EXTRA_KWAI = SEM_FEDCM + ("--disable-notifications", "--no-default-browser-check")
# O "Instale o app" e janela NATIVA do Chrome (instalacao de PWA): o Kwai guarda o evento beforeinstallprompt e
# chama prompt() no primeiro clique da pagina, roubando o clique do "Continue com o Google". Bloquear o evento
# antes dos scripts do Kwai (fase de captura) impede o Kwai de abrir essa janela.
BLOQUEIA_PWA = ("window.addEventListener('beforeinstallprompt', function (e) {"
                " e.preventDefault(); e.stopImmediatePropagation(); }, true);")


def _ler(arq, padrao):
    return json.loads(arq.read_text(encoding="utf-8")) if arq.exists() else padrao


def _gravar(arq, dados):
    arq.parent.mkdir(parents=True, exist_ok=True)
    tmp = arq.with_suffix(".tmp")
    tmp.write_text(json.dumps(dados, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    tmp.replace(arq)


def _registrar(conta, **campos):
    reg = _ler(REGISTRO, {})
    reg.setdefault(conta, {}).update(campos)
    _gravar(REGISTRO, reg)


def _contas_tiktok():
    """Contas com cookies de TikTok (servico vivo ou extras) e Google vivo."""
    reg = cofre._ler()["contas"]
    out = []
    for email, i in reg.items():
        if "@" not in email:
            continue
        vivo = i.get("google") == "vivo" or i.get("servicos", {}).get("google") == "vivo"
        s_tt = i.get("servicos", {}).get("tiktok") == "vivo"
        ex = any("tiktok" in str(x.get("servicos", [])) for x in i.get("extras", []))
        if vivo and (s_tt or ex):
            out.append(email.split("@")[0])
    return sorted(out)


def _contas_todas():
    """Todas as contas Google vivas no cofre (a frota inteira; Kwai e por conta Google)."""
    c = cofre._ler()["contas"]
    out = []
    for email, i in c.items():
        if "@" not in email:
            continue
        if i.get("google") == "vivo" or i.get("servicos", {}).get("google") == "vivo":
            out.append(email.split("@")[0])
    return sorted(out)


IG_CONFIG = Path(r"D:\postador-de-videos\config")


def _contas_instagram():
    """Contas Google (do cofre, vivas) que tem um Instagram ligado nos configs do postador.
    So entram as que tem campo 'email' (as antigas usam login so com usuario/senha, sem Google)."""
    c = cofre._ler()["contas"]
    nomes = set()
    for arq in ("instagram_local.json", "instagram_criar_fila.json"):
        p = IG_CONFIG / arq
        if not p.exists():
            continue
        for _ig, i in _ler(p, {}).items():
            em = i.get("email")
            if not em or "@" not in em:
                continue
            info = c.get(em, {})
            vivo = info.get("google") == "vivo" or info.get("servicos", {}).get("google") == "vivo"
            if vivo:
                nomes.add(em.split("@")[0])
    return sorted(nomes)


def _fechar_popups(page):
    """Fecha os aviso que o Kwai joga na tela (PWA 'Instale o app', etc.) sem fechar o modal de login.
    O modal de login NAO tem 'Cancelar'; o 'Instale o app' tem, por isso e seguro clicar nele."""
    for _ in range(3):
        fechou = False
        for sel in ('button:has-text("Cancelar")', 'div[role=button]:has-text("Cancelar")',
                    '[class*="install"] [class*="close"]', '[class*="download"] [class*="close"]'):
            try:
                loc = page.locator(sel).first
                if loc.count() and loc.is_visible():
                    loc.click(timeout=2000)
                    fechou = True
                    time.sleep(0.4)
            except Exception:
                pass
        if not fechou:
            return


def _logado(page):
    """Logado no Kwai web = sumiu o botao 'Fazer login'."""
    try:
        txt = page.inner_text("body", timeout=4000)
    except Exception:
        return False
    return "Fazer login" not in txt and "Faca login" not in txt


def _resolver_google(popup, email):
    """No popup OAuth do Google: escolhe a conta e aceita, ate o popup fechar."""
    fim = time.time() + 60
    while time.time() < fim:
        if popup.is_closed():
            return True
        try:
            # escolher a conta pelo e-mail
            alvo = popup.get_by_text(email, exact=False).first
            if alvo.count() and alvo.is_visible():
                alvo.click(timeout=4000)
                _esperar(popup, 2)
                continue
            # consentimento: Continuar / Continue / Permitir / Allow / Confirmar
            for txt in ("Continuar", "Continue", "Permitir", "Allow", "Confirmar", "Confirm"):
                b = popup.get_by_role("button", name=txt).first
                if b.count() and b.is_visible():
                    b.click(timeout=4000)
                    _esperar(popup, 2)
                    break
        except Exception:
            pass
        _esperar(popup, 1.5)
    return popup.is_closed()


def _esperar(page, s):
    """Espera deixando o Playwright processar eventos (janela nova, popup fechado). time.sleep trava isso."""
    try:
        page.wait_for_timeout(int(s * 1000))
    except Exception:
        time.sleep(s)


def _matar_chrome_da_pasta(pasta):
    """Mata o Chrome preso que ficou segurando a pasta do perfil (sobra de execucao anterior)."""
    pasta = str(pasta)
    try:
        ps = ("Get-CimInstance Win32_Process -Filter \"Name='chrome.exe'\" | "
              f"Where-Object {{ $_.CommandLine -like '*{pasta}*' }} | "
              "ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }")
        subprocess.run(["powershell", "-NoProfile", "-Command", ps], timeout=30,
                       capture_output=True)
    except Exception:
        pass


def _abrir(conta_nome, e):
    """cofre.abrir resiliente: se o Chrome nao abrir a porta (pasta presa), mata o preso e tenta de novo."""
    try:
        return cofre.abrir(conta_nome, url=KWAI_URL, visivel=True, extra=EXTRA_KWAI)
    except RuntimeError:
        _matar_chrome_da_pasta(e.get("pasta", ""))
        time.sleep(3)
        return cofre.abrir(conta_nome, url=KWAI_URL, visivel=True, extra=EXTRA_KWAI)


def logar(conta_nome, visivel=True):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return {"sucesso": False, "erro": "Playwright nao instalado"}

    email, e = cofre.conta(conta_nome)
    if e.get("google") != "vivo" and e.get("servicos", {}).get("google") != "vivo":
        return {"sucesso": False, "conta": conta_nome, "erro": "google_deslogado_no_cofre (cofre.py logar)"}

    print(f"[{conta_nome}] Abrindo Kwai...", flush=True)
    try:
        porta, proc = _abrir(conta_nome, e)
    except Exception as ex:
        return {"sucesso": False, "conta": conta_nome, "erro": f"nao_abriu_chrome: {str(ex)[:150]}"}
    try:
        with sync_playwright() as p:
            br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
            ctx = br.contexts[0]
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            # o init script so vale em navegacao nova: por isso carrega o Kwai de novo depois de registrar
            ctx.add_init_script(BLOQUEIA_PWA)
            page.goto(KWAI_URL, timeout=45000, wait_until="domcontentloaded")
            _esperar(page, 7)
            _fechar_popups(page)

            if _logado(page):
                print(f"[{conta_nome}] Ja estava logado.", flush=True)
                _registrar(email, logado=True, visto_em=datetime.now(timezone.utc).isoformat(timespec="seconds"))
                cofre.fechar(proc, br, nome=conta_nome)
                return {"sucesso": True, "conta": conta_nome, "nota": "ja logado"}

            # abrir o modal de login (se o botao "Continue com o Google" ainda nao estiver na tela)
            gbtn = page.get_by_text("Continue com o Google", exact=False).first
            if not (gbtn.count() and gbtn.is_visible()):
                for sel in ('button:has-text("Fazer login")', 'text=Fazer login'):
                    try:
                        page.locator(sel).first.click(timeout=5000)
                        break
                    except Exception:
                        pass
                time.sleep(4)
                _fechar_popups(page)
                gbtn = page.get_by_text("Continue com o Google", exact=False).first

            if not (gbtn.count() and gbtn.is_visible()):
                page.screenshot(path=str(DIR / f"_kwai_{conta_nome}_sembotao.png"))
                cofre.fechar(proc, br, nome=conta_nome)
                return {"sucesso": False, "conta": conta_nome, "erro": "botao Google nao apareceu"}

            # o botao "Continue com o Google" e um iframe do GSI; esperar ele carregar antes de clicar
            gsi = page.frame_locator('iframe[src*="accounts.google.com/gsi/button"]').locator("div[role=button]").first
            for _ in range(10):
                try:
                    if gsi.count() and gsi.is_visible():
                        break
                except Exception:
                    pass
                time.sleep(1)

            # clique real de mouse no centro do botao (atinge o iframe invisivel do Google por cima).
            # A janela de escolha de conta do Google demora (>8 s): procurar por ela ate 30 s antes de clicar de novo.
            popup = None
            for tentativa in range(2):
                _fechar_popups(page)  # o "Instale o app" volta e cobre o botao; tira antes de cada clique
                try:
                    bb = gbtn.bounding_box()
                    page.mouse.click(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2)
                except Exception:
                    try:
                        gsi.click(timeout=5000)
                    except Exception:
                        pass
                for _ in range(30):
                    _esperar(page, 1)
                    novas = [pg for pg in ctx.pages if "accounts.google.com" in pg.url and pg is not page]
                    if novas:
                        popup = novas[-1]
                        break
                    if _logado(page):
                        break
                if popup is not None or _logado(page):
                    break
            if popup is not None:
                print(f"[{conta_nome}] Popup do Google, escolhendo conta...", flush=True)
                # email_google no cofre: perfil cujo apelido nao e o e-mail real (ex.: contapessoal)
                _resolver_google(popup, e.get("email_google") or email)
            else:
                # sem popup: pode ser redirect/one-tap na mesma aba
                time.sleep(6)

            # esperar logar (ate 40s)
            ok = False
            for _ in range(20):
                if _logado(page):
                    ok = True
                    break
                time.sleep(2)

            if ok:
                print(f"[{conta_nome}] LOGADO.", flush=True)
                _registrar(email, logado=True, criado_em=datetime.now(timezone.utc).isoformat(timespec="seconds"))
                cofre.fechar(proc, br, nome=conta_nome)
                return {"sucesso": True, "conta": conta_nome}
            else:
                abas = [pg.url[:120] for pg in ctx.pages]
                try:
                    page.screenshot(path=str(DIR / f"_kwai_{conta_nome}_falha.png"), timeout=10000)
                except Exception:
                    pass
                if popup is not None and not popup.is_closed():
                    try:
                        popup.screenshot(path=str(DIR / f"_kwai_{conta_nome}_google.png"), timeout=10000)
                        print(popup.inner_text("body", timeout=5000)[:600], flush=True)
                    except Exception:
                        pass
                cofre.fechar(proc, br, nome=conta_nome)
                return {"sucesso": False, "conta": conta_nome, "erro": "nao confirmou login", "abas": abas,
                        "popup": popup is not None}
    except Exception as ex:
        try:
            cofre.fechar(proc, br, nome=conta_nome)
        except Exception:
            pass
        return {"sucesso": False, "conta": conta_nome, "erro": str(ex)[:250]}


def assistido(conta_nome, espera_min=10):
    """Google deslogado no perfil: abre o Chrome da conta no cofre, digita o e-mail e espera a dona digitar a
    senha (e o 2FA). Logou = marca google=vivo no cofre (vale pra todos os projetos) e ja cria o Kwai."""
    from playwright.sync_api import sync_playwright
    email, e = cofre.conta(conta_nome)
    kiro = Path(cofre.__file__).resolve().parent / "kiro_contas_unica.json"
    if kiro.exists() and json.loads(kiro.read_text(encoding="utf-8"))["contas"].get(email, {}).get("bloqueada_novo_login"):
        return {"sucesso": False, "conta": conta_nome, "erro": "bloqueada_novo_login (Kiro): nao logar"}
    url = "https://accounts.google.com/ServiceLogin?continue=https%3A%2F%2Fmyaccount.google.com%2F"
    porta, proc = cofre.abrir(email, url=url, visivel=True)
    logou = False
    with sync_playwright() as p:
        br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
        ctx = br.contexts[0]
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(url, timeout=45000, wait_until="domcontentloaded")
        _esperar(page, 3)
        if urlparse(page.url).netloc != "myaccount.google.com":
            # digita o e-mail tecla por tecla e confere se chegou na tela de senha; senao tenta de novo
            for _ in range(3):
                try:
                    escolher = page.get_by_text("Usar outra conta", exact=False).first
                    if escolher.count() and escolher.is_visible():
                        escolher.click(timeout=5000)
                        _esperar(page, 3)
                    campo = page.locator('#identifierId, input[name="identifier"], input[type="email"]').first
                    campo.wait_for(state="visible", timeout=15000)
                    campo.click()
                    campo.press("Control+A")
                    campo.press("Delete")
                    campo.type(email, delay=60)
                    _esperar(page, 0.5)
                    avancar = page.get_by_role("button", name="Avançar").first
                    if avancar.count() and avancar.is_visible():
                        avancar.click(timeout=5000)
                    else:
                        campo.press("Enter")
                    page.wait_for_url("**/challenge/**", timeout=15000)
                    break
                except Exception:
                    page.goto(url, timeout=45000, wait_until="domcontentloaded")
                    _esperar(page, 3)
            if "/challenge/" in page.url:
                print(f"\n>>> {email}: e-mail digitado. DIGITE A SENHA na janela do Chrome (ate {espera_min} min).",
                      flush=True)
            else:
                print(f"\n>>> {email}: NAO consegui passar do e-mail ({page.url[:80]}). Veja a janela.", flush=True)
        fim = time.time() + espera_min * 60
        while time.time() < fim:
            try:
                if any(urlparse(pg.url).netloc == "myaccount.google.com" for pg in ctx.pages):
                    logou = True
                    break
            except Exception:
                pass
            _esperar(page, 2)
        if logou:
            # o Chrome grava cookies no disco a cada ~30 s; fechar antes disso perde o login
            print(f">>> {email}: logou, esperando 35 s o Chrome gravar o login...", flush=True)
            _esperar(page, 35)
        cofre.fechar(proc, br, nome=email)
    if not logou:
        print(f">>> {email}: nao logou em {espera_min} min.", flush=True)
        return {"sucesso": False, "conta": conta_nome, "erro": "senha nao digitada a tempo"}
    cofre._marcar(email, google="vivo", checado=datetime.now().isoformat(timespec="minutes"))
    print(f">>> {email}: Google LOGADO no cofre. Criando o Kwai...", flush=True)
    time.sleep(3)
    return logar(conta_nome)


def criar_massa(contas, tiktok=False, instagram=False, todas=False):
    if tiktok:
        lista = _contas_tiktok()
    elif instagram:
        lista = _contas_instagram()
    elif todas:
        lista = _contas_todas()
    else:
        lista = list(contas)
    # nao refaz quem ja esta logado (registro), mas reavalia falhas
    reg = _ler(REGISTRO, {})
    jalog = {e.split("@")[0] for e, v in reg.items() if v.get("logado")}
    lista = [c for c in lista if c not in jalog]
    if not lista:
        return {"erro": "nenhuma conta nova (todas ja logadas ou lista vazia)"}
    print(f"[Kwai] {len(lista)} conta(s) -- {datetime.now():%H:%M:%S}", flush=True)
    res = []
    for i, c in enumerate(lista, 1):
        print(f"\n[{i}/{len(lista)}] {c}", flush=True)
        r = logar(c)
        print(f"  -> {'OK' if r.get('sucesso') else 'FALHA'} {r.get('nota') or r.get('erro','')}", flush=True)
        res.append(r)
        if i < len(lista):
            time.sleep(20)
    # segunda passada: a janela do Google as vezes demora e a primeira tentativa falha
    falhas = [r["conta"] for r in res if not r.get("sucesso") and r.get("conta")]
    if falhas:
        print(f"\n[Kwai] 2a passada em {len(falhas)} falha(s)", flush=True)
        for c in falhas:
            print(f"\n[2a] {c}", flush=True)
            r = logar(c)
            print(f"  -> {'OK' if r.get('sucesso') else 'FALHA'} {r.get('nota') or r.get('erro','')}", flush=True)
            if r.get("sucesso"):
                res = [x for x in res if x.get("conta") != c] + [r]
            time.sleep(20)
    ok = sum(1 for r in res if r.get("sucesso"))
    print(f"\n[Kwai] {ok}/{len(res)} logadas", flush=True)
    for r in res:
        if not r.get("sucesso"):
            print(f"  FALHOU: {r.get('conta')} -- {r.get('erro','')}", flush=True)
    return {"total": len(res), "ok": ok}


def listar():
    reg = _ler(REGISTRO, {})
    for c, v in sorted(reg.items()):
        print(f"{c:40s} logado={v.get('logado')}  {v.get('criado_em') or v.get('visto_em') or ''}")
    print(f"\nTotal: {sum(1 for v in reg.values() if v.get('logado'))} logadas de {len(reg)}")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        print(__doc__)
    elif a[0] == "logar" and len(a) >= 2:
        print(json.dumps(logar(a[1]), indent=2, ensure_ascii=False))
    elif a[0] == "assistido" and len(a) >= 2:
        for c in a[1:]:
            print(json.dumps(assistido(c), indent=2, ensure_ascii=False), flush=True)
    elif a[0] == "criar_massa":
        if "--tiktok" in a:
            criar_massa([], tiktok=True)
        elif "--instagram" in a:
            criar_massa([], instagram=True)
        elif "--todas" in a:
            criar_massa([], todas=True)
        else:
            criar_massa([x for x in a[1:] if not x.startswith("--")])
    elif a[0] == "listar":
        listar()
    else:
        print(__doc__)
