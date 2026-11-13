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

# ---- seletores confirmados na UI atual (2026-07-02) ----
# A caixa de prompt do Flow e um input[type='text'] (confirmado no diag).
# A geracao via este input + Enter FUNCIONA; o bug do 16:9/sem-audio era o
# painel de settings nao aplicar, nao a caixa de prompt.
PROMPT_SELECTORS = [
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
    btn = _click_button_with_text(page, ["tune", "Configura"], timeout=4000)
    if not btn:
        log("[flow] painel Configuracoes nao encontrado (tune) — usando defaults")
        return
    btn.click()
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
    """Sobe uma imagem para image-to-video via 'Add Media' (botao atualizado 07/2026)."""
    if not image_path or not os.path.exists(image_path):
        return False
    btn = _click_button_with_text(page, ["Add Media", "Adicionar", "Add"], timeout=4000)
    inp = None
    if btn:
        btn.click()
        page.wait_for_timeout(1500)
    try:
        inp = page.wait_for_selector("input[type='file']", timeout=4000, state="attached")
    except PWTimeout:
        inp = page.query_selector("input[type='file']")
    if inp:
        inp.set_input_files(image_path)
        page.evaluate("""(el) => {
            el.dispatchEvent(new Event('change', {bubbles: true}));
            el.dispatchEvent(new Event('input', {bubbles: true}));
        }""", inp)
        log(f"[flow] imagem enviada + change: {image_path}")
        page.wait_for_timeout(4000)
        return True
    log("[flow] input de arquivo nao encontrado — image-to-video ignorado")
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


def generate(apelido, prompt, out_path=None, log=print,
             aspect_ratio=None, duration=None, model=None, audio=None,
             image=None, auto_confirm=True):
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
    if not os.path.exists(sess):
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

    port = _account_port(apelido)
    chrome_proc = _ensure_chrome(apelido, port, log=log)

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
        ctx = browser.contexts[0] if browser.contexts else browser.new_context()
        _restore_session(ctx, apelido, log=log)
        page = ctx.new_page()
        page.on("response", on_response)
        log(f"[flow] abrindo {start_url}")
        page.goto(start_url, wait_until="domcontentloaded")
        page.wait_for_timeout(6000)

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
            shot = os.path.join(config.LOG_DIR, f"{apelido}_noprompt.png")
            page.screenshot(path=shot)
            browser.close()
            raise RuntimeError(f"nao achei caixa de prompt. screenshot: {shot}")
        log(f"[flow] caixa de prompt: {bsel}")
        box.click()
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
            btn.click()
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


def _download_via_button(page, media_id, out_path, log=print):
    """Clica no poster do video (media_id), abre 'Baixar' e captura o download."""
    try:
        thumb = page.query_selector(f"img[src*='{media_id}']")
        if not thumb:
            log(f"[flow] poster {media_id} sumiu do DOM")
            return False
        thumb.scroll_into_view_if_needed(timeout=3000)
        thumb.click(timeout=5000)
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
                baixar.click()
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
                        it.click()
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

    found_videos = []
    _capture_active = False

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

    port = _account_port(apelido)
    chrome_proc = _ensure_chrome(apelido, port, log=log)

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
        ctx = browser.contexts[0] if browser.contexts else browser.new_context()
        _restore_session(ctx, apelido, log=log)
        page = ctx.new_page()
        page.on("response", on_response)
        log(f"[flow] abrindo {start_url} (extend)")
        page.goto(start_url, wait_until="domcontentloaded")
        page.wait_for_timeout(6000)

        _set_settings(page, auto_confirm=True, log=log)

        # sobe o video como midia
        _upload_image(page, video_path, log=log)

        # escreve o prompt de extensao
        box, bsel = _find_first(page, PROMPT_SELECTORS, timeout=15000)
        if not box:
            shot = os.path.join(config.LOG_DIR, f"{apelido}_extend_noprompt.png")
            page.screenshot(path=shot)
            browser.close()
            raise RuntimeError(f"nao achei caixa de prompt (extend). screenshot: {shot}")
        box.click()
        if bsel == "[contenteditable='true']":
            box.type(prompt)
        else:
            box.fill(prompt)
        page.wait_for_timeout(500)

        _capture_active = True
        btn = _click_button_with_text(page, SUBMIT_TEXT_HINTS, timeout=5000)
        if btn:
            log("[flow] submetendo extensao")
            btn.click()
        else:
            box.press("Enter")

        deadline = time.time() + config.GEN_TIMEOUT_S
        while time.time() < deadline:
            if found_videos:
                break
            page.wait_for_timeout(config.POLL_S * 1000)
            log(f"[flow] ...aguardando extensao ({int(deadline - time.time())}s restantes)")

        if not found_videos:
            shot = os.path.join(config.LOG_DIR, f"{apelido}_extend_timeout.png")
            page.screenshot(path=shot)
            browser.close()
            raise RuntimeError(f"timeout extend sem video. screenshot: {shot}")

        video_url = found_videos[-1]
        cookies = ctx.cookies()
        page.close()
        browser.close()

    if not out_path:
        base = os.path.splitext(os.path.basename(video_path))[0]
        out_path = os.path.join(config.OUTPUT_DIR, f"{base}_extended.mp4")
    _download(video_url, out_path, cookies)
    log(f"[flow] OK video estendido: {out_path}")
    return out_path


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
