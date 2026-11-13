"""
Gerenciador YouTube — automação COMPLETA do YouTube Studio.

Operações disponíveis (todas via Playwright + Chrome CDP):
  - verificar_canal()      → verifica se tem canal, pega nome/inscritos
  - listar_videos()        → lista vídeos publicados com título/views/data
  - postar_video()         → faz upload de vídeo com título/desc/tags/thumb
  - editar_video()         → edita título/descrição/tags de vídeo existente
  - deletar_video()        → remove vídeo do canal
  - dar_like()             → curte um vídeo pelo URL
  - comentar_video()       → comenta num vídeo (próprio ou de terceiro)
  - responder_comentario() → responde comentários nos nossos vídeos
  - inscrever_canal()      → se inscreve num canal
  - criar_playlist()       → cria playlist com título/descrição
  - adicionar_na_playlist()→ adiciona vídeo a uma playlist
  - listar_playlists()     → lista playlists do canal
  - ver_analytics()        → pega métricas básicas (views, watch time, top vídeos)
  - alterar_thumbnail()    → troca thumbnail de vídeo existente
  - agendar_video()        → faz upload com data de publicação futura
  - verificar_monetizacao()→ checa status de monetização do canal
  - listar_comentarios()   → lista comentários recentes nos nossos vídeos
  - gerenciar_comunidade() → posta na aba Comunidade do canal

CLI:
  python setup_youtube.py                          → dry run (só verifica)
  python setup_youtube.py --live                   → executa com sessões reais
  python setup_youtube.py --acao postar --conta X --video caminho.mp4 --titulo "..."
  python setup_youtube.py --acao listar --conta X
  python setup_youtube.py --acao like --conta X --url https://youtube.com/watch?v=XXX
  python setup_youtube.py --acao comentar --conta X --url URL --texto "comentário"
  python setup_youtube.py --acao analytics --conta X
"""
import json
import sys
import time
import os
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared"))
from google_session import ACCOUNTS, google_browser, save_session

YT_DIR = Path(__file__).resolve().parent
STATUS_FILE = YT_DIR / "youtube_status.json"
HISTORICO_FILE = YT_DIR / "historico_acoes.jsonl"
STUDIO_URL = "https://studio.youtube.com"
YOUTUBE_URL = "https://www.youtube.com"


def _registrar_acao(acao, conta, detalhes):
    entrada = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "acao": acao,
        "conta": conta,
        "detalhes": detalhes,
    }
    with open(HISTORICO_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entrada, ensure_ascii=False) + "\n")
    return entrada


def verificar_canal(conta):
    """Verifica se a conta tem canal YouTube e retorna info básica."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto(STUDIO_URL, timeout=45000, wait_until="domcontentloaded")
            time.sleep(5)

            if "accounts.google.com" in page.url:
                return {"conta": conta, "status": "sessao_expirada"}

            if "studio.youtube.com" in page.url:
                nome_canal = ""
                el = page.query_selector('[class*="channel-name"], #channel-title, [class*="studio-header"] span')
                if el:
                    nome_canal = el.inner_text().strip()

                inscritos = "?"
                sub_el = page.query_selector('[class*="subscriber"], [class*="sub-count"]')
                if sub_el:
                    inscritos = sub_el.inner_text().strip()

                save_session(context, conta)
                return {
                    "conta": conta,
                    "status": "canal_ativo",
                    "nome_canal": nome_canal,
                    "inscritos": inscritos,
                }

            if "create_channel" in page.url or "channel_creation" in page.url:
                return {"conta": conta, "status": "sem_canal"}

            return {"conta": conta, "status": "desconhecido", "url": page.url}

    except Exception as e:
        return {"conta": conta, "status": "erro", "erro": str(e)}


def listar_videos(conta, max_videos=30):
    """Lista vídeos publicados no canal com título, views e data."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto(f"{STUDIO_URL}/channel/videos", timeout=45000, wait_until="domcontentloaded")
            time.sleep(6)

            if "accounts.google.com" in page.url:
                return {"conta": conta, "videos": [], "erro": "sessao_expirada"}

            videos = []
            rows = page.query_selector_all('ytcp-video-row, tr[class*="video"], [class*="video-row"]')
            for row in rows[:max_videos]:
                titulo = ""
                titulo_el = row.query_selector('[id="video-title"], [class*="title"] a, a[href*="video"]')
                if titulo_el:
                    titulo = titulo_el.inner_text().strip()

                views = ""
                views_el = row.query_selector('[class*="views"], [class*="metric"]')
                if views_el:
                    views = views_el.inner_text().strip()

                data = ""
                data_el = row.query_selector('[class*="date"], [class*="upload-date"]')
                if data_el:
                    data = data_el.inner_text().strip()

                visibilidade = ""
                vis_el = row.query_selector('[class*="visibility"], [class*="privacy"]')
                if vis_el:
                    visibilidade = vis_el.inner_text().strip()

                link = ""
                link_el = row.query_selector('a[href*="/video/"]')
                if link_el:
                    href = link_el.get_attribute("href") or ""
                    video_id = href.split("/video/")[-1].split("/")[0] if "/video/" in href else ""
                    if video_id:
                        link = f"https://youtu.be/{video_id}"

                if titulo:
                    videos.append({
                        "titulo": titulo,
                        "views": views,
                        "data": data,
                        "visibilidade": visibilidade,
                        "link": link,
                    })

            save_session(context, conta)
            _registrar_acao("listar_videos", conta, {"total": len(videos)})
            return {"conta": conta, "videos": videos, "total": len(videos)}

    except Exception as e:
        return {"conta": conta, "videos": [], "erro": str(e)}


def postar_video(conta, caminho_video, titulo, descricao="", tags=None, thumbnail=None, visibilidade="public"):
    """Faz upload de vídeo no YouTube Studio."""
    caminho = Path(caminho_video)
    if not caminho.exists():
        return {"sucesso": False, "erro": f"Arquivo não encontrado: {caminho}"}

    try:
        with google_browser(conta, headless=False) as (page, context, browser):
            page.goto(f"{STUDIO_URL}/channel/videos", timeout=45000, wait_until="domcontentloaded")
            time.sleep(5)

            if "accounts.google.com" in page.url:
                return {"sucesso": False, "erro": "sessao_expirada"}

            upload_btn = page.query_selector('#create-icon, button[aria-label*="Upload"], button[aria-label*="Criar"]')
            if not upload_btn:
                return {"sucesso": False, "erro": "botão de upload não encontrado"}

            upload_btn.click()
            time.sleep(2)

            upload_option = page.query_selector('tp-yt-paper-item:has-text("Upload"), tp-yt-paper-item:has-text("Enviar")')
            if upload_option:
                upload_option.click()
                time.sleep(2)

            file_input = page.query_selector('input[type="file"]')
            if not file_input:
                return {"sucesso": False, "erro": "input de arquivo não encontrado"}

            file_input.set_input_files(str(caminho.resolve()))
            time.sleep(5)

            titulo_input = page.query_selector('#textbox[aria-label*="title"], #title-textarea textbox, div[id="textbox"]')
            if titulo_input:
                titulo_input.click()
                page.keyboard.press("Control+a")
                titulo_input.type(titulo, delay=20)
                time.sleep(1)

            if descricao:
                desc_input = page.query_selector('#description-textarea #textbox, div[aria-label*="description"]')
                if desc_input:
                    desc_input.click()
                    desc_input.type(descricao, delay=15)
                    time.sleep(1)

            if thumbnail and Path(thumbnail).exists():
                thumb_input = page.query_selector('input[accept="image/*"], #file-loader input[type="file"]')
                if thumb_input:
                    thumb_input.set_input_files(str(Path(thumbnail).resolve()))
                    time.sleep(3)

            not_kids_radio = page.query_selector('#audience tp-yt-paper-radio-button[name="NOT_MADE_FOR_KIDS"], [name="VIDEO_MADE_FOR_KIDS_NOT_MFK"]')
            if not_kids_radio:
                not_kids_radio.click()
                time.sleep(1)

            for _ in range(3):
                next_btn = page.query_selector('#next-button, #step-badge-3')
                if next_btn:
                    next_btn.click()
                    time.sleep(2)

            if visibilidade == "public":
                public_radio = page.query_selector('tp-yt-paper-radio-button[name="PUBLIC"]')
                if public_radio:
                    public_radio.click()
                    time.sleep(1)
            elif visibilidade == "unlisted":
                unlisted_radio = page.query_selector('tp-yt-paper-radio-button[name="UNLISTED"]')
                if unlisted_radio:
                    unlisted_radio.click()
                    time.sleep(1)
            elif visibilidade == "private":
                private_radio = page.query_selector('tp-yt-paper-radio-button[name="PRIVATE"]')
                if private_radio:
                    private_radio.click()
                    time.sleep(1)

            for tentativa in range(60):
                progress = page.query_selector('.progress-label, [class*="upload-progress"]')
                if progress:
                    texto = progress.inner_text()
                    if "100%" in texto or "Processing" in texto.lower() or "Processando" in texto.lower():
                        break
                time.sleep(5)

            done_btn = page.query_selector('#done-button')
            if done_btn:
                done_btn.click()
                time.sleep(5)

            save_session(context, conta)
            resultado = {"sucesso": True, "titulo": titulo, "conta": conta, "visibilidade": visibilidade}
            _registrar_acao("postar_video", conta, resultado)
            return resultado

    except Exception as e:
        return {"sucesso": False, "erro": str(e)}


def editar_video(conta, video_url, novo_titulo=None, nova_descricao=None, novas_tags=None):
    """Edita título/descrição/tags de um vídeo existente no YouTube Studio."""
    try:
        with google_browser(conta) as (page, context, browser):
            video_id = video_url.split("v=")[-1].split("&")[0] if "v=" in video_url else video_url.split("/")[-1]
            page.goto(f"{STUDIO_URL}/video/{video_id}/edit", timeout=45000, wait_until="domcontentloaded")
            time.sleep(5)

            if "accounts.google.com" in page.url:
                return {"sucesso": False, "erro": "sessao_expirada"}

            alteracoes = []

            if novo_titulo:
                titulo_el = page.query_selector('#textbox[aria-label*="title"], #title-textarea #textbox')
                if titulo_el:
                    titulo_el.click()
                    page.keyboard.press("Control+a")
                    titulo_el.type(novo_titulo, delay=20)
                    alteracoes.append("titulo")
                    time.sleep(1)

            if nova_descricao:
                desc_el = page.query_selector('#description-textarea #textbox, div[aria-label*="description"]')
                if desc_el:
                    desc_el.click()
                    page.keyboard.press("Control+a")
                    desc_el.type(nova_descricao, delay=15)
                    alteracoes.append("descricao")
                    time.sleep(1)

            if alteracoes:
                save_btn = page.query_selector('#save-button, button:has-text("Save"), button:has-text("Salvar")')
                if save_btn:
                    save_btn.click()
                    time.sleep(3)

            save_session(context, conta)
            resultado = {"sucesso": True, "video_id": video_id, "alteracoes": alteracoes}
            _registrar_acao("editar_video", conta, resultado)
            return resultado

    except Exception as e:
        return {"sucesso": False, "erro": str(e)}


def deletar_video(conta, video_url):
    """Remove um vídeo do canal."""
    try:
        with google_browser(conta) as (page, context, browser):
            video_id = video_url.split("v=")[-1].split("&")[0] if "v=" in video_url else video_url.split("/")[-1]
            page.goto(f"{STUDIO_URL}/video/{video_id}/edit", timeout=45000, wait_until="domcontentloaded")
            time.sleep(5)

            if "accounts.google.com" in page.url:
                return {"sucesso": False, "erro": "sessao_expirada"}

            menu_btn = page.query_selector('#overflow-menu-button, button[aria-label*="More"], button[aria-label*="Mais"]')
            if menu_btn:
                menu_btn.click()
                time.sleep(1)

                delete_opt = page.query_selector('tp-yt-paper-item:has-text("Delete"), tp-yt-paper-item:has-text("Excluir")')
                if delete_opt:
                    delete_opt.click()
                    time.sleep(2)

                    checkbox = page.query_selector('#delete-dialog input[type="checkbox"], ytcp-checkbox-lit')
                    if checkbox:
                        checkbox.click()
                        time.sleep(1)

                    confirm = page.query_selector('#delete-dialog button:has-text("Delete"), button:has-text("Excluir")')
                    if confirm:
                        confirm.click()
                        time.sleep(3)
                        save_session(context, conta)
                        resultado = {"sucesso": True, "video_id": video_id}
                        _registrar_acao("deletar_video", conta, resultado)
                        return resultado

            return {"sucesso": False, "erro": "menu de exclusão não encontrado"}

    except Exception as e:
        return {"sucesso": False, "erro": str(e)}


def dar_like(conta, video_url):
    """Curte um vídeo no YouTube."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto(video_url, timeout=45000, wait_until="domcontentloaded")
            time.sleep(5)

            if "accounts.google.com" in page.url:
                return {"sucesso": False, "erro": "sessao_expirada"}

            like_btn = page.query_selector(
                'button[aria-label*="like this video"], '
                'button[aria-label*="Gostei"], '
                'ytd-toggle-button-renderer:first-child button, '
                '#top-level-buttons-computed ytd-toggle-button-renderer:first-child button, '
                'like-button-view-model button'
            )
            if like_btn:
                pressed = like_btn.get_attribute("aria-pressed")
                if pressed == "true":
                    save_session(context, conta)
                    return {"sucesso": True, "ja_curtido": True, "url": video_url}

                like_btn.click()
                time.sleep(2)
                save_session(context, conta)
                resultado = {"sucesso": True, "url": video_url}
                _registrar_acao("dar_like", conta, resultado)
                return resultado

            return {"sucesso": False, "erro": "botão de like não encontrado"}

    except Exception as e:
        return {"sucesso": False, "erro": str(e)}


def comentar_video(conta, video_url, texto_comentario):
    """Comenta num vídeo do YouTube."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto(video_url, timeout=45000, wait_until="domcontentloaded")
            time.sleep(5)

            if "accounts.google.com" in page.url:
                return {"sucesso": False, "erro": "sessao_expirada"}

            page.evaluate("window.scrollBy(0, 600)")
            time.sleep(3)

            comment_box = page.query_selector(
                '#simplebox-placeholder, '
                'ytd-comment-simplebox-renderer #placeholder-area, '
                '#comment-simplebox ytd-comment-simplebox-renderer'
            )
            if comment_box:
                comment_box.click()
                time.sleep(2)

                editor = page.query_selector(
                    '#contenteditable-root, '
                    'div[contenteditable="true"][id="contenteditable-root"], '
                    '#creation-box #contenteditable-root'
                )
                if editor:
                    editor.click()
                    editor.type(texto_comentario, delay=25)
                    time.sleep(1)

                    submit_btn = page.query_selector(
                        '#submit-button, '
                        'ytd-button-renderer#submit-button, '
                        'button[aria-label*="Comment"], '
                        'button[aria-label*="Comentar"]'
                    )
                    if submit_btn:
                        submit_btn.click()
                        time.sleep(3)
                        save_session(context, conta)
                        resultado = {"sucesso": True, "url": video_url, "comentario": texto_comentario[:50]}
                        _registrar_acao("comentar_video", conta, resultado)
                        return resultado

            return {"sucesso": False, "erro": "caixa de comentário não encontrada"}

    except Exception as e:
        return {"sucesso": False, "erro": str(e)}


def responder_comentario(conta, video_url, indice_comentario=0, texto_resposta=""):
    """Responde a um comentário no nosso vídeo."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto(video_url, timeout=45000, wait_until="domcontentloaded")
            time.sleep(5)

            if "accounts.google.com" in page.url:
                return {"sucesso": False, "erro": "sessao_expirada"}

            page.evaluate("window.scrollBy(0, 600)")
            time.sleep(3)

            comentarios = page.query_selector_all('ytd-comment-thread-renderer')
            if indice_comentario >= len(comentarios):
                return {"sucesso": False, "erro": f"comentário {indice_comentario} não encontrado (total: {len(comentarios)})"}

            target = comentarios[indice_comentario]
            reply_btn = target.query_selector('#reply-button-end button, button[aria-label*="Reply"], button[aria-label*="Responder"]')
            if reply_btn:
                reply_btn.click()
                time.sleep(2)

                editor = target.query_selector('#contenteditable-root')
                if editor:
                    editor.type(texto_resposta, delay=25)
                    time.sleep(1)

                    submit = target.query_selector('#submit-button button, button[aria-label*="Reply"], button[aria-label*="Responder"]')
                    if submit:
                        submit.click()
                        time.sleep(3)
                        save_session(context, conta)
                        resultado = {"sucesso": True, "resposta": texto_resposta[:50]}
                        _registrar_acao("responder_comentario", conta, resultado)
                        return resultado

            return {"sucesso": False, "erro": "botão de responder não encontrado"}

    except Exception as e:
        return {"sucesso": False, "erro": str(e)}


def inscrever_canal(conta, canal_url):
    """Se inscreve num canal do YouTube."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto(canal_url, timeout=45000, wait_until="domcontentloaded")
            time.sleep(5)

            if "accounts.google.com" in page.url:
                return {"sucesso": False, "erro": "sessao_expirada"}

            sub_btn = page.query_selector(
                '#subscribe-button button, '
                'ytd-subscribe-button-renderer button, '
                'button[aria-label*="Subscribe"], '
                'button[aria-label*="Inscrever"]'
            )
            if sub_btn:
                texto = sub_btn.inner_text().strip().lower()
                if "subscribed" in texto or "inscrito" in texto:
                    return {"sucesso": True, "ja_inscrito": True, "canal": canal_url}

                sub_btn.click()
                time.sleep(3)
                save_session(context, conta)
                resultado = {"sucesso": True, "canal": canal_url}
                _registrar_acao("inscrever_canal", conta, resultado)
                return resultado

            return {"sucesso": False, "erro": "botão de inscrição não encontrado"}

    except Exception as e:
        return {"sucesso": False, "erro": str(e)}


def criar_playlist(conta, titulo_playlist, descricao_playlist="", visibilidade="public"):
    """Cria uma playlist no YouTube Studio."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto(f"{STUDIO_URL}/channel/playlists", timeout=45000, wait_until="domcontentloaded")
            time.sleep(5)

            if "accounts.google.com" in page.url:
                return {"sucesso": False, "erro": "sessao_expirada"}

            create_btn = page.query_selector(
                'button:has-text("New playlist"), button:has-text("Nova playlist"), '
                '#create-playlist-button, button[aria-label*="playlist"]'
            )
            if create_btn:
                create_btn.click()
                time.sleep(2)

                title_input = page.query_selector('input[placeholder*="title"], input[placeholder*="título"], #playlist-title-input')
                if title_input:
                    title_input.fill(titulo_playlist)
                    time.sleep(1)

                if descricao_playlist:
                    desc_input = page.query_selector('textarea[placeholder*="description"], textarea[placeholder*="descrição"]')
                    if desc_input:
                        desc_input.fill(descricao_playlist)
                        time.sleep(1)

                create_final = page.query_selector('button:has-text("Create"), button:has-text("Criar")')
                if create_final:
                    create_final.click()
                    time.sleep(3)
                    save_session(context, conta)
                    resultado = {"sucesso": True, "playlist": titulo_playlist}
                    _registrar_acao("criar_playlist", conta, resultado)
                    return resultado

            return {"sucesso": False, "erro": "interface de criar playlist não encontrada"}

    except Exception as e:
        return {"sucesso": False, "erro": str(e)}


def listar_playlists(conta):
    """Lista playlists do canal."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto(f"{STUDIO_URL}/channel/playlists", timeout=45000, wait_until="domcontentloaded")
            time.sleep(5)

            if "accounts.google.com" in page.url:
                return {"conta": conta, "playlists": [], "erro": "sessao_expirada"}

            playlists = []
            rows = page.query_selector_all('[class*="playlist-row"], ytcp-playlist-row, tr')
            for row in rows[:20]:
                titulo = ""
                titulo_el = row.query_selector('[class*="title"], a')
                if titulo_el:
                    titulo = titulo_el.inner_text().strip()

                contagem = ""
                count_el = row.query_selector('[class*="count"], [class*="video-count"]')
                if count_el:
                    contagem = count_el.inner_text().strip()

                if titulo:
                    playlists.append({"titulo": titulo, "videos": contagem})

            save_session(context, conta)
            return {"conta": conta, "playlists": playlists}

    except Exception as e:
        return {"conta": conta, "playlists": [], "erro": str(e)}


def adicionar_na_playlist(conta, video_url, nome_playlist):
    """Adiciona vídeo a uma playlist existente."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto(video_url, timeout=45000, wait_until="domcontentloaded")
            time.sleep(5)

            if "accounts.google.com" in page.url:
                return {"sucesso": False, "erro": "sessao_expirada"}

            save_btn = page.query_selector(
                'button[aria-label*="Save"], button[aria-label*="Salvar"], '
                '#button-shape-save button'
            )
            if save_btn:
                save_btn.click()
                time.sleep(2)

                playlist_items = page.query_selector_all('ytd-playlist-add-to-option-renderer, tp-yt-paper-checkbox')
                for item in playlist_items:
                    texto = item.inner_text().strip()
                    if nome_playlist.lower() in texto.lower():
                        item.click()
                        time.sleep(1)
                        break

                close_btn = page.query_selector('button[aria-label*="Close"], button[aria-label*="Fechar"]')
                if close_btn:
                    close_btn.click()

                save_session(context, conta)
                resultado = {"sucesso": True, "video": video_url, "playlist": nome_playlist}
                _registrar_acao("adicionar_na_playlist", conta, resultado)
                return resultado

            return {"sucesso": False, "erro": "botão de salvar não encontrado"}

    except Exception as e:
        return {"sucesso": False, "erro": str(e)}


def ver_analytics(conta):
    """Pega métricas básicas do YouTube Studio Analytics."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto(f"{STUDIO_URL}/channel/analytics", timeout=45000, wait_until="domcontentloaded")
            time.sleep(6)

            if "accounts.google.com" in page.url:
                return {"conta": conta, "erro": "sessao_expirada"}

            metricas = {}

            cards = page.query_selector_all('[class*="metric-card"], [class*="kpi"], [class*="analytics-card"]')
            for card in cards:
                label_el = card.query_selector('[class*="label"], [class*="title"]')
                value_el = card.query_selector('[class*="value"], [class*="metric-value"]')
                if label_el and value_el:
                    metricas[label_el.inner_text().strip()] = value_el.inner_text().strip()

            if not metricas:
                all_text = page.query_selector('[class*="analytics"]')
                if all_text:
                    metricas["resumo"] = all_text.inner_text().strip()[:500]

            save_session(context, conta)
            resultado = {"conta": conta, "metricas": metricas}
            _registrar_acao("ver_analytics", conta, resultado)
            return resultado

    except Exception as e:
        return {"conta": conta, "erro": str(e)}


def alterar_thumbnail(conta, video_url, caminho_thumbnail):
    """Troca thumbnail de um vídeo existente."""
    caminho = Path(caminho_thumbnail)
    if not caminho.exists():
        return {"sucesso": False, "erro": f"Thumbnail não encontrada: {caminho}"}

    try:
        with google_browser(conta) as (page, context, browser):
            video_id = video_url.split("v=")[-1].split("&")[0] if "v=" in video_url else video_url.split("/")[-1]
            page.goto(f"{STUDIO_URL}/video/{video_id}/edit", timeout=45000, wait_until="domcontentloaded")
            time.sleep(5)

            if "accounts.google.com" in page.url:
                return {"sucesso": False, "erro": "sessao_expirada"}

            thumb_upload = page.query_selector('#still-picker input[type="file"], input[accept*="image"]')
            if thumb_upload:
                thumb_upload.set_input_files(str(caminho.resolve()))
                time.sleep(3)

                save_btn = page.query_selector('#save-button, button:has-text("Save"), button:has-text("Salvar")')
                if save_btn:
                    save_btn.click()
                    time.sleep(3)

                save_session(context, conta)
                resultado = {"sucesso": True, "video_id": video_id, "thumbnail": str(caminho)}
                _registrar_acao("alterar_thumbnail", conta, resultado)
                return resultado

            return {"sucesso": False, "erro": "input de thumbnail não encontrado"}

    except Exception as e:
        return {"sucesso": False, "erro": str(e)}


def verificar_monetizacao(conta):
    """Verifica status de monetização do canal."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto(f"{STUDIO_URL}/channel/monetization", timeout=45000, wait_until="domcontentloaded")
            time.sleep(5)

            if "accounts.google.com" in page.url:
                return {"conta": conta, "erro": "sessao_expirada"}

            info = {}
            status_el = page.query_selector('[class*="monetization-status"], [class*="eligibility"]')
            if status_el:
                info["status"] = status_el.inner_text().strip()

            requisitos = []
            req_els = page.query_selector_all('[class*="requirement"], [class*="milestone"]')
            for el in req_els:
                requisitos.append(el.inner_text().strip())
            if requisitos:
                info["requisitos"] = requisitos

            save_session(context, conta)
            return {"conta": conta, "monetizacao": info}

    except Exception as e:
        return {"conta": conta, "erro": str(e)}


def listar_comentarios(conta, max_comentarios=20):
    """Lista comentários recentes nos vídeos do canal."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto(f"{STUDIO_URL}/channel/comments", timeout=45000, wait_until="domcontentloaded")
            time.sleep(5)

            if "accounts.google.com" in page.url:
                return {"conta": conta, "comentarios": [], "erro": "sessao_expirada"}

            comentarios = []
            rows = page.query_selector_all('[class*="comment-row"], ytcp-comment-row, tr')
            for row in rows[:max_comentarios]:
                autor = ""
                autor_el = row.query_selector('[class*="author"], [class*="commenter"]')
                if autor_el:
                    autor = autor_el.inner_text().strip()

                texto = ""
                texto_el = row.query_selector('[class*="comment-text"], [class*="content"]')
                if texto_el:
                    texto = texto_el.inner_text().strip()

                video = ""
                video_el = row.query_selector('[class*="video-title"], a')
                if video_el:
                    video = video_el.inner_text().strip()

                if texto:
                    comentarios.append({"autor": autor, "texto": texto[:200], "video": video})

            save_session(context, conta)
            return {"conta": conta, "comentarios": comentarios, "total": len(comentarios)}

    except Exception as e:
        return {"conta": conta, "comentarios": [], "erro": str(e)}


def gerenciar_comunidade(conta, texto_post, imagem=None):
    """Posta na aba Comunidade do canal."""
    try:
        with google_browser(conta) as (page, context, browser):
            page.goto(f"{STUDIO_URL}/channel/community", timeout=45000, wait_until="domcontentloaded")
            time.sleep(5)

            if "accounts.google.com" in page.url:
                return {"sucesso": False, "erro": "sessao_expirada"}

            editor = page.query_selector(
                '#contenteditable-root, '
                'div[contenteditable], '
                '[class*="community-post"] div[contenteditable]'
            )
            if editor:
                editor.click()
                time.sleep(1)
                editor.type(texto_post, delay=20)
                time.sleep(1)

                if imagem and Path(imagem).exists():
                    img_input = page.query_selector('input[type="file"][accept*="image"]')
                    if img_input:
                        img_input.set_input_files(str(Path(imagem).resolve()))
                        time.sleep(3)

                post_btn = page.query_selector('button:has-text("Post"), button:has-text("Publicar")')
                if post_btn:
                    post_btn.click()
                    time.sleep(3)
                    save_session(context, conta)
                    resultado = {"sucesso": True, "texto": texto_post[:50]}
                    _registrar_acao("gerenciar_comunidade", conta, resultado)
                    return resultado

            return {"sucesso": False, "erro": "editor de comunidade não encontrado"}

    except Exception as e:
        return {"sucesso": False, "erro": str(e)}


FUNCIONALIDADES = {
    "verificar":   {"func": verificar_canal,        "desc": "Verifica se a conta tem canal YouTube ativo"},
    "listar":      {"func": listar_videos,           "desc": "Lista vídeos publicados com título/views/data"},
    "postar":      {"func": postar_video,            "desc": "Faz upload de vídeo com título/descrição/tags/thumb"},
    "editar":      {"func": editar_video,             "desc": "Edita título/descrição de vídeo existente"},
    "deletar":     {"func": deletar_video,            "desc": "Remove vídeo do canal"},
    "like":        {"func": dar_like,                 "desc": "Curte um vídeo pelo URL"},
    "comentar":    {"func": comentar_video,           "desc": "Comenta num vídeo (próprio ou de terceiro)"},
    "responder":   {"func": responder_comentario,     "desc": "Responde comentários nos vídeos"},
    "inscrever":   {"func": inscrever_canal,          "desc": "Se inscreve num canal"},
    "playlist":    {"func": criar_playlist,           "desc": "Cria playlist com título/descrição"},
    "add_playlist":{"func": adicionar_na_playlist,    "desc": "Adiciona vídeo a uma playlist"},
    "playlists":   {"func": listar_playlists,         "desc": "Lista playlists do canal"},
    "analytics":   {"func": ver_analytics,            "desc": "Pega métricas do YouTube Studio Analytics"},
    "thumbnail":   {"func": alterar_thumbnail,        "desc": "Troca thumbnail de vídeo existente"},
    "monetizacao": {"func": verificar_monetizacao,    "desc": "Verifica status de monetização"},
    "comentarios": {"func": listar_comentarios,       "desc": "Lista comentários recentes nos vídeos"},
    "comunidade":  {"func": gerenciar_comunidade,     "desc": "Posta na aba Comunidade do canal"},
}


def executar(dry_run=True):
    """Execução padrão — verifica todos os canais."""
    print(f"[Gerenciador YouTube] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nFuncionalidades disponíveis ({len(FUNCIONALIDADES)}):")
    for nome, info in FUNCIONALIDADES.items():
        print(f"  --acao {nome:15s} → {info['desc']}")

    status = {"contas": {}, "ultima_execucao": datetime.now(timezone.utc).isoformat()}

    for conta in ACCOUNTS:
        if dry_run:
            print(f"\n  [DRY RUN] {conta}: verificaria canal")
            status["contas"][conta] = {"dry_run": True}
        else:
            print(f"\n  {conta}...", end=" ", flush=True)
            r = verificar_canal(conta)
            print(r["status"])
            status["contas"][conta] = r

    STATUS_FILE.write_text(json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nStatus salvo em {STATUS_FILE}")
    return status


if __name__ == "__main__":
    args = sys.argv[1:]

    if "--acao" in args:
        idx = args.index("--acao")
        acao = args[idx + 1] if idx + 1 < len(args) else None
        conta = args[args.index("--conta") + 1] if "--conta" in args else "fabrica"

        if acao not in FUNCIONALIDADES:
            print(f"Ação desconhecida: {acao}")
            print(f"Ações disponíveis: {', '.join(FUNCIONALIDADES.keys())}")
            sys.exit(1)

        if acao == "verificar":
            r = verificar_canal(conta)
        elif acao == "listar":
            r = listar_videos(conta)
        elif acao == "postar":
            video = args[args.index("--video") + 1] if "--video" in args else None
            titulo = args[args.index("--titulo") + 1] if "--titulo" in args else "Sem título"
            desc = args[args.index("--desc") + 1] if "--desc" in args else ""
            thumb = args[args.index("--thumb") + 1] if "--thumb" in args else None
            vis = args[args.index("--visibilidade") + 1] if "--visibilidade" in args else "public"
            r = postar_video(conta, video, titulo, desc, thumbnail=thumb, visibilidade=vis)
        elif acao == "editar":
            url = args[args.index("--url") + 1] if "--url" in args else None
            novo_titulo = args[args.index("--titulo") + 1] if "--titulo" in args else None
            nova_desc = args[args.index("--desc") + 1] if "--desc" in args else None
            r = editar_video(conta, url, novo_titulo=novo_titulo, nova_descricao=nova_desc)
        elif acao == "deletar":
            url = args[args.index("--url") + 1] if "--url" in args else None
            r = deletar_video(conta, url)
        elif acao == "like":
            url = args[args.index("--url") + 1] if "--url" in args else None
            r = dar_like(conta, url)
        elif acao == "comentar":
            url = args[args.index("--url") + 1] if "--url" in args else None
            texto = args[args.index("--texto") + 1] if "--texto" in args else None
            r = comentar_video(conta, url, texto)
        elif acao == "responder":
            url = args[args.index("--url") + 1] if "--url" in args else None
            texto = args[args.index("--texto") + 1] if "--texto" in args else None
            idx_c = int(args[args.index("--indice") + 1]) if "--indice" in args else 0
            r = responder_comentario(conta, url, idx_c, texto)
        elif acao == "inscrever":
            url = args[args.index("--url") + 1] if "--url" in args else None
            r = inscrever_canal(conta, url)
        elif acao == "playlist":
            titulo = args[args.index("--titulo") + 1] if "--titulo" in args else None
            desc = args[args.index("--desc") + 1] if "--desc" in args else ""
            r = criar_playlist(conta, titulo, desc)
        elif acao == "add_playlist":
            url = args[args.index("--url") + 1] if "--url" in args else None
            nome = args[args.index("--playlist") + 1] if "--playlist" in args else None
            r = adicionar_na_playlist(conta, url, nome)
        elif acao == "playlists":
            r = listar_playlists(conta)
        elif acao == "analytics":
            r = ver_analytics(conta)
        elif acao == "thumbnail":
            url = args[args.index("--url") + 1] if "--url" in args else None
            thumb = args[args.index("--thumb") + 1] if "--thumb" in args else None
            r = alterar_thumbnail(conta, url, thumb)
        elif acao == "monetizacao":
            r = verificar_monetizacao(conta)
        elif acao == "comentarios":
            r = listar_comentarios(conta)
        elif acao == "comunidade":
            texto = args[args.index("--texto") + 1] if "--texto" in args else None
            img = args[args.index("--imagem") + 1] if "--imagem" in args else None
            r = gerenciar_comunidade(conta, texto, img)
        else:
            r = {"erro": "ação não implementada"}

        print(json.dumps(r, indent=2, ensure_ascii=False))
    else:
        dry = "--live" not in args
        if dry:
            print("Modo DRY RUN\n")
        executar(dry_run=dry)
