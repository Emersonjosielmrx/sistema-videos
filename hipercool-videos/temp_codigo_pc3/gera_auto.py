#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Geracao 100% automatica no Flow: escreve prompt, submete, aprova se pedir
(clique robusto compativel com React), espera poster novo e baixa o mp4.
Uso: python gera_auto.py "prompt aqui" caminho/saida.mp4"""
import sys, os, time, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright
import config, flow_bot
from contas import PROFILE_MAP  # fonte unica das contas — edite contas.py

PORT = int(os.environ.get("FLOW_PORT", "9250"))
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
    """URL de entrada: projeto salvo da sessao > FLOW_PROJ com /project/ > HOME.
    FLOW_SESSION + flow_projetos.json tem prioridade pra garantir que cada
    conta entra no SEU projeto (nao na landing page publica)."""
    sess = os.environ.get("FLOW_SESSION", "")
    salvo = _load_proj_map().get(sess)
    if salvo:
        return salvo
    env = os.environ.get("FLOW_PROJ")
    if env and "/project/" in env:
        return env
    return _FLOW_HOME


PROJ = _proj_inicial()

# clique robusto: dispara pointer+mouse events na sequencia que o React espera,
# no elemento cujo texto bate (ou seu ancestral com onclick).
JS_ROBUST_CLICK = r"""
(needle) => {
  let alvo = null;
  document.querySelectorAll('*').forEach(e => {
    const t = (e.innerText || e.textContent || '').trim();
    if (t === needle && e.children.length <= 1) alvo = e;
  });
  if (!alvo) return 'nao-achei';
  let cur = alvo;
  while (cur && !cur.onclick && getComputedStyle(cur).cursor !== 'pointer') cur = cur.parentElement;
  const target = cur || alvo;
  const r = target.getBoundingClientRect();
  const x = r.x + r.width / 2, y = r.y + r.height / 2;
  const opts = {bubbles:true, cancelable:true, clientX:x, clientY:y, view:window, button:0};
  for (const type of ['pointerover','pointerenter','pointerdown','mousedown','pointerup','mouseup','click']) {
    const E = type.startsWith('pointer') ? PointerEvent : MouseEvent;
    target.dispatchEvent(new E(type, opts));
  }
  return 'ok';
}
"""

# ---------------------------------------------------------------------------
# DETECCAO DE CREDITOS ESGOTADOS  ->  ver creditos.py
# ---------------------------------------------------------------------------
# A logica foi extraida pra creditos.py (mais facil de achar/ajustar).
# Importamos com os nomes antigos (_prefixo) pra nao mudar os call sites.
from creditos import (
    CreditosEsgotadosError,
    creditos_esgotados as _creditos_esgotados,
    ler_saldo_creditos as _ler_saldo_creditos,
    salvar_evidencia as _salvar_evidencia_creditos_esgotados,
)


def poster_ids(page):
    try:
        return set(page.evaluate(
            """() => Array.from(document.querySelectorAll('img[src*=getMediaUrlRedirect]'))
                .map(i => { const m = i.src.match(/name=([0-9a-f-]+)/i); return m ? m[1] : null; })
                .filter(Boolean)"""))
    except Exception:
        return set()


def poster_ids_ordenados(page):
    """Como poster_ids() mas preserva a ORDEM do DOM (o render costuma entrar no
    topo da grade) e sem duplicatas."""
    try:
        ids = page.evaluate(
            """() => Array.from(document.querySelectorAll('img[src*=getMediaUrlRedirect]'))
                .map(i => { const m = i.src.match(/name=([0-9a-f-]+)/i); return m ? m[1] : null; })
                .filter(Boolean)""")
    except Exception:
        return []
    out, seen = [], set()
    for v in ids:
        if v not in seen:
            seen.add(v)
            out.append(v)
    return out


def video_ids(page):
    """Retorna UUIDs de <video src*=getMediaUrlRedirect> com readyState>=2 (carregados)."""
    try:
        return page.evaluate(
            """() => Array.from(document.querySelectorAll('video[src*="getMediaUrlRedirect"]'))
                .filter(v => v.readyState >= 2)
                .map(v => { const m = v.src.match(/name=([0-9a-f-]+)/i); return m ? m[1] : null; })
                .filter(Boolean)""")
    except Exception:
        return []


def _click_texto(page, texto, log=print):
    """Clica no elemento cujo texto bate, usando mouse REAL do Playwright
    (mais confiavel que .click() JS no React). Retorna True se clicou."""
    try:
        loc = page.locator(f"text={texto}").last
        loc.scroll_into_view_if_needed(timeout=3000)
        box = loc.bounding_box()
        if not box:
            return False
        page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        return True
    except Exception as e:
        log(f"  [click '{texto}'] falhou: {type(e).__name__}")
        return False


def garantir_modo_veo(page, aspect="9:16", modelo="Veo 3.1 - Fast", log=print):
    """Verifica se Veo esta ativo. NAO mexe em radios/settings (causa switch pro
    modo imagem Nano Banana). Confiamos no _enrich_prompt pra instruir o agente."""
    try:
        txt = page.evaluate("() => document.body.innerText")
        if "Veo" in txt:
            log("[veo] Veo ja ativo (detectado no texto)")
            return True
    except Exception:
        pass
    log("[veo] Veo nao detectado no texto — prompt vai instruir o agente")
    return True

def _subir_imagem(page, image_path, log=print):
    """image-to-video: sobe uma imagem como primeiro frame e ANEXA ao prompt.

    Fluxo validado (2026-07-25, conta seebotsia 1050 creditos):
      ATENCAO: o botao 'Adicionar midia' da toolbar top leva ao EDITOR de
      midia (modo imagem Nano Banana), NAO anexa ao chat. O caminho
      CORRETO e o botao 'add_2' (com icone +) que fica DENTRO da caixa de
      prompt, ao lado da textarea. Clicando nele, abre-se o painel de
      upload dentro do chat, com botao 'Enviar midia' que aciona
      file_chooser.
      1) Clicar 'add_2' lateral a caixa de prompt (BOTAO + )
      2) Aguardar popover 'Enviar midia' aparecer
      3) Clicar 'Enviar midia' com expect_file_chooser -> injeta o arquivo
      4) Modal 'Aviso direitos autorais' -> clicar 'Concordo' (1a vez)
      5) Esperar upload terminar (sair do <NN>%)
      6) Imagem vai aparecer anexada no chat (flow adiciona automatico)
      7) Se nao anexou, clicar na thumbnail e depois 'Incluir no comando'
    Retorna True se anexou."""
    if not image_path or not os.path.exists(image_path):
        log(f"[img] arquivo nao existe: {image_path}")
        return False

    def _click_visible_button(needles, timeout_ms=4000, ignore_visibility=False):
        """Clica no PRIMEIRO botao visivel cujo innerText bate (substring).
        Usa mouse click via coordenadas (Material UI exige mouse-real)."""
        import time as _t
        deadline = _t.time() + (timeout_ms / 1000.0)
        while _t.time() < deadline:
            res = page.evaluate("""
            (args) => {
                const [needles, ignoreVis] = args;
                const all = Array.from(document.querySelectorAll('button'));
                for (const b of all) {
                    if (!ignoreVis && !b.offsetParent) continue;
                    const t = (b.innerText || '').trim();
                    for (const n of needles) {
                        if (t.includes(n)) {
                            const r = b.getBoundingClientRect();
                            return {x: r.x + r.width/2, y: r.y + r.height/2, text: t};
                        }
                    }
                }
                return null;
            }
            """, [needles, ignore_visibility])
            if res and 'x' in res:
                page.mouse.click(res['x'], res['y'])
                return res['text']
            _t.sleep(0.3)
        return None

    # --- Passo 1: clicar o botao '+' (add_2) DENTRO da caixa de prompt ---
    # IMPORTANTE: o '+' da toolbar top (Adicionar midia) leva ao editor
    # de midia (modo imagem). O '+' certo fica embaixo da textarea.
    # Vamos achar TODOS os botoes com icone 'add_2' e clicar o que esta
    # perto da textarea (geralmente x > 700 e y > 500).
    log("[img] clicando '+' (add_2) na caixa de prompt...")
    res = page.evaluate("""() => {
        const btns = Array.from(document.querySelectorAll('button'));
        // acha a textarea
        const ta = document.querySelector('textarea, [contenteditable="true"]');
        if (!ta) return null;
        const tr = ta.getBoundingClientRect();
        // botao add_2 mais proximo da textarea (geralmente abaixo-esquerda)
        let best = null, bestDist = Infinity;
        for (const b of btns) {
            if (!b.offsetParent) continue;
            const t = (b.innerText || '');
            if (!t.includes('add_2')) continue;
            const r = b.getBoundingClientRect();
            const cx = r.x + r.width/2, cy = r.y + r.height/2;
            const dx = cx - tr.x, dy = cy - tr.y;
            const dist = Math.hypot(dx, dy);
            if (dist < bestDist) { bestDist = dist; best = {x: cx, y: cy, dist}; }
        }
        return best;
    }""")
    if not res:
        log("[img] FALHA: nao encontrei botao '+' perto da caixa de prompt")
        return False
    log(f"[img] rect add_2: x={res['x']:.0f} y={res['y']:.0f} dist={res['dist']:.0f}")
    page.mouse.click(res['x'], res['y'])
    time.sleep(2)

    # --- Passo 2: clicar 'Enviar midia' com file chooser ---
    try:
        with page.expect_file_chooser(timeout=10000) as fc_info:
            txt = _click_visible_button(
                ["Enviar midia", "Enviar mídia", "Upload media", "Upload file"],
                timeout_ms=4000)
            log(f"[img] clicou '{txt}' p/ abrir file_chooser")
        fc = fc_info.value
        fc.set_files(image_path)
        log("[img] arquivo injetado via file_chooser")
    except Exception as e:
        log(f"[img] file_chooser falhou ({type(e).__name__}): {e}")
        return False

    # --- Passo 3: aceitar modal de direitos autorais se aparecer ---
    time.sleep(2)
    body_txt = (page.evaluate("() => document.body.innerText") or "").lower()
    if "concordo" in body_txt or "i agree" in body_txt:
        log("[img] modal 'Concordo' detectado — clicando")
        _click_visible_button(["Concordo", "I agree", "Concordar"])
        time.sleep(2000/1000)

    # --- Passo 4: esperar upload terminar ---
    log("[img] aguardando upload concluir...")
    for i in range(30):
        time.sleep(2)
        body_txt = page.evaluate("() => document.body.innerText") or ""
        import re
        pct_match = re.search(r'(\d{1,3})%', body_txt)
        if not pct_match:
            log(f"[img] upload aparenta concluido (sem %) apos {(i+1)*2}s")
            break
        pct = int(pct_match.group(1))
        if pct >= 100:
            log(f"[img] upload 100% apos {(i+1)*2}s")
            break
    else:
        log("[img] AVISO: upload nao terminou em 60s — prosseguindo")

    time.sleep(2)

    # --- Passo 5: verificar se a imagem ja foi anexada ao chat ---
    # Se apareceu um thumbnail novo na area do prompt, sucesso.
    # Senao, tentar clicar na imagem e 'Incluir no comando'.
    has_thumb = page.evaluate("""() => {
        // thumbnail no chat/img pequenas (geralmente < 200px) perto da textarea
        const ta = document.querySelector('textarea, [contenteditable="true"]');
        if (!ta) return false;
        const tr = ta.getBoundingClientRect();
        const imgs = Array.from(document.querySelectorAll('img[src*="getMediaUrlRedirect"]'));
        return imgs.some(img => {
            if (!img.offsetParent) return false;
            // thumbnails de upload costumam ter w<=200 e estar proximos da caixa
            const r = img.getBoundingClientRect();
            const dist = Math.hypot(r.x - tr.x, r.y - tr.y);
            return dist < 300 && img.width <= 200;
        });
    }""")
    if has_thumb:
        log("[img] thumbnail anexada ao chat automaticamente")
        return True

    # --- Passo 6: tentar clicar na imagem + 'Incluir no comando' ---
    log("[img] sem thumbnail no chat — tentando 'Incluir no comando'")
    clicked = page.evaluate("""() => {
        const imgs = Array.from(document.querySelectorAll('img[src*="getMediaUrlRedirect"]'));
        const vis = imgs.filter(i => i.offsetParent && i.width >= 50);
        if (!vis.length) return null;
        const t = vis[vis.length - 1];
        const r = t.getBoundingClientRect();
        return {x: r.x + r.width/2, y: r.y + r.height/2};
    }""")
    if clicked:
        page.mouse.click(clicked['x'], clicked['y'])
        time.sleep(2)
    txt = _click_visible_button([
        "Incluir no comando", "Include in prompt",
        "Add to prompt", "Usar no comando", "Use as",
    ], timeout_ms=4000)
    if txt:
        log(f"[img] '{txt}' clicado — imagem anexada ao prompt")
        return True

    log("[img] AVISO: foto pode ja ter ido pro contexto, prosseguindo")
    return False


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
        return False, ""
    except Exception:
        return False, ""


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
    """Garante que o Chrome esta rodando na porta CDP. Abre se necessario."""
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
    log(f"[chrome] abrindo Chrome na porta {port} (sessao={session_name}, perfil={profile_name})...")
    subprocess.Popen([
        chrome,
        f"--remote-debugging-port={port}",
        "--no-first-run",
        "--disable-session-crashed-bubble",
        "--disable-gpu",
        "--disable-software-rasterizer",
        f"--user-data-dir={profile}",
        "about:blank",
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    import time as _time
    for _ in range(20):
        _time.sleep(1)
        try:
            urllib.request.urlopen(url, timeout=2)
            log(f"[chrome] Chrome aberto com sucesso (sessao={session_name})")
            return True
        except Exception:
            pass
    log("[chrome] FALHA ao abrir Chrome!")
    return False


def gerar(prompt, out_path, image=None, aspect="9:16", modelo="Veo 3.1 - Fast",
          duration="8S", log=print):
    _ensure_chrome_running(PORT, log)
    with sync_playwright() as p:
        b = p.chromium.connect_over_cdp(f"http://127.0.0.1:{PORT}")
        ctx = b.contexts[0]
        flow_pages = [pg for pg in ctx.pages if "flow" in pg.url]
        if flow_pages:
            page = flow_pages[0]
        else:
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(PROJ, wait_until="domcontentloaded")
        page.wait_for_timeout(8000)
        page.bring_to_front()

        # DETECCAO DE SESSAO EXPIRADA: se apos o goto estamos na tela de login
        # do Google, NAO adianta tentar — o usuario precisa logar de novo.
        # Detectamos UMA vez e falhamos cedo pra nao desperdiçar 3 tentativas.
        is_login, login_url = _is_login_page(page)
        if is_login:
            log(f"[SESSAO_EXPIRADA] pagina de login detectada ({login_url}).")
            log(f"[SESSAO_EXPIRADA] rode relogin_fabrica.bat e faca login no Google.")
            raise SessaoExpiradaError(f"sessao expirada (url={login_url})")

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
        # 2026-07-29 (pedido Haylla): o vídeo mais barato do Flow (Veo Lite)
        # custa ~10 creditos. Uma conta com saldo ABAIXO disso (ex: 5) nao
        # gera nada — antes o check era <=0 e o bot desperdicava 24min tentando
        # numa conta com 5 creditos. Agora marca esgotada se saldo < CREDITO_MINIMO.
        CREDITO_MINIMO = 10
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

        if "Adicionar midia" not in _body and "Adicionar mídia" not in _body and \
           "Nova sessão" not in _body and "Nova sessao" not in _body:
            log("[sessao] fora de um projeto — tentando criar novo")
            res = page.evaluate("""() => {
                const btns = Array.from(document.querySelectorAll('button, a'));
                for (const b of btns) {
                    const t = (b.innerText || '').trim();
                    if (t.includes('Novo projeto') || t === 'Create' ||
                        t.includes('Create new') || t.includes('New project')) {
                        const r = b.getBoundingClientRect();
                        return {x: r.x + r.width/2, y: r.y + r.height/2, text: t};
                    }
                }
                return null;
            }""")
            if res:
                page.mouse.click(res['x'], res['y'])
                log(f"[sessao] novo projeto click: '{res['text']}'")
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
                        const r = b.getBoundingClientRect();
                        return {x: r.x + r.width/2, y: r.y + r.height/2, text: t};
                    }
                }
                return null;
            }""")
            if res:
                page.mouse.click(res['x'], res['y'])
                log(f"[sessao] criou projeto: '{res['text']}'")
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

        # NOVA SESSAO: reseta o chat pra geracao limpa.
        # UI 2026-07: botao tem icone material ("edit_square") + texto ("Nova sessão")
        # Usamos mouse click via coordenadas (Material UI exige).
        _sessao_ok = False
        for txt_ns in ["Nova sessão", "Nova sessao", "New session"]:
            res = page.evaluate("""(needle) => {
                const all = Array.from(document.querySelectorAll('button'));
                for (const b of all) {
                    if (!b.offsetParent) continue;
                    const t = (b.innerText || '').trim();
                    if (t.includes(needle)) {
                        const r = b.getBoundingClientRect();
                        return {x: r.x + r.width/2, y: r.y + r.height/2, text: t};
                    }
                }
                return null;
            }""", txt_ns)
            if res:
                page.mouse.click(res['x'], res['y'])
                log(f"[sessao] nova sessao criada ({res['text']})")
                page.wait_for_timeout(3000)
                _sessao_ok = True
                break
        if not _sessao_ok:
            log("[sessao] AVISO: nao achei botao nova sessao — continuando na atual")

        final = flow_bot._enrich_prompt(prompt, model=modelo.split(" - ")[0],
                                        audio=True, duration=duration,
                                        aspect_ratio=aspect)
        # Se tem imagem, instruir o agente a usar image-to-video
        if image:
            final = (f"Use the uploaded image as the starting frame "
                     f"(image-to-video mode). Animate it: {final}")
        log("prompt: " + final)

        # CAUSA RAIZ (jobs em sequencia falhavam no .type): ao terminar um render,
        # o Flow deixa aberto o modal "Gerar video, que custa N creditos?" com os
        # botoes renderizados FORA da tela (y negativo). Ele NAO fecha por clique
        # (mouse real, .click() nativo, dispatchEvent, locator force — testados,
        # todos falham) e BLOQUEIA o .type() do proximo job. O unico jeito
        # confiavel de dispensa-lo e recarregar a pagina. Por isso: preparar (modo
        # Veo + digitar + enviar) com RETRY que recarrega em caso de falha.
        def _modal_creditos_aberto():
            try:
                t = page.evaluate("() => document.body.innerText")
                return ("custa" in t and "crédito" in t)
            except Exception:
                return False

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

                if _modal_creditos_aberto():
                    log("modal de creditos aberto — recarregando p/ dispensar")
                    page.goto(PROJ, wait_until="domcontentloaded")
                    page.wait_for_timeout(6000)

                # GARANTIR MODO VEO (video) — senao sai imagem Nano Banana
                garantir_modo_veo(page, aspect=aspect, modelo=modelo, log=log)

                # image-to-video: sobe a imagem inicial ANTES do prompt
                if image:
                    _subir_imagem(page, image, log=log)

                before = poster_ids(page)
                log(f"posters antes: {len(before)} (tentativa {tentativa})")

                box, bsel = flow_bot._find_first(
                    page, flow_bot.PROMPT_SELECTORS, timeout=20000)
                if not box:
                    raise RuntimeError("caixa de prompt nao achada")
                # Fechar overlays que interceptam cliques (painel lateral/media)
                page.evaluate("""() => {
                    document.querySelectorAll('[data-state="open"][aria-hidden="true"]')
                        .forEach(el => el.style.display = 'none');
                }""")
                page.wait_for_timeout(300)
                # Force click pra ignorar interceptacao de overlays
                box.click(timeout=8000, force=True)
                page.wait_for_timeout(500)
                # .type() char a char e o unico metodo que o React do Flow reconhece.
                # Prompts agora sao curtos (<400 chars) entao 60s e suficiente.
                if bsel == "[contenteditable='true']":
                    box.type(final, timeout=60000)
                else:
                    box.fill(final, timeout=30000)
                page.wait_for_timeout(600)
                # Submit: usar o mesmo metodo do flow_bot (testado e funcional)
                btn = flow_bot._click_button_with_text(
                    page, flow_bot.SUBMIT_TEXT_HINTS, timeout=8000)
                if btn:
                    btn.click()
                    log("prompt submetido (botao arrow_forward)")
                else:
                    log("AVISO: botao submit nao encontrado, tentando Enter")
                    box.press("Enter")
                page.wait_for_timeout(2000)
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
                except Exception:
                    pass
        else:
            raise RuntimeError(f"nao consegui enviar o prompt: {ultimo_erro}")

        # DOWNLOAD direto: videos gerados aparecem como <video src*=getMediaUrlRedirect>
        # no DOM. Basta pegar a URL e baixar via request autenticado (cookies da sessao).
        def _baixar_video_direto(vid):
            """Baixa video pela API redirect usando cookies da sessao. Retorna True se OK."""
            url = f"https://labs.google/fx/api/trpc/media.getMediaUrlRedirect?name={vid}"
            try:
                resp = page.request.get(url)
                ct = resp.headers.get("content-type", "")
                body = resp.body()
                if not resp.ok:
                    log(f"  download {vid[:8]}: status={resp.status}")
                    return False
                if "video" not in ct:
                    log(f"  download {vid[:8]}: nao e video (content-type={ct}, {len(body)//1024}KB)")
                    return False
                if len(body) < 500_000:
                    log(f"  download {vid[:8]}: muito pequeno ({len(body)//1024}KB) — provavelmente thumbnail")
                    return False
                os.makedirs(os.path.dirname(out_path), exist_ok=True)
                with open(out_path, "wb") as f:
                    f.write(body)
                log(f"OK video salvo: {out_path} ({len(body)//1024}KB)")
                return True
            except Exception as e:
                log(f"  download {vid[:8]} falhou: {e}")
            return False

        # CRITICO (bug md5 identico 03/07): NAO recarregar a pagina no loop — o
        # goto(PROJ) reembaralhava a grade e trazia VIDEOS VELHOS de volta como
        # "novos", que eram baixados no lugar do render atual. O poster do render
        # aparece via React sem reload. Alem disso, render Veo real NUNCA termina
        # em segundos: so aceitamos poster novo apos MIN_ESPERA_S.
        MIN_ESPERA_S = 45
        # retry do erro transitorio "Algo deu errado" (lista p/ mutar no loop)
        _retry_erro = [0]
        _MAX_RETRY_ERRO = 3
        t0 = time.time()
        vistos = set(before)  # posters ja conhecidos (inclui a imagem uploadada)
        vistos_video = set(video_ids(page))  # videos ja presentes antes do prompt
        deadline = time.time() + config.GEN_TIMEOUT_S + 120
        while time.time() < deadline:
            page.wait_for_timeout(config.POLL_S * 1000)
            body = ""
            try:
                body = page.evaluate("() => document.body.innerText")
            except Exception:
                pass
            if "Aprovar e não perguntar de novo" in body:
                r = page.evaluate(JS_ROBUST_CLICK, "Aprovar e não perguntar de novo")
                print(f"[aprovacao] clique robusto: {r}", flush=True)
                page.wait_for_timeout(1500)

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
                            btn.click()
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

            # === DETECCAO PRIMARIA: <video> tags novas (metodo confiavel) ===
            vids_agora = video_ids(page)
            novos_vids = [v for v in vids_agora if v not in vistos_video]
            if novos_vids and (time.time() - t0) >= MIN_ESPERA_S:
                for vid in novos_vids:
                    log(f"video novo detectado: {vid[:8]}... -> baixando")
                    if _baixar_video_direto(vid):
                        return out_path
                    vistos_video.add(vid)
            elif novos_vids:
                for vid in novos_vids:
                    log(f"video cedo demais ({int(time.time()-t0)}s), marcando visto: {vid[:8]}")
                    vistos_video.add(vid)

            # === DETECCAO SECUNDARIA: img posters (fallback legado) ===
            atuais = poster_ids_ordenados(page)
            novos = [v for v in atuais if v not in vistos]
            if novos and (time.time() - t0) < MIN_ESPERA_S:
                for vid in novos:
                    vistos.add(vid)
                novos = []
            for vid in novos:
                log("poster novo: " + vid + " -> tentando download direto")
                if _baixar_video_direto(vid):
                    return out_path
                vistos.add(vid)

            rem = int(deadline - time.time())
            log(f"...aguardando ({rem}s)")

        # VARREDURA FINAL: tenta tudo que apareceu no ultimo momento
        log("deadline atingido — varredura final")
        for vid in video_ids(page):
            if vid not in vistos_video:
                log(f"video (final): {vid[:8]}... -> baixando")
                if _baixar_video_direto(vid):
                    return out_path
        for vid in poster_ids_ordenados(page):
            if vid not in vistos:
                log(f"poster (final): {vid[:8]}... -> baixando")
                if _baixar_video_direto(vid):
                    return out_path

        raise RuntimeError("timeout sem video novo baixavel")

def _sistema_pausado():
    """Le logs/PAUSE_SYSTEM. True se pausa ativa (until no futuro OU sem until).
    Checa ANTES de abrir Chrome. Nao remove o arquivo (quem gerencia e o cron)."""
    import json as _json
    pause_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", "PAUSE_SYSTEM")
    if not os.path.exists(pause_file):
        return False
    try:
        with open(pause_file, "r", encoding="utf-8") as f:
            data = _json.load(f)
        until = data.get("until")
        if not until:
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
    except DireitosAutoraisError as e:
        # Marcador p/ cron distinguir de falha normal: NAO re-enfileirar igual.
        print(f"DIREITOS_AUTORAIS '{e}'", flush=True)
        sys.exit(4)  # exit code 4 = recusado por politica/direitos
