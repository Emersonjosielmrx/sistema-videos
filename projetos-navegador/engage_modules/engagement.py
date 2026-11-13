"""
engagement.py — Lógica de interação com UM vídeo no YouTube.

OBJETIVO:
    Funções que executam as ações dentro de uma página do YouTube:
    - simulate_watch() → finge assistir o vídeo (scroll + espera)
    - do_subscribe()   → clica no botão de inscrever
    - do_like()        → clica no botão de like
    - do_comment()     → digita e posta um comentário

    Cada função recebe a page (Playwright) e retorna True/False.

COMO FUNCIONA:
    O worker.py chama essas funções em sequência pra cada vídeo.
    Se qualquer uma falhar, retorna False (sem crashar).

DEPENDENCIAS:
    - random, time (stdlib)
    - comments.py (get_comment)
"""
import random
import time
from .logger import log


def simulate_watch(page, watch_time_range, is_short=False):
    """
    Simula assistir o vídeo com scrolls aleatórios.
    Isso aumenta o watch-time e faz o bot parecer humano.

    Args:
        page: objeto Page do Playwright
        watch_time_range: lista [min_segundos, max_segundos]
        is_short: True se for Short (ajusta comportamento)

    Comportamento:
        - Espera entre min e max segundos
        - A cada 2-5s, tem 30% de chance de scrollar pra baixo
        - Shorts: scroll mais ativo (simula swipe)
    """
    wt = random.uniform(watch_time_range[0], watch_time_range[1])
    elapsed = 0

    # Scroll antes de assistir (comportamento humano)
    if random.random() < 0.6:
        for _ in range(random.randint(1, 3)):
            page.keyboard.press("PageDown" if not is_short else "ArrowDown")
            time.sleep(random.uniform(0.3, 0.8))

    while elapsed < wt:
        wait_chunk = random.uniform(2, 5) if not is_short else random.uniform(1, 3)
        time.sleep(wait_chunk)
        elapsed += wait_chunk

        # Scroll durante assistência
        if is_short:
            # Shorts: scroll mais ativo (swipe simulation)
            if random.random() < 0.5:
                page.keyboard.press("ArrowDown")
        else:
            # Vídeos longos: scroll ocasional
            if random.random() < 0.3:
                page.keyboard.press("PageDown")


def do_subscribe(page):
    """
    Clica no botão de inscrever-se se ainda não estiver inscrito.

    Args:
        page: objeto Page do Playwright

    Returns:
        True se inscreveu (ou já estava inscrito), False se falhou

    JavaScript injetado:
        Procura o botão de subscribe, verifica se já está inscrito,
        e clica se não estiver.
    """
    try:
        sub_js = """() => {
            const btn = document.querySelector(
                "ytd-subscribe-button-renderer button, #subscribe-button button"
            );
            if (!btn) return "nf";
            const label = (btn.textContent || "").toLowerCase();
            if (label.includes("subscribed") ||
                label.includes("inscrito") ||
                btn.getAttribute("aria-pressed") === "true") return "al";
            btn.click();
            return "ok";
        }"""
        result = page.evaluate(sub_js)
        return result in ("ok", "al")
    except Exception:
        return False


def do_like(page):
    """
    Clica no botão de like se ainda não deu like.

    Args:
        page: objeto Page do Playwright

    Returns:
        True se curtiu (ou já tinha curtido), False se falhou

    JavaScript injetado:
        Procura o botão de like, verifica aria-pressed,
        e clica se não estiver ativado.
    """
    try:
        like_js = """() => {
            const btn = document.querySelector("like-button-view-model button");
            if (!btn) return "nf";
            if (btn.getAttribute("aria-pressed") === "true") return "al";
            btn.click();
            return "ok";
        }"""
        result = page.evaluate(like_js)
        return result in ("ok", "al")
    except Exception:
        return False


def _check_youtube_login(page):
    """Verifica se o browser esta logado no YouTube. Retorna True se logado."""
    try:
        return page.evaluate("""() => {
            const signin = document.querySelector(
                'a[href*="accounts.google.com"], ' +
                'ytd-button-renderer.style-suggestive a[href*="ServiceLogin"], ' +
                'a[href*="ServiceLogin"]'
            );
            if (signin) return false;
            const avatar = document.querySelector(
                '#avatar-btn, ' +
                'yt-img-shadow.ytd-topbar-menu-button-renderer img, ' +
                'button#avatar-btn'
            );
            return !!avatar;
        }""")
    except Exception:
        return True


def do_comment(page, comment_text):
    """Posta um comentário no vídeo."""
    try:
        if not _check_youtube_login(page):
            log("[COMMENT] SESSAO EXPIRADA — conta nao esta logada no YouTube, pulando comentario")
            return False

        for _ in range(5):
            page.keyboard.press("PageDown")
            time.sleep(random.uniform(0.4, 1.0))

        has_box = False
        for attempt in range(8):
            has_box = page.evaluate(
                "() => !!document.querySelector('ytd-comment-simplebox-renderer, ytd-comments-header-renderer')"
            )
            if has_box:
                break
            page.keyboard.press("PageDown")
            time.sleep(1)

        if not has_box:
            log("[COMMENT-DEBUG] Caixa de comentario nao apareceu apos 8 scrolls")
            return False

        page.evaluate("""() => {
            const box = document.querySelector('ytd-comment-simplebox-renderer');
            if (box) box.scrollIntoView({block: 'center'});
        }""")
        time.sleep(random.uniform(0.5, 1.0))

        ce_selectors = [
            "#contenteditable-root",
            "div#contenteditable-root",
            "ytd-commentbox #contenteditable-root",
            "[contenteditable='true']",
            "div[contenteditable='plaintext-only']",
            "div[contenteditable]",
            "ytd-commentbox [contenteditable]",
        ]

        root = None
        click_methods = [
            ("page.click placeholder-area", lambda: page.click('ytd-comment-simplebox-renderer #placeholder-area', timeout=3000)),
            ("page.click simplebox-placeholder", lambda: page.click('#simplebox-placeholder', timeout=3000)),
            ("page.click simplebox-renderer", lambda: page.click('ytd-comment-simplebox-renderer', timeout=3000)),
            ("js center-click placeholder", lambda: page.evaluate("""() => {
                const el = document.querySelector('#placeholder-area') ||
                           document.querySelector('#simplebox-placeholder');
                if (!el) return false;
                const rect = el.getBoundingClientRect();
                const x = rect.left + rect.width / 2;
                const y = rect.top + rect.height / 2;
                const target = document.elementFromPoint(x, y) || el;
                for (const evt of ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click']) {
                    target.dispatchEvent(new PointerEvent(evt, {
                        bubbles: true, composed: true, cancelable: true,
                        clientX: x, clientY: y, pointerId: 1,
                        pointerType: 'mouse', view: window
                    }));
                }
                return true;
            }""")),
            ("focus+enter placeholder", lambda: (
                page.focus('#placeholder-area') or True,
                time.sleep(0.3),
                page.keyboard.press("Enter"),
            )),
        ]

        for method_name, method_fn in click_methods:
            try:
                method_fn()
            except Exception:
                continue
            time.sleep(random.uniform(2.0, 3.5))
            for selector in ce_selectors:
                try:
                    root = page.query_selector(selector)
                    if root:
                        log(f"[COMMENT-DEBUG] contenteditable encontrado via {method_name}: {selector}")
                        break
                except:
                    continue
            if root:
                break

        if not root:
            diag = page.evaluate("""() => {
                const box = document.querySelector('ytd-comment-simplebox-renderer');
                if (!box) return 'simplebox=null';
                const vis = window.getComputedStyle(box).display;
                if (vis === 'none') return 'display:none';
                const all = box.querySelectorAll('*');
                const tags = [];
                for (const el of all) {
                    if (el.id || el.getAttribute('contenteditable')) {
                        tags.push(el.tagName + '#' + el.id + '[ce=' + (el.getAttribute('contenteditable')||'') + ']');
                    }
                }
                return 'N=' + all.length + ' vis=' + vis + ' ids=' + tags.slice(0,12).join(',');
            }""")
            log(f"[COMMENT-DEBUG] contenteditable nao encontrado DOM={diag}")
            return False

        root.click()
        time.sleep(random.uniform(0.3, 0.6))
        root.focus()
        time.sleep(random.uniform(0.1, 0.3))

        for char in comment_text:
            page.keyboard.type(char, delay=random.uniform(50, 180))

        page.evaluate("""() => {
            const sels = ['#contenteditable-root', '[contenteditable="true"]', 'div[contenteditable]'];
            for (const sel of sels) {
                const r = document.querySelector(sel);
                if (r && r.textContent) {
                    r.dispatchEvent(new Event('input', {bubbles: true}));
                    r.dispatchEvent(new Event('change', {bubbles: true}));
                    return;
                }
            }
        }""")

        time.sleep(random.uniform(0.8, 1.5))

        submit_clicked = page.evaluate("""() => {
            const selectors = [
                'ytd-commentbox #submit-button button',
                'ytd-button-renderer#submit-button button',
                '#submit-button button',
                '#submit-button tp-yt-paper-button',
                'button[aria-label*="Comment"]',
                'button[aria-label*="Comentar"]',
                'ytd-button-renderer.ytd-commentbox button',
                '#submit-button'
            ];
            for (const sel of selectors) {
                const s = document.querySelector(sel);
                if (s && !s.disabled && !s.hasAttribute('disabled')) {
                    s.click();
                    return 'ok:' + sel;
                }
                if (s) {
                    s.removeAttribute('disabled');
                    s.disabled = false;
                    s.click();
                    return 'forced:' + sel;
                }
            }
            return '';
        }""")

        if not submit_clicked:
            log("[COMMENT-DEBUG] Botao submit nao encontrado")
            return False

        time.sleep(random.uniform(2, 4))
        return True

    except Exception as e:
        log(f"[COMMENT-DEBUG] Exception do_comment: {e}")
        return False


def do_reply_comment(page):
    """Responde a um comentário existente (primeiro visível)."""
    try:
        for _ in range(5):
            page.keyboard.press("PageDown")
            time.sleep(random.uniform(0.5, 1))

        reply_js = """() => {
            const comments = document.querySelectorAll('ytd-comment-thread-renderer');
            if (comments.length < 2) return "nf";
            const idx = Math.floor(Math.random() * Math.min(comments.length, 5));
            const replyBtn = comments[idx]?.querySelector('#reply-button-end button, [aria-label*="Reply"], [aria-label*="Responder"]');
            if (!replyBtn) return "nf";
            replyBtn.click();
            return "ok";
        }"""
        result = page.evaluate(reply_js)
        if result != "ok":
            return False, ""

        time.sleep(random.uniform(1, 2))

        reply_texts = [
            "Concordo!", "Exatamente!", "Bem isso!", "Perfeito!",
            "Agreed!", "So true!", "Exactly!", "Facts!",
            "Right!", "100%!", "True!", "This!",
        ]
        reply = random.choice(reply_texts)

        root = page.query_selector("#contenteditable-root")
        if not root:
            return False, ""

        root.click()
        time.sleep(random.uniform(0.2, 0.4))
        for char in reply:
            page.keyboard.type(char, delay=random.uniform(40, 150))

        page.evaluate("""() => {
            const root = document.querySelector("#contenteditable-root");
            if (root) root.dispatchEvent(new Event("input", {bubbles: true}));
        }""")
        time.sleep(random.uniform(0.5, 1))

        submit_clicked = page.evaluate("""() => {
            const s = document.querySelector(
                "ytd-button-renderer#submit-button button, #submit-button"
            );
            if (s) { s.removeAttribute("disabled"); s.click(); return true; }
            return false;
        }""")

        if submit_clicked:
            time.sleep(random.uniform(1.5, 3))
            return True, reply

        return False, ""
    except Exception:
        return False, ""


def read_description(page):
    """Simula clicar em 'Mostrar mais' pra ler a descrição."""
    try:
        expanded = page.evaluate("""() => {
            const more = document.querySelector(
                'tp-yt-paper-button#expand, #description-inline-expander #expand'
            );
            if (more) { more.click(); return true; }
            const expandBtn = document.querySelector(
                '#expand[role="button"], ytd-text-inline-expander #expand'
            );
            if (expandBtn) { expandBtn.click(); return true; }
            return false;
        }""")
        if expanded:
            time.sleep(random.uniform(2, 5))
            for _ in range(random.randint(1, 3)):
                page.keyboard.press("PageDown")
                time.sleep(random.uniform(0.5, 1.5))
        return expanded
    except Exception:
        return False


def interact_endscreen(page):
    """Clica em end-screen/cards se visíveis (não navega, só engaja)."""
    try:
        result = page.evaluate("""() => {
            const card = document.querySelector(
                '.ytp-ce-element, .ytp-suggestion-set, .iv-card'
            );
            if (card) { card.click(); return "card"; }
            const endscreen = document.querySelector('.ytp-endscreen-content a');
            if (endscreen) { endscreen.click(); return "endscreen"; }
            return "nf";
        }""")
        if result != "nf":
            time.sleep(random.uniform(2, 5))
            page.go_back()
            time.sleep(1)
            return True
        return False
    except Exception:
        return False


def check_video_dead(page):
    """Verifica se o video eh privado/removido/indisponivel."""
    try:
        return page.evaluate("""() => {
            const t = document.title.toLowerCase();
            const body = document.body?.innerText?.substring(0, 500)?.toLowerCase() || "";
            if (t.includes("não disponível") || t.includes("unavailable")) return "dead";
            if (body.includes("este vídeo não está disponível") ||
                body.includes("this video isn't available") ||
                body.includes("this video is private") ||
                body.includes("vídeo privado") ||
                body.includes("been removed") ||
                body.includes("foi removido")) return "dead";
            const player = document.querySelector('.ytp-error-content-wrap');
            if (player) return "dead";
            return "ok";
        }""")
    except Exception:
        return "ok"


def detect_ban_signals(page, account):
    """Detecta sinais de shadowban/restricao na conta."""
    try:
        signals = page.evaluate("""() => {
            const body = document.body?.innerText?.substring(0, 2000)?.toLowerCase() || "";
            const result = {banned: false, signals: []};
            if (body.includes("unusual activity") || body.includes("atividade incomum")) {
                result.signals.push("unusual_activity");
                result.banned = true;
            }
            if (body.includes("verify") && body.includes("human")) {
                result.signals.push("captcha");
                result.banned = true;
            }
            if (body.includes("restricted") || body.includes("restrito")) {
                result.signals.push("restricted");
            }
            if (body.includes("suspended") || body.includes("suspensa")) {
                result.signals.push("suspended");
                result.banned = true;
            }
            const likeBtn = document.querySelector("like-button-view-model button");
            if (!likeBtn) result.signals.push("no_like_btn");
            const commentBox = document.querySelector("ytd-comment-simplebox-renderer");
            if (!commentBox && document.querySelectorAll("ytd-comment-thread-renderer").length === 0) {
                result.signals.push("comments_disabled");
            }
            return result;
        }""")
        return signals
    except Exception:
        return {"banned": False, "signals": []}


def engage_community_post(page, post_url):
    """Engaja com um Community Post (like)."""
    try:
        page.goto(post_url, timeout=30000, wait_until="domcontentloaded")
        time.sleep(random.uniform(2, 4))

        liked = page.evaluate("""() => {
            const btn = document.querySelector(
                '#vote-count-middle, like-button-view-model button, #like-button button'
            );
            if (!btn) return false;
            if (btn.getAttribute("aria-pressed") === "true") return true;
            btn.click();
            return true;
        }""")

        time.sleep(random.uniform(1, 3))
        return liked
    except Exception:
        return False


def discover_sidebar_channels(page):
    """
    Descobre canais novos a partir da sidebar de vídeos sugeridos.
    Retorna lista de handles/@channel encontrados.
    """
    try:
        channels = page.evaluate("""() => {
            const handles = new Set();
            // Pega links de canal na sidebar de sugestões
            const links = document.querySelectorAll(
                'ytd-compact-video-renderer a[href*="/@"],'
                'ytd-video-renderer a[href*="/@"],'
                '#related ytd-compact-video-renderer .ytd-channel-name a'
            );
            for (const a of links) {
                const href = a.href || '';
                const match = href.match(/@([\\w.-]+)/);
                if (match) handles.add('@' + match[1]);
            }
            return [...handles];
        }""")
        return channels if channels else []
    except Exception:
        return []
