#!/usr/bin/env python3
r"""gemini_video.py — Gera VÍDEO (Veo) pelo app gemini.google.com (navegador oculto).

Segunda fonte de vídeo, independente do Flow (D:\veo) e da API paga: usa a cota de
vídeo do app web do Gemini ("Create video" -> Veo), SEPARADA da do Flow e da de texto
do Argon. Roda de preferência em contas que já esgotaram o Argon (texto zerado; vídeo
é outra cota) — assim não gasta crédito de texto. Se o Flow cair/esgotar, esta fonte
continua, e vice-versa.

Reaproveita do gemini_argon.py: cofre (Chrome oculto pela saída fixa da conta), a FILA
de contas e a limpeza de conversa. Cada conta fala só pela própria saída (regra do IP).

Fluxo (mapeado 13/11): campo -> "Upload & tools" -> "Create video" -> digita prompt ->
Enter -> espera 1-5 min (vigia por print, nunca timeout cego) -> baixa o <video>.

Uso módulo:
    from gemini_video import gerar
    ok, detalhe = gerar("a cat astronaut floating in space, cinematic", r"D:\saida\gato.mp4")

Uso CLI:
    python -X utf8 -I gemini_video.py "prompt do vídeo" D:\saida\video.mp4
    python -X utf8 -I gemini_video.py --conta murilodoctor192 --visivel "prompt" saida.mp4
"""
import argparse
import logging
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, r"D:\logins-google")
sys.path.insert(0, r"D:\gemini-argo")   # -I tira a pasta do script do path
import cofre
import gemini_argon as ga

log = logging.getLogger("gemini_video")
if not log.handlers:
    logging.basicConfig(
        filename=str(Path(r"D:\gemini-argo") / "video.log"),
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

TIMEOUT_VIDEO = 420   # Veo leva 1-5 min; 7 min de folga
PRINT_DIR = Path(r"D:\gemini-argo\_teste_video")
RECUSA = ("can't create", "cannot create", "unable to", "não posso", "nao posso",
          "I'm not able", "I am unable", "violates", "can't help with")


def _esperar_app(pg, timeout_s=40):
    """Espera o app do Gemini carregar de verdade (campo de texto visível)."""
    inicio = time.time()
    while time.time() - inicio < timeout_s:
        for sel in ('div[contenteditable="true"]', '[aria-label*="Gemini"]', 'div[role="textbox"]'):
            try:
                if pg.locator(sel).first.is_visible(timeout=800):
                    return True
            except Exception:
                pass
        time.sleep(1.5)
    return False


def _fechar_popups(pg):
    """Fecha avisos/modais que bloqueiam cliques. Inclui o modal grande 'Conectar estes apps
    do Google ao Gemini?' (botão 'Continuar'), que aparece com atraso e intercepta cliques."""
    for _ in range(6):
        achou = False
        for t in ("Teste já", "Try it", "Teste ja", "Continuar", "Continue", "Entendi",
                  "Got it", "Ok", "OK", "Aceitar", "No thanks", "Agora não", "Começar", "Get started"):
            try:
                b = pg.locator(f'button:has-text("{t}")').first
                if b.is_visible(timeout=500):
                    b.click(force=True, timeout=4000)
                    achou = True
                    time.sleep(0.7)
            except Exception:
                pass
        # Esc fecha menus/diálogos que não têm botão
        if not achou:
            break
        time.sleep(0.5)


def _abrir_create_video(pg):
    """Abre o menu 'Envio e ferramentas' (+ na barra) e clica em 'Criar vídeo'. PT e EN."""
    _fechar_popups(pg)
    # foca o campo primeiro (o botão de tools fica na barra de composição)
    for sel in ('div[contenteditable="true"]', 'div[role="textbox"]'):
        try:
            c = pg.locator(sel).first
            if c.is_visible(timeout=2000):
                c.click()
                time.sleep(0.4)
                break
        except Exception:
            continue
    # abre o menu (tenta várias vezes; às vezes o 1º clique só dá foco ou um popup bloqueia)
    aberto = False
    for _ in range(4):
        _fechar_popups(pg)   # modal "Conectar apps" pode reaparecer antes de cada tentativa
        for sel in ['button[aria-label*="Envio e ferramentas"]', 'button[aria-label*="ferramentas"]',
                    'button[aria-label*="Upload & tools"]', 'button[aria-label*="tools"]',
                    'button[aria-label*="Upload"]']:
            try:
                b = pg.locator(sel).first
                if b.is_visible(timeout=2000):
                    b.click(force=True, timeout=5000)
                    time.sleep(1.3)
                    aberto = True
                    break
            except Exception:
                continue
        if aberto and (pg.locator('text=Criar vídeo').count() or pg.locator('text=Create video').count()):
            break
        time.sleep(0.8)
    if not aberto:
        return False
    # itens do menu são texto puro: clica pelo texto (PT primeiro, depois EN)
    for sel in ['text=Criar vídeo', 'text=Criar video', 'text=Create video',
                ':text("Criar vídeo")', ':text("Create video")']:
        try:
            el = pg.locator(sel).first
            if el.is_visible(timeout=2500):
                el.click(force=True, timeout=5000)
                time.sleep(1.5)
                log.info("Criar vídeo ativado via %s", sel)
                return True
        except Exception:
            continue
    return False


def _enviar_prompt(pg, texto):
    # no modo "Criar vídeo" o campo é um <textarea>; no chat normal é contenteditable
    for sel in ("textarea", 'div[contenteditable="true"]', 'div[role="textbox"]', ".ql-editor"):
        try:
            campo = pg.locator(sel).first
            if campo.is_visible(timeout=3000):
                campo.click()
                time.sleep(0.3)
                pg.keyboard.insert_text(texto)
                time.sleep(0.6)
                pg.keyboard.press("Enter")
                return True
        except Exception:
            continue
    return False


def _esperar_video(pg, apelido, timeout_s=TIMEOUT_VIDEO):
    """Espera o <video> ficar pronto. Vigia por print a cada 30 s (nunca timeout cego).
    Retorna o locator do video, 'recusa' ou None."""
    inicio = time.time()
    ultima_print = 0
    while time.time() - inicio < timeout_s:
        decorrido = int(time.time() - inicio)
        # vigia por print periódico (memória: navegador longo -> print, nunca espera cega)
        if decorrido - ultima_print >= 30:
            ultima_print = decorrido
            try:
                PRINT_DIR.mkdir(parents=True, exist_ok=True)
                pg.screenshot(path=str(PRINT_DIR / f"vigia_{apelido}_{decorrido:03d}s.png"))
            except Exception:
                pass
            log.info("%s: esperando vídeo há %ds", apelido, decorrido)
        # vídeo pronto?
        try:
            for v in pg.locator("video").all():
                try:
                    if not v.is_visible(timeout=200):
                        continue
                    src = v.get_attribute("src") or ""
                    if src:   # <video> com src = render terminou
                        time.sleep(2)
                        return v
                except Exception:
                    continue
        except Exception:
            pass
        # recusa em texto (sem nenhum vídeo na página)
        try:
            if not pg.locator("video").count():
                corpo = pg.locator('[data-message-author-role="model"]').last.inner_text(timeout=1200)
                if corpo and len(corpo) > 40 and any(r.lower() in corpo.lower() for r in RECUSA):
                    return "recusa"
        except Exception:
            pass
        time.sleep(5)
    return None


def _baixar(pg, video, saida):
    """Baixa o vídeo. 1º tenta o botão de download; senão pega o src do <video>."""
    Path(saida).parent.mkdir(parents=True, exist_ok=True)
    # 1) botão de download (hover no vídeo revela os controles)
    try:
        video.hover(timeout=3000)
        time.sleep(0.5)
    except Exception:
        pass
    for sel in ['button[aria-label*="Download"]', 'button[aria-label*="Baixar"]',
                'button[aria-label*="download"]']:
        try:
            btn = pg.locator(sel).first
            if btn.is_visible(timeout=2000):
                with pg.expect_download(timeout=60000) as dl:
                    btn.click()
                dl.value.save_as(str(saida))
                if Path(saida).exists() and Path(saida).stat().st_size > 10000:
                    return True
        except Exception:
            continue
    # 2) src direto do <video> (pode ser http ou blob)
    try:
        src = video.get_attribute("src") or ""
        if src.startswith("http"):
            # baixa com os cookies da sessão
            try:
                cookies = pg.context.cookies()
                ck = "; ".join(f"{c['name']}={c['value']}" for c in cookies)
            except Exception:
                ck = ""
            req = urllib.request.Request(src, headers={"Cookie": ck, "User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=120) as r:
                Path(saida).write_bytes(r.read())
            return Path(saida).exists() and Path(saida).stat().st_size > 10000
        if src.startswith("blob:"):
            # blob: busca via fetch dentro da página e devolve base64
            b64 = pg.evaluate("""async (u) => {
                const r = await fetch(u); const b = await r.blob();
                return await new Promise(res => { const fr = new FileReader();
                    fr.onload = () => res(fr.result.split(',')[1]); fr.readAsDataURL(b); });
            }""", src)
            import base64
            Path(saida).write_bytes(base64.b64decode(b64))
            return Path(saida).exists() and Path(saida).stat().st_size > 10000
    except Exception as e:
        log.error("baixar via src falhou: %s", e)
    return False


def gerar(prompt, saida, conta=None, visivel=False):
    """Gera um vídeo e salva em `saida`. Percorre a fila de contas. Retorna (ok, detalhe)."""
    from playwright.sync_api import sync_playwright

    tentadas, ultimo = 0, ""
    max_tentativas = 1 if conta else 4
    while tentadas < max_tentativas:
        try:
            apelido = conta or ga.proxima_conta()
        except RuntimeError as e:
            return False, f"sem conta pronta ({e})"
        tentadas += 1
        log.info("Gerando vídeo com %s: %s", apelido, prompt[:60])
        porta, proc = cofre.abrir(apelido, url="about:blank", visivel=visivel)
        br = None
        try:
            with sync_playwright() as pw:
                br = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
                pg = br.contexts[0].new_page()
                pg.goto("https://gemini.google.com/app", wait_until="domcontentloaded", timeout=60000)
                time.sleep(4)
                ga._fechar_popup_idade(pg)
                if not _esperar_app(pg):
                    ga.marcar_uso(apelido, sucesso=False, erro_msg="app não carregou")
                    ultimo = "app do Gemini não carregou (tela em branco)"
                    continue
                time.sleep(3)         # deixa o modal "Conectar apps" aparecer
                _fechar_popups(pg)

                if not _abrir_create_video(pg):
                    # página pode ter vindo quebrada (CSS/render instável): recarrega 1x
                    log.info("%s: Criar vídeo não abriu, recarregando página", apelido)
                    pg.goto("https://gemini.google.com/app", wait_until="domcontentloaded", timeout=60000)
                    time.sleep(4)
                    _esperar_app(pg)
                    time.sleep(3)
                    _fechar_popups(pg)
                    if not _abrir_create_video(pg):
                        ga.marcar_uso(apelido, sucesso=False, erro_msg="não achei Criar vídeo")
                        ultimo = "não achei 'Criar vídeo' no menu (página instável)"
                        continue
                # onboarding "Crie vídeos com o Gemini Omni" (botão "Teste já") cobre o campo
                time.sleep(1.5)
                _fechar_popups(pg)
                if not _enviar_prompt(pg, prompt):
                    try:
                        PRINT_DIR.mkdir(parents=True, exist_ok=True)
                        pg.screenshot(path=str(PRINT_DIR / f"falha_campo_{apelido}.png"))
                        (PRINT_DIR / f"falha_campo_{apelido}.html").write_text(pg.content(), encoding="utf-8")
                    except Exception:
                        pass
                    ga.marcar_uso(apelido, sucesso=False, erro_msg="não enviou prompt")
                    ultimo = "não achei o campo de texto"
                    continue

                res = _esperar_video(pg, apelido)
                if res == "recusa":
                    ga.marcar_uso(apelido, sucesso=True)
                    ga._limpar_conversa(pg)
                    return False, "Gemini recusou o prompt (política)"
                if res is None:
                    ga.marcar_uso(apelido, sucesso=False, erro_msg="sem vídeo no tempo")
                    ga.marcar_sem_cota(apelido)   # provável cota de vídeo esgotada
                    ultimo = "não gerou vídeo (cota de vídeo pode ter acabado ou demorou demais)"
                    ga._limpar_conversa(pg)
                    continue

                if _baixar(pg, res, saida):
                    ga.marcar_uso(apelido, sucesso=True)
                    ga._limpar_conversa(pg)
                    return True, f"Gemini vídeo ({apelido})"
                ga.marcar_uso(apelido, sucesso=False, erro_msg="gerou mas não baixou")
                ultimo = "gerou mas não consegui baixar"
                ga._limpar_conversa(pg)
        except Exception as e:
            log.error("erro com %s: %s", apelido, e)
            ga.marcar_uso(apelido, sucesso=False, erro_msg=str(e))
            ultimo = str(e)[:100]
        finally:
            try: cofre.fechar(proc, br, apelido)
            except Exception: pass
            ga.soltar(apelido)
        if conta:
            break
    return False, f"falhou após {tentadas} conta(s): {ultimo}"


def main():
    ap = argparse.ArgumentParser(description="Gera vídeo pelo app Gemini (Veo, navegador oculto)")
    ap.add_argument("prompt")
    ap.add_argument("saida", help="caminho do .mp4 de saída")
    ap.add_argument("--conta", help="apelido fixo (senão usa a fila do Argon)")
    ap.add_argument("--visivel", action="store_true")
    args = ap.parse_args()
    ok, det = gerar(args.prompt, args.saida, conta=args.conta, visivel=args.visivel)
    print(("OK: " if ok else "FALHOU: ") + det)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
