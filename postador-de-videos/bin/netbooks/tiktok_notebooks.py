"""tiktok_notebooks.py — loga o TikTok ("Continuar com Google") nos NOTEBOOKS, sozinho, quando um deles está livre
(dona 23/10/2026: "o login do TikTok você pode fazer entre uma ação e outra do notebook estando livre; não esqueça que
tem que rolar pra baixo ou reduzir o zoom pro botão aparecer"). Desde 23/10: página emulada em 1280x1000 + rolagem (o zoom por CSS desalinhava o clique).

Pra cada conta da fila (e-mail já logado no Google no notebook, TikTok ainda não): abre o perfil NA TELA, zoom menor,
clica "Continuar com Google", escolhe a conta, aceita o "Continuar" do Google. Logou = liga o TikTok dessa conta naquele
notebook (reuso_plataformas.json "maquina"). Pediu CÓDIGO por e-mail = deixa a janela aberta na tela com o Gmail ao lado
e avisa a dona no Telegram (o código é ela quem digita). Google abriria cadastro novo = para, não cria nada.
Senha nunca. Várias contas por rodada, até 17 min, enquanto houver notebook livre (o vigia geral chama a cada 20 min).

    python bin\\netbooks\\tiktok_notebooks.py            # uma conta, no notebook que estiver livre
    python bin\\netbooks\\tiktok_notebooks.py --fila     # mostra quem falta
"""
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import maquina_remota as mr  # noqa: E402

ESTADO = mr.ROOT / "config" / "tiktok_notebooks.json"


def _ler():
    try:
        return json.loads(ESTADO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def fila():
    """[(perfil, notebook)] com Google logado lá e TikTok ainda não, só de quem tem conta do TikTok cadastrada."""
    logins, est, out = mr._logins(), _ler(), []
    for perfil, info in mr._mapa_perfis().items():
        if not info.get("tiktok") or perfil in ("fabricadeautomacoesia", "filmescomia00"):  # dona 24/10: não precisam
            continue
        for nome, v in (logins.get(perfil) or {}).items():
            if nome not in mr.MAQUINAS or not isinstance(v, dict) or not (v.get("youtube") or v.get("google")) \
                    or v.get("tiktok"):
                continue
            ult = (est.get(perfil) or {}).get(nome) or {}
            # código/verificação pendentes: confere de novo em 1 h (a dona já pode ter resolvido); o resto, em 6 h
            # 23/10: erro (Chrome fechou no meio, conexão) também volta em 1 h — era 6 h e a fila andava ~20 h
            espera = 3600 if ult.get("resultado") in ("codigo", "captcha") or str(ult.get("resultado", "")).startswith("erro") \
                else 6 * 3600
            if ult.get("resultado") in ("sem_conta",) or time.time() - ult.get("t", 0) < espera:
                continue  # sem conta: não insiste; tentou há < 6 h (código pendente etc.): espera
            out.append((perfil, nome))
    # contas SÓ de TikTok primeiro: sem o TikTok elas não servem pra postar nada nos notebooks
    so_tt = {p for p, i in mr._mapa_perfis().items() if i.get("tiktok") and not i.get("youtube")}
    return sorted(out, key=lambda x: x[0] not in so_tt)


SEM_APP_JS = r"""(() => {
  const ok = u => { const s = String(u || ''); return !/^[a-z][a-z0-9+.-]*:/i.test(s) || /^(https?|about|blob|data|javascript):/i.test(s); };
  const d = Object.getOwnPropertyDescriptor(HTMLIFrameElement.prototype, 'src');
  Object.defineProperty(HTMLIFrameElement.prototype, 'src', { configurable: true,
    get() { return d.get.call(this); }, set(v) { if (ok(v)) d.set.call(this, v); } });
  const sa = Element.prototype.setAttribute;
  Element.prototype.setAttribute = function (n, v) {
    if (this.tagName === 'IFRAME' && String(n).toLowerCase() === 'src' && !ok(v)) return;
    return sa.call(this, n, v);
  };
  const wo = window.open;
  window.open = function (u, ...r) { if (u && !ok(u)) return null; return wo.call(this, u, ...r); };
})();"""


def _sessao(ctx):
    return any(c["name"] == "sessionid" and c["value"] for c in ctx.cookies("https://www.tiktok.com"))


def _confirmar(ctx, pg, perfil, nome):
    """Dona 24/10: "você está contando como logado sem estar" — o cookie sessionid sozinho mentia (velho/inválido, ou o
    popup do Google fechou antes do fim). Logado de verdade = o próprio TikTok devolve a conta em /passport/web/
    account/info/ depois de abrir o feed. Devolve "@usuario" (ou "logado" se só a tela confirma) ou "" se não está."""
    try:  # 24/10: sem olhar o cookie antes — logo após abrir o Chrome ele ainda não aparece (aulacomia desmarcada em 17 s)
        pg.goto("https://www.tiktok.com/foryou", wait_until="domcontentloaded", timeout=90000)
        pg.wait_for_timeout(8000)
        if not _sessao(ctx):
            pg.wait_for_timeout(7000)
    except Exception:  # noqa: BLE001
        pass
    info = ""
    for _ in range(6):  # 24/10: o Acer (lento) ainda montava a página — repete até o TikTok responder de fato
        try:
            # 12/11 STI: com o popup do Google (one tap) na página, o fetch nunca voltava e a rodada ficava presa
            info = pg.evaluate("async () => { try { const c = new AbortController(); setTimeout(() => c.abort(), 20000); "
                               "const r = await fetch('/passport/web/account/info/?aid=1459', "
                               "{credentials: 'include', signal: c.signal}); return await r.text(); } "
                               "catch (e) { return 'ERRO ' + e; } }")
        except Exception as e:  # noqa: BLE001
            info = f"ERRO {e}"
        if info and not str(info).startswith("ERRO") and '"message"' in info:
            break
        time.sleep(8)
    _passo(pg, perfil, nome, "conferencia")
    m = re.search(r'"username"\s*:\s*"([^"]+)"', info or "")
    if m:
        return "@" + m.group(1)
    if info and not str(info).startswith("ERRO") and '"message"' in info:
        return ""  # o TikTok respondeu e não tem conta: sessão inválida
    return None  # sem resposta do TikTok: não sei — não desmarca nada


def _passo(pg, perfil, nome, etapa):
    """Dona 24/10: print a cada fim de ação — logs/tiktok_tela/<notebook>_<perfil>_<hh-mm-ss>_<etapa>.png."""
    pasta = mr.ROOT / "logs" / "tiktok_tela"
    pasta.mkdir(parents=True, exist_ok=True)
    arq = pasta / f"{nome}_{perfil}_{time.strftime('%H-%M-%S')}_{etapa}.png"
    try:
        pg.screenshot(path=str(arq), timeout=20000)
    except Exception:  # noqa: BLE001 — 24/10: no Acer o print da página estoura o tempo: tira o da tela inteira
        try:
            import base64
            png = base64.b64decode(mr.Remoto(nome)._ssh(TELA_CMD, timeout=40).stdout or b"")
            if png[:4] == b"\x89PNG":
                arq.write_bytes(png)
        except Exception:  # noqa: BLE001
            pass


def _ligar(perfil, nome):
    """Logou: põe o notebook na lista do TikTok das contas desse perfil e anota no netbooks_logins.
    24/10: antes de o Chrome fechar, 40 s pra ele gravar os cookies no disco (grava ~a cada 30 s): inovaremanhwaverseita
    logou 13:26, fechou 20 s depois e às 13:54 estava deslogada."""
    time.sleep(40)
    pol = mr._politica()
    arq = pol.CONFIG_DIR / "reuso_plataformas.json"
    dados = pol.ler_json(arq, {})
    for conta in (mr._mapa_perfis().get(perfil) or {}).get("tiktok", []):
        r = (dados.get("tiktok") or {}).get("contas", {}).get(conta)
        if r is not None:
            maqs = [m for m in mr._lista(r.get("maquina")) if m != nome] + [nome]
            r["maquina"], r["perfil_remoto"] = maqs, perfil
    pol.gravar_json(arq, dados)
    lg = mr._logins()
    lg.setdefault(perfil, {}).setdefault(nome, {})["tiktok"] = True
    pol.gravar_json(mr.LOGINS, lg)


def _avisar(texto):
    try:
        sys.path.insert(0, r"D:\video-fila")
        import avisos
        avisos.enviar(texto, "tiktok notebooks", importante=True)
    except Exception:  # noqa: BLE001
        print("aviso não saiu:", texto)


def _codigos_gmail(ctx):
    """([códigos de 6 dígitos dos e-mails do TikTok, o mais novo primeiro], assinatura). A assinatura é o texto da linha
    mais nova com código: muda quando chega e-mail novo MESMO com o mesmo código (24/10: o TikTok reenviou 959140 e o
    robô, que descartava código já visto, esperou à toa). Como o sightengine_contas._confirmar_email: se a lista não
    mostrar o código, abre o e-mail mais novo e lê o corpo."""
    g = ctx.new_page()
    try:
        g.goto("https://mail.google.com/mail/u/0/#search/from%3Atiktok+newer_than%3A1h",
               wait_until="domcontentloaded", timeout=90000)
        # 24/10: só as VISÍVEIS — o Gmail deixa as linhas da caixa de entrada escondidas na página enquanto a busca
        # carrega, e o texto delas vem vazio (o código 959140 estava lá e o robô leu "nada")
        linhas = g.locator("tr.zA:visible")
        try:  # 24/10: no Acer (lento) o Gmail leva >10 s pra montar a lista — com espera fixa lia a página vazia
            linhas.first.wait_for(timeout=60000)
        except Exception:  # noqa: BLE001
            pass
        textos = [linhas.nth(i).inner_text() for i in range(min(linhas.count(), 5))]
        busca_ok = bool(textos)
        if not busca_ok:  # 24/10: no Acer a BUSCA do Gmail fica girando; a caixa de entrada carrega — lê o TikTok de lá
            g.goto("https://mail.google.com/mail/u/0/#inbox", wait_until="domcontentloaded", timeout=90000)
            try:
                linhas.first.wait_for(timeout=60000)
            except Exception:  # noqa: BLE001
                pass
            textos = [t for t in (linhas.nth(i).inner_text() for i in range(min(linhas.count(), 8)))
                      if "tiktok" in t.lower()]
        com_cod = [t for t in textos if re.search(r"\b\d{6}\b", t)]
        cods = [m for t in com_cod for m in re.findall(r"\b\d{6}\b", t)]
        assinatura = com_cod[0] if com_cod else ""
        if not cods and busca_ok:  # abre o 1º só na busca (na caixa de entrada o 1º pode não ser do TikTok)
            assinatura = textos[0]
            linhas.first.click()
            g.wait_for_timeout(6000)
            cods = re.findall(r"\b\d{6}\b", " ".join(g.locator("div.a3s").all_inner_texts()))
        return cods, assinatura
    except Exception:  # noqa: BLE001
        return [], ""
    finally:
        g.close()


def _digitar_codigo(ctx, pg, antes):
    """Espera até 6 min o e-mail NOVO do código (assinatura diferente de `antes`) e digita no TikTok. True se digitou."""
    fim = time.time() + 360  # 24/10: no Acer cada leitura do Gmail leva ~2 min
    while time.time() < fim:
        time.sleep(10)
        if _sessao(ctx):
            return True
        novos, assinatura = _codigos_gmail(ctx)
        if novos and assinatura != antes:
            pg.bring_to_front()
            campo = pg.locator("input:visible").first
            campo.click()
            pg.keyboard.type(novos[0], delay=120)
            pg.wait_for_timeout(1500)
            for t in ("Verificar", "Avançar", "Next", "Confirmar", "Enviar"):
                b = pg.get_by_role("button", name=t)
                if b.count() and b.first.is_visible() and b.first.is_enabled():
                    b.first.click()
                    break
            return True
    return False


def _print(pg, perfil, nome):
    """23/10: "não logou" sem pista de onde parou — guarda a tela (logs/tiktok_nb_<perfil>_<notebook>.png)."""
    try:
        pg.screenshot(path=str(mr.ROOT / "logs" / f"tiktok_nb_{perfil}_{nome}.png"))
    except Exception:  # noqa: BLE001
        pass


TELA_CMD = ("export DISPLAY=:0; rm -f /tmp/tt_tela.png; gnome-screenshot -f /tmp/tt_tela.png 2>/dev/null || "
            "scrot -o /tmp/tt_tela.png 2>/dev/null || import -window root /tmp/tt_tela.png 2>/dev/null; "
            "base64 -w0 /tmp/tt_tela.png")


def _prints_tela(perfil, nome, parar):
    """Dona 24/10: "a cada conta que você coloca lá, prints pra acompanhar se está sendo feito" — print da TELA do
    notebook a cada minuto enquanto o login roda: logs/tiktok_tela/<notebook>_<perfil>_<hh-mm-ss>.png (+ <notebook>.png
    = o último)."""
    import base64
    pasta = mr.ROOT / "logs" / "tiktok_tela"
    pasta.mkdir(parents=True, exist_ok=True)
    r = mr.Remoto(nome)
    while not parar.wait(20 if not any(pasta.glob(f"{nome}_{perfil}_*")) else 60):
        try:
            png = base64.b64decode(r._ssh(TELA_CMD, timeout=40).stdout or b"")
            if png[:4] == b"\x89PNG":
                (pasta / f"{nome}_{perfil}_{time.strftime('%H-%M-%S')}.png").write_bytes(png)
                (pasta / f"{nome}.png").write_bytes(png)
        except Exception:  # noqa: BLE001
            pass
    for velho in sorted(pasta.glob("*_*_*.png"), key=lambda p: p.stat().st_mtime)[:-200]:
        velho.unlink(missing_ok=True)


def logar(perfil, nome, porta=None):
    """porta: Chrome EXTRA (9461–9479) pro login em lote (tiktok_lote.py); sem ela, a porta normal da máquina."""
    import threading
    parar = threading.Event()
    if not porta:  # print da tela a cada tanto: só no modo uma-por-vez (no lote seriam vários ao mesmo tempo)
        threading.Thread(target=_prints_tela, args=(perfil, nome, parar), daemon=True).start()
    try:
        return _logar(perfil, nome, porta)
    finally:
        parar.set()


def _logar(perfil, nome, porta_extra=None):
    from playwright.sync_api import sync_playwright
    email = (mr._mapa_perfis().get(perfil) or {}).get("email") or f"{perfil}@gmail.com"
    r = mr.Remoto(nome)
    if porta_extra:
        r.porta = porta_extra
    deixar_aberto = False
    try:
        # URL de login = janela NA TELA e o painel do telão sai da frente (chrome_conta marca login)
        r.ceder_veo()
        porta = r.abrir(perfil, "https://www.tiktok.com/login", sem_espera=True)
        with sync_playwright() as p:
            br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
            ctx = br.contexts[0]
            pg0 = next((x for x in ctx.pages if "tiktok.com" in x.url), None) or ctx.new_page()
            ja = _confirmar(ctx, pg0, perfil, nome)
            if ja:
                _ligar(perfil, nome)
                return f"logado {ja}"
            # "Abrir xdg-open?" (o TikTok cria um iframe bytedance:// pra abrir o app) travava a página até alguém clicar
            # Cancelar; o bloqueio pelas preferências do Chrome não pegou nesta versão. Antes de carregar: link que não
            # é http/https não sai da página.
            ctx.add_init_script(SEM_APP_JS)
            pg = next((x for x in ctx.pages if "tiktok.com" in x.url), None) or ctx.new_page()
            # 23/10 (dona: "o script do TikTok nunca vai fazer nos notebooks porque a tela é pequena: tem que rolar pra
            # aparecer a opção de login com Google"). O zoom por CSS (document...style.zoom) mostrava o botão mas
            # DESALINHAVA o clique (print 22:00 rezaulkarimul355: botão focado, nada abriu). Agora a página é emulada
            # num tamanho de tela maior (o clique bate certo) e, se ainda faltar, rola com a roda do mouse até ele.
            pg.set_viewport_size({"width": 1280, "height": 1000})
            pg.goto("https://www.tiktok.com/login", timeout=120000)
            pg.bring_to_front()
            pg.wait_for_timeout(5000)
            _passo(pg, perfil, nome, "1_login")
            botao =pg.get_by_text(re.compile(r"(Continu\w+ com (o )?Google|Continue with Google)", re.I)).first
            try:  # 26/10 PC2 com 10 Chrome: o botão do Google ficou só com o ícone girando por >30 s (print 14:00)
                botao.wait_for(state="attached", timeout=90000)
            except Exception:  # noqa: BLE001
                pass
            for _ in range(12):
                try:
                    if botao.is_visible() and botao.bounding_box() and botao.bounding_box()["y"] < 900:
                        break
                except Exception:  # noqa: BLE001
                    pass
                pg.mouse.move(640, 500)
                pg.mouse.wheel(0, 300)
                pg.wait_for_timeout(700)
            botao.scroll_into_view_if_needed(timeout=30000)
            with ctx.expect_page(timeout=40000) as nova:
                botao.click()
            pop = nova.value
            pop.wait_for_load_state("domcontentloaded")
            _passo(pop, perfil, nome, "2_google")
            try:  # o popup do Google também cabe inteiro (botões "Continuar" no fim da página)
                pop.set_viewport_size({"width": 1000, "height": 900})
            except Exception:  # noqa: BLE001
                pass
            try:  # escolha da conta no popup do Google (o perfil só tem essa)
                conta = pop.locator(f'[data-identifier="{email.lower()}"], [data-email="{email.lower()}"]')
                try:
                    conta.first.wait_for(timeout=10000)
                except Exception:  # noqa: BLE001 — 24/10: tela nova do Google sem data-identifier: clica na linha
                    conta = pop.get_by_role("link", name=re.compile(re.escape(email), re.I))
                    try:
                        conta.first.wait_for(timeout=10000)
                    except Exception:  # noqa: BLE001
                        conta = pop.get_by_text(email.lower(), exact=True)
                        conta.first.wait_for(timeout=10000)
                conta.first.click()
                pop.wait_for_timeout(2000)
                _passo(pop, perfil, nome, "3_conta")
            except Exception:  # noqa: BLE001
                pass
            fim, sess_t = time.time() + 90, 0.0
            while time.time() < fim:
                # o cookie aparece antes de o TikTok terminar (às vezes ainda pede verificação): espera o popup fechar ou
                # 8 s com o cookie, e só então confere de verdade
                if _sessao(ctx):
                    sess_t = sess_t or time.time()
                    if pop.is_closed() or time.time() - sess_t > 8:
                        break
                # 23/10: no X200MA o Google pede "Confirm you're not a robot" (verificação de robô) — quem resolve é a
                # dona. A janela fica NA TELA e ela é avisada (antes esperava 90 s e desistia como "nao_logou").
                try:
                    if not pop.is_closed() and ("challenge/recaptcha" in pop.url or
                                                re.search(r"not a robot|não sou um robô|nao sou um robo",
                                                          pop.inner_text("body", timeout=3000), re.I)):
                        pop.bring_to_front()
                        deixar_aberto = True
                        return "captcha"
                except Exception:  # noqa: BLE001
                    pass
                if not pop.is_closed():
                    try:  # 26/10 PC2 lento: o 1º clique na conta não pegou e o popup ficou parado em "Choose an account"
                        if re.search(r"choose an account|escolha uma conta|escolher uma conta",
                                     pop.inner_text("body", timeout=3000), re.I):
                            # o texto do e-mail não é o que recebe o clique (print 14:45 jornalcomia): a LINHA é
                            linha = pop.get_by_role("link", name=re.compile(re.escape(email), re.I))
                            alvo = linha if linha.count() else pop.get_by_text(email.lower(), exact=True)
                            if alvo.count() and alvo.first.is_visible():
                                alvo.first.click(timeout=5000)
                                pop.wait_for_timeout(1500)
                                if not pop.is_closed() and alvo.count() and alvo.first.is_visible():
                                    alvo.first.focus()
                                    pop.keyboard.press("Enter")
                    except Exception:  # noqa: BLE001
                        pass
                    for t in ("Continuar", "Continue", "Permitir", "Allow"):
                        try:
                            b = pop.get_by_role("button", name=t)
                            if b.count() and b.first.is_visible():
                                b.first.click()
                                break
                        except Exception:  # noqa: BLE001
                            pass
                try:
                    txt = pg.inner_text("body", timeout=3000).lower()
                except Exception:  # noqa: BLE001
                    txt = ""
                if "nascimento" in txt or "birthday" in txt:
                    return "sem_conta"  # o Google abriria cadastro novo: não cria nada
                # "código" sozinho não: a própria página de login tem "código QR"
                if re.search(r"verifi(que se é|ca que és)|verify it'?s you|verifique sua identidade|verification code", txt):
                    _passo(pg, perfil, nome, "4_pediu_codigo")
                    antes = _codigos_gmail(ctx)[1]
                    try:  # escolhe E-mail e pede o código
                        pg.get_by_text(re.compile(r"^\s*E-?mail\s*$", re.I)).first.click(timeout=8000)
                        pg.wait_for_timeout(3000)
                        for t in ("Enviar código", "Enviar", "Send code"):
                            b = pg.get_by_role("button", name=t)
                            if b.count() and b.first.is_visible() and b.first.is_enabled():
                                b.first.click()
                                break
                    except Exception:  # noqa: BLE001
                        pass
                    # 24/10 (dona: "antes ele pegava o código do e-mail sozinho"): lê no Gmail do mesmo perfil e digita
                    if _digitar_codigo(ctx, pg, antes):
                        _passo(pg, perfil, nome, "5_codigo_digitado")
                        fim2 = time.time() + 40
                        while time.time() < fim2 and not _sessao(ctx):
                            time.sleep(2)
                        time.sleep(5)
                        ok = _confirmar(ctx, pg, perfil, nome)
                        if ok:
                            _ligar(perfil, nome)
                            return f"logado {ok}"
                        pg.goto("https://www.tiktok.com/login", timeout=120000)
                    gm = ctx.new_page()
                    gm.goto("https://mail.google.com/mail/u/0/#inbox", timeout=120000)
                    pg.bring_to_front()
                    deixar_aberto = True
                    return "codigo"
                time.sleep(2)
            ok = _confirmar(ctx, pg, perfil, nome)
            if ok:
                _ligar(perfil, nome)
                return f"logado {ok}"
            _print(pg, perfil, nome)
            _passo(pg, perfil, nome, "6_nao_logou")
            return "nao_logou"
    finally:
        if deixar_aberto:  # a dona digita o código; a janela de login se fecha sozinha depois de 45 min
            r.aberto = False
            if r.tunel:
                r.tunel.terminate()
        else:
            r.fechar()


def _desligar(perfil, nome):
    """Contrário do _ligar: o TikTok dessa conta NÃO está logado naquele notebook."""
    pol = mr._politica()
    arq = pol.CONFIG_DIR / "reuso_plataformas.json"
    dados = pol.ler_json(arq, {})
    for conta in (mr._mapa_perfis().get(perfil) or {}).get("tiktok", []):
        r = (dados.get("tiktok") or {}).get("contas", {}).get(conta)
        if r is not None:
            r["maquina"] = [m for m in mr._lista(r.get("maquina")) if m != nome]
    pol.gravar_json(arq, dados)
    lg = mr._logins()
    lg.setdefault(perfil, {}).setdefault(nome, {})["tiktok"] = False
    pol.gravar_json(mr.LOGINS, lg)


def _conferir_um(perfil, nome):
    from playwright.sync_api import sync_playwright
    r = mr.Remoto(nome)
    try:
        porta = r.abrir(perfil, "https://www.tiktok.com/foryou", sem_espera=True)
        with sync_playwright() as p:
            ctx = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}").contexts[0]
            pg = next((x for x in ctx.pages if "tiktok.com" in x.url), None) or ctx.new_page()
            return _confirmar(ctx, pg, perfil, nome)
    finally:
        r.fechar()


def conferir(nome):
    """Dona 24/10: confere de verdade cada conta marcada com TikTok no notebook; a que não está logada volta pra fila."""
    for perfil, maqs in sorted(mr._logins().items()):
        v = (maqs or {}).get(nome)
        if not isinstance(v, dict) or not v.get("tiktok"):
            continue
        for _ in range(30):  # espera a vez (login/Veo/telão) até ~15 min
            if Remoto_livre(nome):
                break
            time.sleep(30)
        else:
            mr.log(f"conferir tiktok: {nome} ocupado, parei")
            return
        vez = f"conferir tiktok {perfil}"
        mr.ocupar(nome, vez, 10)
        try:
            ok = _conferir_um(perfil, nome)
        except Exception as e:  # noqa: BLE001
            ok = None
            mr.log(f"conferir tiktok {perfil} no {nome}: erro {type(e).__name__}: {str(e)[:80]}")
        finally:
            mr.liberar(nome, quem=vez)
        if ok == "":
            _desligar(perfil, nome)
            est = _ler()
            est.setdefault(perfil, {})[nome] = {"resultado": "conferido_sem_login", "t": 0}
            ESTADO.write_text(json.dumps(est, ensure_ascii=False, indent=2), encoding="utf-8")
        mr.log(f"conferir tiktok {perfil} no {nome}: "
               f"{'sem resposta do TikTok (fica como está)' if ok is None else ok or 'NÃO está logado (volta pra fila)'}")


def main(a):
    if "--conferir" in a:  # python bin\netbooks\tiktok_notebooks.py --conferir [x200ma|acer]
        import threading
        alvos = [n for n in ("x200ma", "acer") if n in a] or ["x200ma", "acer"]
        ts = [threading.Thread(target=conferir, args=(n,)) for n in alvos]
        for t in ts:
            t.start()
        for t in ts:
            t.join()
        return
    # dona 23/10: "loga os Google primeiro, depois os TikTok de uma vez" — com este arquivo o vigia não roda o lote
    if (mr.ROOT / "config" / "tiktok_notebooks_PAUSA").exists() and "--fila" not in a and "--agora" not in a:
        return
    if "--fila" in a:
        for perfil, nome in fila():
            print(f"{perfil} no {nome}")
        return
    # 23/10 (dona: "que ande com todas"): várias contas por rodada, enquanto houver notebook livre, até 17 min (o vigia
    # chama a cada 20); notebook com 2 erros seguidos sai da rodada. Antes era 1 conta por rodada (~20 h pra fila).
    est, fim, erros, feitos = _ler(), time.time() + 17 * 60, {}, set()
    so = [n for n in mr.MAQUINAS if n in a]  # 24/10: "--agora x200ma" = só esse notebook (uma rodada por notebook)
    for perfil, nome in fila():
        if time.time() > fim:
            break
        if so and nome not in so:
            continue
        if erros.get(nome, 0) >= 2 or (perfil, nome) in feitos or not Remoto_livre(nome):
            continue
        feitos.add((perfil, nome))
        vez = f"login tiktok {perfil}"
        mr.ocupar(nome, vez, 15)  # 23/10: pega a vez da máquina — telão e Veo esperam (motivo "login")
        try:
            res = logar(perfil, nome)
        except Exception as e:  # noqa: BLE001
            res = f"erro: {type(e).__name__}: {str(e)[:100]}"
        # 24/10 tarde: o robô já lê o código no Gmail; se não conseguiu, segurar 45 min esperando a dona (indisponível)
        # travava o Acer — fecha sempre e tenta de novo em 1 h
        if res in ("codigo", "captcha"):
            # 24/10 madrugada: a dona dorme — segurar 45 min travava o notebook à toa. Fecha, segue pra próxima conta
            # e só tenta de novo (6 h depois) quando ela estiver acordada pra digitar o código
            r = mr.Remoto(nome)
            try:
                r._ssh(f"{r.run} fechar 0; {r.run} fechar {r.porta}", timeout=60)
            except Exception:  # noqa: BLE001
                pass
            mr.liberar(nome, quem=vez)
            res += "_noite"
        elif res in ("codigo", "captcha"):
            mr.ocupar(nome, vez, 45)  # a janela fica na tela pra dona: segura a vez enquanto ela resolve
        else:
            mr.liberar(nome, quem=vez)
        erros[nome] = erros.get(nome, 0) + 1 if res.startswith("erro") else 0
        est = _ler()
        est.setdefault(perfil, {})[nome] = {"resultado": res, "t": time.time()}
        ESTADO.write_text(json.dumps(est, ensure_ascii=False, indent=2), encoding="utf-8")
        mr.log(f"tiktok {perfil} no {nome}: {res}")
        if res == "codigo":
            _avisar(f"TikTok da conta {perfil} no {nome.upper()} pediu o CÓDIGO do e-mail. A janela está aberta na tela "
                    f"do {nome} com o Gmail ao lado: pegue o código e confirme.")
        elif res == "captcha":
            _avisar(f"TikTok da conta {perfil} no {nome.upper()}: o Google pediu a verificação 'não sou um robô'. A "
                    f"janela está aberta na tela do {nome}: resolva a verificação e o login continua.")
        elif res == "sem_conta":
            _avisar(f"TikTok: o Google de {perfil} abriria uma conta NOVA no TikTok (não criei nada). Confira qual "
                    "e-mail é dono do TikTok dessa conta.")
        # (23/10: não para mais na 1ª conta — segue enquanto houver notebook livre)


def _reservado(nome):
    """23/10: o Veo reserva os notebooks do Flow quando o PC1 está sem memória (D:\\veo\\beta\\cron_gerar_video_llm
    ._reservar_notebooks): enquanto valer, o login do TikTok não pega esse notebook (o Veo parou 3 h por isso)."""
    try:
        r = json.loads((mr.ROOT / "config" / "notebooks_reservados.json").read_text(encoding="utf-8")).get(nome) or {}
        return float(r.get("ate", 0)) > time.time()
    except (OSError, ValueError, TypeError):
        return False


def Remoto_livre(nome):  # noqa: N802
    """Livre = sem a vez de outro (Veo, login...), sem Chrome aberto do chrome_conta e sem vídeo tocando no telão
    (dona 23/10: "o TikTok tem que ser como as outras coisas: entra na fila e faz quando não estiver logando outras
    contas, exibindo vídeos ou fazendo Veo")."""
    if _reservado(nome) or mr.reservado(nome):
        return False
    r = mr.Remoto(nome)
    try:
        if not r.win:  # telão tocando (~/vitrine/TOCANDO, marca do player; velha de 15 min não vale)
            t = r._txt(r._ssh("f=~/vitrine/TOCANDO; [ -f $f ] && [ $(( $(date +%s) - $(stat -c %Y $f) )) -lt 900 ] "
                              "&& echo TOCANDO || echo LIVRE", timeout=25))
            if "TOCANDO" in t:
                return False
        s = r._txt(r._ssh(f"{r.run} estado", timeout=25)).strip().splitlines()[-1]
        return not json.loads(s).get("aberto")
    except Exception:  # noqa: BLE001
        return False


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main(sys.argv[1:])
