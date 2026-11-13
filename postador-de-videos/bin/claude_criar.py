# -*- coding: utf-8 -*-
r"""claude_criar.py — cria (ou entra, se já existir) a conta do **claude.ai** pelo "Continuar com Google", usando a
conta Google que já está logada nos perfis das máquinas remotas (pc2, desktop, x200ma, acer via maquina_remota.py) ou
no cofre local (D:\logins-google\cofre). Feito no molde do bin\netbooks\tiktok_notebooks.py.

Por padrão, prioriza as máquinas remotas (pc2 -> desktop -> x200ma -> acer) onde o Google da conta já está logado,
pois o Cloudflare no PC1 costuma barrar com "Não foi possível verificar seu navegador".

    python bin\claude_criar.py --lista                        # mostra quais contas de empresa entrariam
    python bin\claude_criar.py --empresas                     # faz todas as de empresa que ainda não têm Claude
    python bin\claude_criar.py --empresas --uma               # só a próxima de empresa que falta (1 por vez)
    python bin\claude_criar.py empressinovare inovarecap      # contas específicas
    python bin\claude_criar.py --maquina pc2 empressinovare   # força máquina específica (pc2, x200ma, acer, desktop, pc1)
"""
import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, r"D:\logins-google")
sys.path.insert(0, str(Path(__file__).resolve().parent))

import maquina_remota as mr  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ESTADO = ROOT / "config" / "claude_contas.json"
FILA_IG = ROOT / "config" / "instagram_criar_fila.json"
GRUPOS = Path(r"D:\postador-de-videos\config\instagram_produtos.json")
PRINTS = ROOT / "logs" / "claude_tela"

ORGS = "https://claude.ai/api/organizations"
BTN_GOOGLE = re.compile(r"Continuar com(?: o)? Google|Continue with Google", re.I)
VERIFY_CF = re.compile(r"verificar seu navegador|couldn't verify your browser|verify you are human|confirme que você é humano", re.I)
PEDE_TELEFONE = re.compile(r"telefone|phone number|verify your phone|número de celular|enviar código.*sms", re.I)
PEDE_NOME = re.compile(r"como podemos te chamar|what should we call you|seu nome|your name|full name|nome completo", re.I)
CONTINUAR = ("Continuar", "Continue", "Concordar", "Agree", "Aceitar", "Accept", "I agree", "Começar", "Get started",
             "Próximo", "Next")
COOKIES = ("Aceitar tudo", "Accept all", "Aceitar todos os cookies", "Accept all cookies", "Allow all")

# Ordem padrão para o Claude: PC2 e desktop primeiro (pedido da dona), depois notebooks
ORDEM_MAQUINAS = ("pc2", "desktop", "x200ma", "acer")


def _ler(arq):
    try:
        return json.loads(arq.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _gravar_res(email, **campos):
    est = _ler(ESTADO)
    est.setdefault(email, {}).update({**campos, "t": time.time()})
    ESTADO.write_text(json.dumps(est, ensure_ascii=False, indent=2), encoding="utf-8")


def _liberar_ram():
    try:
        sys.path.insert(0, str(ROOT / "bin" / "netbooks"))
        import chrome_conta
        chrome_conta._liberar_ram()
    except Exception:  # noqa: BLE001
        pass


def _avisar(texto):
    try:
        sys.path.insert(0, r"D:\video-fila")
        import avisos
        avisos.enviar(texto, "claude criar", importante=True)
    except Exception:  # noqa: BLE001
        print("aviso não saiu:", texto)


def _print(pg, apelido, maq, etapa):
    try:
        PRINTS.mkdir(parents=True, exist_ok=True)
        pg.screenshot(path=str(PRINTS / f"{maq}_{apelido}_{time.strftime('%H-%M-%S')}_{etapa}.png"), timeout=20000)
    except Exception:  # noqa: BLE001
        pass
    for velho in sorted(PRINTS.glob("*.png"), key=lambda x: x.stat().st_mtime)[:-300]:
        velho.unlink(missing_ok=True)


def _texto(pg):
    try:
        return pg.inner_text("body", timeout=3000)
    except Exception:  # noqa: BLE001
        return ""


def _clicar(alvo, textos):
    for t in textos:
        try:
            b = alvo.get_by_role("button", name=t)
            if b.count() and b.first.is_visible() and b.first.is_enabled():
                b.first.click()
                alvo.wait_for_timeout(1000)
                return True
        except Exception:  # noqa: BLE001
            pass
    return False


def _logado(pg):
    try:
        if "claude.ai" not in pg.url:
            return False
        if re.search(r"claude\.ai/(chat/|new|recents|project)", pg.url):
            return True  # já na área logada (a API de organizações às vezes não responde no onboarding)
        r = pg.evaluate(f"async () => {{ const x = await fetch('{ORGS}', {{credentials:'include'}});"
                        " return x.ok ? await x.text() : ''; }}")
        dados = json.loads(r) if r else []
        return bool(dados) and bool((dados[0] or {}).get("uuid"))
    except Exception:  # noqa: BLE001
        return False


def _escolher_conta_popup(pop, email):
    """Seleciona a conta no popup do Google (suporta [data-identifier], [data-email], link ou texto exato)."""
    try:
        pop.set_viewport_size({"width": 1000, "height": 900})
    except Exception:  # noqa: BLE001
        pass
    seletores = [
        pop.locator(f'[data-identifier="{email.lower()}"], [data-email="{email.lower()}"]'),
        pop.get_by_role("link", name=re.compile(re.escape(email), re.I)),
        pop.get_by_text(email.lower(), exact=True),
    ]
    for sel in seletores:
        try:
            sel.first.wait_for(timeout=8000)
            sel.first.click()
            pop.wait_for_timeout(1500)
            return True
        except Exception:  # noqa: BLE001
            continue
    return False


def _consentir_popup(pop, email):
    if pop.is_closed():
        return
    try:
        txt_pop = pop.inner_text("body", timeout=2000)
        if re.search(r"choose an account|escolha uma conta|escolher uma conta", txt_pop, re.I):
            linha = pop.get_by_role("link", name=re.compile(re.escape(email), re.I))
            alvo = linha if linha.count() else pop.get_by_text(email.lower(), exact=True)
            if alvo.count() and alvo.first.is_visible():
                alvo.first.click(timeout=5000)
                pop.wait_for_timeout(1000)
    except Exception:  # noqa: BLE001
        pass
    _clicar(pop, ("Continuar", "Continue", "Permitir", "Allow"))


def _preencher_nome(pg, nome):
    try:
        campo = pg.locator("input[type=text]:visible, input:not([type]):visible").first
        if campo.count():
            campo.click()
            campo.fill(nome)
            pg.wait_for_timeout(500)
    except Exception:  # noqa: BLE001
        pass
    _clicar(pg, CONTINUAR)


CRIAR_CONTA = re.compile(r"vamos criar sua conta|let'?s create your account", re.I)
TERMOS = re.compile(r"agree|concordo|termos|terms", re.I)


PULAR = re.compile(r"^\s*(Pular|Skip|Agora não|Not now|Maybe later|Talvez mais tarde|Configurar depois|Set up later|"
                   r"Fazer isso depois|Do this later|Pular por enquanto|Skip for now)\s*$", re.I)


def _pular(pg):
    """Telas opcionais do cadastro (baixar app de desktop etc.): clica "Pular" (botão ou link)."""
    try:
        b = pg.get_by_text(PULAR)
        if b.count() and b.first.is_visible():
            b.first.click(timeout=5000)
            pg.wait_for_timeout(1500)
            return True
    except Exception:  # noqa: BLE001
        pass
    return False


def _tem_caixa(pg):
    return bool(pg.locator("input[type=checkbox]:visible, [role=checkbox]:visible").count())


def _aceitar_termos(pg):
    """Marca só a caixa dos TERMOS (+18); a de e-mails promocionais fica desmarcada."""
    try:
        caixas = pg.locator("input[type=checkbox], [role=checkbox]")
        for i in range(caixas.count()):
            c = caixas.nth(i)
            rotulo = c.evaluate("e => (e.closest('label') || e.parentElement.parentElement || e).innerText || ''")
            if not TERMOS.search(rotulo) or re.search(r"subscribe|promo", rotulo, re.I):
                continue
            marcado = c.get_attribute("aria-checked") == "true" or c.evaluate("e => !!e.checked")
            if not marcado:
                c.click(timeout=3000, force=True)
                pg.wait_for_timeout(500)
    except Exception:  # noqa: BLE001
        pass
    return _clicar(pg, ("Criar conta", "Create account", *CONTINUAR))


def _fluxo_claude(br, email, apelido, nome_exibicao, maq):
    """Executa a navegação no claude.ai/login dentro do Browser já conectado via CDP.
    Retorna (sucesso: bool, repetir_outra_maq: bool, mensagem: str)."""
    ctx = br.contexts[0]
    pg = ctx.new_page()
    try:
        pg.set_viewport_size({"width": 1280, "height": 1000})
    except Exception:  # noqa: BLE001
        pass
    pg.goto("https://claude.ai/login", wait_until="domcontentloaded", timeout=60000)
    pg.wait_for_timeout(4000)
    _clicar(pg, COOKIES)
    if _logado(pg):
        _print(pg, apelido, maq, "ja_logado")
        return True, False, f"{email} [{maq}]: já tinha conta no Claude (entrou)"

    txt0 = _texto(pg)
    if VERIFY_CF.search(txt0) and not BTN_GOOGLE.search(txt0):
        _print(pg, apelido, maq, "cloudflare_bloqueou")
        return False, True, f"{email} [{maq}]: Cloudflare bloqueou verificação do navegador"
    if "/onboarding" in pg.url or CRIAR_CONTA.search(txt0) or _tem_caixa(pg):
        # Google já confirmado numa tentativa anterior: a página abre direto no "Vamos criar sua conta"
        return _concluir(pg, None, email, apelido, nome_exibicao, maq, onboarding=True)

    botao = pg.get_by_role("button", name=BTN_GOOGLE)
    if not botao.count():
        botao = pg.get_by_text(BTN_GOOGLE)
    try:
        botao.first.wait_for(timeout=25000)
    except Exception:  # noqa: BLE001
        txt1 = _texto(pg)
        _print(pg, apelido, maq, "sem_botao_google")
        if VERIFY_CF.search(txt1):
            return False, True, f"{email} [{maq}]: Cloudflare bloqueou verificação do navegador"
        return False, True, f"{email} [{maq}]: não achei 'Continuar com Google' (ver {maq}_{apelido}_*sem_botao_google.png)"

    with ctx.expect_page(timeout=35000) as nova:
        botao.first.click()
    pop = nova.value
    pop.wait_for_load_state("domcontentloaded")
    _print(pop, apelido, maq, "popup_abriu")

    if not _escolher_conta_popup(pop, email):
        if not pop.is_closed():
            txt_p = _texto(pop)
            _print(pop, apelido, maq, "popup_sem_conta")
            if re.search(r"fazer login|sign in|use your google account|digite seu e-mail|enter your email", txt_p, re.I):
                return False, True, f"{email} [{maq}]: Google não está logado neste perfil"
        return False, True, f"{email} [{maq}]: Google não mostrou a conta no popup"
    return _concluir(pg, pop, email, apelido, nome_exibicao, maq)


def _concluir(pg, pop, email, apelido, nome_exibicao, maq, onboarding=False):
    """Telas depois do Google: termos/"Criar conta", nome, botões Continuar — até a API confirmar a organização."""
    espera = int(os.environ.get("CL_ESPERA", "60"))
    fim = time.time() + espera
    avisou_tel = False
    prox_diag = 0.0
    while time.time() < fim and not _logado(pg):
        if pop is not None:
            _consentir_popup(pop, email)
        txt = _texto(pg)
        if time.time() >= prox_diag:
            prox_diag = time.time() + 15
            _print(pg, apelido, maq, "espera")
            try:
                print(f"   [{maq}:{apelido}] url={pg.url} | {' '.join(txt.split())[:160]}", flush=True)
            except Exception:  # noqa: BLE001
                pass
        if VERIFY_CF.search(txt):
            _print(pg, apelido, maq, "cf_pos_google")
            return False, True, f"{email} [{maq}]: Cloudflare bloqueou após clicar em Continuar com Google"
        if PEDE_TELEFONE.search(txt):
            onboarding = True
            if not avisou_tel:
                avisou_tel = True
                _print(pg, apelido, maq, "pede_telefone")
                print(f"   [{maq}:{apelido}] PEDIU TELEFONE (SMS) — não peço SMS sozinho", flush=True)
            return False, False, f"{email} [{maq}]: Claude pediu verificação por TELEFONE (SMS) — parado na etapa de telefone"
        if PEDE_NOME.search(txt):
            onboarding = True
            _print(pg, apelido, maq, "nome")
            _preencher_nome(pg, nome_exibicao)
            fim = max(fim, time.time() + 30)
        elif re.search(r"planos que crescem|plans that grow|choose (a|your) plan", txt, re.I):
            # só o plano GRÁTIS; nunca Pro/Max (pago)
            onboarding = True
            _print(pg, apelido, maq, "planos")
            _clicar(pg, ("Use o Claude gratuitamente", "Use Claude for free", "Continuar com o Free",
                         "Continue with Free", "Stay on Free"))
            fim = max(fim, time.time() + 30)
        elif _pular(pg):
            onboarding = True
            fim = max(fim, time.time() + 30)
        elif _tem_caixa(pg) or CRIAR_CONTA.search(txt):
            onboarding = True
            _aceitar_termos(pg)
            fim = max(fim, time.time() + 30)
        elif _clicar(pg, CONTINUAR):
            fim = max(fim, time.time() + 20)
        time.sleep(2)

    if not _logado(pg):
        _print(pg, apelido, maq, "nao_entrou")
        return False, True, f"{email} [{maq}]: não concluiu em {espera}s (ver {maq}_{apelido}_*.png)"
    time.sleep(5)  # aguarda gravar cookies
    _print(pg, apelido, maq, "ok")
    return True, False, f"{email} [{maq}]: {'CONTA CRIADA no Claude' if onboarding else 'já tinha conta (entrou)'}"


def _maquinas_candidatas(apelido, maq_forcada=None):
    if maq_forcada:
        return [maq_forcada]
    lg = (mr._logins().get(apelido) or {})
    com_google = []
    sem_google = []
    for m in ORDEM_MAQUINAS:
        v = lg.get(m)
        if isinstance(v, dict) and (v.get("google") or v.get("youtube")):
            com_google.append(m)
        else:
            sem_google.append(m)
    return com_google + sem_google


# ───────── login do Google SEM Playwright (28/10: com ele ligado na aba, o claude.ai responde "Não foi possível
# verificar seu navegador" na volta do Google). Cliques por CDP cru: acha o botão pelo DOM e manda mouse de verdade.
def _alvos(porta):
    import urllib.request
    try:
        return json.loads(urllib.request.urlopen(f"http://127.0.0.1:{porta}/json", timeout=10).read())
    except Exception:  # noqa: BLE001
        return []


def _url_pagina(porta, filtro):
    return next((t.get("url", "") for t in _alvos(porta) if t.get("type") == "page" and filtro in t.get("url", "")), "")


async def _cdp_clicar(ws_url, xpaths):
    import asyncio
    import aiohttp
    async with aiohttp.ClientSession() as s:
        async with s.ws_connect(ws_url, max_msg_size=0) as ws:
            n = 0

            async def cmd(metodo, **params):
                nonlocal n
                n += 1
                mid = n
                await ws.send_json({"id": mid, "method": metodo, "params": params})
                while True:
                    m = await ws.receive_json(timeout=30)
                    if m.get("id") == mid:
                        return m.get("result") or {}

            await cmd("DOM.getDocument", depth=0)
            for xp in xpaths:
                r = await cmd("DOM.performSearch", query=xp)
                if not r.get("resultCount"):
                    continue
                ids = (await cmd("DOM.getSearchResults", searchId=r["searchId"], fromIndex=0,
                                 toIndex=r["resultCount"])).get("nodeIds", [])
                for nid in ids:
                    try:
                        await cmd("DOM.scrollIntoViewIfNeeded", nodeId=nid)
                        q = (await cmd("DOM.getBoxModel", nodeId=nid))["model"]["content"]
                    except (KeyError, IndexError):
                        continue
                    x, y = (q[0] + q[4]) / 2, (q[1] + q[5]) / 2
                    if x <= 0 or y <= 0:
                        continue
                    for tipo in ("mouseMoved", "mousePressed", "mouseReleased"):
                        await cmd("Input.dispatchMouseEvent", type=tipo, x=x, y=y, button="left", clickCount=1)
                        await asyncio.sleep(0.08)
                    return True
            return False


def _cru(porta, filtro_url, xpaths):
    """Clica o 1º elemento visível dos xpaths na aba cuja URL contém filtro_url. Thread própria (o Playwright sync
    não deixa abrir outro loop asyncio na mesma thread)."""
    import asyncio
    import threading
    alvo = next((t for t in _alvos(porta) if t.get("type") == "page" and filtro_url in t.get("url", "")), None)
    if not alvo:
        return False
    ws_url = re.sub(r"ws://[^/]+", f"ws://127.0.0.1:{porta}", alvo["webSocketDebuggerUrl"])  # túnel: porta local
    out = {}

    def rodar():
        try:
            out["r"] = asyncio.run(_cdp_clicar(ws_url, xpaths))
        except Exception as e:  # noqa: BLE001
            out["erro"] = e
    th = threading.Thread(target=rodar, daemon=True)
    th.start()
    th.join(90)
    if out.get("erro"):
        print(f"   cdp cru em {filtro_url}: {type(out['erro']).__name__}: {str(out['erro'])[:160]}", flush=True)
    return bool(out.get("r"))


def _area(u):
    return bool(re.search(r"claude\.ai/(chat|new|recents|project|onboarding)", u or ""))


def _google_cru(porta, email):
    """'pronto' (claude.ai saiu do /login), 'sem_botao', 'sem_popup' ou 'ficou_no_login'."""
    fim = time.time() + 60
    while time.time() < fim and not _url_pagina(porta, "claude.ai"):
        time.sleep(2)
    time.sleep(8)
    if _area(_url_pagina(porta, "claude.ai")):
        return "pronto"
    if not _cru(porta, "claude.ai/login", ["//button[contains(., 'Continuar com o Google')]",
                                          "//button[contains(., 'Continue with Google')]",
                                          "//button[contains(., 'Google')]"]):
        time.sleep(5)  # já logado: o /login ainda estava redirecionando pro chat
        return "pronto" if _area(_url_pagina(porta, "claude.ai")) else "sem_botao"
    fim = time.time() + 120  # o botão fica girando enquanto o claude.ai verifica o navegador, antes do popup
    while time.time() < fim and not _url_pagina(porta, "accounts.google.com"):
        if _area(_url_pagina(porta, "claude.ai")):
            return "pronto"
        time.sleep(2)
    if not _url_pagina(porta, "accounts.google.com"):
        return "sem_popup"
    time.sleep(3)
    fim = time.time() + 90
    while time.time() < fim and _url_pagina(porta, "accounts.google.com"):
        _cru(porta, "accounts.google.com", [f"//*[@data-identifier='{email}']", f"//*[@data-email='{email}']",
                                            "//button[contains(., 'Continuar')]", "//button[contains(., 'Continue')]",
                                            "//button[contains(., 'Permitir')]", "//button[contains(., 'Allow')]"])
        time.sleep(4)
    fim = time.time() + 40
    while time.time() < fim:
        u = _url_pagina(porta, "claude.ai")
        if _area(u):
            return "pronto"
        time.sleep(2)
    return "ficou_no_login"


def _tentar_remoto(p, maq, email, apelido, nome_exibicao):
    r = mr.Remoto(maq)
    if not r.vivo():
        return False, True, f"{email} [{maq}]: máquina não respondeu ao SSH"
    # No PC2, se a porta 9460 estiver ocupada, podemos usar a porta extra 9465 (suportada pelo chrome_conta.py 9461-9479)
    if maq == "pc2" and not mr.maquina_livre("pc2", cache_s=0):
        r.porta = 9465
    try:
        porta = r.abrir(apelido, "https://claude.ai/login", sem_espera=True)
        etapa = _google_cru(porta, email)
        print(f"   [{maq}:{apelido}] Google sem Playwright: {etapa}", flush=True)
        br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}", timeout=60000)
        ctx = br.contexts[0]
        pg = next((x for x in ctx.pages if "claude.ai" in x.url), None)
        if pg is None:
            return False, True, f"{email} [{maq}]: aba do claude.ai sumiu"
        if etapa != "pronto":
            txt = _texto(pg)
            _print(pg, apelido, maq, f"google_{etapa}")
            if VERIFY_CF.search(txt):
                return False, True, f"{email} [{maq}]: Cloudflare bloqueou (mesmo sem Playwright no login)"
            return False, True, f"{email} [{maq}]: login do Google não concluiu ({etapa})"
        if _logado(pg):
            _print(pg, apelido, maq, "ok")
            return True, False, f"{email} [{maq}]: já tinha conta no Claude (entrou)"
        return _concluir(pg, None, email, apelido, nome_exibicao, maq, onboarding=True)
    except Exception as ex:  # noqa: BLE001
        return False, True, f"{email} [{maq}]: {type(ex).__name__}: {str(ex)[:140]}"
    finally:
        # 28/10: fechado logo após o login, o Chrome não gravou o sessionKey no disco (inovaremanhwaverse perdeu a
        # sessão). Como no tiktok_notebooks._ligar: 40 s pra ele gravar os cookies antes de fechar.
        time.sleep(40)
        r.fechar()


def _tentar_pc1(p, email, apelido, nome_exibicao):
    import cofre
    _, e = cofre.conta(email)
    if e.get("google") != "vivo":
        return False, False, f"{email} [pc1]: Google '{e.get('google')}' no cofre local"
    _liberar_ram()
    porta, proc = cofre.abrir(email, "about:blank", visivel=True)
    br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
    try:
        return _fluxo_claude(br, email, apelido, nome_exibicao, "pc1")
    finally:
        cofre.fechar(proc, br, email)


def criar(p, nome_cofre, nome_exibicao=None, maq_forcada=None):
    import cofre
    try:
        email, e = cofre.conta(nome_cofre)
        apelido = (e.get("apelido") or email.split("@")[0]).lower()
        if e.get("tipo") == "instagram":
            return f"{email}: perfil só de Instagram, sem Google — pular"
    except Exception:
        apelido = nome_cofre.split("@")[0].lower()
        email = nome_cofre if "@" in nome_cofre else f"{apelido}@gmail.com"
    nome_exibicao = nome_exibicao or apelido

    if maq_forcada == "pc1":
        _, _, msg = _tentar_pc1(p, email, apelido, nome_exibicao)
        return msg

    erros = []
    for maq in _maquinas_candidatas(apelido, maq_forcada):
        print(f"-> Tentando {email} em [{maq}]...", flush=True)
        ok, repetir, msg = _tentar_remoto(p, maq, email, apelido, nome_exibicao)
        if ok or not repetir:
            return msg
        print(f"   {msg}", flush=True)
        erros.append(msg)

    return erros[-1] if erros else f"{email}: nenhuma máquina disponível"


# ─────────────────────────── seleção das contas de empresa ─────────────────────────
def _nome_por_produto():
    g = {}
    for grupo in (_ler(GRUPOS).get("grupos") or []):
        g[grupo.get("produto")] = grupo.get("nome")
    return g


def empresas():
    nomes = _nome_por_produto()
    out, vistos = [], set()
    for _tiktok, r in _ler(FILA_IG).items():
        prod = r.get("produto")
        email = (r.get("email") or "").lower()
        if prod and email and email not in vistos:
            vistos.add(email)
            out.append((email, nomes.get(prod) or prod))
    return out


def _falta(email):
    res = str((_ler(ESTADO).get(email) or {}).get("resultado", ""))
    return "CRIADA" not in res and "já tinha conta" not in res


def main(a):
    from playwright.sync_api import sync_playwright
    maq_forcada = None
    if "--maquina" in a:
        idx = a.index("--maquina")
        if idx + 1 < len(a):
            maq_forcada = a[idx + 1]
            a = a[:idx] + a[idx + 2:]

    quer_empresas = "--empresas" in a or "--lista" in a
    explicitos = [x for x in a if not x.startswith("--")]

    if quer_empresas:
        alvos = [(e, n) for e, n in empresas() if _falta(e)]
    else:
        alvos = [(x, None) for x in explicitos]

    if "--lista" in a:
        print(f"Contas de empresa que ainda não têm Claude ({len(alvos)}):")
        for email, nome in alvos:
            print(f"  {email:40} {nome}")
        return
    if not alvos:
        print("Nada a fazer (todas as contas de empresa já têm Claude, ou nenhuma conta informada).")
        return
    if "--uma" in a:
        alvos = alvos[:1]

    with sync_playwright() as p:
        for email, nome in alvos:
            try:
                r = criar(p, email, nome, maq_forcada=maq_forcada)
            except Exception as ex:  # noqa: BLE001
                r = f"{email}: ERRO {type(ex).__name__}: {str(ex)[:160]}"
            print(r, flush=True)
            res = ("CONTA CRIADA no Claude" if "CRIADA" in r else
                   "já tinha conta" if "já tinha conta" in r else r.split(": ", 1)[-1])
            _gravar_res(email if "@" in email else f"{email}@gmail.com", resultado=res, nome=nome)


if __name__ == "__main__":
    if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main(sys.argv[1:])
