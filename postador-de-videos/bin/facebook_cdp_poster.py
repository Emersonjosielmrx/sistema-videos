#!/usr/bin/env python3
"""Posta video/Reel no Facebook via Playwright (conecta no Chrome CDP ja logado).

Usa Playwright conectando no Chrome real (porta CDP) com sessao logada.
Playwright.set_input_files() funciona com React, diferente do CDP puro.

Uso:
  python facebook_cdp_poster.py --video "D:/path/video.mp4" --caption "texto #hash"
  python facebook_cdp_poster.py --video "D:/path/video.mp4" --page "https://www.facebook.com/mundosolarenergia/" --port 9401
"""
import sys
import time
import argparse
from pathlib import Path

if sys.stdout:  # pythonw (tarefa agendada) não tem stdout

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
DEFAULT_PORT = 9401
DEFAULT_CAPTION = "Energia solar que transforma! #energiasolar #solar #fyp #viral"
DEFAULT_PAGE = "https://www.facebook.com/mundosolarenergia/"


def post_reel_facebook(video_path, port, caption, page_url):
    from politica import garantir_1080 as _g1080  # 31/10 REGRA da dona: nada sai com menos de 1080p
    video_path = type(video_path)(_g1080(video_path)) if not isinstance(video_path, str) else str(_g1080(video_path))
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
        context = browser.contexts[0] if browser.contexts else browser.new_context()
        page = context.new_page()

        try:
            # 1. Navegar pra pagina
            print(f"  Navegando pra {page_url}", flush=True)
            page.goto(page_url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(5)

            url = page.url
            print(f"  URL: {url}", flush=True)
            if "login" in url.lower():
                print(f"  NAO LOGADO — faca login manual na janela do Chrome (porta {port})", flush=True)
                return False

            # 2. Ir pra reels da pagina
            reel_url = page_url.rstrip("/") + "/reels/"
            print(f"  Navegando pra {reel_url}", flush=True)
            page.goto(reel_url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(4)

            # 3. Clicar "Criar reel"
            print("  Procurando botao Criar Reel...", flush=True)
            criar_btn = None
            for _ in range(10):
                for el in page.query_selector_all("a, button, div[role=button], span[role=button]"):
                    txt = (el.text_content() or "").strip().lower()
                    if "criar reel" in txt or "create reel" in txt:
                        criar_btn = el
                        break
                if criar_btn:
                    break
                time.sleep(2)

            if not criar_btn:
                print("  ERRO: botao 'Criar Reel' nao encontrado", flush=True)
                return False

            criar_btn.click()
            print("  Criar Reel clicado", flush=True)
            time.sleep(4)

            # 4. Upload do video
            video_abs = str(Path(video_path).resolve())
            uploaded = False

            # Estrategia 1: FileChooser via botao "Carregar" (intercepta dialogo nativo)
            print("  Estrategia 1: FileChooser via botao Carregar...", flush=True)
            upload_btn = None
            for _ in range(10):
                for el in page.query_selector_all("button, div[role=button], label, span[role=button]"):
                    txt = (el.text_content() or "").strip().lower()
                    if txt in ("carregar", "upload"):
                        upload_btn = el
                        break
                if upload_btn:
                    break
                time.sleep(1)

            if upload_btn:
                try:
                    with page.expect_file_chooser(timeout=10000) as fc_info:
                        upload_btn.click()
                    file_chooser = fc_info.value
                    file_chooser.set_files(video_abs)
                    print(f"  FileChooser OK: {Path(video_path).name}", flush=True)
                    time.sleep(5)
                    uploaded = _check_upload_accepted(page)
                except Exception as e:
                    print(f"  FileChooser falhou: {e}", flush=True)

            # Estrategia 2: set_input_files no input[type=file]
            if not uploaded:
                print("  Estrategia 2: set_input_files...", flush=True)
                file_input = page.query_selector("input[type=file]")
                if file_input:
                    file_input.set_input_files(video_abs)
                    time.sleep(5)
                    uploaded = _check_upload_accepted(page)
                    print(f"  set_input_files: accepted={uploaded}", flush=True)
                else:
                    print("  input[type=file] nao encontrado", flush=True)

            # Estrategia 3: JS com dispatch change event no input
            if not uploaded:
                print("  Estrategia 3: dispatch change event...", flush=True)
                file_input = page.query_selector("input[type=file]")
                if file_input:
                    file_input.set_input_files(video_abs)
                    page.evaluate("""(input) => {
                        input.dispatchEvent(new Event('change', {bubbles: true}));
                        input.dispatchEvent(new Event('input', {bubbles: true}));
                    }""", file_input)
                    time.sleep(5)
                    uploaded = _check_upload_accepted(page)
                    print(f"  dispatch change: accepted={uploaded}", flush=True)

            if not uploaded:
                print("  TODAS as estrategias de upload falharam", flush=True)
                _debug_page(page)
                return False

            # 5. Clicar "Avançar" repetidamente ate chegar na tela de descricao/publicar
            # Facebook Reel Studio tem multiplas telas: upload → edit/trim → descricao
            # Cada tela tem um botao "Avançar" que leva pra proxima
            print("  Navegando pelas telas do Reel Studio...", flush=True)
            avancar_clicks = 0
            reached_final = False
            total_elapsed = 0

            for round_num in range(6):  # max 6 rodadas (upload + trim + descricao + margem)
                # Esperar botao Avançar ou tela final (Publicar/editor de descricao)
                found_next = False
                for i in range(30):  # ate 150s por rodada
                    time.sleep(5)
                    total_elapsed += 5

                    btns_text = []
                    for el in page.query_selector_all("button, div[role=button], span[role=button], a[role=button]"):
                        txt = (el.text_content() or "").strip()
                        if txt and len(txt) < 60:
                            btns_text.append(txt)

                    if i % 3 == 0:
                        editors = page.query_selector_all("[contenteditable=true], [role=textbox], textarea")
                        print(f"  [{total_elapsed}s] ronda={round_num+1} clicks={avancar_clicks} botoes={[b for b in btns_text if len(b) < 35][:12]} eds={len(editors)}", flush=True)

                    # Checar se ja chegou na tela final (tem Publicar ou editor de descricao)
                    has_publish = False
                    for el in page.query_selector_all("button, div[role=button]"):
                        txt = (el.text_content() or "").strip().lower()
                        if txt in ("publicar", "publish", "compartilhar reel", "share reel",
                                   "publicar reel", "publish reel", "compartilhar", "share"):
                            has_publish = True
                            break

                    editors = page.query_selector_all("[contenteditable=true], [role=textbox], textarea")
                    has_caption_editor = False
                    for ed in editors:
                        aria = (ed.get_attribute("aria-label") or "").lower()
                        ph = (ed.get_attribute("placeholder") or "").lower()
                        if any(k in aria + ph for k in ("descri", "caption", "escrev", "write", "diga", "texto")):
                            has_caption_editor = True
                            break

                    if has_publish or has_caption_editor:
                        print(f"  Tela final encontrada ({total_elapsed}s): pub={has_publish} caption={has_caption_editor} eds={len(editors)}", flush=True)
                        reached_final = True
                        break

                    # Se tiver editors genéricos + nao for tela de upload, considerar final
                    btns_lower = [b.lower() for b in btns_text]
                    still_upload = any("arraste e solte" in t or "drag and drop" in t for t in btns_lower)
                    if len(editors) > 0 and not still_upload and avancar_clicks >= 1:
                        print(f"  Editor generico encontrado ({total_elapsed}s): eds={len(editors)}", flush=True)
                        reached_final = True
                        break

                    # Procurar e clicar Avançar/Next
                    for el in page.query_selector_all("button, div[role=button], span[role=button]"):
                        txt = (el.text_content() or "").strip().lower()
                        if txt in ("avançar", "next", "próximo", "proximo"):
                            el.click()
                            avancar_clicks += 1
                            print(f"  Avançar #{avancar_clicks} clicado ({total_elapsed}s)", flush=True)
                            found_next = True
                            time.sleep(4)
                            total_elapsed += 4
                            break
                    if found_next:
                        break

                if reached_final:
                    break

                if not found_next and round_num > 0:
                    print(f"  Nenhum Avançar encontrado na ronda {round_num+1}, tentando mais...", flush=True)
                    if total_elapsed > 180:
                        break

            if not reached_final and avancar_clicks == 0:
                print("  ERRO: nunca encontrou botao Avançar", flush=True)
                _debug_page(page)
                return False

            if not reached_final:
                print(f"  WARN: clicou {avancar_clicks}x Avançar mas nao chegou na tela final", flush=True)
                _debug_page(page)

            # 7. Preencher caption
            time.sleep(2)
            print("  Preenchendo descricao...", flush=True)
            wrote = False
            for el in page.query_selector_all("[contenteditable=true], [role=textbox]"):
                aria = (el.get_attribute("aria-label") or "").lower()
                ph = (el.get_attribute("placeholder") or "").lower()
                if any(k in aria + ph for k in ("descri", "caption", "escrev", "write", "diga algo", "texto", "text")):
                    el.click()
                    time.sleep(0.5)
                    el.fill("")
                    page.keyboard.type(caption, delay=10)
                    wrote = True
                    print(f"  Caption escrita via editor ({aria[:30]})", flush=True)
                    break

            if not wrote:
                editors = page.query_selector_all("[contenteditable=true], [role=textbox]")
                if editors:
                    editors[0].click()
                    time.sleep(0.5)
                    page.keyboard.type(caption, delay=10)
                    wrote = True
                    print("  Caption escrita via fallback editor", flush=True)

            if not wrote:
                ta = page.query_selector("textarea")
                if ta:
                    ta.fill(caption)
                    wrote = True
                    print("  Caption escrita via textarea", flush=True)

            if not wrote:
                print("  WARN: nao encontrou campo de descricao", flush=True)

            # 8. Clicar "Publicar" / "Share"
            time.sleep(2)
            print("  Clicando Publicar...", flush=True)
            shared = False
            for _ in range(15):
                for el in page.query_selector_all("button, div[role=button]"):
                    txt = (el.text_content() or "").strip().lower()
                    if txt in ("publicar", "publish", "compartilhar reel", "share reel",
                               "publicar reel", "publish reel", "compartilhar", "share",
                               "postar", "post"):
                        disabled = el.get_attribute("disabled") or el.get_attribute("aria-disabled")
                        if not disabled or disabled == "false":
                            el.click()
                            shared = True
                            print(f"  Publicar clicado: '{txt}'", flush=True)
                            break
                if shared:
                    break
                time.sleep(2)

            if not shared:
                print("  ERRO: nao encontrou botao Publicar/Share", flush=True)
                _debug_page(page)
                return False

            # 9. Aguardar confirmacao
            print("  Aguardando confirmacao...", flush=True)
            for i in range(40):
                time.sleep(3)
                body_text = (page.text_content("body") or "").lower()
                if any(x in body_text for x in (
                    "reel foi publicado", "reel was published",
                    "reel foi compartilhado", "reel has been shared",
                    "publicado com sucesso", "published successfully",
                    "video publicado", "video published",
                    "your reel", "seu reel"
                )):
                    print(f"  POSTADO com sucesso! ({(i+1)*3}s)", flush=True)
                    return True

            print("  Publicar clicado — confirmacao textual nao detectada (provavel sucesso)", flush=True)
            return True

        except Exception as e:
            print(f"  ERRO: {e}", flush=True)
            return False
        finally:
            page.close()


def _check_upload_accepted(page):
    """Verifica se a UI do Facebook saiu do estado 'upload' pro estado 'editor'."""
    has_video = page.query_selector("video") is not None
    btns_text = []
    for el in page.query_selector_all("button, div[role=button], span[role=button]"):
        txt = (el.text_content() or "").strip().lower()
        if txt and len(txt) < 60:
            btns_text.append(txt)
    still_upload = any("arraste e solte" in t or "drag and drop" in t for t in btns_text)
    has_next = any(t in ("avançar", "next", "próximo", "proximo") for t in btns_text)
    has_publish = any(t in ("publicar", "publish", "compartilhar", "share") for t in btns_text)
    editors = page.query_selector_all("[contenteditable=true], [role=textbox], textarea")
    accepted = has_video or has_next or has_publish or (len(editors) > 0 and not still_upload)
    print(f"  _check: video={has_video} still_upload={still_upload} next={has_next} pub={has_publish} eds={len(editors)} → accepted={accepted}", flush=True)
    return accepted


def _debug_page(page):
    btns = []
    for el in page.query_selector_all("button, div[role=button], a"):
        txt = (el.text_content() or "").strip()[:40]
        if txt:
            btns.append(txt)
    print(f"  Botoes visiveis: {btns[:20]}", flush=True)
    editors = page.query_selector_all("[contenteditable=true], [role=textbox], textarea")
    print(f"  Editores: {len(editors)}", flush=True)
    print(f"  URL: {page.url}", flush=True)


def main():
    parser = argparse.ArgumentParser(description="Posta video/Reel no Facebook via Playwright CDP")
    parser.add_argument("--video", required=True, help="Caminho do video MP4")
    parser.add_argument("--caption", default=DEFAULT_CAPTION, help="Texto + hashtags")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Porta CDP do Chrome")
    parser.add_argument("--page", default=DEFAULT_PAGE, help="URL da pagina do Facebook")
    args = parser.parse_args()

    if not Path(args.video).exists():
        print(f"ERRO: video nao encontrado: {args.video}", flush=True)
        sys.exit(1)

    print(f"Chrome CDP porta {args.port}", flush=True)
    print(f"Video: {args.video}", flush=True)
    print(f"Pagina: {args.page}", flush=True)
    print(f"Caption: {args.caption[:80]}...", flush=True)

    ok = post_reel_facebook(args.video, args.port, args.caption, args.page)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
