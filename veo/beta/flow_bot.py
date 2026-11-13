#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bot do Flow (labs.google/fx) — dirige o site logado pra gerar video.

O Flow e um AGENTE CONVERSACIONAL (ver FLOW_CAPABILITIES.md):
  - endpoint aisandbox-pa/v1/flowCreationAgent/sessions/{id}
  - o agente le o prompt e DECIDE modelo/modo/formato pelo texto
  - o painel "Configuracoes" (icone tune) controla aspect ratio (16:9/9:16) e duracao (1x-4x)
  - "Confirmar antes de gerar = Nunca" faz gerar automatico sem clique extra

Estrategia:
  - carrega storage_state da sessao capturada
  - (opcional) abre Configuracoes e ajusta ratio/duracao
  - (opcional) sobe imagem pra image-to-video
  - escreve o prompt (enriquecido com model/audio hints), submete
  - fareja a REDE: captura URLs de video (.mp4 / fife / videoUri)
  - baixa o mp4 pro OUTPUT_DIR

Uso direto (teste):
    python flow_bot.py <apelido> "meu prompt aqui"
"""
import sys, os, re, json, time, subprocess, urllib.request
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
import config

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
_BASE_CDP_PORT = 9300  # portas CDP: 9300, 9301, 9302... (uma por conta)

VIDEO_URL_RE = re.compile(r'https?://[^\s"\']+\.mp4[^\s"\']*', re.I)
VIDEO_URI_RE = re.compile(r'"videoUri"\s*:\s*"(https?://[^"]+)"', re.I)

# ---- seletores confirmados na UI atual (2026-08-28) ----
# O Flow migrou pra Slate.js rich text editor (div[data-slate-editor]).
# [data-slate-editor] e o seletor mais especifico e estavel.
PROMPT_SELECTORS = [
    "[data-slate-editor]",
    "div[role='textbox'][contenteditable='true']",
    "[contenteditable='true']",
    "textarea",
    "input[type='text']",
    "[placeholder*='prompt' i]",
    "[aria-label*='prompt' i]",
]
# botao de gerar: o Flow usa um [role=button] com icone material "arrow_forward" + "Criar".
# NAO usar "Gerar"/"Create"/"Generate" soltos: casam com chips de sugestao
# (ex.: "Gerar arte conceitual"), disparando o elemento errado.
SUBMIT_TEXT_HINTS = ["arrow_forward"]

# aspect ratio -> texto do radio no painel de video
RATIO_RADIO = {
    "PORTRAIT": "9:16",
    "9:16": "9:16",
    "LANDSCAPE": "16:9",
    "16:9": "16:9",
}
# duracao aproximada -> multiplicador de radio (1x mais curto ... x4 mais longo)
DURATION_RADIO = {
    "4S": "1x",
    "6S": "x2",
    "8S": "x3",
    "10S": "x4",
}


def _nuke_changelog(page, log=print):
    """Instala MutationObserver persistente que remove iframes de changelog do Google Flow.
    O React re-injeta o overlay; o observer remove automaticamente.
    CUIDADO: nao remove divs que possam conter prompt box (contenteditable)
    — usa delay pra dar tempo do React renderizar filhos."""
    try:
        page.evaluate("""() => {
            if (window.__changelogNuked) return;
            window.__changelogNuked = true;
            function nuke() {
                document.querySelectorAll('iframe.sc-181bed44-4, iframe[src*="changelogs"]').forEach(f => {
                    try {
                        let target = f.parentElement || f;
                        if (target.querySelector && target.querySelector('[data-slate-editor], [contenteditable="true"]')) {
                            f.remove();
                        } else {
                            target.remove();
                        }
                    } catch(e){}
                });
                document.querySelectorAll('div.sc-1c6805c6-0').forEach(d => {
                    if (d.querySelector && d.querySelector('[data-slate-editor], [contenteditable="true"]')) return;
                    if (d.querySelector && d.querySelector('textarea, input, [role="textbox"]')) return;
                    try { d.remove(); } catch(e){}
                });
            }
            function safeNuke() {
                setTimeout(nuke, 600);
            }
            nuke();
            new MutationObserver(safeNuke).observe(document.body, {childList: true, subtree: true});
        }""")
        log("[flow] _nuke_changelog: MutationObserver instalado")
    except Exception as e:
        log(f"[flow] _nuke_changelog falhou (nao-fatal): {e}")


def _find_first(page, selectors, timeout=8000):
    for sel in selectors:
        try:
            el = page.wait_for_selector(sel, timeout=timeout, state="visible")
            if el:
                return el, sel
        except PWTimeout:
            continue
    return None, None


def _click_button_with_text(page, hints, timeout=5000):
    """Acha o 1o elemento clicavel visivel cujo texto/aria contem algum dos hints.
    Inclui <button> E [role=button] (o Flow usa divs role=button, ex.: submit
    'arrow_forward Criar')."""
    deadline = time.time() + timeout / 1000
    while time.time() < deadline:
        for btn in page.query_selector_all("button, [role=button]"):
            try:
                if not btn.is_visible():
                    continue
                txt = ((btn.inner_text() or "") + " " +
                       (btn.get_attribute("aria-label") or ""))
                if any(h in txt for h in hints):
                    return btn
            except Exception:
                continue
        page.wait_for_timeout(300)
    return None


def _enrich_prompt(prompt, model=None, audio=None, duration=None, aspect_ratio=None):
    """O agente respeita overrides escritos no texto do prompt.
    Usa linguagem direta e imperativa pra maximizar compliance."""
    extra = []
    if aspect_ratio:
        ratio = {"PORTRAIT": "9:16", "9:16": "9:16",
                 "LANDSCAPE": "16:9", "16:9": "16:9"}.get(aspect_ratio.upper())
        if ratio:
            orient = "vertical portrait" if ratio == "9:16" else "horizontal landscape"
            extra.append(f"aspect ratio MUST be {ratio} ({orient})")
    if duration:
        secs = {"4S": "4", "6S": "6", "8S": "8", "10S": "10"}.get(duration, "8")
        extra.append(f"video duration: {secs} seconds")
    if model:
        extra.append(f"use {model} model")
    if audio is True:
        extra.append("MUST include audio/sound")
    elif audio is False:
        extra.append("no audio, completely silent")
    if not extra:
        return prompt
    return f"{prompt.rstrip('. ')}. [{'; '.join(extra)}]"


LANDING_PAGE_BUTTONS = [
    "Create with Google Flow",
    "Criar com o Google Flow",
    "Criar com Google Flow",
    "Create with Flow",
]

WELCOME_BUTTONS = [
    "Try Flow", "Experimentar o Flow", "Experimentar",
    "Accept", "Aceitar", "Concordo", "I agree",
    "Continue", "Continuar", "Got it", "Entendi",
]


def _find_welcome_button(page):
    """Procura botões da tela intermediária de boas-vindas/consentimento."""
    for btn in page.query_selector_all("button, [role=button], a"):
        try:
            if not btn.is_visible():
                continue
            href = (btn.get_attribute("href") or "")
            if href.startswith("#"):
                continue
            txt = (btn.inner_text() or "").strip()
            if any(h.lower() in txt.lower() for h in WELCOME_BUTTONS):
                return btn, txt
        except Exception:
            continue
    return None, None


def _ensure_workspace(page, log=print, max_retries=6):
    """Detecta o estado da pagina e navega pro workspace do Flow.

    Trata 4 estados:
      1) Landing page (marketing) -> clica CTA
      2) Boas-vindas/consentimento -> clica "Try Flow"
      3) Workspace (prompt box) -> retorna direto
      4) OAuth account chooser (accounts.google.com) -> clica na conta ou volta pro Flow
    """
    ctx = page.context
    _log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(_log_dir, exist_ok=True)

    _nuke_changelog(page, log)

    for attempt in range(max_retries):
        # --- Estado 4: OAuth account chooser (accounts.google.com) ---
        if "accounts.google.com" in page.url:
            log(f"[flow] OAuth account chooser detectado (tentativa {attempt+1}): {page.url[:120]}")
            # tentar clicar na conta que aparece (div[data-identifier], li com email)
            acct_clicked = False
            for sel in ["div[data-identifier]", "[data-email]", "li[data-authuser]", "#identifierId"]:
                try:
                    el = page.query_selector(sel)
                    if el and el.is_visible():
                        txt = (el.inner_text() or "").strip()[:60]
                        log(f"[flow] clicando conta OAuth: {sel} -> '{txt}'")
                        el.click(force=True)
                        page.wait_for_timeout(8000)
                        acct_clicked = True
                        break
                except Exception:
                    continue
            if not acct_clicked:
                # sem contas visiveis — voltar pro Flow direto
                log("[flow] OAuth sem contas visiveis — voltando pro Flow")
                try:
                    _diag = os.path.join(_log_dir, f"workspace_oauth_diag_{attempt}.png")
                    page.screenshot(path=_diag)
                    log(f"[flow] screenshot OAuth: {_diag}")
                except Exception:
                    pass
                page.goto("https://labs.google/fx/tools/flow", wait_until="domcontentloaded")
                page.wait_for_timeout(8000)
            continue

        box, _ = _find_first(page, PROMPT_SELECTORS, timeout=5000)
        if box:
            log("[flow] workspace detectado (prompt box presente)")
            return page

        # --- Estado 2: tela de boas-vindas/consentimento ---
        wb, wb_txt = _find_welcome_button(page)
        if wb:
            log(f"[flow] tela de boas-vindas detectada (tentativa {attempt+1}), clicando '{wb_txt}'...")
            try:
                _diag = os.path.join(_log_dir, "workspace_welcome_diag.png")
                page.screenshot(path=_diag)
                log(f"[flow] screenshot pre-welcome: {_diag}")
            except Exception:
                pass
            pages_before = len(ctx.pages)
            wb.click(force=True)
            try:
                page.wait_for_load_state("networkidle", timeout=30000)
            except Exception:
                page.wait_for_timeout(8000)
            if len(ctx.pages) > pages_before:
                page = ctx.pages[-1]
                page.wait_for_load_state("domcontentloaded")
                page.wait_for_timeout(3000)
                log(f"[flow] welcome abriu nova aba, switchando...")

            # --- diagnóstico pós-welcome ---
            log(f"[flow] DIAG pos-welcome: url={page.url}")
            try:
                _diag_post = os.path.join(_log_dir, "workspace_post_welcome_diag.png")
                page.screenshot(path=_diag_post)
                log(f"[flow] screenshot pos-welcome: {_diag_post}")
            except Exception:
                pass

            box2, _ = _find_first(page, PROMPT_SELECTORS, timeout=10000)
            if box2:
                log("[flow] workspace ativo apos welcome")
                return page

            # procurar prompt box em cada frame
            for fi, fr in enumerate(page.frames):
                if fi == 0:
                    continue
                try:
                    box2, _ = _find_first(fr, PROMPT_SELECTORS, timeout=3000)
                    if box2:
                        log(f"[flow] workspace ativo apos welcome (frame[{fi}])")
                        return page
                except Exception:
                    continue

            # enumerar todos os botões visíveis pra diagnóstico
            try:
                visible_btns = []
                for btn in page.query_selector_all("button, [role=button], a"):
                    try:
                        if not btn.is_visible():
                            continue
                        txt = (btn.inner_text() or "").strip()[:80]
                        href = (btn.get_attribute("href") or "")[:80]
                        tag = btn.evaluate("el => el.tagName")
                        if txt:
                            visible_btns.append(f"{tag}|{txt}|href={href}")
                    except Exception:
                        continue
                if visible_btns:
                    log(f"[flow] DIAG {len(visible_btns)} botoes visiveis:")
                    for b in visible_btns[:20]:
                        log(f"[flow]   {b}")
            except Exception:
                pass

            page.wait_for_timeout(5000)
            log("[flow] welcome clicado mas prompt box nao encontrado, continuando...")
            continue

        # --- Estado 1: landing page ---
        cta = None
        for btn in page.query_selector_all("button, [role=button], a"):
            try:
                if not btn.is_visible():
                    continue
                txt = (btn.inner_text() or "").strip()
                if any(h.lower() in txt.lower() for h in LANDING_PAGE_BUTTONS):
                    cta = btn
                    break
            except Exception:
                continue

        if not cta:
            for link in page.query_selector_all("a[href]"):
                try:
                    if not link.is_visible():
                        continue
                    txt = (link.inner_text() or "").strip()
                    href = link.get_attribute("href") or ""
                    if any(h.lower() in txt.lower() for h in LANDING_PAGE_BUTTONS):
                        cta = link
                        break
                    if "/create" in href and "flow" in href.lower():
                        cta = link
                        break
                except Exception:
                    continue

        if cta:
            log(f"[flow] landing page detectada (tentativa {attempt+1}), clicando CTA...")
            pages_before = len(ctx.pages)
            cta.click(force=True)
            page.wait_for_timeout(15000)

            try:
                _diag = os.path.join(_log_dir, "workspace_post_cta_diag.png")
                page.screenshot(path=_diag)
                log(f"[flow] screenshot pos-CTA: {_diag}")
            except Exception:
                pass

            if len(ctx.pages) > pages_before:
                new_page = ctx.pages[-1]
                log(f"[flow] CTA abriu nova aba ({len(ctx.pages)} abas agora), switchando...")
                new_page.wait_for_load_state("domcontentloaded")
                new_page.wait_for_timeout(5000)
                box2, _ = _find_first(new_page, PROMPT_SELECTORS, timeout=10000)
                if box2:
                    log("[flow] workspace ativo na nova aba")
                    return new_page
                page = new_page
                continue

            wb2, wb2_txt = _find_welcome_button(page)
            if wb2:
                log(f"[flow] tela de boas-vindas pos-CTA detectada, clicando '{wb2_txt}'...")
                wb2.click(force=True)
                page.wait_for_timeout(8000)
                box2, _ = _find_first(page, PROMPT_SELECTORS, timeout=10000)
                if box2:
                    log("[flow] workspace ativo apos welcome (pos-CTA)")
                    return page
                continue

            box2, _ = _find_first(page, PROMPT_SELECTORS, timeout=5000)
            if box2:
                log("[flow] workspace ativo apos CTA (mesma aba)")
                return page

            # espera extra — a página pode estar carregando SPA
            log(f"[flow] pos-CTA: nada encontrado ainda, esperando mais 10s...")
            page.wait_for_timeout(10000)
            box2, _ = _find_first(page, PROMPT_SELECTORS, timeout=10000)
            if box2:
                log("[flow] workspace ativo apos CTA (espera extra)")
                return page

            # diagnóstico: enumerar TUDO visível pra entender o estado da página
            log(f"[flow] DIAG pos-CTA: url={page.url}")
            try:
                visible_btns = []
                for btn in page.query_selector_all("button, [role=button], a, [contenteditable], textarea, input"):
                    try:
                        if not btn.is_visible():
                            continue
                        txt = (btn.inner_text() or "").strip()[:80]
                        href = (btn.get_attribute("href") or "")[:80]
                        tag = btn.evaluate("el => el.tagName")
                        role = (btn.get_attribute("role") or "")
                        ph = (btn.get_attribute("placeholder") or "")[:60]
                        aria = (btn.get_attribute("aria-label") or "")[:60]
                        ce = btn.get_attribute("contenteditable") or ""
                        info = f"{tag}|txt={txt}|href={href}|role={role}|ph={ph}|aria={aria}|ce={ce}"
                        visible_btns.append(info)
                    except Exception:
                        continue
                log(f"[flow] DIAG {len(visible_btns)} elementos visiveis pos-CTA:")
                for b in visible_btns[:30]:
                    log(f"[flow]   {b}")
                if not visible_btns:
                    log("[flow] DIAG: nenhum elemento interativo visivel!")
            except Exception as diag_err:
                log(f"[flow] DIAG falhou: {diag_err}")

            # screenshot do estado final antes de tentar de novo
            try:
                _diag2 = os.path.join(_log_dir, f"workspace_post_cta_diag2_{attempt}.png")
                page.screenshot(path=_diag2)
                log(f"[flow] screenshot diag2: {_diag2}")
            except Exception:
                pass

            continue

        # --- Estado 5: lista de projetos (tem "Novo projeto" mas não tem prompt box) ---
        novo_proj = None
        for btn in page.query_selector_all("button, [role=button], a"):
            try:
                if not btn.is_visible():
                    continue
                txt = (btn.inner_text() or "").strip()
                if any(kw in txt for kw in ["Novo projeto", "New project", "Create new"]):
                    novo_proj = btn
                    break
            except Exception:
                continue

        if novo_proj:
            log(f"[flow] lista de projetos detectada (tentativa {attempt+1}), clicando 'Novo projeto'...")
            # Desabilitar nuke temporariamente pra nao matar o prompt box durante transicao
            try:
                page.evaluate("() => { window.__changelogNuked = false; }")
            except Exception:
                pass
            novo_proj.click(force=True)
            page.wait_for_timeout(15000)
            # Re-instalar nuke com delay seguro
            _nuke_changelog(page, log)
            box5, _ = _find_first(page, PROMPT_SELECTORS, timeout=30000)
            if box5:
                log("[flow] workspace ativo apos criar novo projeto")
                return page
            # Fallback: tentar navegar direto pra URL de criacao
            log("[flow] clicou 'Novo projeto' mas prompt box nao apareceu — tentando URL direta...")
            try:
                page.goto("https://labs.google/fx/pt/tools/flow/new", wait_until="domcontentloaded")
                page.wait_for_timeout(10000)
                _nuke_changelog(page, log)
                box5b, _ = _find_first(page, PROMPT_SELECTORS, timeout=20000)
                if box5b:
                    log("[flow] workspace ativo via URL direta /flow/new")
                    return page
            except Exception as e:
                log(f"[flow] fallback URL direta falhou: {e}")
            continue

        log("[flow] nem prompt box, nem welcome, nem CTA, nem lista de projetos — reload")
        # diagnóstico rápido antes do reload
        log(f"[flow] DIAG pre-reload: url={page.url}")
        try:
            vis = []
            for el in page.query_selector_all("button, [role=button], a"):
                try:
                    if not el.is_visible():
                        continue
                    txt = (el.inner_text() or "").strip()[:60]
                    tag = el.evaluate("el => el.tagName")
                    if txt:
                        vis.append(f"{tag}|{txt}")
                except Exception:
                    continue
            if vis:
                log(f"[flow] DIAG {len(vis)} botoes pre-reload: {'; '.join(vis[:15])}")
        except Exception:
            pass
        page.reload(wait_until="domcontentloaded")
        page.wait_for_timeout(8000)

    box, _ = _find_first(page, PROMPT_SELECTORS, timeout=10000)
    if box:
        log("[flow] workspace ativo apos navegacao")
        return page
    log("[flow] WARN: nao conseguiu sair da landing page")
    return page


def _select_radio(page, target, label, log):
    """Clica num radio de forma robusta e confirma que ficou selecionado."""
    for attempt, method in enumerate(("normal", "force", "js")):
        try:
            target.scroll_into_view_if_needed(timeout=2000)
        except Exception:
            pass
        try:
            if method == "js":
                target.evaluate("el => el.click()")
            else:
                target.click(force=(method == "force"), timeout=3000)
        except Exception as e:
            log(f"[flow] clique {method} em '{label}' falhou: {type(e).__name__}")
            continue
        page.wait_for_timeout(400)
        if target.get_attribute("aria-selected") == "true":
            log(f"[flow] {label} selecionado (via {method})")
            return True
    log(f"[flow] AVISO: nao consegui selecionar '{label}'")
    return False


def _set_settings(page, aspect_ratio=None, duration=None, auto_confirm=True, log=print):
    """Abre o painel Configuracoes e ajusta ratio/duracao/confirmacao."""
    if not (aspect_ratio or duration or auto_confirm):
        return
    btn = _click_button_with_text(page, ["tune", "Configura", "Settings", "Configurações"], timeout=8000)
    if not btn:
        log("[flow] painel Configuracoes nao encontrado (tune) — usando defaults")
        return
    btn.click(force=True)
    page.wait_for_timeout(1500)

    radios = page.query_selector_all('[role="radio"], [aria-selected]')
    log(f"[flow] painel aberto: {len(radios)} radios/toggles encontrados")
    for r in radios:
        try:
            t = (r.inner_text() or "").strip().replace("\n", " ")[:30]
            sel = r.get_attribute("aria-selected")
            if t:
                log(f"[flow]   radio '{t}' selected={sel}")
        except Exception:
            pass
    # confirmacao automatica: clicar "Nunca"
    if auto_confirm:
        for r in radios:
            txt = (r.inner_text() or "")
            if "Nunca" in txt and (r.get_attribute("aria-selected") == "false"):
                _select_radio(page, r, "confirmar-antes-de-gerar=Nunca", log)
                break

    # aspect ratio: as opcoes podem ser [role=radio] OU [aria-selected] (divs).
    # o grupo de VIDEO fica mais abaixo na pagina (y maior).
    RADIO_SEL = '[role="radio"], [aria-selected]'
    if aspect_ratio:
        want = RATIO_RADIO.get(aspect_ratio.upper(), None)
        if want:
            candidates = [r for r in page.query_selector_all(RADIO_SEL)
                          if want in (r.inner_text() or "")]
            if candidates:
                target = sorted(candidates,
                                key=lambda e: e.bounding_box()["y"] if e.bounding_box() else 0)[-1]
                _select_radio(page, target, f"aspect ratio {want}", log)
            else:
                log(f"[flow] AVISO: radio de ratio '{want}' nao encontrado")

    # duracao (grupo de video, radios 1x..x4 mais abaixo)
    if duration:
        want = DURATION_RADIO.get(duration.upper(), None)
        if want:
            candidates = [r for r in page.query_selector_all(RADIO_SEL)
                          if (r.inner_text() or "").strip() == want]
            if candidates:
                target = sorted(candidates,
                                key=lambda e: e.bounding_box()["y"] if e.bounding_box() else 0)[-1]
                _select_radio(page, target, f"duracao {want} ({duration})", log)
            else:
                log(f"[flow] AVISO: radio de duracao '{want}' nao encontrado")

    # fechar o painel (Esc costuma funcionar)
    try:
        page.keyboard.press("Escape")
    except Exception:
        pass
    page.wait_for_timeout(500)


def _upload_image(page, image_path, log=print):
    """Sobe imagem/video via 'Add Media' / 'Adicionar mídia' (atualizado 08/2026)."""
    if not image_path or not os.path.exists(image_path):
        return False
    hints = ["Add Media", "Adicionar mídia", "Adicionar", "Add", "mídia", "media"]
    btn = _click_button_with_text(page, hints, timeout=10000)
    inp = None
    if btn:
        btn.click(force=True)
        page.wait_for_timeout(2000)
    else:
        log("[flow] botao Add Media nao encontrado — tentando input direto")
    try:
        inp = page.wait_for_selector("input[type='file']", timeout=8000, state="attached")
    except PWTimeout:
        inp = page.query_selector("input[type='file']")
    if inp:
        inp.set_input_files(image_path)
        page.evaluate("""(el) => {
            el.dispatchEvent(new Event('change', {bubbles: true}));
            el.dispatchEvent(new Event('input', {bubbles: true}));
        }""", inp)
        log(f"[flow] midia enviada + change: {image_path}")
        page.wait_for_timeout(5000)
        return True
    log("[flow] input de arquivo nao encontrado — upload ignorado")
    return False


_ACCOUNT_PORTS = {}
_NEXT_PORT_IDX = 0

def _account_port(apelido):
    """Porta CDP fixa por conta (deterministica via hashlib, não hash())."""
    global _NEXT_PORT_IDX
    if apelido not in _ACCOUNT_PORTS:
        import hashlib
        idx = int(hashlib.md5(apelido.encode()).hexdigest(), 16) % 100
        _ACCOUNT_PORTS[apelido] = _BASE_CDP_PORT + idx
    return _ACCOUNT_PORTS[apelido]


def _ensure_chrome(apelido, port, log=print):
    """Abre Chrome real com CDP se nao estiver rodando na porta."""
    url = f"http://127.0.0.1:{port}/json/version"
    try:
        with urllib.request.urlopen(url, timeout=2):
            log(f"[cdp] Chrome ja rodando na porta {port}")
            return None
    except Exception:
        pass
    profile = os.path.join(config.BASE, f"chrome_gen_{apelido}")
    os.makedirs(profile, exist_ok=True)
    sess = os.path.join(config.SESSIONS_DIR, f"{apelido}.json")
    args = [
        CHROME,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={profile}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-background-timer-throttling",
        "--disable-renderer-backgrounding",
    ]
    log(f"[cdp] abrindo Chrome real na porta {port} (perfil {profile})")
    proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    deadline = time.time() + 15
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2):
                log(f"[cdp] Chrome pronto na porta {port}")
                return proc
        except Exception:
            time.sleep(0.5)
    raise RuntimeError(f"Chrome nao subiu na porta {port} em 15s")


def _restore_session(ctx, apelido, log=print):
    """Carrega cookies da sessao capturada no contexto do Chrome real."""
    sess = os.path.join(config.SESSIONS_DIR, f"{apelido}.json")
    if not os.path.exists(sess):
        raise RuntimeError(f"sessao '{apelido}' nao existe. Rode chrome_cdp.py capture {apelido}")
    with open(sess, encoding="utf-8") as f:
        data = json.load(f)
    cookies = data.get("cookies", [])
    if cookies:
        ctx.add_cookies(cookies)
        log(f"[cdp] {len(cookies)} cookies restaurados pra {apelido}")


def generate(apelido, prompt, *a, **kw):
    """Conta ativada nos notebooks (D:\\postador-de-videos\\bin\\maquina_remota.py ativar): gera pelo Chrome LOGADO de
    lá — o PC1 só espera (dono 22/10: "o Flow também; os projetos que usam navegador usam os mesmos logins"). Notebook
    fora/ocupado ou conta não ativada: gera aqui como sempre."""
    log = kw.get("log") or (a[1] if len(a) > 1 else print)
    # 23/10 (dona): conta logada nos notebooks gera por eles; erro num = o outro; erro de novo (ou conta fora) = aqui
    try:
        sys.path.insert(0, r"D:\postador-de-videos\bin")
        import maquina_remota
        maqs = maquina_remota.maquinas_flow(apelido)
        ordem = maquina_remota.tentativas(maqs, apelido.lower(), log_fn=log) if maqs else iter([None])
    except Exception as e:  # noqa: BLE001
        log(f"[flow] notebooks indisponíveis ({e}) — gera aqui")
        ordem = iter([None])
    try:
        for rem in ordem:
            if rem is None:
                return _generate(apelido, prompt, *a, **kw)
            log(f"[flow] gerando pelo Chrome do {rem.nome}")
            try:
                return _generate(apelido, prompt, *a, _porta=rem.porta_local, **kw)
            except Exception as e:  # noqa: BLE001
                # revisão 23/10: só troca de máquina se a falha foi de CONEXÃO com o Chrome. Erro depois de pedir o
                # vídeo (timeout sem vídeo, download) já gastou crédito — gerar de novo em outra máquina gastaria 2x.
                txt = f"{type(e).__name__}: {e}"
                if not re.search(r"connect|Target (page, context or browser )?closed|Browser has been closed|"
                                 r"ECONNREFUSED|WebSocket|túnel|tunel", txt, re.I):
                    raise
                log(f"[flow] falhou no {rem.nome} ({txt[:120]}) — tento na próxima máquina")
    finally:
        if hasattr(ordem, "close"):
            ordem.close()


def _generate(apelido, prompt, out_path=None, log=print,
              aspect_ratio=None, duration=None, model=None, audio=None,
              image=None, auto_confirm=True, _porta=None):
    """
    Gera um video no Flow usando Chrome real via CDP.
      aspect_ratio: 'PORTRAIT'/'9:16' ou 'LANDSCAPE'/'16:9'
      duration: '4S'|'6S'|'8S'|'10S'
      model: ex 'Veo 3.1' (dica textual pro agente)
      audio: True/False/None (None = padrao do modelo)
      image: caminho local -> image-to-video
      auto_confirm: seta 'Nunca confirmar' pra gerar sem clique extra
    """
    sess = os.path.join(config.SESSIONS_DIR, f"{apelido}.json")
    if not _porta and not os.path.exists(sess):
        raise RuntimeError(f"sessao '{apelido}' nao existe. Rode chrome_cdp.py capture {apelido}")
    url_file = os.path.join(config.SESSIONS_DIR, f"{apelido}.url.txt")
    start_url = config.FLOW_URL
    if os.path.exists(url_file):
        start_url = open(url_file, encoding="utf-8").read().strip() or start_url

    found_videos = []
    _capture_active = False  # so captura apos submit

    def on_response(resp):
        if not _capture_active:
            return
        try:
            ct = resp.headers.get("content-type", "")
            u = resp.url
            if u.lower().endswith(".mp4") or "video/mp4" in ct:
                found_videos.append(u)
                return
            if ("labs.google" in u or "aisandbox" in u or "googleusercontent" in u):
                if ct.startswith("application/json") or "text" in ct:
                    body = resp.text()
                    for m in VIDEO_URL_RE.findall(body):
                        found_videos.append(m)
                    for m in VIDEO_URI_RE.findall(body):
                        if m not in found_videos:
                            found_videos.append(m)
        except Exception:
            pass

    port = _porta or _account_port(apelido)
    chrome_proc = None if _porta else _ensure_chrome(apelido, port, log=log)

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
        ctx = browser.contexts[0] if browser.contexts else browser.new_context()
        if not _porta:  # no notebook o perfil já é logado lá: não leva cookie salvo deste PC pra outra máquina
            _restore_session(ctx, apelido, log=log)
        page = ctx.new_page()
        page.on("response", on_response)
        log(f"[flow] abrindo {start_url}")
        page.goto(start_url, wait_until="domcontentloaded")
        page.wait_for_timeout(6000)

        _nuke_changelog(page, log)
        page = _ensure_workspace(page, log=log)
        page.on("response", on_response)

        # tirar screenshot antes de qualquer acao (debug)
        shot_pre = os.path.join(config.LOG_DIR, f"{apelido}_pre_settings.png")
        page.screenshot(path=shot_pre)
        log(f"[flow] screenshot pre-settings: {shot_pre}")

        # NAO abrir "Nova conversa": no Flow atual isso navega pro modo
        # Nano Banana (imagem), que NAO tem o botao de submit de video
        # (arrow_forward Criar). A deteccao de video novo ja e feita pelo
        # diff de posters (posters_before), entao nao precisamos de nova
        # conversa pra evitar capturar video antigo.

        # 2) NAO mexer em NENHUM radio do painel (ratio, duracao OU o
        # "Nunca"/confirmar): qualquer clique de radio switcha o compositor
        # pro modo Nano Banana (imagem), fazendo sumir o botao de submit de
        # video (arrow_forward Criar). Em vez disso confiamos no _enrich_prompt
        # (adiciona "9:16 vertical portrait aspect ratio" e "N-second video"
        # ao texto — o agente do Flow respeita instrucoes de texto).
        # Pulamos _set_settings por completo.
        log("[flow] settings via prompt (painel de radios switcha p/ imagem)")

        # 3) image-to-video (se pedido)
        if image:
            _upload_image(page, image, log=log)

        # 4) escrever o prompt (enriquecido)
        final_prompt = _enrich_prompt(prompt, model=model, audio=audio,
                                      duration=duration, aspect_ratio=aspect_ratio)
        box, bsel = _find_first(page, PROMPT_SELECTORS, timeout=15000)
        if not box:
            # Chrome frio: a pagina pode subir preta/vazia e o compositor so
            # renderiza depois. Recarrega e tenta de novo antes de desistir.
            log("[flow] caixa nao apareceu; reload + retry (chrome frio?)")
            page.reload(wait_until="domcontentloaded")
            page.wait_for_timeout(8000)
            box, bsel = _find_first(page, PROMPT_SELECTORS, timeout=20000)
        if not box:
            # pode estar na landing/lista de projetos apos timeout/navegacao
            log("[flow] caixa nao apareceu apos reload; tentando _ensure_workspace")
            try:
                page = _ensure_workspace(page, log=log)
                box, bsel = _find_first(page, PROMPT_SELECTORS, timeout=20000)
            except Exception as ew:
                log(f"[flow] _ensure_workspace falhou: {ew}")
        if not box:
            shot = os.path.join(config.LOG_DIR, f"{apelido}_noprompt.png")
            page.screenshot(path=shot)
            browser.close()
            raise RuntimeError(f"nao achei caixa de prompt. screenshot: {shot}")
        log(f"[flow] caixa de prompt: {bsel}")
        box.click(force=True)
        if bsel == "[contenteditable='true']":
            box.type(final_prompt)
        else:
            box.fill(final_prompt)
        page.wait_for_timeout(500)

        # snapshot dos posters ja existentes (pra detectar o NOVO video)
        def _poster_ids():
            try:
                return set(page.evaluate(
                    """() => Array.from(document.querySelectorAll('img[src*=getMediaUrlRedirect]'))
                        .map(i => { const m = i.src.match(/name=([0-9a-f-]+)/i); return m ? m[1] : null; })
                        .filter(Boolean)"""
                ) or [])
            except Exception:
                return set()
        posters_before = _poster_ids()
        log(f"[flow] posters antes do submit: {len(posters_before)}")

        # 5) submeter — AGORA ativa captura de video
        _capture_active = True
        btn = _click_button_with_text(page, SUBMIT_TEXT_HINTS, timeout=5000)
        if btn:
            log("[flow] submetendo (botao gerar)")
            btn.click(force=True)
        else:
            log("[flow] sem botao claro, tentando Enter")
            box.press("Enter")

        # screenshot apos submit (debug, nunca fatal)
        page.wait_for_timeout(2000)
        shot_post = os.path.join(config.LOG_DIR, f"{apelido}_post_submit.png")
        try:
            page.screenshot(path=shot_post, timeout=8000)
            log(f"[flow] screenshot pos-submit: {shot_post}")
        except Exception as e:
            log(f"[flow] screenshot pos-submit falhou (ignorado): {type(e).__name__}")

        # 6) esperar o NOVO video renderizar e baixar via botao "Baixar".
        # O Flow NAO expoe <video>/mp4 direto: cada clip vira um <img> poster
        # (getMediaUrlRedirect?name=UUID). Detectamos o poster NOVO (que nao
        # existia antes do submit), clicamos nele e usamos o botao de download
        # nativo (page.expect_download) — que espelha o humano e e confiavel.
        if not out_path:
            out_path = os.path.join(config.OUTPUT_DIR, f"flow_{int(time.time())}.mp4")

        # a galeria de posters NAO atualiza sozinha na mesma sessao: o video
        # renderiza no thread da conversa. Recarregamos a pagina periodicamente
        # (geracao e server-side, reload e seguro) pra forcar a galeria a
        # mostrar o poster novo.
        new_id = None
        deadline = time.time() + config.GEN_TIMEOUT_S
        last_reload = time.time()
        while time.time() < deadline:
            page.wait_for_timeout(config.POLL_S * 1000)
            novos = _poster_ids() - posters_before
            if novos:
                new_id = list(novos)[-1]
                log(f"[flow] video novo renderizado: {new_id}")
                break
            # re-navega a cada ~30s pra atualizar a galeria.
            # NAO usar page.reload(): deixa a pagina PRETA (o compositor SPA
            # nao re-hidrata e a galeria some -> _poster_ids() volta vazio e
            # o diff nunca detecta o poster novo). goto(start_url) sobe fresco
            # e a galeria popula (provado quota-zero pelo probe_count.py).
            if time.time() - last_reload > 30:
                try:
                    page.goto(start_url, wait_until="domcontentloaded")
                    page.wait_for_timeout(6000)
                except Exception as e:
                    log(f"[flow] re-goto falhou (ignorado): {type(e).__name__}")
                last_reload = time.time()
            log(f"[flow] ...aguardando render ({int(deadline - time.time())}s restantes)")

        if not new_id:
            shot = os.path.join(config.LOG_DIR, f"{apelido}_timeout.png")
            try:
                page.screenshot(path=shot, timeout=8000)
            except Exception:
                pass
            browser.close()
            raise RuntimeError(f"timeout sem video. screenshot: {shot}")

        ok = _download_via_button(page, new_id, out_path, log=log)
        if not ok:
            # fallback: baixa o poster/mp4 pela URL de redirect com os cookies
            cookies = ctx.cookies()
            redirect = f"https://labs.google/fx/api/trpc/media.getMediaUrlRedirect?name={new_id}"
            log("[flow] botao de download falhou; tentando redirect URL")
            _download(redirect, out_path, cookies)

        page.close()
        browser.close()

    log(f"[flow] OK video salvo: {out_path}")
    return out_path


def _enter_project_for_download(page, media_id, log=print):
    """Navega da galeria de projetos pra dentro do projeto que contem o video.

    Apos o re-goto durante polling, a pagina fica na galeria (grid de thumbnails).
    O botao "Baixar" so existe dentro da conversa do projeto. Essa funcao:
    1) Localiza o poster do video na galeria
    2) Encontra o card/container do projeto pai
    3) Clica nele pra entrar na conversa
    4) Espera a conversa carregar (prompt box aparece)
    """
    try:
        thumb = page.query_selector(f"img[src*='{media_id}']")
        if not thumb:
            log(f"[flow] _enter_project: poster {media_id} nao encontrado na galeria")
            return False

        # O poster pode estar dentro de um card de projeto na galeria.
        # Tenta encontrar o container pai clicavel (link, card, article, div com role)
        project_link = page.evaluate("""(mediaId) => {
            const img = document.querySelector(`img[src*='${mediaId}']`);
            if (!img) return null;
            // sobe ate encontrar um <a> ancestral ou elemento com onclick/role
            let el = img.parentElement;
            for (let i = 0; i < 10 && el; i++) {
                if (el.tagName === 'A' && el.href) return el.href;
                if (el.getAttribute('role') === 'link' || el.getAttribute('role') === 'button')
                    return '__click__';
                el = el.parentElement;
            }
            return null;
        }""", media_id)

        if project_link and project_link.startswith("http"):
            log(f"[flow] _enter_project: navegando via link do projeto: {project_link[:80]}...")
            page.goto(project_link, wait_until="domcontentloaded")
            page.wait_for_timeout(6000)
            log("[flow] _enter_project: dentro do projeto (via link)")
            return True

        # Se nao achou link, tenta clicar diretamente no poster/card
        # e verificar se a pagina mudou pra conversa
        thumb.scroll_into_view_if_needed(timeout=3000)
        thumb.click(timeout=5000, force=True)
        page.wait_for_timeout(4000)

        # Verificar se estamos agora dentro de uma conversa (prompt box presente)
        in_conversation = page.query_selector(
            "textarea, [contenteditable='true'], input[type='text']"
        )
        if in_conversation:
            log("[flow] _enter_project: dentro do projeto (via click no poster)")
            return True

        # Pode ter aberto um preview/overlay. Tenta click duplo ou clica no titulo
        log("[flow] _enter_project: click no poster nao abriu conversa, tentando overlay...")
        page.wait_for_timeout(2000)

        diag = os.path.join(config.LOG_DIR, "enter_project_diag.png")
        try:
            page.screenshot(path=diag, timeout=5000)
            log(f"[flow] _enter_project: screenshot diag: {diag}")
        except Exception:
            pass

        return False
    except Exception as e:
        log(f"[flow] _enter_project erro: {type(e).__name__}: {e}")
        return False


def _download_via_button(page, media_id, out_path, log=print):
    """Clica no poster do video (media_id), abre 'Baixar' e captura o download."""
    try:
        thumb = page.query_selector(f"img[src*='{media_id}']")
        if not thumb:
            log(f"[flow] poster {media_id} sumiu do DOM")
            return False
        thumb.scroll_into_view_if_needed(timeout=3000)
        thumb.click(timeout=5000, force=True)
        page.wait_for_timeout(3500)

        # botao "Baixar" (icone material download) no canvas do resultado
        baixar = None
        for b in page.query_selector_all("button, [role=button], a"):
            try:
                if not b.is_visible():
                    continue
                blob = ((b.inner_text() or "") + " " +
                        (b.get_attribute("aria-label") or "")).lower()
                if "baixar" in blob or "download" in blob:
                    baixar = b
                    break
            except Exception:
                pass
        if not baixar:
            log("[flow] botao 'Baixar' nao encontrado no canvas")
            return False

        # o Baixar pode disparar download direto OU abrir submenu de resolucao
        try:
            with page.expect_download(timeout=15000) as di:
                baixar.click(force=True)
            d = di.value
            d.save_as(out_path)
            log(f"[flow] download OK (direto): {d.suggested_filename}")
            return True
        except Exception:
            pass

        page.wait_for_timeout(1500)
        # submenu: procura item de resolucao/original (evita Cortar/Nano Banana)
        for it in page.query_selector_all("[role=menuitem], li, button, a"):
            try:
                if not it.is_visible():
                    continue
                t = (it.inner_text() or "").strip().lower()
                if not t:
                    continue
                if any(k in t for k in ["720", "1080", "mp4", "original", "gif"]) \
                   and "cortar" not in t and "banana" not in t and "crop" not in t:
                    with page.expect_download(timeout=25000) as di:
                        it.click(force=True)
                    d = di.value
                    d.save_as(out_path)
                    log(f"[flow] download OK (submenu '{t}'): {d.suggested_filename}")
                    return True
            except Exception:
                continue
        log("[flow] submenu de download sem item de video utilizavel")
        return False
    except Exception as e:
        log(f"[flow] _download_via_button erro: {type(e).__name__}: {e}")
        return False


def extend(apelido, video_path, extend_prompt=None, out_path=None, log=print,
           model=None, audio=None):
    """
    Estende um video existente no Flow (VIDEO_EXTENSION mode).
    Sobe o video como midia, pede pra estender com prompt opcional.
    """
    if not os.path.exists(video_path):
        raise RuntimeError(f"video nao encontrado: {video_path}")
    prompt = extend_prompt or "extend this video, continue the same scene smoothly"
    prompt = _enrich_prompt(prompt, model=model, audio=audio)

    sess = os.path.join(config.SESSIONS_DIR, f"{apelido}.json")
    if not os.path.exists(sess):
        raise RuntimeError(f"sessao '{apelido}' nao existe")
    url_file = os.path.join(config.SESSIONS_DIR, f"{apelido}.url.txt")
    start_url = config.FLOW_URL
    if os.path.exists(url_file):
        start_url = open(url_file, encoding="utf-8").read().strip() or start_url

    port = _account_port(apelido)
    chrome_proc = _ensure_chrome(apelido, port, log=log)

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
        ctx = browser.contexts[0] if browser.contexts else browser.new_context()
        _restore_session(ctx, apelido, log=log)
        page = ctx.new_page()
        log(f"[flow] abrindo {start_url} (extend)")
        page.goto(start_url, wait_until="domcontentloaded")
        page.wait_for_timeout(6000)

        _nuke_changelog(page, log)
        page = _ensure_workspace(page, log=log)

        log("[flow] settings via prompt (painel de radios switcha p/ imagem)")

        # sobe o video como midia
        uploaded = _upload_image(page, video_path, log=log)
        if not uploaded:
            log("[flow] WARN: upload falhou, tentando enviar prompt primeiro e depois upload")
            box2, _ = _find_first(page, PROMPT_SELECTORS, timeout=8000)
            if box2:
                box2.click(force=True)
                page.wait_for_timeout(500)
                uploaded = _upload_image(page, video_path, log=log)

        # escreve o prompt de extensao
        box, bsel = _find_first(page, PROMPT_SELECTORS, timeout=15000)
        if not box:
            shot = os.path.join(config.LOG_DIR, f"{apelido}_extend_noprompt.png")
            page.screenshot(path=shot)
            browser.close()
            raise RuntimeError(f"nao achei caixa de prompt (extend). screenshot: {shot}")
        box.click(force=True)
        if bsel == "[contenteditable='true']":
            box.type(prompt)
        else:
            box.fill(prompt)
        page.wait_for_timeout(500)

        # snapshot dos posters antes do submit (mesma estrategia da generate)
        def _poster_ids():
            try:
                return set(page.evaluate(
                    """() => Array.from(document.querySelectorAll('img[src*=getMediaUrlRedirect]'))
                        .map(i => { const m = i.src.match(/name=([0-9a-f-]+)/i); return m ? m[1] : null; })
                        .filter(Boolean)"""
                ) or [])
            except Exception:
                return set()
        posters_before = _poster_ids()
        log(f"[flow] posters antes do submit: {len(posters_before)}")

        btn = _click_button_with_text(page, SUBMIT_TEXT_HINTS, timeout=5000)
        if btn:
            log("[flow] submetendo extensao")
            btn.click(force=True)
        else:
            box.press("Enter")

        page.wait_for_timeout(2000)
        shot_post = os.path.join(config.LOG_DIR, f"{apelido}_extend_post_submit.png")
        try:
            page.screenshot(path=shot_post, timeout=8000)
            log(f"[flow] screenshot pos-submit: {shot_post}")
        except Exception as e:
            log(f"[flow] screenshot pos-submit falhou (ignorado): {type(e).__name__}")

        # Captura a URL do projeto ANTES de polling. Usar ela no re-goto
        # mantem a pagina dentro da conversa (onde o botao Baixar funciona),
        # em vez de ir pra galeria de projetos (start_url).
        project_url = page.url
        log(f"[flow] project_url pro re-goto: {project_url[:120]}")

        if not out_path:
            base = os.path.splitext(os.path.basename(video_path))[0]
            out_path = os.path.join(config.OUTPUT_DIR, f"{base}_extended.mp4")

        new_id = None
        deadline = time.time() + config.GEN_TIMEOUT_S
        last_reload = time.time()
        while time.time() < deadline:
            page.wait_for_timeout(config.POLL_S * 1000)
            novos = _poster_ids() - posters_before
            if novos:
                new_id = list(novos)[-1]
                log(f"[flow] video estendido renderizado: {new_id}")
                break
            if time.time() - last_reload > 30:
                try:
                    page.goto(project_url, wait_until="domcontentloaded")
                    page.wait_for_timeout(6000)
                except Exception as e:
                    log(f"[flow] re-goto falhou (ignorado): {type(e).__name__}")
                last_reload = time.time()
            log(f"[flow] ...aguardando extensao ({int(deadline - time.time())}s restantes)")

        if not new_id:
            shot = os.path.join(config.LOG_DIR, f"{apelido}_extend_timeout.png")
            try:
                page.screenshot(path=shot, timeout=8000)
            except Exception:
                pass
            browser.close()
            raise RuntimeError(f"timeout extend sem video. screenshot: {shot}")

        diag = os.path.join(config.LOG_DIR, f"{apelido}_extend_pre_download.png")
        try:
            page.screenshot(path=diag, timeout=8000)
            log(f"[flow] screenshot pre-download: {diag}")
        except Exception:
            pass

        # ESTRATEGIA DE DOWNLOAD (conversa do Flow)
        # Na conversa, clicar no poster abre player inline (SEM overlay "Baixar").
        # Ordem:
        # 1) Intercepta rede + clica poster → captura URL do MP4 carregado pelo player
        # 2) Tenta URL de CDN direto (flow-content.google/video/UUID)
        # 3) Navega pra galeria → _download_via_button (como generate)
        # 4) Fallback: _download_via_video_element (blob/DOM)

        ok = _download_via_network_intercept(page, new_id, out_path, log=log)
        if not ok:
            log("[flow] intercept falhou; tentando CDN video direto")
            ok = _download_via_cdn_video_url(page, new_id, out_path, log=log)
        if not ok:
            log("[flow] CDN direto falhou; navegando pra galeria pra tentar _download_via_button")
            try:
                page.goto(start_url, wait_until="domcontentloaded")
                page.wait_for_timeout(6000)
            except Exception as e:
                log(f"[flow] goto galeria falhou (ignorado): {type(e).__name__}")
            ok = _download_via_button(page, new_id, out_path, log=log)
        if not ok:
            log("[flow] galeria falhou; tentando video element/blob")
            try:
                page.goto(project_url, wait_until="domcontentloaded")
                page.wait_for_timeout(4000)
            except Exception:
                pass
            ok = _download_via_video_element(page, new_id, out_path, log=log)
        if not ok:
            log("[flow] video element falhou; tentando redirect via browser")
            redirect = f"https://labs.google/fx/api/trpc/media.getMediaUrlRedirect?name={new_id}"
            ok = _download_via_browser_redirect(page, redirect, out_path, log=log)
        if not ok:
            raise RuntimeError(f"download do video estendido falhou (todos os metodos). new_id={new_id}")

        page.close()
        browser.close()

    log(f"[flow] OK video estendido: {out_path}")
    return out_path


def _download_via_network_intercept(page, media_id, out_path, log=print):
    """Clica no poster e captura a URL do video MP4 via interceptacao de rede."""
    try:
        captured_urls = []

        def on_response(response):
            url = response.url
            ct = ""
            try:
                ct = response.headers.get("content-type", "")
            except Exception:
                pass
            if ("video" in ct or ".mp4" in url or "flow-content.google/video" in url
                    or ("flow-content.google" in url and "video" in url)):
                captured_urls.append({"url": url, "ct": ct, "status": response.status})

        page.on("response", on_response)

        thumb = page.query_selector(f"img[src*='{media_id}']")
        if not thumb:
            log(f"[flow] _net_intercept: poster {media_id} nao encontrado")
            page.remove_listener("response", on_response)
            return False

        thumb.scroll_into_view_if_needed(timeout=3000)
        thumb.click(timeout=5000, force=True)
        page.wait_for_timeout(6000)

        page.remove_listener("response", on_response)

        if captured_urls:
            log(f"[flow] _net_intercept: capturou {len(captured_urls)} URLs de video")
            for cap in captured_urls:
                log(f"[flow]   → {cap['url'][:120]} (ct={cap['ct']}, status={cap['status']})")

            best = None
            for cap in captured_urls:
                if cap["status"] == 200 and ("video" in cap["ct"] or ".mp4" in cap["url"]):
                    best = cap
                    break
            if not best:
                best = captured_urls[0]

            try:
                cookies = page.context.cookies()
                _download(best["url"], out_path, cookies)
                sz = os.path.getsize(out_path) if os.path.exists(out_path) else 0
                if sz > 50000:
                    log(f"[flow] download OK (network intercept): {sz} bytes")
                    return True
                else:
                    log(f"[flow] network intercept download muito pequeno ({sz}b)")
            except Exception as e:
                log(f"[flow] network intercept download falhou: {type(e).__name__}: {e}")

            import base64
            for cap in captured_urls:
                try:
                    resp = page.evaluate("""async (url) => {
                        try {
                            const r = await fetch(url, {credentials: 'include'});
                            if (!r.ok) return 'ERR:HTTP_' + r.status;
                            const ct = r.headers.get('content-type') || '';
                            if (!ct.includes('video')) return 'ERR:not_video_' + ct;
                            const buf = await r.arrayBuffer();
                            const bytes = new Uint8Array(buf);
                            let bin = '';
                            const chunk = 0x8000;
                            for (let i = 0; i < bytes.length; i += chunk)
                                bin += String.fromCharCode.apply(null, bytes.subarray(i, i + chunk));
                            return btoa(bin);
                        } catch (e) { return 'ERR:' + e.message; }
                    }""", cap["url"])
                    if resp and not resp.startswith("ERR:"):
                        data = base64.b64decode(resp)
                        if len(data) > 50000:
                            with open(out_path, "wb") as f:
                                f.write(data)
                            log(f"[flow] download OK (net intercept fetch): {len(data)} bytes")
                            return True
                except Exception:
                    pass
        else:
            log("[flow] _net_intercept: nenhuma URL de video capturada ao clicar poster")

            diag_shot = os.path.join(config.LOG_DIR, "extend_after_poster_click.png")
            try:
                page.screenshot(path=diag_shot, timeout=5000)
                log(f"[flow] debug screenshot apos clicar poster: {diag_shot}")
            except Exception:
                pass
            dom_info = page.evaluate("""() => {
                const videos = document.querySelectorAll('video');
                const buttons = [];
                for (const b of document.querySelectorAll('button, [role=button], a')) {
                    try {
                        if (b.offsetParent !== null) {
                            const txt = (b.innerText || '').trim().substring(0, 60);
                            const aria = (b.getAttribute('aria-label') || '').substring(0, 60);
                            if (txt || aria) buttons.push(txt + '|' + aria);
                        }
                    } catch(e) {}
                }
                return {
                    video_count: videos.length,
                    video_srcs: Array.from(videos).map(v => (v.src || '').substring(0, 150)),
                    visible_buttons: buttons.slice(0, 20)
                };
            }""")
            log(f"[flow] DOM apos click: {json.dumps(dom_info, ensure_ascii=False)}")
        return False
    except Exception as e:
        log(f"[flow] _download_via_network_intercept erro: {type(e).__name__}: {e}")
        return False


def _download_via_cdn_video_url(page, media_id, out_path, log=print):
    """Tenta construir a URL de video direto no CDN do Flow e baixar."""
    try:
        thumb = page.query_selector(f"img[src*='{media_id}']")
        poster_src = thumb.get_attribute("src") if thumb else None

        if poster_src and "flow-content.google" in poster_src:
            video_url = poster_src.replace("/image/", "/video/")
            log(f"[flow] tentando CDN video URL: {video_url[:120]}")
            import base64
            resp = page.evaluate("""async (url) => {
                try {
                    const r = await fetch(url, {credentials: 'include'});
                    if (!r.ok) return 'ERR:HTTP_' + r.status;
                    const ct = r.headers.get('content-type') || '';
                    const buf = await r.arrayBuffer();
                    const bytes = new Uint8Array(buf);
                    let bin = '';
                    const chunk = 0x8000;
                    for (let i = 0; i < bytes.length; i += chunk)
                        bin += String.fromCharCode.apply(null, bytes.subarray(i, i + chunk));
                    return JSON.stringify({ct: ct, b64: btoa(bin), size: bytes.length});
                } catch (e) { return 'ERR:' + e.message; }
            }""", video_url)
            if resp and not resp.startswith("ERR:"):
                info = json.loads(resp)
                data = base64.b64decode(info["b64"])
                ct = info.get("ct", "")
                log(f"[flow] CDN video: ct={ct}, size={len(data)}")
                if "video" in ct and len(data) > 50000:
                    with open(out_path, "wb") as f:
                        f.write(data)
                    log(f"[flow] download OK (CDN video): {len(data)} bytes")
                    return True
                elif len(data) > 500000:
                    with open(out_path, "wb") as f:
                        f.write(data)
                    log(f"[flow] download OK (CDN video, ct={ct}): {len(data)} bytes")
                    return True
                else:
                    log(f"[flow] CDN video rejeitado (ct={ct}, size={len(data)}b)")
            else:
                log(f"[flow] CDN video fetch: {resp}")
        else:
            log("[flow] _cdn_video: poster sem URL flow-content.google, tentando redirect getMediaUrl")
            import base64
            redirect = f"https://labs.google/fx/api/trpc/media.getMediaUrlRedirect?name={media_id}"
            resp = page.evaluate("""async (url) => {
                try {
                    const r = await fetch(url, {credentials: 'include', redirect: 'follow'});
                    const finalUrl = r.url;
                    if (!r.ok) return 'ERR:HTTP_' + r.status;
                    const ct = r.headers.get('content-type') || '';
                    return JSON.stringify({url: finalUrl, ct: ct});
                } catch (e) { return 'ERR:' + e.message; }
            }""", redirect)
            if resp and not resp.startswith("ERR:"):
                info = json.loads(resp)
                final_url = info.get("url", "")
                ct = info.get("ct", "")
                log(f"[flow] redirect resolveu pra: {final_url[:120]} (ct={ct})")
                if "flow-content.google" in final_url and "/image/" in final_url:
                    video_url = final_url.replace("/image/", "/video/")
                    log(f"[flow] trocando /image/ por /video/: {video_url[:120]}")
                    r2 = page.evaluate("""async (url) => {
                        try {
                            const r = await fetch(url, {credentials: 'include'});
                            if (!r.ok) return 'ERR:HTTP_' + r.status;
                            const ct = r.headers.get('content-type') || '';
                            const buf = await r.arrayBuffer();
                            const bytes = new Uint8Array(buf);
                            let bin = '';
                            const chunk = 0x8000;
                            for (let i = 0; i < bytes.length; i += chunk)
                                bin += String.fromCharCode.apply(null, bytes.subarray(i, i + chunk));
                            return JSON.stringify({ct: ct, b64: btoa(bin), size: bytes.length});
                        } catch (e) { return 'ERR:' + e.message; }
                    }""", video_url)
                    if r2 and not r2.startswith("ERR:"):
                        i2 = json.loads(r2)
                        data = base64.b64decode(i2["b64"])
                        ct2 = i2.get("ct", "")
                        if "video" in ct2 and len(data) > 50000:
                            with open(out_path, "wb") as f:
                                f.write(data)
                            log(f"[flow] download OK (CDN video via redirect): {len(data)} bytes")
                            return True
                        else:
                            log(f"[flow] CDN video via redirect rejeitado (ct={ct2}, size={len(data)}b)")
                    else:
                        log(f"[flow] CDN video via redirect fetch: {r2}")
            else:
                log(f"[flow] redirect resolve falhou: {resp}")
        return False
    except Exception as e:
        log(f"[flow] _download_via_cdn_video_url erro: {type(e).__name__}: {e}")
        return False


def _download_via_video_element(page, media_id, out_path, log=print):
    """Clica no poster dentro da conversa e tenta capturar a URL do <video>."""
    try:
        thumb = page.query_selector(f"img[src*='{media_id}']")
        if not thumb:
            log(f"[flow] _video_elem: poster {media_id} nao encontrado")
            return False
        thumb.scroll_into_view_if_needed(timeout=3000)
        thumb.click(timeout=5000, force=True)
        page.wait_for_timeout(4000)

        # Debug: screenshot + dump DOM apos clicar poster
        try:
            diag_shot = os.path.join(config.LOG_DIR, "extend_after_poster_click.png")
            page.screenshot(path=diag_shot, timeout=5000)
            log(f"[flow] debug screenshot apos clicar poster: {diag_shot}")
        except Exception:
            pass
        dom_info = page.evaluate("""() => {
            const videos = document.querySelectorAll('video');
            const buttons = [];
            for (const b of document.querySelectorAll('button, [role=button], a')) {
                try {
                    if (b.offsetParent !== null) {
                        const txt = (b.innerText || '').trim().substring(0, 60);
                        const aria = (b.getAttribute('aria-label') || '').substring(0, 60);
                        if (txt || aria) buttons.push(txt + '|' + aria);
                    }
                } catch(e) {}
            }
            return {
                video_count: videos.length,
                video_srcs: Array.from(videos).map(v => (v.src || '').substring(0, 150)),
                visible_buttons: buttons.slice(0, 20)
            };
        }""")
        log(f"[flow] DOM apos click: {json.dumps(dom_info, ensure_ascii=False)}")

        # Procura <video> com src que contenha o media_id ou .mp4
        video_url = page.evaluate("""() => {
            const vids = document.querySelectorAll('video');
            for (const v of vids) {
                // checa src do video
                if (v.src && (v.src.includes('.mp4') || v.src.includes('blob:') || v.src.includes('video'))) {
                    return v.src;
                }
                // checa <source> filhos
                for (const s of v.querySelectorAll('source')) {
                    if (s.src) return s.src;
                }
            }
            return null;
        }""")
        if video_url:
            log(f"[flow] video element src encontrado: {video_url[:120]}")
            if video_url.startswith("blob:"):
                # blob URL: precisa extrair via fetch in-browser
                import base64
                resp = page.evaluate("""async (url) => {
                    try {
                        const r = await fetch(url);
                        const buf = await r.arrayBuffer();
                        const bytes = new Uint8Array(buf);
                        let bin = '';
                        const chunk = 0x8000;
                        for (let i = 0; i < bytes.length; i += chunk)
                            bin += String.fromCharCode.apply(null, bytes.subarray(i, i + chunk));
                        return btoa(bin);
                    } catch (e) { return 'ERR:' + e.message; }
                }""", video_url)
                if resp and not resp.startswith("ERR:"):
                    data = base64.b64decode(resp)
                    if len(data) > 50000:
                        with open(out_path, "wb") as f:
                            f.write(data)
                        log(f"[flow] download OK (blob video): {len(data)} bytes")
                        return True
                    else:
                        log(f"[flow] blob video muito pequeno ({len(data)}b)")
                else:
                    log(f"[flow] blob fetch falhou: {resp}")
            else:
                # URL direta: baixa com cookies
                try:
                    cookies = page.context.cookies()
                    _download(video_url, out_path, cookies)
                    sz = os.path.getsize(out_path) if os.path.exists(out_path) else 0
                    if sz > 50000:
                        log(f"[flow] download OK (video element): {sz} bytes")
                        return True
                    else:
                        log(f"[flow] video element download muito pequeno ({sz}b)")
                except Exception as e:
                    log(f"[flow] video element download falhou: {type(e).__name__}: {e}")
        else:
            log("[flow] nenhum <video> element encontrado apos clicar poster")

        # Tenta tambem procurar botao Baixar no overlay/modal que pode ter aberto
        for b in page.query_selector_all("button, [role=button], a"):
            try:
                if not b.is_visible():
                    continue
                blob = ((b.inner_text() or "") + " " +
                        (b.get_attribute("aria-label") or "")).lower()
                if "baixar" in blob or "download" in blob:
                    try:
                        with page.expect_download(timeout=15000) as di:
                            b.click(force=True)
                        d = di.value
                        d.save_as(out_path)
                        log(f"[flow] download OK (botao no overlay conversa): {d.suggested_filename}")
                        return True
                    except Exception:
                        pass
            except Exception:
                pass
        return False
    except Exception as e:
        log(f"[flow] _download_via_video_element erro: {type(e).__name__}: {e}")
        return False


def _download_via_browser_redirect(page, redirect_url, out_path, log=print):
    """Navega no browser diretamente pra URL de redirect, capturando o download."""
    try:
        with page.expect_download(timeout=30000) as di:
            page.goto(redirect_url)
        d = di.value
        d.save_as(out_path)
        log(f"[flow] download OK (browser redirect): {d.suggested_filename}")
        return True
    except Exception as e:
        log(f"[flow] browser redirect falhou: {type(e).__name__}: {e}")
    try:
        resp = page.evaluate("""async (url) => {
            try {
                const r = await fetch(url, {credentials: 'include'});
                if (!r.ok) return 'ERR:HTTP_' + r.status;
                const buf = await r.arrayBuffer();
                const bytes = new Uint8Array(buf);
                let bin = '';
                const chunk = 0x8000;
                for (let i = 0; i < bytes.length; i += chunk)
                    bin += String.fromCharCode.apply(null, bytes.subarray(i, i + chunk));
                return btoa(bin);
            } catch (e) { return 'ERR:' + (e && e.message ? e.message : String(e)); }
        }""", redirect_url)
        if resp and not resp.startswith("ERR:"):
            import base64
            data = base64.b64decode(resp)
            if len(data) > 10000:
                with open(out_path, "wb") as f:
                    f.write(data)
                log(f"[flow] download OK (fetch in-browser): {len(data)} bytes")
                return True
            else:
                log(f"[flow] fetch in-browser retornou dados muito pequenos ({len(data)}b)")
        else:
            log(f"[flow] fetch in-browser: {resp}")
    except Exception as e:
        log(f"[flow] fetch in-browser falhou: {type(e).__name__}: {e}")
    return False


def _download_poster_src(page, media_id, out_path, log=print):
    """Extrai a URL src do poster e tenta baixar o MP4 via fetch no browser."""
    try:
        thumb = page.query_selector(f"img[src*='{media_id}']")
        if not thumb:
            log(f"[flow] poster {media_id} nao encontrado pra download direto")
            return False
        src = thumb.get_attribute("src")
        if not src:
            return False
        log(f"[flow] tentando download da src do poster: {src[:120]}...")
        resp = page.evaluate("""async (url) => {
            try {
                const r = await fetch(url, {credentials: 'include'});
                if (!r.ok) return 'ERR:HTTP_' + r.status;
                const ct = r.headers.get('content-type') || '';
                const buf = await r.arrayBuffer();
                const bytes = new Uint8Array(buf);
                let bin = '';
                const chunk = 0x8000;
                for (let i = 0; i < bytes.length; i += chunk)
                    bin += String.fromCharCode.apply(null, bytes.subarray(i, i + chunk));
                return JSON.stringify({ct: ct, b64: btoa(bin), size: bytes.length});
            } catch (e) { return 'ERR:' + (e && e.message ? e.message : String(e)); }
        }""", src)
        if resp and not resp.startswith("ERR:"):
            import base64, json
            info = json.loads(resp)
            data = base64.b64decode(info["b64"])
            ct = info.get("ct", "")
            log(f"[flow] poster src: content-type={ct}, size={len(data)}")
            if "video" in ct and len(data) > 50000:
                with open(out_path, "wb") as f:
                    f.write(data)
                log(f"[flow] download OK (poster src video): {len(data)} bytes")
                return True
            elif "image" in ct:
                log(f"[flow] poster src retornou imagem ({ct}, {len(data)}b) — rejeitando (nao e video)")
            elif len(data) > 50000:
                with open(out_path, "wb") as f:
                    f.write(data)
                log(f"[flow] download OK (poster src, ct={ct}): {len(data)} bytes")
                return True
            else:
                log(f"[flow] poster src muito pequeno ({len(data)}b) ou nao e video (ct={ct})")
        else:
            log(f"[flow] poster src fetch: {resp}")
    except Exception as e:
        log(f"[flow] _download_poster_src erro: {type(e).__name__}: {e}")
    return False


def _download(url, out_path, cookies):
    jar = "; ".join(f"{c['name']}={c['value']}" for c in cookies)
    req = urllib.request.Request(url, headers={
        "Cookie": jar,
        "User-Agent": "Mozilla/5.0",
    })
    with urllib.request.urlopen(req, timeout=120) as r, open(out_path, "wb") as f:
        f.write(r.read())


def _download_blob(page, blob_url, out_path, log=print):
    """
    Extrai os bytes de um blob:/MediaSource URL de dentro do browser.
    Tenta fetch() (funciona pra Blob normal). Se for MediaSource (MSE),
    fetch falha e caimos no <video> com captureStream nao ajuda, entao
    a ultima cartada e ler via XHR. Retorna base64 pro Python salvar.
    """
    import base64
    b64 = page.evaluate(
        """async (url) => {
            try {
                const resp = await fetch(url);
                const buf = await resp.arrayBuffer();
                const bytes = new Uint8Array(buf);
                let bin = '';
                const chunk = 0x8000;
                for (let i = 0; i < bytes.length; i += chunk) {
                    bin += String.fromCharCode.apply(null, bytes.subarray(i, i + chunk));
                }
                return btoa(bin);
            } catch (e) {
                return 'ERR:' + (e && e.message ? e.message : String(e));
            }
        }""",
        blob_url,
    )
    if not b64 or b64.startswith("ERR:"):
        raise RuntimeError(f"nao consegui extrair blob ({b64}). "
                           f"provavel MediaSource — precisa capturar via rede.")
    data = base64.b64decode(b64)
    with open(out_path, "wb") as f:
        f.write(data)
    log(f"[flow] blob extraido: {len(data)} bytes")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print('uso: python flow_bot.py <apelido> "prompt" [ratio] [duration]')
        sys.exit(1)
    kw = {}
    if len(sys.argv) > 3:
        kw["aspect_ratio"] = sys.argv[3]
    if len(sys.argv) > 4:
        kw["duration"] = sys.argv[4]
    generate(sys.argv[1], sys.argv[2], **kw)
