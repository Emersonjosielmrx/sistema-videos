#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Geracao 100% automatica no Flow: escreve prompt, submete, aprova se pedir
(clique robusto compativel com React), espera poster novo e baixa o mp4.
Uso: python gera_auto.py "prompt aqui" caminho/saida.mp4"""
import sys, os, re, time, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright
from filelock import FileLock, Timeout as FileLockTimeout
import config, flow_bot
from contas import PROFILE_MAP  # fonte unica das contas — edite contas.py

PORT = int(os.environ.get("FLOW_PORT", "9250"))

# Proxy rotativo (Webshare) — muda o IP visto pelo Google Flow.
# Formato: user:pass@host:port  (ex: "abc123:xyz@45.39.15.202:6632")
_FLOW_PROXY_RAW = os.environ.get("FLOW_PROXY", "").strip()
_FLOW_PROXY_HOST = ""   # host:port pro --proxy-server
_FLOW_PROXY_USER = ""
_FLOW_PROXY_PASS = ""
if _FLOW_PROXY_RAW and "@" in _FLOW_PROXY_RAW:
    _cred, _hp = _FLOW_PROXY_RAW.rsplit("@", 1)
    _FLOW_PROXY_HOST = _hp
    if ":" in _cred:
        _FLOW_PROXY_USER, _FLOW_PROXY_PASS = _cred.split(":", 1)
elif _FLOW_PROXY_RAW:
    _FLOW_PROXY_HOST = _FLOW_PROXY_RAW
_FLOW_HOME = "https://labs.google/fx/pt/tools/flow"

# Projeto POR CONTA. Cada conta do Flow tem o SEU projeto — usar a URL de
# outra conta cai em "Algo deu errado" e trava a automacao. Guardamos o
# project-url de cada sessao num json e resolvemos por FLOW_SESSION.
_PROJ_MAP_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "logs", "flow_projetos.json")


def _load_proj_map():
    import json
    try:
        with open(_PROJ_MAP_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_proj_url(session, url):
    """Salva o project-url descoberto pra essa sessao (reuso na proxima)."""
    import json
    if not session or "/project/" not in (url or ""):
        return
    try:
        m = _load_proj_map()
        if m.get(session) != url:
            m[session] = url
            os.makedirs(os.path.dirname(_PROJ_MAP_FILE), exist_ok=True)
            with open(_PROJ_MAP_FILE, "w", encoding="utf-8") as f:
                json.dump(m, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _proj_inicial():
    """URL de entrada: FLOW_PROJ se apontar para um projeto, senao o projeto salvo da sessao, senao FLOW_PROJ/HOME.
    NUNCA usa um project-id fixo hardcoded (era da conta seebotsia e quebrava
    todas as outras contas). O ms-energy exporta FLOW_PROJ = pagina inicial do Flow; ela nao pode passar na frente
    do projeto salvo da conta."""
    env = os.environ.get("FLOW_PROJ", "")
    if "/project/" in env:
        return env
    salvo = _load_proj_map().get(os.environ.get("FLOW_SESSION", ""))
    return salvo or env or _FLOW_HOME


PROJ = _proj_inicial()

# ---------------------------------------------------------------------------
# DETECCAO DE CREDITOS ESGOTADOS  ->  ver creditos.py
# ---------------------------------------------------------------------------
# A logica foi extraida pra creditos.py (mais facil de achar/ajustar).
# Importamos com os nomes antigos (_prefixo) pra nao mudar os call sites.
from creditos import (
    CreditosEsgotadosError,
    creditos_esgotados as _creditos_esgotados,
    fechar_menu_conta as _fechar_menu_conta,
    ler_saldo_creditos as _ler_saldo_creditos,
    salvar_evidencia as _salvar_evidencia_creditos_esgotados,
)


# Midias do projeto (UI de 12/10/2026, flow.google.com): o bloco da grade e um <img> com src
# https://flow.google.com/asb/<token> ou https://flow-content.google/image/<uuid>. Passando o mouse por cima, o Flow
# carrega o <video src=".../asb/<token>=mm,...">, que baixa direto (video/mp4) com os cookies da sessao. O endereco
# antigo (labs.google/fx/api/trpc/media.getMediaUrlRedirect?name=) responde 401 desde a troca de dominio.
_RE_MIDIA = re.compile(r"/asb/([A-Za-z0-9_-]{20,})|flow-content\.google/(?:image|video)/([0-9a-f-]{36})"
                       r"|getMediaUrlRedirect\?name=([0-9a-f-]{20,})")


def _chave_midia(src):
    m = _RE_MIDIA.search(src or "")
    return next((g for g in m.groups() if g), None) if m else None


def midias(page):
    """{chave: {tag, src, x, y, w, h}} das miniaturas da grade (img >= 80 px) e dos <video> da pagina."""
    try:
        itens = page.evaluate("""() => [...document.querySelectorAll('img, video')].map(e => {
            const r = e.getBoundingClientRect();
            return {tag: e.tagName, src: e.currentSrc || e.src || '', x: r.x, y: r.y, w: r.width, h: r.height}; })""")
    except Exception:
        return {}
    out = {}
    for it in itens:
        if it["tag"] == "IMG" and (it["w"] < 80 or it["h"] < 80):
            continue
        k = _chave_midia(it["src"])
        if k and (k not in out or it["tag"] == "VIDEO"):
            out[k] = it
    return out


def _video_do_bloco(page, it, log=print):
    """Endereco do mp4 de um bloco da grade: passa o mouse para o Flow carregar o <video>. None se nao e video."""
    if it["tag"] == "VIDEO":
        return it["src"]
    try:
        page.mouse.move(it["x"] + it["w"] / 2, it["y"] + it["h"] / 2)
        page.wait_for_timeout(2500)
    except Exception:
        log(f"  [video_do_bloco] falha ao mover mouse para bloco {it['src'][:40]}...")
        return None
    v = midias(page).get(_chave_midia(it["src"]))
    if v and v["tag"] == "VIDEO":
        return v["src"]
    if "/asb/" in it["src"]:  # mesmo endereco do poster com o sufixo de video que o Flow usa no <video>
        url_tentativa = it["src"].split("=")[0] + "=mm,22,15"
        log(f"  [video_do_bloco] IMG /asb/ nao virou VIDEO, tentando URL construida: {url_tentativa[:60]}...")
        return url_tentativa
    log(f"  [video_do_bloco] IMG sem /asb/, nao e video: {it['src'][:60]}...")
    return None


def _baixar_url(page, url, out_path, log=print):
    """Baixa o mp4 com os cookies da sessao. True so se veio video de verdade (> 500 KB)."""
    try:
        resp = page.request.get(url, timeout=120000)
        tipo = resp.headers.get("content-type", "")
        body = resp.body()
    except Exception as e:
        log(f"  download falhou: {type(e).__name__}: {str(e)[:80]}")
        return False
    if not resp.ok or "video" not in tipo or len(body) < 500_000:
        log(f"  download: status={resp.status} tipo={tipo or '?'} {len(body)//1024}KB — nao e o video")
        return False
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(body)
    log(f"OK video salvo: {out_path} ({len(body)//1024}KB)")
    return True


def _click_texto(page, texto, log=print):
    """Clica no elemento cujo texto bate, usando mouse REAL do Playwright
    (mais confiavel que .click() JS no React). Retorna True se clicou."""
    try:
        loc = page.locator(f"text={texto}").last
        loc.scroll_into_view_if_needed(timeout=3000)
        loc.click(force=True, timeout=5000)
        return True
    except Exception as e:
        log(f"  [click '{texto}'] falhou: {type(e).__name__}")
        return False


# Botoes da UI de 12/10/2026 (aria-label PT/EN; o texto do icone material vale nas duas linguas)
_BTN_AJUSTES = "button[aria-label='Configurações'], button[aria-label='Settings'], button:has-text('tune')"
_BTN_NOVA_SESSAO = ("button[aria-label='Iniciar nova sessão'], button[aria-label='Start new session'], "
                    "button:has-text('edit_square')")
_BTN_ABRIR_CONVERSA = "button[aria-label='Abrir'], button[aria-label='Open'], button:has-text('expand_content')"
_RE_MODELO = re.compile(r"^\s*(Veo \d|Omni )")
# Cartao "Quer que eu inicie essa geracao, que custa N creditos?" (so aparece se 'Confirmar antes de gerar' = Sempre)
_ROTULOS_APROVAR = ("Sempre aprovar", "Always approve", "Aprovar e não perguntar de novo", "Aprovar", "Approve")
_SEL_APROVAR = ", ".join(f"[aria-label='{r}']" for r in _ROTULOS_APROVAR)


def _abrir_conversa(page, log=print):
    """O painel da conversa com o agente (a direita) pode estar fechado. True se o botao de nova sessao aparece."""
    nova = page.locator(_BTN_NOVA_SESSAO)
    if nova.count() and nova.first.is_visible():
        return True
    abrir = page.locator(_BTN_ABRIR_CONVERSA).first
    try:
        if abrir.count() and abrir.is_visible():
            abrir.click(timeout=5000)
            page.wait_for_timeout(2500)
    except Exception as e:
        log(f"[sessao] nao abri a conversa: {type(e).__name__}")
    return nova.count() > 0 and nova.first.is_visible()


def nova_sessao(page, log=print):
    """Conversa nova com o agente, sem o contexto dos pedidos anteriores."""
    if not _abrir_conversa(page, log):
        log("[sessao] AVISO: botao de nova sessao nao apareceu — continuando na conversa atual")
        return False
    try:
        page.locator(_BTN_NOVA_SESSAO).first.click(timeout=5000)
        page.wait_for_timeout(2500)
        log("[sessao] nova sessao criada")
        return True
    except Exception as e:
        log(f"[sessao] AVISO: nova sessao falhou ({type(e).__name__}) — continuando na conversa atual")
        return False


def garantir_modo_veo(page, aspect="9:16", modelo="Veo 3.1 - Fast", log=print):
    """Painel 'Configurações do agente' (botao tune ao lado do enviar): video na proporcao pedida, 1 resultado (x1),
    o modelo pedido e 'Confirmar antes de gerar' = Nunca; salva (fica gravado na conta). Sem isso o agente usa o padrao
    da conta (12/10/2026: Veo 3.1 - Lite, 16:9) e para pedindo aprovacao. True se o modelo ficou confirmado na tela."""
    ratio = {"PORTRAIT": "9:16", "LANDSCAPE": "16:9"}.get(aspect.upper(), aspect)
    try:
        page.locator(_BTN_AJUSTES).last.click(timeout=8000)
        page.wait_for_timeout(1500)
        dd = page.get_by_text(_RE_MODELO).last
        dd.wait_for(state="visible", timeout=8000)
        # o bloco de VIDEO e o ultimo do painel: proporcao e quantidade vem antes do seletor de modelo
        for rotulo in (ratio, "x1"):
            try:
                dd.locator(f"xpath=preceding::*[normalize-space(.)='{rotulo}'][1]").click(timeout=4000, force=True)
            except Exception as e:
                log(f"[veo] AVISO: nao cliquei '{rotulo}' no painel ({type(e).__name__})")
        try:
            page.locator("mat-radio-button, [role=radio]").filter(
                has_text=re.compile(r"^\s*(Nunca|Never)")).first.click(timeout=4000)
        except Exception as e:
            log(f"[veo] AVISO: nao marquei 'Confirmar antes de gerar: Nunca' ({type(e).__name__})")
        atual = (dd.inner_text() or "").strip()
        if modelo not in atual:
            dd.click(timeout=5000)
            page.wait_for_timeout(1000)
            page.locator("[role=menuitem], [role=option], mat-option").filter(has_text=modelo).first.click(timeout=5000)
            page.wait_for_timeout(800)
            atual = (page.get_by_text(_RE_MODELO).last.inner_text() or "").strip()
        page.locator("button").filter(has_text=re.compile(r"^\s*(Salvar|Save)\s*$")).last.click(timeout=5000)
        page.wait_for_timeout(1500)
        atual = atual.replace("arrow_drop_down", "").strip()
        ok = modelo in atual
        log(f"[veo] ajustes do agente: video {ratio}, x1, modelo '{atual}'" + ("" if ok else f" (AVISO: pedi '{modelo}')"))
        return ok
    except Exception as e:
        log(f"[veo] AVISO: painel de ajustes falhou ({type(e).__name__}: {str(e)[:80]}) — o prompt ainda pede o modelo")
        try:
            page.keyboard.press("Escape")
        except Exception:
            pass
        return False


def _aprovar_se_pedir(page, ja_vistos, log=print):
    """Clica 'Sempre aprovar' (ou 'Aprovar') num cartao de aprovacao NOVO. Devolve quantos cartoes ja foram vistos."""
    try:
        n = page.locator(_SEL_APROVAR).count()
    except Exception:
        return ja_vistos
    if n <= ja_vistos:
        return ja_vistos
    for rotulo in _ROTULOS_APROVAR:
        loc = page.locator(f"[aria-label='{rotulo}']")
        try:
            if loc.count() and loc.last.is_visible():
                loc.last.click(timeout=5000)
                log(f"[aprovacao] cliquei '{rotulo}'")
                page.wait_for_timeout(1500)
                break
        except Exception as e:
            log(f"[aprovacao] clique em '{rotulo}' falhou: {type(e).__name__}")
    try:
        return page.locator(_SEL_APROVAR).count()
    except Exception:
        return n

_RE_ENVIAR_MIDIA = re.compile(r"(Enviar m[ií]dia|Upload media|Upload file|Fazer upload)", re.I)
_JS_CAIXA = "document.querySelector('[data-slate-editor], textarea, [contenteditable=\"true\"]')"


def _subir_imagem(page, image_path, log=print, caminho_no_chrome=None):
    """image-to-video (UI de 12/10/2026): o '+' da caixa de comando abre o navegador de midias; 'Enviar midia' abre o
    seletor de arquivo; a imagem entra na lista com o nome do arquivo; CLICAR nela a anexa a caixa de comando
    (miniatura acima do texto) e fecha o popover. Retorna True se a miniatura apareceu."""
    if not image_path or not os.path.exists(image_path):
        log(f"[img] arquivo nao existe: {image_path}")
        return False
    # caminho_no_chrome: caminho JA no disco de outra maquina (arquivo grande mandado por maquina_remota.enviar). Foto
    # pequena nao precisa: com connect_over_cdp o Playwright transfere o arquivo pela conexao.
    nome = os.path.splitext(os.path.basename(caminho_no_chrome or image_path))[0][:24]
    # o '+' certo e o mais perto da caixa de comando (o '+' do topo abre o menu de arquivos do projeto)
    pos = page.evaluate("""() => {
        const caixa = """ + _JS_CAIXA + """;
        if (!caixa) return null;
        const c = caixa.getBoundingClientRect();
        let best = null, bd = Infinity;
        for (const b of document.querySelectorAll('button')) {
            const t = (b.innerText || '').trim();
            if (t !== 'add' && t !== 'add_2') continue;
            const r = b.getBoundingClientRect();
            if (!r.width) continue;
            const d = Math.hypot(r.x + r.width / 2 - (c.x + c.width / 2), r.y + r.height / 2 - (c.y + c.height / 2));
            if (d < bd) { bd = d; best = {x: r.x + r.width / 2, y: r.y + r.height / 2}; }
        }
        return best; }""")
    if not pos:
        log("[img] FALHA: nao achei o '+' da caixa de comando")
        return False
    page.mouse.click(pos["x"], pos["y"])
    page.wait_for_timeout(2000)
    try:
        with page.expect_file_chooser(timeout=10000) as fc:
            page.locator("button, [role=button], [role=menuitem]").filter(
                has_text=_RE_ENVIAR_MIDIA).last.click(timeout=5000)
        fc.value.set_files(caminho_no_chrome or image_path)
        log("[img] arquivo enviado pelo seletor de arquivo")
    except Exception as e:
        log(f"[img] envio falhou ({type(e).__name__}): {str(e)[:80]}")
        page.keyboard.press("Escape")
        return False
    page.wait_for_timeout(2000)
    try:  # aviso de direitos autorais (1a vez em algumas contas)
        concordo = page.locator("button").filter(has_text=re.compile(r"^\s*(Concordo|I agree|Aceito)\s*$", re.I))
        if concordo.count() and concordo.first.is_visible():
            concordo.first.click(timeout=4000)
            log("[img] aviso 'Concordo' aceito")
    except Exception:
        pass
    item = page.locator("flow-add-menu-popover-content *, .cdk-overlay-pane *").filter(has_text=nome)
    for _ in range(40):
        if item.count() and item.last.is_visible():
            break
        page.wait_for_timeout(1500)
    else:
        log(f"[img] AVISO: '{nome}' nao apareceu na lista de midias")
        page.keyboard.press("Escape")
        return False
    page.wait_for_timeout(2000)
    item.last.click(timeout=5000)
    page.wait_for_timeout(2500)
    anexada = page.evaluate("""() => {
        const caixa = """ + _JS_CAIXA + """;
        if (!caixa) return false;
        const c = caixa.getBoundingClientRect();
        return [...document.querySelectorAll('img')].some(i => { const r = i.getBoundingClientRect();
            return r.width >= 20 && r.width <= 120 && r.y < c.y && r.y > c.y - 160 && r.x > c.x - 60 && r.x < c.x + c.width; });
    }""")
    log("[img] imagem anexada a caixa de comando" if anexada else "[img] AVISO: nao vi a miniatura anexada")
    return bool(anexada)


def _texto_caixa(page):
    try:
        return page.evaluate("() => { const e = " + _JS_CAIXA + "; return e ? (e.value || e.innerText || '') : ''; }") or ""
    except Exception:
        return ""


def _passar_boas_vindas(page, log=print):
    """Conta nova no Flow (23/10, mentoriaiapro no acer): janela 'Conheca e molde ferramentas de IA...' com
    'Sair'/'Avancar' cobre a home e o 'Novo projeto' nao abre. Avanca (sem marcar os e-mails de marketing) ate sumir."""
    # 1a versao (clique por JS) ficou repetindo 'Continuar' 5x e a janela voltava: botao desabilitado ate aceitar
    # os termos / rolar o texto. Agora: clique real do Playwright, marca SO caixa de termos (nunca e-mail de
    # marketing/pesquisa), rola o texto e grava cada passo no log pra conferir.
    sel = "[role=dialog], [role=alertdialog], dialog[open]"
    ok = re.compile(r"^\s*(Avançar|Next|Continuar|Continue|Aceitar|Accept|Concordo|I agree|Aceito|Concluir|Done|"
                    r"Começar|Get started|Entendi|Got it|Vamos lá|Let's go|Comece a criar|Start creating)\s*$", re.I)
    ultimo = None
    for _ in range(10):
        dlg = page.locator(sel).last
        try:
            if not dlg.count() or not dlg.is_visible():
                return
            texto = " ".join((dlg.inner_text(timeout=3000) or "").split())
        except Exception:
            return
        if ultimo is None and not re.search(r"Conheça e molde|Experimente e molde|um (lugar|local) onde as pessoas|"
                                            r"boas-vindas|Welcome to|Experience and shape|"
                                            r"a place where people can experience|"  # 06/11 desktop 9481 (inglês)
                                            r"Termos|Terms of|feedback sobre|Get started", texto, re.I):
            return  # outra janela (ajustes do agente, nome do projeto...): nao e o cadastro, nao mexe
        page.evaluate("""(sel) => { const d = [...document.querySelectorAll(sel)].pop(); if (!d) return;
            for (const c of d.querySelectorAll('input[type=checkbox], [role=checkbox]')) {
                const rot = ((c.closest('label') || c.parentElement || {}).innerText || c.getAttribute('aria-label') || '').toLowerCase();
                const marcado = c.checked ?? (c.getAttribute('aria-checked') === 'true');
                const opcional = /marketing|pesquisa|research|e-mail|email|novidades|news/.test(rot);
                if (opcional ? marcado : !marcado) c.click();   // opcional sai; termos obrigatorios entram
            }
            for (const e of d.querySelectorAll('*')) if (e.scrollHeight > e.clientHeight + 5) e.scrollTop = e.scrollHeight;
        }""", sel)
        page.wait_for_timeout(800)
        botao = dlg.locator("button").filter(has_text=ok).last
        if not botao.count():
            # 03/11: o Flow trocou a janela ("Experimente e molde...", "um local onde...") e o botão novo não estava na
            # lista — a MS ficou o dia sem clipe ("o texto nao entrou na caixa"). Sem botão conhecido: o último botão
            # habilitado que não seja sair/cancelar/fechar; e o log mostra os nomes para entrar na lista.
            nomes = [" ".join((b.inner_text() or "").split()) for b in dlg.locator("button").all()]
            nao = re.compile(r"^\s*(Sair|Exit|Fechar|Close|Cancelar|Cancel|Voltar|Back|Não|No)?\s*$", re.I)
            cand = [b for b, n in zip(dlg.locator("button").all(), nomes) if not nao.match(n) and b.is_enabled()]
            log(f"[sessao] boas-vindas do Flow sem botao conhecido (botoes: {nomes}): {texto[:160]}")
            if not cand:
                return
            botao = cand[-1]
        nome = " ".join(botao.inner_text().split())
        if (nome, texto) == ultimo:
            log(f"[sessao] boas-vindas do Flow travada em '{nome}' (habilitado={botao.is_enabled()}): {texto[:200]}")
            page.keyboard.press("Escape")
            return
        ultimo = (nome, texto)
        log(f"[sessao] boas-vindas do Flow: '{nome}' — {texto[:90]}")
        try:
            botao.click(timeout=8000)
        except Exception as e:
            log(f"[sessao] boas-vindas: clique em '{nome}' falhou ({type(e).__name__})")
            return
        page.wait_for_timeout(2500)


def _dismiss_changelog_overlay(page, log=print):
    """Instala um MutationObserver PERSISTENTE que neutraliza iframes de changelog
    do Google Flow que interceptam pointer events. Tambem faz limpeza imediata."""
    try:  # 23/10: conta nova tem a janela de cadastro do Flow por cima de tudo (tambem dentro do projeto)
        _passar_boas_vindas(page, log)
    except Exception as e:
        log(f"[sessao] boas-vindas: {type(e).__name__}")
    removed = page.evaluate("""() => {
        let count = 0;

        function _nuke_changelog() {
            // 1. Remover iframes de changelog (protege workspace/slate)
            document.querySelectorAll('iframe').forEach(iframe => {
                const src = iframe.src || '';
                if (src.includes('changelogs') || src.includes('gstatic.com/aitestkitchen')) {
                    let el = iframe;
                    for (let i = 0; i < 5; i++) {
                        if (el.parentElement && el.parentElement !== document.body) {
                            el = el.parentElement;
                        } else break;
                    }
                    if (el.querySelector && el.querySelector('[data-slate-editor], [contenteditable="true"]')) {
                        iframe.remove();
                    } else {
                        el.remove();
                    }
                    count++;
                }
            });
            // 2. Remover containers do overlay por classe (PROTEGER workspace/slate)
            document.querySelectorAll('div[class*="sc-1c6805c6"], div[class*="sc-181bed44"]').forEach(el => {
                if (el.querySelector && el.querySelector('[data-slate-editor], [contenteditable="true"]')) return;
                el.remove();
                count++;
            });
            // 3. Neutralizar overlays aria-hidden que bloqueiam pointer events
            document.querySelectorAll('[data-state="open"][aria-hidden="true"]').forEach(el => {
                el.style.pointerEvents = 'none';
                el.style.display = 'none';
                count++;
            });
        }

        // Limpeza imediata
        _nuke_changelog();

        // MutationObserver persistente — mata qualquer changelog que o React reinjetar
        if (!window.__changelog_observer) {
            window.__changelog_observer = new MutationObserver(() => { _nuke_changelog(); });
            window.__changelog_observer.observe(document.body, {childList: true, subtree: true});
        }

        return count;
    }""")
    if removed:
        log(f"[changelog] removidos {removed} elementos de overlay/changelog")
    try:  # 06/11: modal "Introducing Omni 1.2!" travou todos os Chrome do PC2 — fecha a janela de novidades em si
        removed += _fechar_modal_novidades(page, log)
    except Exception as e:  # noqa: BLE001
        log(f"[changelog] modal: {type(e).__name__}")
    return removed


_NOVIDADES = ("changelog", "registros de altera", "registos de altera", "introducing", "apresentando", "novidade",
              "what's new", "o que há de novo")
_NOVIDADES_BOTOES = ("Get started", "Começar", "Got it", "Entendi", "Close", "Fechar", "Dismiss", "OK", "Done",
                     "Concluído", "Not now", "Agora não")


def _fechar_modal_novidades(page, log=print):
    """Diálogo de novidades/changelog do Flow aberto = clica o botão de fechar (ou Esc). Nunca mexe na verificação
    de idade nem em login."""
    feitos = 0
    for _ in range(3):
        ds = page.evaluate("""() => [...document.querySelectorAll('[role=dialog],[role=alertdialog],dialog[open],[aria-modal=true]')]
            .filter(e => { const r = e.getBoundingClientRect(); return r.width > 50 && r.height > 50; })
            .map(e => (e.innerText || '').slice(0, 400).toLowerCase())""")
        alvo = [t for t in ds if any(k in t for k in _NOVIDADES) and "idade" not in t and " age" not in t]
        if not alvo:
            return feitos
        clicou = False
        for nome in _NOVIDADES_BOTOES:
            loc = page.locator("[role=dialog], [aria-modal=true], dialog[open]").get_by_role("button", name=nome, exact=True)
            try:
                if loc.count() and loc.first.is_visible():
                    loc.first.click(timeout=4000)
                    clicou = True
                    break
            except Exception:  # noqa: BLE001
                pass
        if not clicou:
            page.keyboard.press("Escape")
        feitos += 1
        log(f"[changelog] janela de novidades fechada ({'botão' if clicou else 'Esc'}): {alvo[0][:60]!r}")
        page.wait_for_timeout(1500)
    return feitos


def _is_login_page(page):
    """Detecta se a pagina atual e a tela de login do Google (sessao expirada).
    Retorna (True, url) se detectou, (False, '') se nao."""
    try:
        url = page.url or ""
        if "accounts.google.com" in url or "ServiceLogin" in url or "signin" in url.lower():
            return True, url
        # Tambem detecta se o body nao tem nada do Flow (caixa de prompt etc.)
        try:
            t = page.evaluate("() => document.body.innerText") or ""
        except Exception:
            t = ""
        if "AI Test Kitchen" in t and "Fazer login" in t:
            return True, url
        # flow.google.com/about = landing de quem nao esta logado no Flow; /age-restricted = conta bloqueada por idade
        if "flow.google.com/about" in url or "age-restricted" in url:
            return True, url
        # 04/11 18:40 (claude-38/dona): x200ma travado HORAS na janela de boas-vindas do Flow ("Experience and shape AI
        # tools for creativity", opt-in + Sign out/Next; o Next não fecha). Conta nesse estado = trata como a de idade
        # (sai SÓ desta máquina 6 h, segue com outra) em vez de esperar o tempo-limite.
        if "Experience and shape AI tools" in t:
            return True, url + "#age-restricted-boas-vindas"
        return False, ""
    except Exception:
        return False, ""


class RecaptchaError(Exception):
    """reCAPTCHA Enterprise bloqueando a pagina do Flow."""
    pass


class SessaoExpiradaError(Exception):
    """Sessao do Google expirou — botao de re-login manual necessario."""
    pass


class DireitosAutoraisError(Exception):
    """Flow recusou o comando por politica (pessoas famosas/direitos autorais).
    NAO gastou credito. Nao adianta re-tentar igual — o cron deve trocar
    prompt, depois trocar foto e por fim ISOLAR a foto ofensora."""
    pass


# Frases do card de recusa por politica (aparecem no body innerText do Flow).
# Normalizado sem acento pra casar mesmo se a pagina variar acentuacao.
_MARCADORES_DIREITOS = (
    "pessoas famosas",
    "geracao de imagens de pessoas",
    "pode violar nossas politicas",
    "violar nossas politicas",
    "against our policies",
    "famous people",
)


def _tem_recusa_direitos(body_text):
    """True se o texto da pagina contem o card de recusa por politica.
    Exige simultaneamente a palavra 'Falha' e um marcador de politica pra
    nao dar falso-positivo em textos que citem 'politicas' em outro contexto."""
    if not body_text:
        return False
    import unicodedata
    t = unicodedata.normalize("NFKD", body_text).encode("ascii", "ignore").decode().lower()
    tem_falha = "falha" in t or "failed" in t
    tem_marcador = any(m in t for m in _MARCADORES_DIREITOS)
    return tem_falha and tem_marcador


def _ensure_chrome_running(port, log=print):
    """Garante que o Chrome esta rodando na porta CDP. Abre se necessario.
    Devolve "novo" quando FOI ESTA chamada que abriu (quem abriu fecha: fechar_chrome), True se ja estava aberto."""
    import urllib.request, subprocess
    url = f"http://127.0.0.1:{port}/json/version"
    try:
        urllib.request.urlopen(url, timeout=3)
        return True
    except Exception:
        pass
    session_name = os.environ.get("FLOW_SESSION", "seebotsia")
    profile_name = os.environ.get("FLOW_PROFILE", PROFILE_MAP.get(session_name, f"chrome_profile_{session_name}"))
    profile = os.path.join(os.path.dirname(os.path.abspath(__file__)), profile_name)
    os.makedirs(profile, exist_ok=True)
    chrome = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    if not os.path.exists(chrome):
        log("[chrome] chrome.exe nao encontrado!")
        return False
    chrome_args = [
        chrome,
        f"--remote-debugging-port={port}",
        "--no-first-run",
        "--disable-session-crashed-bubble",
        "--disable-gpu",
        "--disable-software-rasterizer",
        "--disable-blink-features=AutomationControlled",
        "--disable-features=IsolateOrigins,site-per-process",
        "--disable-web-security",
        f"--user-data-dir={profile}",
    ]
    if os.environ.get("FLOW_JANELA_OCULTA") == "1":
        # 29/10 (D28/D30): Chrome aberto so para o token do reCAPTCHA (flow_gerar no PC1) fica fora da tela, como o
        # chrome_conta.py faz nas maquinas; a dona viu janelas "about:blank" da seebotsia aparecendo no PC1
        chrome_args.append("--window-position=-3000,0")
    if _FLOW_PROXY_HOST:
        chrome_args.append(f"--proxy-server=http://{_FLOW_PROXY_HOST}")
        log(f"[chrome] proxy ativo: {_FLOW_PROXY_HOST}")
    chrome_args.append("about:blank")
    log(f"[chrome] abrindo Chrome na porta {port} (sessao={session_name}, perfil={profile_name})...")
    subprocess.Popen(chrome_args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    import time as _time
    for _ in range(20):
        _time.sleep(1)
        try:
            urllib.request.urlopen(url, timeout=2)
            log(f"[chrome] Chrome aberto com sucesso (sessao={session_name})")
            return "novo"
        except Exception:
            pass
    log("[chrome] FALHA ao abrir Chrome!")
    return False


def fechar_chrome(port, log=print):
    """Fecha o Chrome da porta CDP: pelo CDP primeiro (grava os cookies = o login nao cai), depois taskkill se travar.
    Dono 22/10/2026: "o Flow nao esta fechando depois de fazer o servico, ai fica ocupando espaco" — o Chrome aberto
    por _ensure_chrome_running ficava ate a proxima pausa do sistema (cada um ~0,5-1 GB de memoria)."""
    import urllib.request, subprocess
    url = f"http://127.0.0.1:{port}/json/version"
    try:
        with sync_playwright() as p:
            p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}").new_browser_cdp_session().send("Browser.close")
    except Exception:
        pass
    for _ in range(20):
        try:
            urllib.request.urlopen(url, timeout=1)
        except Exception:
            log(f"[chrome] Chrome da porta {port} fechado")
            return True
        time.sleep(0.5)
    try:
        out = subprocess.run(["netstat", "-ano"], capture_output=True, text=True, timeout=15).stdout
        for linha in out.splitlines():
            if f":{port} " in linha and "LISTENING" in linha and linha.split()[-1].isdigit():
                subprocess.run(["taskkill", "/PID", linha.split()[-1], "/T", "/F"], capture_output=True, timeout=15)
        log(f"[chrome] Chrome da porta {port} fechado a forca (nao saiu pelo CDP)")
    except Exception as e:
        log(f"[chrome] AVISO: nao consegui fechar o Chrome da porta {port}: {e}")
    return False


_RE_ERRO_CONEXAO = re.compile(r"connect|Target (page, context or browser )?closed|Browser has been closed|"
                              r"ECONNREFUSED|WebSocket|t[uú]nel", re.I)


def _gerar_nos_notebooks(prompt, out_path, image, aspect, modelo, duration, log):
    """Conta ativada nos notebooks (postador\\bin\\maquina_remota.py ativar): gera pelo Chrome LOGADO de la (dono 23/10:
    "videos Veo rodando nos notebooks" — o PC1 ficava sem memoria com os Chromes do Flow). Um falhou = o outro.
    Devolve o caminho, ou None = gerar aqui. So troca de maquina em erro de CONEXAO: erro depois de pedir o video ja
    gastou credito (mesma regra do flow_bot.generate). FLOW_NOTEBOOKS=0 desliga."""
    sess = os.environ.get("FLOW_SESSION", "")
    if os.environ.get("FLOW_NOTEBOOKS", "1") == "0" or not sess:
        return None
    try:
        sys.path.insert(0, r"D:\postador-de-videos\bin")
        import maquina_remota
        import contas
        perfil = contas.perfil_notebook(sess)
        maqs = maquina_remota.maquinas_flow(perfil)
        # 23/10 (cadeia de alternativas, cadeia_veo.py): o cron manda a ETAPA (VEO_MAQUINAS=notebooks/desktop/pc2;
        # "pc1" = so este PC) e as maquinas de castigo ficam de fora
        import cadeia_veo
        _etapa = [m for m in os.environ.get("VEO_MAQUINAS", "").split(",") if m]
        if _etapa:
            maqs = [m for m in cadeia_veo.maquinas_da_conta(perfil) if m in _etapa]
        maqs = [m for m in maqs if not cadeia_veo.castigo(m)]
        # 01/11: a conta pode estar logada num notebook e deslogada noutro (painel de saúde por conta@máquina);
        # máquina onde o painel lê a conta deslogada fica de fora, se sobrar alguma
        try:
            import flow_saldo_real
            mortas = set((flow_saldo_real.conta(sess) or {}).get("mortas") or [])
            if mortas and [m for m in maqs if m not in mortas]:
                maqs = [m for m in maqs if m not in mortas]
        except Exception:  # noqa: BLE001
            pass
    except Exception as e:
        log(f"[notebook] indisponivel ({e}) — gera aqui")
        return None
    if not maqs:
        return None
    ordem = maquina_remota.tentativas(maqs, perfil.lower(), log_fn=log)
    pediu_login = []
    try:
        for rem in ordem:
            if rem is None:  # as que sobram estão ocupadas: troca de conta sem castigo, como antes
                return None
            # 29/10 (D30): primeiro por HTTP na maquina (cadeia_veo.http_remoto: o Chrome de la so fabrica o token do
            # reCAPTCHA); recusou/falhou antes de pedir = o Chrome de la, como sempre
            feito, estado = cadeia_veo.http_remoto(rem, sess, perfil, prompt, out_path, image, aspect, modelo, log)
            if feito:
                return feito
            if estado == "pediu":
                raise RuntimeError(f"HTTP no {rem.nome}: o Flow aceitou o pedido e o arquivo nao veio (credito gasto)")
            if estado == "sem_credito":
                raise CreditosEsgotadosError("saldo insuficiente (creditos=0) lido por HTTP")
            if estado == "login":  # 01/11: nada gasto ainda — tenta a conta na próxima máquina
                log(f"[notebook] Flow pediu login no {rem.nome} (HTTP) — proxima maquina")
                pediu_login.append(rem.nome)
                continue
            log(f"[notebook] gerando pelo Chrome do {rem.nome} (conta {sess})")
            try:
                return _gerar_impl(prompt, out_path, image, aspect, modelo, duration, log, porta=rem.porta_local)
            except Exception as e:
                txt = f"{type(e).__name__}: {e}"
                antes_de_pedir = type(e).__name__ in ("SessaoExpiradaError", "RecaptchaError")  # nada gasto ainda
                if not (antes_de_pedir or _RE_ERRO_CONEXAO.search(txt)):
                    raise
                if "age-restricted" in txt:
                    # 04/11 dona: "a verificação de idade é da CONTA, não da máquina — as outras contas funcionam":
                    # marca a CONTA fora (FLOW_BLOQUEADAS por 6 h), a máquina segue no ar com outra conta
                    try:
                        maquina_remota.flow_idade_bloquear(perfil, maquina=rem.nome)
                        log(f"[notebook] conta {perfil} pediu verificação de idade no {rem.nome} — ela sai 6 h SÓ desta máquina (3+ contas na mesma máquina = máquina fora); "
                            "a máquina segue com as outras contas")
                    except Exception as e2:  # noqa: BLE001
                        log(f"[notebook] não marquei a conta {perfil} ({type(e2).__name__})")
                log(f"[notebook] falhou no {rem.nome} ({txt[:120]}) — proxima maquina")
    finally:
        ordem.close()
    if pediu_login:
        raise SessaoExpiradaError(f"Flow pediu login em {', '.join(pediu_login)} (visto por HTTP)")
    return None


def _gerar_http(prompt, out_path, image, aspect, modelo, log):
    """29/10 (dona: "faça" — navegador sem navegador na produção): pede o video ao agente do Flow por HTTP
    (D:\\projeto-navegador-sem-navegador\\services\\veo_flow\\flow_gerar.py; o Chrome so fabrica o token do reCAPTCHA,
    sem clicar na tela). Falhou = None e segue a tela como antes. Desligar: FLOW_HTTP=0."""
    if os.environ.get("FLOW_HTTP") == "0":
        return None
    nsn = r"D:\projeto-navegador-sem-navegador"
    if nsn not in sys.path:
        sys.path.append(nsn)  # no fim (regra 23/10)
    sess = os.environ.get("FLOW_SESSION", "")
    try:
        from services.veo_flow.flow_gerar import FlowGerador
        with FlowGerador(sess, log=log) as fg:
            r = fg.video(prompt, out_path, formato=aspect, modelo=modelo, imagem_inicial=image or None)
        if os.path.exists(out_path) and os.path.getsize(out_path) > 100000:
            log(f"[http] {sess}: video gerado por HTTP (sem clicar na tela) em {r['segundos']} s -> {out_path}")
            return out_path
        log(f"[http] {sess}: HTTP nao entregou o arquivo -> tela")
    except Exception as e:  # noqa: BLE001
        log(f"[http] {sess}: HTTP falhou ({type(e).__name__}: {str(e)[:150]}) -> tela")
    return None


def gerar(prompt, out_path, image=None, aspect="9:16", modelo="Veo 3.1 - Fast",
          duration="8S", log=print):
    feito = _gerar_nos_notebooks(prompt, out_path, image, aspect, modelo, duration, log)
    if feito:
        return feito
    import contas
    if contas.so_notebook(os.environ.get("FLOW_SESSION", "")) or os.environ.get("VEO_SO_NOTEBOOK") == "1":
        # conta logada so nas maquinas (23/10): aqui o Chrome abriria deslogado. VEO_SO_NOTEBOOK=1 (etapa remota da
        # cadeia ou PC1 sem RAM): conta local tambem NAO cai pra este PC
        raise RuntimeError("SO_NOTEBOOK: maquinas ocupadas ou fora — esta conta nao gera neste PC")
    feito = _gerar_http(prompt, out_path, image, aspect, modelo, log)
    if feito:
        return feito
    _lock_path =os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "logs", f".cdp_lock_{PORT}")
    try:
        _cdp_lock = FileLock(_lock_path, timeout=900)
        _cdp_lock.acquire()
        log(f"[lock] porta {PORT} adquirida")
    except FileLockTimeout:
        raise RuntimeError(f"porta CDP {PORT} travada por outro processo (>900s)")
    # dentro da trava: quem esperava a porta nao pode achar "aberto" um Chrome que o anterior esta fechando
    abri = _ensure_chrome_running(PORT, log) == "novo"
    try:
        return _gerar_impl(prompt, out_path, image, aspect, modelo, duration, log)
    finally:
        if abri and os.environ.get("FLOW_MANTER_ABERTO") != "1":
            fechar_chrome(PORT, log)
        _cdp_lock.release()
        log(f"[lock] porta {PORT} liberada")


def _gerar_impl(prompt, out_path, image, aspect, modelo, duration, log, porta=None):
    with sync_playwright() as p:
        b = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta or PORT}")
        ctx = b.contexts[0]
        ctx.add_init_script("""
            // --- stealth anti-fingerprint ---
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            delete navigator.__proto__.webdriver;
            window.chrome = window.chrome || {};
            window.chrome.runtime = window.chrome.runtime || {
                PlatformOs: {MAC: 'mac', WIN: 'win', ANDROID: 'android', CROS: 'cros', LINUX: 'linux', OPENBSD: 'openbsd'},
                PlatformArch: {ARM: 'arm', X86_32: 'x86-32', X86_64: 'x86-64', MIPS: 'mips', MIPS64: 'mips64'},
                PlatformNaclArch: {ARM: 'arm', X86_32: 'x86-32', X86_64: 'x86-64', MIPS: 'mips', MIPS64: 'mips64'},
                RequestUpdateCheckStatus: {THROTTLED: 'throttled', NO_UPDATE: 'no_update', UPDATE_AVAILABLE: 'update_available'},
                OnInstalledReason: {INSTALL: 'install', UPDATE: 'update', CHROME_UPDATE: 'chrome_update', SHARED_MODULE_UPDATE: 'shared_module_update'},
                OnRestartRequiredReason: {APP_UPDATE: 'app_update', OS_UPDATE: 'os_update', PERIODIC: 'periodic'},
            };
            if (!window.chrome.csi) { window.chrome.csi = function() { return {startE: Date.now(), onloadT: Date.now(), pageT: Math.random()*1000+500, tran: 15}; }; }
            if (!window.chrome.loadTimes) { window.chrome.loadTimes = function() { return {commitLoadTime: Date.now()/1000, connectionInfo: 'h2', finishDocumentLoadTime: Date.now()/1000+0.1, finishLoadTime: Date.now()/1000+0.2, firstPaintAfterLoadTime: 0, firstPaintTime: Date.now()/1000+0.05, navigationType: 'Other', npnNegotiatedProtocol: 'h2', requestTime: Date.now()/1000-0.5, startLoadTime: Date.now()/1000-0.5, wasAlternateProtocolAvailable: false, wasFetchedViaSpdy: true, wasNpnNegotiated: true}; }; }
            const origQuery = window.Permissions.prototype.query;
            window.Permissions.prototype.query = function(params) {
                if (params && params.name === 'notifications') {
                    return Promise.resolve({state: Notification.permission});
                }
                return origQuery.call(this, params);
            };
            Object.defineProperty(navigator, 'plugins', {
                get: () => {
                    const p = [
                        {name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format'},
                        {name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: ''},
                        {name: 'Native Client', filename: 'internal-nacl-plugin', description: ''}
                    ];
                    p.length = 3;
                    return p;
                }
            });
            Object.defineProperty(navigator, 'languages', {get: () => ['pt-BR', 'pt', 'en-US', 'en']});
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(param) {
                if (param === 37445) return 'Intel Inc.';
                if (param === 37446) return 'Intel Iris OpenGL Engine';
                return getParameter.call(this, param);
            };
        """)

        # Proxy auth via CDP Fetch domain (Webshare exige user:pass)
        # NOTA: so intercepta Fetch.authRequired (proxy challenge).
        # NAO interceptar Fetch.requestPaused — quebra todo o roteamento de requests.
        if _FLOW_PROXY_USER and _FLOW_PROXY_PASS:
            try:
                cdp = ctx.new_cdp_session(ctx.pages[0] if ctx.pages else ctx.new_page())
                cdp.send("Fetch.enable", {"handleAuthRequests": True})
                def _on_auth(params):
                    cdp.send("Fetch.continueWithAuth", {
                        "requestId": params["requestId"],
                        "authChallengeResponse": {
                            "response": "ProvideCredentials",
                            "username": _FLOW_PROXY_USER,
                            "password": _FLOW_PROXY_PASS,
                        }
                    })
                cdp.on("Fetch.authRequired", _on_auth)
                log(f"[proxy] auth CDP configurado para {_FLOW_PROXY_USER}@{_FLOW_PROXY_HOST}")
            except Exception as e:
                log(f"[proxy] AVISO: falha configurando auth CDP: {e}")
        flow_pages = [pg for pg in ctx.pages if "flow" in pg.url]
        if flow_pages:
            page = flow_pages[0]
        else:
            page = ctx.pages[0] if ctx.pages else ctx.new_page()

        # Limpar artefatos reCAPTCHA antes de carregar o Flow
        try:
            page.evaluate("""() => {
                // limpa localStorage entries do reCAPTCHA
                const keys = Object.keys(localStorage);
                keys.forEach(k => {
                    if (k.startsWith('_grecaptcha') || k.startsWith('rc::')) {
                        localStorage.removeItem(k);
                    }
                });
                // limpa sessionStorage tambem
                const skeys = Object.keys(sessionStorage);
                skeys.forEach(k => {
                    if (k.startsWith('_grecaptcha') || k.startsWith('rc::')) {
                        sessionStorage.removeItem(k);
                    }
                });
            }""")
        except Exception:
            pass
        # Limpar cookies reCAPTCHA/recaptcha via CDP
        try:
            _cdp_clean = ctx.new_cdp_session(page)
            cookies = _cdp_clean.send("Network.getAllCookies").get("cookies", [])
            rc_cookies = [c for c in cookies if "recaptcha" in c.get("name", "").lower() or "grecaptcha" in c.get("name", "").lower() or "recaptcha" in c.get("domain", "").lower()]
            for c in rc_cookies:
                _cdp_clean.send("Network.deleteCookies", {"name": c["name"], "domain": c.get("domain", "")})
            if rc_cookies:
                log(f"[stealth] removidos {len(rc_cookies)} cookies reCAPTCHA")
            _cdp_clean.detach()
        except Exception:
            pass

        # Limpar Service Workers que podem carregar reCAPTCHA em cache
        try:
            _cdp_sw = ctx.new_cdp_session(page)
            versions = _cdp_sw.send("ServiceWorker.enable") or {}
            _cdp_sw.send("ServiceWorker.disable")
            _cdp_sw.detach()
        except Exception:
            pass
        try:
            _cdp_cache = ctx.new_cdp_session(page)
            caches = _cdp_cache.send("CacheStorage.requestCacheNames", {"securityOrigin": "https://labs.google"}).get("caches", [])
            for c in caches:
                _cdp_cache.send("CacheStorage.deleteCache", {"cacheId": c["cacheId"]})
            if caches:
                log(f"[stealth] removidos {len(caches)} CacheStorage entries")
            _cdp_cache.detach()
        except Exception:
            pass

        page.goto(PROJ, wait_until="domcontentloaded")
        page.wait_for_timeout(8000)
        page.bring_to_front()

        _dismiss_changelog_overlay(page, log)

        # DETECCAO DE SESSAO EXPIRADA: se apos o goto estamos na tela de login
        # do Google, NAO adianta tentar — o usuario precisa logar de novo.
        # Detectamos UMA vez e falhamos cedo pra nao desperdiçar 3 tentativas.
        is_login, login_url = _is_login_page(page)
        if is_login:
            log(f"[SESSAO_EXPIRADA] pagina de login detectada ({login_url}).")
            if "age-restricted" in login_url:
                log("[SESSAO_EXPIRADA] o Flow bloqueou esta conta por idade: a dona precisa confirmar a idade no Google.")
            else:
                log("[SESSAO_EXPIRADA] logar de novo: python D:\\logins-google\\cofre.py logar <conta>")
            raise SessaoExpiradaError(f"sessao expirada (url={login_url})")

        # DETECCAO DE RECAPTCHA ENTERPRISE: iframe de scoring pode estar presente
        # mas o Flow continua funcional (textarea acessivel). Logar e continuar.
        _has_recaptcha = page.evaluate("""() => {
            const frames = Array.from(document.querySelectorAll('iframe'));
            return frames.some(f => (f.src || '').includes('recaptcha/enterprise'));
        }""")
        if _has_recaptcha:
            _has_textarea = page.evaluate("() => !!document.querySelector('textarea')")
            if _has_textarea:
                log("[RECAPTCHA] iframe presente mas textarea acessivel — continuando normalmente")
            else:
                log("[RECAPTCHA] iframe presente SEM textarea — tentando reload")
                page.reload(wait_until="domcontentloaded")
                page.wait_for_timeout(8000)
                _has_textarea2 = page.evaluate("() => !!document.querySelector('textarea')")
                if not _has_textarea2:
                    log("[RECAPTCHA] sem textarea apos reload — abortando")
                    raise RecaptchaError("reCAPTCHA Enterprise bloqueando Flow (sem textarea)")
                else:
                    log("[RECAPTCHA] textarea apareceu apos reload — continuando")

        # DETECCAO DE CREDITOS ESGOTADOS: checa IMEDIATAMENTE apos carregar a
        # pagina. Se a conta ja esta sem creditos, nem vale a pena tentar
        # preparar prompt/enviar. Falha rapido + cooldown longo (ate o reset
        # diario) — evita desperdiçar 8 minutos na sessao errada.
        try:
            esgotado, padrao = _creditos_esgotados(page)
            if esgotado:
                log(f"[CREDITOS] ESGOTADOS ao carregar pagina. padrao='{padrao}'")
                _salvar_evidencia_creditos_esgotados(page, log)
                raise CreditosEsgotadosError(f"creditos esgotados no goto (padrao='{padrao}')")
        except CreditosEsgotadosError:
            raise

        # CHECAGEM DE SALDO: quando o saldo e 0, o Flow NAO mostra banner —
        # a geracao trava e da timeout de 480s. Lemos o saldo no menu de conta
        # ANTES de gastar tempo tentando gerar.
        # 2026-08-24: Veo 3.1 - Fast custa ~20 creditos por geracao.
        # Contas com 15 travavam o bot (timeout 480s sem erro visivel).
        CREDITO_MINIMO = int(os.environ.get("VEO_CREDITO_MINIMO", "20"))  # 23/10: o mesmo do creditos_contas.py
        try:
            saldo = _ler_saldo_creditos(page, log=log)
            if saldo is not None and saldo < CREDITO_MINIMO:
                log(f"[CREDITOS] saldo insuficiente ({saldo} < {CREDITO_MINIMO}) — pulando sessao sem gerar")
                _salvar_evidencia_creditos_esgotados(page, log)
                raise CreditosEsgotadosError(f"saldo insuficiente (creditos={saldo})")
        except CreditosEsgotadosError:
            raise
        except Exception as e:
            log(f"[CREDITOS] checagem de saldo falhou (seguindo): {str(e)[:60]}")

        # 2026-07-25: PROJ pode redirecionar para home (/tools/flow) se o ID do
        # projeto salvo expirar. Garantir que entramos num projeto clicando
        # 'Novo projeto' / '+ Novo projeto' se nao houver caixa de prompt.
        # O botao pode ter offsetParent=null (eh um floating action button).
        # usaremos mouse click via coordenadas (Material UI precisa).
        page.wait_for_timeout(2000)
        _body = page.evaluate("() => document.body.innerText") or ""

        # TELA DE ERRO ("Algo deu errado" / "Voltar aos projetos"): acontece
        # quando a URL aponta pra um projeto de OUTRA conta (id que nao existe
        # nesta). O botao presente e "Voltar aos projetos" — clicamos nele (ou
        # vamos pra HOME) pra sair do beco sem saida antes de criar um novo.
        if ("Algo deu errado" in _body or "Something went wrong" in _body or
                "Voltar aos projetos" in _body or "Back to projects" in _body):
            log("[sessao] tela de erro (projeto de outra conta) — voltando pra home")
            try:
                page.goto(_FLOW_HOME, wait_until="domcontentloaded")
                page.wait_for_timeout(5000)
            except Exception:
                pass
            _body = page.evaluate("() => document.body.innerText") or ""

        if "/project/" not in page.url:
            log("[sessao] fora de um projeto — tentando criar novo")
            _passar_boas_vindas(page, log)
            _dismiss_changelog_overlay(page, log)
            res = page.evaluate("""() => {
                const btns = Array.from(document.querySelectorAll('button, a, [role=button]'));
                for (const b of btns) {
                    const t = (b.innerText || '').trim();
                    if (t.includes('Novo projeto') || t === 'Create' ||
                        t.includes('Create new') || t.includes('New project')) {
                        b.click();
                        return t;
                    }
                }
                return null;
            }""")
            if res:
                log(f"[sessao] novo projeto click: '{res}'")
            else:
                log("[sessao] nao achei botao 'Novo projeto'")
            page.wait_for_timeout(6000)
            # Se abriu modal pedindo nome do projeto, clicar 'Concluir'
            res = page.evaluate("""() => {
                const btns = Array.from(document.querySelectorAll('button'));
                for (const b of btns) {
                    if (!b.offsetParent) continue;
                    const t = (b.innerText||'').trim();
                    if (t === 'Concluir' || t === 'Done' || t === 'Criar' || t === 'Create') {
                        b.click();
                        return t;
                    }
                }
                return null;
            }""")
            if res:
                log(f"[sessao] criou projeto: '{res}'")
            page.wait_for_timeout(3000)

        # Salva o project-url desta conta (se ja estamos num /project/...) pra
        # a proxima geracao entrar direto, sem passar pela home/criacao.
        try:
            _sess = os.environ.get("FLOW_SESSION", "")
            if "/project/" in page.url:
                _save_proj_url(_sess, page.url)
                log(f"[sessao] projeto salvo p/ '{_sess}': ...{page.url[-20:]}")
        except Exception:
            pass

        # NOVA SESSAO: conversa limpa com o agente (botao 'Iniciar nova sessão'; abre o painel se estiver fechado)
        _fechar_menu_conta(page, log)
        nova_sessao(page, log)

        final = flow_bot._enrich_prompt(prompt, model=modelo,
                                        audio=True, duration=duration,
                                        aspect_ratio=aspect)
        # Se tem imagem, instruir o agente a usar image-to-video
        if image:
            final = (f"Use the uploaded image as the starting frame "
                     f"(image-to-video mode). Animate it: {final}")
        log("prompt: " + final)

        before = None
        ultimo_erro = None
        for tentativa in range(1, 4):
            try:
                # Re-checar login a cada tentativa (caso a pagina tenha redirecionado)
                if _is_login_page(page)[0]:
                    log(f"[SESSAO_EXPIRADA] tentativa {tentativa}: pagina de login.")
                    raise SessaoExpiradaError("sessao expirada durante retry")

                # DETECCAO DE CREDITOS ESGOTADOS: se a pagina exibe "no credits"
                # / "0 creditos restantes" / "atingiu o limite diario" etc,
                # NAO adianta tentar novamente nessa sessao — os creditos resetam
                # so amanha. Salva evidencia + lanca erro especial pra o cron
                # marcar cooldown longo.
                esgotado, padrao = _creditos_esgotados(page)
                if esgotado:
                    log(f"[CREDITOS] ESGOTADOS! padrao='{padrao}' — pulando sessao")
                    _salvar_evidencia_creditos_esgotados(page, log)
                    raise CreditosEsgotadosError(f"creditos esgotados (padrao='{padrao}')")

                # NAVEGAR AO WORKSPACE se a pagina estiver na landing/welcome
                page = flow_bot._ensure_workspace(page, log=log)
                _fechar_menu_conta(page, log)  # aberto, cobre o botao de enviar

                if tentativa > 1:
                    nova_sessao(page, log)

                # GARANTIR MODO VEO (video) — senao sai imagem Nano Banana
                garantir_modo_veo(page, aspect=aspect, modelo=modelo, log=log)

                # Limpar changelog overlay antes de qualquer mouse click
                _dismiss_changelog_overlay(page, log)

                # image-to-video: sobe a imagem inicial ANTES do prompt
                # 12/11: o retorno era IGNORADO — a foto não anexava ("envio falhou", botão do '+' mudou) e o prompt
                # seguia com "Use the uploaded image": o agente do Flow respondia "I couldn't find an uploaded image...
                # Generate initial image first / text-to-video?" e PARAVA esperando escolha; o código aguardava ~20 min
                # e repetia (tela que "sempre se repete" no STI/x200ma; 14 falhas seguidas desde 05:34). Agora: 2ª
                # tentativa de anexar; não anexou = tira a instrução da imagem e pede o vídeo direto em texto
                # (VEO_EXIGIR_FOTO=1 volta a falhar sem foto).
                if image:
                    anexou = _subir_imagem(page, image, log=log)
                    if not anexou:
                        page.wait_for_timeout(1500)
                        anexou = _subir_imagem(page, image, log=log)
                    if not anexou:
                        if os.environ.get("VEO_EXIGIR_FOTO") == "1":
                            raise RuntimeError("foto não anexou (VEO_EXIGIR_FOTO=1)")
                        sem_foto = final.split("Animate it: ", 1)[-1]
                        if final != sem_foto:
                            final = ("Create the video directly from this description (text-to-video mode, do NOT "
                                     "ask questions, generate now): " + sem_foto)
                            log("[img] foto NÃO anexou — gero por texto (sem 'uploaded image', o agente parava pra perguntar)")

                before = set(midias(page))
                n_aprov = page.locator(_SEL_APROVAR).count()
                log(f"midias antes: {len(before)} (tentativa {tentativa})")

                box, bsel = flow_bot._find_first(
                    page, flow_bot.PROMPT_SELECTORS, timeout=20000)
                if not box:
                    raise RuntimeError("caixa de prompt nao achada")
                _dismiss_changelog_overlay(page, log)
                # a caixa e recriada quando a foto e anexada: localizar de novo na hora e digitar no foco
                # (o elemento guardado antes dava "Element is not attached to the DOM")
                caixa = page.locator(bsel).last
                caixa.click(timeout=8000, force=True)
                page.wait_for_timeout(500)
                if bsel in ("textarea", "input[type='text']"):
                    caixa.fill(final, timeout=30000)
                else:
                    page.keyboard.type(final)
                # 26/10: no acer (Atom) a digitação do pedido longo ainda estava acontecendo aos 0,8 s e a conta
                # inovaremultiatendimento falhava sempre aqui -> espera o texto aparecer (até 20 s)
                for _ in range(25):
                    page.wait_for_timeout(800)
                    if " ".join(final.split())[:40] in " ".join(_texto_caixa(page).split()):
                        break
                else:
                    raise RuntimeError("o texto nao entrou na caixa do pedido")
                # botao 'Iniciar geracao': icone arrow_forward EXATO ('Mostrar raciocinio' tem arrow_forward_ios)
                enviar = page.locator("button").filter(has_text=re.compile(r"^\s*arrow_forward\s*$")).last
                enviar.wait_for(state="visible", timeout=8000)
                for _ in range(20):  # fica desabilitado enquanto a foto termina de subir
                    if enviar.is_enabled():
                        break
                    page.wait_for_timeout(1000)
                enviar.click(timeout=8000)
                log("prompt submetido (botao Iniciar geracao)")
                page.wait_for_timeout(3000)
                # o Flow limpa a caixa quando recebe o pedido; se o texto ficou, o clique nao enviou
                resto = " ".join(_texto_caixa(page).split())
                if " ".join(final.split())[:40] in resto:
                    raise RuntimeError("o pedido continua na caixa (envio nao aconteceu)")
                break  # sucesso
            except SessaoExpiradaError as e:
                log(f"[SESSAO_EXPIRADA] parando tentativas. Login necessario.")
                raise
            except CreditosEsgotadosError as e:
                log(f"[CREDITOS] parando tentativas. {e}")
                raise
            except Exception as e:
                ultimo_erro = e
                log(f"[tentativa {tentativa}] falhou ao preparar/digitar: "
                    f"{type(e).__name__}: {str(e)[:80]}")
                # recarrega tela limpa e tenta de novo (dispensa modal residual)
                try:
                    page.goto(PROJ, wait_until="domcontentloaded")
                    page.wait_for_timeout(6000)
                    _dismiss_changelog_overlay(page, log)
                    page = flow_bot._ensure_workspace(page, log=log)
                except Exception:
                    pass
        else:
            raise RuntimeError(f"nao consegui enviar o prompt: {ultimo_erro}")

        # ESPERA PELO VIDEO (UI de 12/10/2026). CRITICO (bug md5 identico 03/07): NAO recarregar a pagina no loop — o
        # reload reembaralhava a grade e trazia videos VELHOS como "novos". Render Veo real NUNCA termina em segundos:
        # so tentamos baixar bloco novo (midia que nao estava na pagina antes do envio) apos MIN_ESPERA_S.
        MIN_ESPERA_S = 45
        SEM_SINAL_S = 480  # nenhum bloco novo nem progresso em 8 min: o pedido nao virou geracao
        # retry do erro transitorio "Algo deu errado" (lista p/ mutar no loop)
        _retry_erro = [0]
        _MAX_RETRY_ERRO = 3
        t0 = time.time()
        vistos = set(before)
        houve_sinal = False
        deadline = time.time() + config.GEN_TIMEOUT_S + 120

        def _tentar_baixar(novos):
            for k, it in novos.items():
                url = _video_do_bloco(page, it, log)
                if url:
                    log(f"bloco novo {k[:10]}... -> baixando")
                    if _baixar_url(page, url, out_path, log):
                        return True
                else:
                    log(f"bloco {k[:10]}... tag={it['tag']} src={it['src'][:60]}... (sem URL de video)")
            return False

        while time.time() < deadline:
            page.wait_for_timeout(config.POLL_S * 1000)
            body = ""
            try:
                body = page.evaluate("() => document.body.innerText") or ""
            except Exception:
                pass
            n_aprov = _aprovar_se_pedir(page, n_aprov, log)

            # === "Algo deu errado. Tente novamente" — erro TRANSITORIO do Flow ===
            # (nao e recusa de politica). Basta RE-SUBMETER o prompt que ele gera.
            # A dona confirmou: so apertar 'tentar novamente' resolve. Fazemos
            # ate _MAX_RETRY_ERRO vezes, sem reload (nao perde o projeto/sessao).
            if (("Algo deu errado" in body or "Something went wrong" in body or
                 "Tente novamente" in body or "Try again" in body)
                    and _retry_erro[0] < _MAX_RETRY_ERRO):
                _retry_erro[0] += 1
                log(f"[retry] 'Algo deu errado' detectado — re-submetendo "
                    f"({_retry_erro[0]}/{_MAX_RETRY_ERRO})")
                # 1) tenta um botao explicito de 'Tente novamente'/'Try again'
                clicou = page.evaluate("""() => {
                    const btns = Array.from(document.querySelectorAll('button, a'));
                    for (const b of btns) {
                        const t = (b.innerText||'').trim().toLowerCase();
                        if (t.includes('tente novamente') || t.includes('try again') ||
                            t.includes('tentar novamente')) {
                            b.click(); return t;
                        }
                    }
                    return null;
                }""")
                if not clicou:
                    # 2) senao, re-submete o prompt do zero (botao arrow_forward)
                    try:
                        btn = flow_bot._click_button_with_text(
                            page, flow_bot.SUBMIT_TEXT_HINTS, timeout=5000)
                        if btn:
                            btn.click(force=True)
                            log("[retry] prompt re-submetido (arrow_forward)")
                    except Exception:
                        pass
                else:
                    log(f"[retry] cliquei em '{clicou}'")
                # reseta o relogio da espera pra dar tempo ao novo render
                t0 = time.time()
                page.wait_for_timeout(4000)
                continue

            # === DETECCAO DE RECUSA POR POLITICA (copyright/famosos) ===
            # O Flow mostra um card "Falha - Esse comando pode violar nossas
            # politicas contra a geracao de imagens de pessoas famosas..."
            # NAO consome credito, mas TRAVA a geracao atual. Detectamos
            # cedo pra devolver o controle pro cron trocar prompt/foto.
            if (time.time() - t0) >= 15 and _tem_recusa_direitos(body):
                log(f"[DIREITOS] card de recusa por politica detectado em {int(time.time()-t0)}s")
                raise DireitosAutoraisError(
                    "Flow recusou por politica contra pessoas famosas / direitos autorais"
                )

            novos = {k: v for k, v in midias(page).items() if k not in vistos}
            if novos or re.search(r"\b\d{1,3}\s?%", body):
                houve_sinal = True
            if novos and (time.time() - t0) >= MIN_ESPERA_S and _tentar_baixar(novos):
                return out_path
            if not houve_sinal and (time.time() - t0) > SEM_SINAL_S:
                raise RuntimeError("nada comecou a gerar em 8 min (nenhum bloco novo nem progresso na tela)")
            log(f"...aguardando ({int(deadline - time.time())}s, blocos novos: {len(novos)})")

        # VARREDURA FINAL: tenta tudo que apareceu no ultimo momento
        log("deadline atingido — varredura final")
        if _tentar_baixar({k: v for k, v in midias(page).items() if k not in vistos}):
            return out_path

        raise RuntimeError("timeout sem video novo baixavel")

def _sistema_pausado():
    """Le logs/PAUSE_SYSTEM. True se pausa ativa (until no futuro OU sem until).
    Checa ANTES de abrir Chrome. Nao remove o arquivo (quem gerencia e o cron)."""
    if os.environ.get("SKIP_RESOURCE_CHECK") == "1":
        return False
    import json as _json
    pause_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", "PAUSE_SYSTEM")
    if not os.path.exists(pause_file):
        return False
    try:
        with open(pause_file, "r", encoding="utf-8") as f:
            data = _json.load(f)
        until = data.get("until")
        if not until:
            # 23/10: pausa por carga do PC1 + cron mandou "so notebook" = o Chrome abre na maquina, nao aqui
            # 24/10: MS Energy (02:21) parou assim com conta so-notebook — essas nunca abrem Chrome aqui
            if data.get("tipo") == "carga":
                # 01/11: carga = só o PC1 sai (o cron do Veo segue nos notebooks/desktop/PC2). Antes qualquer conta
                # logada também no PC1 parava aqui com exit 5 e as solares ficavam sem Reel a tarde inteira; agora
                # gera só fora do PC1 (gerar() não cai para cá com VEO_SO_NOTEBOOK=1)
                os.environ["VEO_SO_NOTEBOOK"] = "1"
                return False
            return True
        return datetime.datetime.now() < datetime.datetime.fromisoformat(until)
    except Exception:
        return True


if __name__ == "__main__":
    # PAUSA REAL: aborta ANTES de abrir Chrome se o sistema esta pausado.
    if _sistema_pausado():
        print("SISTEMA_PAUSADO", flush=True)
        sys.exit(5)  # exit code 5 = pausado (cron ignora sem penalizar a conta)
    # uso: gera_auto.py "prompt" saida.mp4 [imagem_inicial.jpg]
    prompt = sys.argv[1] if len(sys.argv) > 1 else \
        "A cute orange cat walking slowly through a sunny garden, cinematic, high detail"
    out = sys.argv[2] if len(sys.argv) > 2 else \
        os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "videos", "teste_haylla", "teste1.mp4")
    img = sys.argv[3] if len(sys.argv) > 3 else None
    os.makedirs(os.path.dirname(out), exist_ok=True)
    try:
        gerar(prompt, out, image=img,
              aspect=os.environ.get("FLOW_ASPECT", "9:16"),
              modelo=os.environ.get("FLOW_MODEL", "Veo 3.1 - Fast"),
              duration=os.environ.get("FLOW_DURATION", "8S"))
    except CreditosEsgotadosError as e:
        # Marcador detectado pelo cron_gerar_video_llm.py
        # Extrai padrao da mensagem
        import re as _re
        m = _re.search(r"padrao='([^']*)'", str(e))
        padrao = m.group(1) if m else ""
        print(f"CREDITOS_ESGOTADOS padrao='{padrao}'", flush=True)
        sys.exit(2)  # exit code 2 = creditos esgotados
    except SessaoExpiradaError as e:
        print(f"SESSAO_EXPIRADA url='{e}'", flush=True)
        sys.exit(3)
    except RecaptchaError as e:
        print(f"RECAPTCHA_BLOQUEIO", flush=True)
        sys.exit(7)
    except DireitosAutoraisError as e:
        # Marcador p/ cron distinguir de falha normal: NAO re-enfileirar igual.
        print(f"DIREITOS_AUTORAIS '{e}'", flush=True)
        sys.exit(4)  # exit code 4 = recusado por politica/direitos
