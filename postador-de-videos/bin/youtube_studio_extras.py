#!/usr/bin/env python3
"""youtube_studio_extras.py — acabamento no YouTube Studio DEPOIS do upload, pelo navegador (sem Data API).

Mesmo Chrome/perfil/trava do youtube_web_poster.py. Cada ação nunca derruba as outras e devolve um texto curto:
"ok", "ja" (já estava feito), "pendente: <motivo>" (tentar de novo mais tarde) ou "aviso: <motivo>" (print em
logs/yt_web).

- tela_final        modelo "1 vídeo, 1 playlist": vídeo = melhor para o espectador, playlist = a pedida (se houver
                    duas com o mesmo nome, a que tem mais vídeos). Short não tem tela final.
- relacionado       liga o Short ao vídeo completo ("Vídeo relacionado" do Short).
- teste_ab          teste A/B de capa (até 3 capas).
- comentar_fixar    comentário do canal na página do vídeo, fixado no topo. Só em vídeo já público.
- limpar_rascunhos  apaga os rascunhos presos no Conteúdo (uploads que travaram no meio).

"Vídeo relacionado" e teste A/B exigem o canal verificado: com "A verificação por vídeo está em análise" (até 24 h
depois de pedir) voltam "pendente". As telas desses dois só foram vistas até esse aviso (15/10): na 1ª vez que
passarem, conferir os prints em logs/yt_web.

Uso:
  python bin/youtube_studio_extras.py --canal <id|nome> --video ID [--tela-final "Playlist"]
      [--relacionado ID_DO_COMPLETO] [--ab capa1.jpg,capa2.jpg,capa3.jpg] [--comentario "texto"]
  python bin/youtube_studio_extras.py --canal <id|nome> --limpar-rascunhos [--apagar-mesmo]
      (sem --apagar-mesmo so LISTA; com ele apaga TODOS os rascunhos presos do canal - confira a lista antes)
Última linha: RESULTADO: {"acao": "status", ...}
"""
import argparse
import json
import re
from datetime import datetime
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import youtube_web_poster as yw  # noqa: E402

VERIFICACAO = re.compile(r"verifica\S*\s.{0,40}em an[aá]lise|verification.{0,40}(review|pending)", re.I | re.S)
# bloqueios da CONTA (não se resolvem tentando de novo; 15/10): o canal pt teve os recursos avançados negados
# ("violou as políticas antes", pedir de novo em 14/11/2026 ou contestar); os de língua pedem a "verificação única"
# (telefone) pra ligar Short a vídeo. Quem resolve é o dono, no Studio.
# 02/11: texto novo do Studio "Você perdeu o acesso aos recursos avançados" (Assist-IA, até 29/11/2026)
NEGADO = re.compile(r"recursos avançados não estão disponíveis|perdeu o acesso aos recursos avançados|"
                    r"advanced features (are )?(not|un)available|lost access to advanced features|"
                    r"contestação relacionada aos recursos avançados foi negada|acesso aos recursos avançados está bloqueado|"
                    r"appeal (related to|for) advanced features (was|has been) (denied|rejected)", re.I)
VERIF_UNICA = re.compile(r"verificação única|one-time verification", re.I)
MESES = {"jan": 1, "fev": 2, "mar": 3, "abr": 4, "mai": 5, "jun": 6, "jul": 7, "ago": 8, "set": 9, "out": 10,
         "nov": 11, "dez": 12}


# 05/11 (dona): o robô esbarrou ~70 vezes no MESMO bloqueio (fixar comentário, teste A/B, vídeo relacionado) em
# canais que já estavam sem recursos avançados — o aviso diz "se confirmarmos que está tentando burlar, encerramos a
# conta". Agora a 1ª negativa grava o canal + data aqui e NENHUM recurso avançado é tentado nele até a data.
NEGADOS_FILE = Path(__file__).resolve().parent.parent / "config" / "recursos_negados.json"
_SLUG = None


def _ler_negados():
    try:
        return json.loads(NEGADOS_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _marcar_negado(data):
    if not _SLUG:
        return
    d = _ler_negados()
    d[_SLUG] = {"ate": data or "", "em": datetime.now().isoformat("T", "minutes")}
    NEGADOS_FILE.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")


def negado_ate(slug):
    """Data (AAAA-MM-DD) até quando o canal está sem recursos avançados; '' sem data conhecida; None = liberado."""
    x = _ler_negados().get(slug)
    if not x:
        return None
    ate = x.get("ate") or ""
    if ate and datetime.now().date().isoformat() >= ate:
        return None
    return ate


def _bloqueio_conta(pg, espera_ms=4000):
    """Diálogo de bloqueio da conta visível? Fecha e devolve o status "bloqueado: ..." (ou None)."""
    dlg = pg.locator("tp-yt-paper-dialog:visible, ytcp-dialog:visible, ytd-popup-container [role=dialog]:visible, "
                     "yt-dialog-view-model:visible, [role=dialog]:visible")
    try:
        dlg.filter(has_text=re.compile(f"{NEGADO.pattern}|{VERIF_UNICA.pattern}", re.I)).first.wait_for(
            state="visible", timeout=espera_ms)
    except Exception:  # noqa: BLE001
        return None
    txt = " ".join(dlg.all_inner_texts())
    yw._shot(pg, "bloqueio_conta")
    if NEGADO.search(txt):
        m = re.search(r"novamente (?:em|a partir de) (\d{1,2}) de (\w{3})\w* de (\d{4})", txt, re.I)
        data = f"{m.group(3)}-{MESES.get(m.group(2).lower()[:3], 1):02d}-{int(m.group(1)):02d}" if m else ""
        _marcar_negado(data)
        st = (f"bloqueado: recursos avançados negados pelo YouTube (pedir de novo/contestar) até {data}" if data
              else "bloqueado: recursos avançados negados pelo YouTube (dono pode contestar no Studio)")
    else:
        # 13/11 dona ("esse também já estava verificado" — Fio da Meada e Manhwa Noturno com telefone OK): o diálogo
        # de "verificação única" aparece quando o canal passa do limite diário de miniaturas/recursos, mesmo com o
        # telefone verificado. Não é pendência da dona: é limite do dia (tenta de novo amanhã).
        st = "bloqueado: limite do dia do Studio (diálogo de 'verificação única'; telefone já verificado) — tenta amanhã"
    for rot in (r"^\s*(cancelar|cancel)\s*$", r"^\s*(entendi|ok|got it|fechar|close)\s*$"):
        b = dlg.locator("button, ytcp-button, yt-button-renderer, tp-yt-paper-button").filter(
            has_text=re.compile(rot, re.I)).first
        if b.count():
            b.click()
            break
    else:
        pg.keyboard.press("Escape")
    return st
TPL_VIDEO_PLAYLIST = "[role=gridcell][aria-label='1 vídeo, 1 playlist'], [role=gridcell][aria-label='1 video, 1 playlist']"
RASCUNHO = re.compile(r"Editar rascunho|Edit draft", re.I)
log = yw.log


@contextmanager
def sessao(e):
    """Chrome da conta (cofre), uma aba nova; abas velhas do YouTube fechadas (aba do Studio esquecida aberta deixa
    a próxima presa no painel em branco — 15/10)."""
    from contextlib import nullcontext
    from playwright.sync_api import sync_playwright
    proc, rem = None, None
    if e.get("maquina"):  # 22/10 (dono): canal ativado nos notebooks confere/edita pelo Chrome de lá; fora = aqui
        import maquina_remota
        rem = maquina_remota.tentar(e["maquina"], e.get("perfil_remoto"), log_fn=log)
        if rem:
            e = dict(e, porta=rem.porta_local)
            yw.REMOTO = rem  # capa/arquivo vão pelo ssh (yw._escolher_arquivo)
    with (nullcontext() if rem else yw.Trava()):
        try:
            proc = None if rem else yw.abrir_conta(e)
            with sync_playwright() as p:
                br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{e['porta']}")
                ctx = br.contexts[0]
                velhas = list(ctx.pages)
                pg = ctx.new_page()  # antes de fechar as velhas: sem nenhuma aba o Chrome recusa abrir outra
                for v in velhas:
                    # about:blank fica: em Chrome de outro projeto (o do TikTok usa o mesmo perfil) fechar a ultima
                    # aba dele + a nossa no fim deixa o Chrome sem abas e ele se encerra (15/10)
                    if "youtube.com" in v.url:
                        try:
                            v.close(run_before_unload=False)
                        except Exception:  # noqa: BLE001
                            pass
                pg.on("dialog", lambda d: d.accept())
                pg.set_viewport_size({"width": 1500, "height": 1000})
                try:
                    yield pg
                finally:
                    try:
                        pg.close(run_before_unload=False)
                    except Exception:  # noqa: BLE001
                        pass
                    yw.soltar(br, proc)
        finally:
            if rem:
                rem.fechar()
                yw.REMOTO = None
            yw.fechar_chrome(proc, e)


def ler_recursos(pg, channel_id):
    """12/11: status dos recursos avançados do canal — só LEITURA (não clica em contestar nem em nada).
    Devolve {"estado": liberado|negado|em_analise|verificacao|?, "data": ..., "texto": ...}."""
    pg.goto(f"https://studio.youtube.com/channel/{channel_id}/editing/details", wait_until="domcontentloaded",
             timeout=60000)
    pg.wait_for_timeout(4000)
    st = _bloqueio_conta(pg, espera_ms=3000)  # o diálogo de "negado" aparece sozinho ao entrar
    # Configurações > Canal > Qualificação de recursos (o diálogo de configurações abre por cima do Studio)
    pg.goto(f"https://studio.youtube.com/channel/{channel_id}", wait_until="domcontentloaded", timeout=60000)
    pg.wait_for_timeout(6000)
    try:  # menu lateral: "Configurações" é um item de navegação (#settings-item), não texto clicável solto
        pg.locator("#settings-item, ytcp-navigation-drawer [test-id='settings'], a#settings-item, "
                   "tp-yt-paper-icon-item:has-text('Configurações')").first.click(timeout=8000)
        pg.wait_for_timeout(3000)
    except Exception:  # noqa: BLE001
        pass
    for rot in (r"^\s*(Canal|Channel)\s*$", r"Qualificação de recursos|Feature eligibility",
                r"Recursos avançados|Advanced features"):
        try:
            b = pg.locator("ytcp-dialog:visible, tp-yt-paper-dialog:visible").get_by_text(re.compile(rot, re.I)).first
            if b.count():
                b.click(timeout=5000)
                pg.wait_for_timeout(2500)
        except Exception:  # noqa: BLE001
            pass
    txt = re.sub(r"\s+", " ", " ".join(pg.locator("ytcp-dialog:visible, tp-yt-paper-dialog:visible, body").first
                                       .all_inner_texts()))[:2500]
    yw._shot(pg, f"recursos_{channel_id[:8]}")
    if st:
        estado = "negado" if "negados" in st else "verificacao"
    elif re.search(r"recursos avançados (estão )?(ativ|dispon|liberad)|advanced features (are )?(enabled|on|available)|"
                   r"já tem acesso|you have access", txt, re.I):
        estado = "liberado"
    elif re.search(r"em análise|under review|analisando", txt, re.I):
        estado = "em_analise"
    elif NEGADO.search(txt):
        estado = "negado"
    else:
        estado = "?"
    m = re.search(r"(\d{1,2}) de (\w{3})\w* de (\d{4})", txt)
    data = f"{m.group(3)}-{MESES.get(m.group(2).lower()[:3], 1):02d}-{int(m.group(1)):02d}" if m else ""
    return {"estado": estado, "data": data, "bloqueio": st or "", "texto": txt[:500]}


def _abrir_edicao(pg, vid):
    pg.goto(f"https://studio.youtube.com/video/{vid}/edit", wait_until="domcontentloaded", timeout=90000)
    if yw.esperar_assentar(pg) == "login":
        raise yw.Falha("morto", "perfil do navegador não está logado (rode youtube_web_poster.py --logar)")
    for _ in range(3):  # às vezes fica no painel em branco: recarregar resolve
        try:
            pg.locator("#title-textarea").first.wait_for(state="visible", timeout=30000)
            pg.wait_for_timeout(2500)
            return
        except Exception:  # noqa: BLE001
            # 02/11: 7 trocas seguidas caíram em "Page.reload: Timeout 30000ms" — o Studio às vezes demora mais
            try:
                pg.reload(wait_until="domcontentloaded", timeout=90000)
            except Exception:  # noqa: BLE001
                pg.goto(f"https://studio.youtube.com/video/{vid}/edit", wait_until="domcontentloaded", timeout=90000)
    raise yw.Falha("erro", f"a página de edição do vídeo {vid} não abriu")


def _barrado_verificacao(pg, espera_ms=5000):
    """Aviso "A verificação por vídeo está em análise" (recurso que exige canal verificado): fecha e devolve True."""
    dlg = pg.locator("tp-yt-paper-dialog, ytcp-dialog").filter(has_text=VERIFICACAO).last
    try:
        dlg.wait_for(state="visible", timeout=espera_ms)
    except Exception:  # noqa: BLE001
        return False
    if not yw._clicar_se_existe(pg, "#close-button", 3000):
        pg.keyboard.press("Escape")
    return True


def _salvar_pagina(pg):
    """Botão Salvar do topo da página de detalhes (fica cinza quando não há nada a salvar)."""
    # 03/11: o Studio novo trocou o botão (preto, "Salvar"); o seletor antigo falhava calado e a capa "enviada" nunca
    # era salva (Animescomia/CenaReact com a capa antiga no ar). Tenta os 2 jeitos e CONFERE que salvou.
    cands = [pg.locator("ytcp-button#save").first,
             pg.get_by_role("button", name=re.compile(r"^\s*(Salvar|Save)\s*$", re.I)).first]
    for bt in cands:
        try:
            if not bt.count() or not bt.is_visible():
                continue
            if bt.get_attribute("aria-disabled", timeout=3000) == "true" or bt.is_disabled():
                return True
            bt.click(timeout=10000)
            for _ in range(15):
                pg.wait_for_timeout(2000)
                if not bt.is_visible() or bt.get_attribute("aria-disabled") == "true" or bt.is_disabled():
                    return True
        except Exception:  # noqa: BLE001
            continue
    yw._shot(pg, "salvar_falhou")
    return False


def _fechar_editor_tela_final(pg):
    if yw._clicar_se_existe(pg, "#discard-button", 3000):
        yw._clicar_se_existe(pg, "ytcp-confirmation-dialog #confirm-button, tp-yt-paper-dialog #discard-button", 2000)


# ─────────────────────────── tela final ────────────────────────────────────
def tela_final(pg, vid, playlist):
    _abrir_edicao(pg, vid)
    link = pg.locator("#endscreen-editor-link").first
    if not link.count():
        return "aviso: este vídeo não tem tela final (Short?)"
    link.scroll_into_view_if_needed()
    link.click()
    pg.locator("#save-button").first.wait_for(state="visible", timeout=60000)
    pg.wait_for_timeout(5000)
    linhas = pg.locator("ytve-endscreen-row:visible")
    if linhas.count():
        txt = " | ".join(t.strip() for t in linhas.all_inner_texts())
        _fechar_editor_tela_final(pg)
        return "ja" if playlist.lower() in txt.lower() else f"aviso: já tem outra tela final ({txt[:80]}); não mexi"
    pg.locator(TPL_VIDEO_PLAYLIST).first.click()
    pg.wait_for_timeout(4000)
    yw._clicar_se_existe(pg, "#best-for-viewer", 5000)
    # o elemento playlist vem vazio (vermelho): seleciona pela linha da linha do tempo; clique comum é interceptado
    linha = linhas.filter(has_text=re.compile(r"^\s*Playlist", re.I)).first
    caixa = linha.locator("#element").first.bounding_box()
    pg.mouse.click(caixa["x"] + 40, caixa["y"] + caixa["height"] / 2)
    pg.wait_for_timeout(2500)
    pg.locator("ytcp-dropdown-trigger").filter(has_text=re.compile(r"^\s*Playlist", re.I)).last.click()
    pg.wait_for_timeout(3000)
    cartoes = pg.locator("ytcp-entity-card:visible").filter(has_text=playlist)
    if not cartoes.count():
        yw._shot(pg, "tela_final_sem_playlist")
        pg.keyboard.press("Escape")
        _fechar_editor_tela_final(pg)
        return f"aviso: a playlist '{playlist}' não aparece na tela final"
    qtd = [int((re.search(r"(\d+)\s*v[ií]deo", t) or [0, 0])[1]) for t in cartoes.all_inner_texts()]
    cartoes.nth(qtd.index(max(qtd))).click()  # nome repetido: a que tem mais vídeos
    pg.wait_for_timeout(2500)
    if playlist.lower() not in " ".join(linhas.all_inner_texts()).lower():
        yw._shot(pg, "tela_final_nao_marcou")
        _fechar_editor_tela_final(pg)
        return "aviso: a playlist não ficou na tela final"
    pg.locator("#save-button").first.click()
    try:
        pg.locator("#save-button").first.wait_for(state="hidden", timeout=30000)
    except Exception:  # noqa: BLE001
        yw._shot(pg, "tela_final_nao_salvou")
        _fechar_editor_tela_final(pg)
        return "aviso: o editor da tela final não salvou"
    yw._shot(pg, "tela_final")
    return "ok"


# ─────────────────────────── vídeo relacionado (Short) ─────────────────────
def relacionado(pg, vid_short, vid_completo, titulo_completo=""):
    _abrir_edicao(pg, vid_short)
    link = pg.locator("#linked-video-editor-link").first
    if not link.count():
        return "aviso: sem 'Vídeo relacionado' (não é Short?)"
    atual = link.inner_text().strip()
    if titulo_completo and titulo_completo[:30].lower() in atual.lower():
        return "ja"
    link.click()
    if _barrado_verificacao(pg):
        return "pendente: canal em verificação (vídeo relacionado libera depois)"
    bloqueio = _bloqueio_conta(pg)
    if bloqueio:
        return bloqueio
    yw._shot(pg, "relacionado_dialogo")
    dlg = pg.locator("tp-yt-paper-dialog:visible, ytcp-dialog:visible").last
    busca = dlg.locator("input:visible").first
    if busca.count() and titulo_completo:
        busca.fill(titulo_completo[:60])
        pg.wait_for_timeout(3000)
    alvo = dlg.locator(f"[href*='{vid_completo}'], img[src*='{vid_completo}']").first
    if not alvo.count() and titulo_completo:
        alvo = dlg.get_by_text(titulo_completo[:40]).first
    if not alvo.count():
        pg.keyboard.press("Escape")
        return "aviso: não achei o vídeo completo na lista do 'Vídeo relacionado' (ver print relacionado_dialogo)"
    alvo.click()
    pg.wait_for_timeout(2500)
    _salvar_pagina(pg)
    novo = pg.locator("#linked-video-editor-link").first.inner_text().strip()
    yw._shot(pg, "relacionado")
    return "ok" if novo != atual else "aviso: o 'Vídeo relacionado' não mudou (ver prints)"


# ─────────────────────────── teste A/B de capa ─────────────────────────────
def teste_ab(pg, vid, capas):
    capas = [Path(c) for c in capas if Path(c).is_file() and Path(c).stat().st_size <= 2_000_000][:3]
    if len(capas) < 2:
        return "aviso: teste A/B precisa de 2 ou 3 capas (até 2 MB)"
    _abrir_edicao(pg, vid)
    corpo = pg.locator("ytcp-video-thumbnail-editor").first.inner_text()
    if re.search(r"teste a/b em andamento|a/b test(ing)? in progress|testando|testing", corpo, re.I):
        return "ja"
    # 02/11: o Studio novo só mostra o ⋮ da miniatura com o mouse em cima (timeout de 30 s no clique sem hover)
    mini = pg.locator("ytcp-thumbnail-uploader, ytcp-video-thumbnail-editor").first
    mini.scroll_into_view_if_needed()
    for alvo in (mini.locator("img").first, mini):
        try:
            alvo.hover(timeout=5000)
            break
        except Exception:  # noqa: BLE001
            continue
    pg.wait_for_timeout(800)
    pg.locator("ytcp-thumbnail-uploader #options-button, ytcp-video-thumbnail-editor #options-button").first.click(
        force=True, timeout=15000)
    pg.wait_for_timeout(1500)
    item = pg.locator("tp-yt-paper-item:visible").filter(
        has_text=re.compile(r"teste a/b|a/b test|testar e comparar|test & compare", re.I)).first
    if not item.count():
        pg.keyboard.press("Escape")
        return "aviso: o menu da miniatura não tem teste A/B"
    item.click()
    if _barrado_verificacao(pg):
        return "pendente: canal em verificação (teste A/B libera depois)"
    bloqueio = _bloqueio_conta(pg)
    if bloqueio:
        return bloqueio
    pg.wait_for_timeout(2500)
    yw._shot(pg, "ab_dialogo")
    dlg = pg.locator("tp-yt-paper-dialog:visible, ytcp-dialog:visible").last
    for i, capa in enumerate(capas):
        entradas = dlg.locator("input[type=file]")
        if not entradas.count():
            pg.keyboard.press("Escape")
            return f"aviso: o diálogo do teste A/B não tem campo de arquivo (capa {i + 1}; ver print ab_dialogo)"
        yw._escolher_arquivo(pg, entradas.nth(min(i, entradas.count() - 1)), capa)
        pg.wait_for_timeout(5000)
    yw._shot(pg, "ab_capas")
    botao = dlg.locator("ytcp-button:visible, button:visible").filter(
        has_text=re.compile(r"^\s*(concluído|concluir|salvar|iniciar|done|save|start)", re.I)).last
    if not botao.count():
        pg.keyboard.press("Escape")
        return "aviso: não achei o botão de concluir do teste A/B (ver print ab_capas)"
    botao.click()
    pg.wait_for_timeout(4000)
    _salvar_pagina(pg)
    yw._shot(pg, "ab")
    return "ok"


def _registrar_resultado_ab(vid, vencedor):
    """Localiza a pasta do vídeo no ledger e pontua a vencedora no Thompson e vencedora_ab.json."""
    pasta = None
    ledger = Path(r"D:\postador-de-videos\logs\uploads_ledger.jsonl")
    if ledger.exists():
        for ln in reversed(ledger.read_text("utf-8").splitlines()):
            try:
                r = json.loads(ln)
                if r.get("video_id") == vid and r.get("caminho"):
                    p = Path(r["caminho"]).parent
                    if p.exists():
                        pasta = p
                        break
            except Exception:
                continue
    if not pasta:  # sem a pasta não há as poses: só a letra, uma vez (registrar_vencedora_ab já pontua a letra)
        try:
            import placar_titulos
            placar_titulos.registrar_item("capas_ab", "parceiro", str(vencedor).upper(), True,
                                          f"{vid}_ab_{str(vencedor).lower()}")
        except Exception as ex:  # noqa: BLE001
            yw.log(f"  aviso: placar capas_ab falhou ({ex})")
        return []
    try:
        if r"D:\recapd-ambientes\producao\bin" not in sys.path:
            sys.path.append(r"D:\recapd-ambientes\producao\bin")
        import capa_ia_anime
        return capa_ia_anime.registrar_vencedora_ab(pasta, vencedor, vid)
    except Exception as ex:  # noqa: BLE001
        yw.log(f"  aviso: registrar_vencedora_ab falhou ({ex})")
        return []


def checar_vencedor_ab(pg, vid):
    """Verifica no YouTube Studio se o teste A/B do vídeo terminou e qual miniatura venceu."""
    _abrir_edicao(pg, vid)
    try:
        pg.wait_for_selector("ytcp-video-thumbnail-editor", timeout=15000)
    except Exception:
        pass
    corpo = pg.locator("ytcp-video-thumbnail-editor").first.inner_text() if pg.locator("ytcp-video-thumbnail-editor").count() else ""
    yw._shot(pg, f"ab_status_{vid}")
    if re.search(r"teste a/b em andamento|a/b test(ing)? in progress|testando|testing", corpo, re.I):
        return {"status": "em_andamento", "video": vid}
    if re.search(r"vencedor|winner|maior tempo de exibi[cç][aã]o|highest watch time", corpo, re.I):
        m = re.search(r"\b(miniatura|thumbnail|variante|variant)\s*([A-C])\b", corpo, re.I)
        if not m:  # 31/10: antes caía em "a" e gravava vitória falsa; sem a letra lida não registra nada
            return {"status": "concluido_sem_letra", "video": vid, "texto": corpo[:200]}
        vencedor = m.group(2).lower()
        reg = _registrar_resultado_ab(vid, vencedor)
        return {"status": "concluido", "vencedor": vencedor, "video": vid, "texto": corpo[:200], "registrado": reg}
    return {"status": "sem_teste_ab", "video": vid, "texto": corpo[:150]}


# ─────────────────────────── comentário fixado ─────────────────────────────
_BOTAO_DIALOGO = re.compile(r"^\s*(ok|entendi|got it|continuar|continue|comentar|comment|fechar|close|postar|post)\s*$", re.I)


def _fechar_dialogo(dlg, onde=""):
    """Clica o botao de confirmar/fechar de uma janela do YouTube (16/10: o botao do aviso nao era 'ok/entendi' e o
    clique esperava 30 s ate estourar). Loga o texto da janela para a gente aprender as variantes. True se clicou."""
    try:
        yw.log(f"  janela ({onde}): {dlg.inner_text(timeout=3000)[:160]!r}")
    except Exception:  # noqa: BLE001
        pass
    botoes = dlg.locator("button, yt-button-renderer, tp-yt-paper-button, yt-button-shape")
    alvo = botoes.filter(has_text=_BOTAO_DIALOGO).last
    try:
        alvo.click(timeout=5000)
        return True
    except Exception:  # noqa: BLE001
        try:
            dlg.page.keyboard.press("Escape")
        except Exception:  # noqa: BLE001
            pass
        return False


def curtir(pg, vid):
    """Like do canal no próprio vídeo (aba própria, página pública). Só funciona em vídeo já público."""
    wp = pg.context.new_page()
    wp.on("dialog", lambda d: d.accept())
    wp.set_viewport_size({"width": 1400, "height": 1000})
    try:
        return _curtir(wp, vid)
    finally:
        try:
            wp.close(run_before_unload=False)
        except Exception:  # noqa: BLE001
            pass


def _curtir(pg, vid):
    pg.goto(f"https://www.youtube.com/watch?v={vid}", wait_until="domcontentloaded", timeout=90000)
    pg.wait_for_timeout(5000)
    try:
        pg.evaluate("() => { const v = document.querySelector('video'); if (v) v.pause(); }")
    except Exception:  # noqa: BLE001
        pass
    if pg.locator("yt-playability-error-supported-renderers:visible, ytd-player-error-message-renderer:visible").count():
        return "pendente: o vídeo ainda não é público (privado/agendado/processando)"
    r = pg.evaluate("""() => {
        const btn = document.querySelector("like-button-view-model button");
        if (!btn) return "nf";
        if (btn.getAttribute("aria-pressed") === "true") return "al";
        btn.click();
        return "ok";
    }""")
    if r == "al":
        return "ja"
    if r == "ok":
        pg.wait_for_timeout(2000)
        return "ok"
    yw._shot(pg, "curtir_sem_botao")
    return "aviso: botão de like não encontrado na página"


def comentar_fixar(pg, vid, texto):
    """Numa aba própria: a aba do Studio com edição aberta não sai da página com goto (15/10)."""
    wp = pg.context.new_page()
    wp.on("dialog", lambda d: d.accept())
    wp.set_viewport_size({"width": 1400, "height": 1000})
    try:
        return _comentar_fixar(wp, vid, texto)
    finally:
        try:
            wp.close(run_before_unload=False)
        except Exception:  # noqa: BLE001
            pass


def _comentar_fixar(pg, vid, texto):
    pg.goto(f"https://www.youtube.com/watch?v={vid}", wait_until="domcontentloaded", timeout=90000)
    pg.wait_for_timeout(5000)
    try:
        pg.evaluate("() => { const v = document.querySelector('video'); if (v) v.pause(); }")
    except Exception:  # noqa: BLE001
        pass
    if pg.locator("yt-playability-error-supported-renderers:visible, ytd-player-error-message-renderer:visible").count():
        return "pendente: o vídeo ainda não é público (privado/agendado/processando)"
    caixa = pg.locator("#simplebox-placeholder").first
    for _ in range(8):  # os comentários só carregam depois de rolar
        try:
            pg.locator("ytd-comments#comments").first.scroll_into_view_if_needed(timeout=3000)
        except Exception:  # noqa: BLE001
            pg.mouse.wheel(0, 700)
        pg.wait_for_timeout(1500)
        if caixa.is_visible():
            break
    if not caixa.is_visible():
        corpo = pg.locator("ytd-comments#comments").first.inner_text(timeout=3000) if pg.locator("ytd-comments#comments").count() else ""
        if re.search(r"desativad|turned off", corpo, re.I):
            return "aviso: comentários desativados neste vídeo"
        yw._shot(pg, "comentario_sem_caixa")
        return "pendente: a caixa de comentário não apareceu"
    chave = re.sub(r"[^\w\s\"'?!.,:-]", "", texto).strip()[:35]  # emoji vira <img> na página: some do texto
    threads = pg.locator("ytd-comment-thread-renderer")
    meu = threads.filter(has_text=chave).first
    if meu.count() and re.search(r"Fixado por|Pinned by", meu.inner_text(), re.I):
        return "ja"
    if not meu.count():
        caixa.click()
        editor = pg.locator("#contenteditable-root").first
        editor.wait_for(state="visible", timeout=10000)
        editor.click()
        pg.keyboard.insert_text(texto)
        pg.wait_for_timeout(800)
        enviar = pg.locator("ytd-commentbox #submit-button").first
        aviso = pg.locator("tp-yt-paper-dialog:visible, ytd-popup-container [role=dialog]:visible").filter(
            has_text=re.compile(r"todos podem ver|everyone can see", re.I)).first
        for _ in range(3):  # 1º comentário do canal: aviso "Vale lembrar que todos podem ver" segura o envio
            if enviar.is_visible():
                enviar.click()
            try:
                meu.wait_for(state="visible", timeout=8000)
                break
            except Exception:  # noqa: BLE001
                if aviso.count():
                    _fechar_dialogo(aviso, "aviso do 1o comentario")
                    pg.wait_for_timeout(1500)
        if not meu.is_visible():
            yw._shot(pg, "comentario_nao_saiu")
            return "aviso: o comentário não apareceu depois de enviar"
        pg.wait_for_timeout(2000)
    if _SLUG and negado_ate(_SLUG) is not None:  # 05/11: fixar = recurso avançado negado; não esbarra de novo
        return f"aviso: comentário postado; fixar pulado (recursos avançados negados até {negado_ate(_SLUG) or '?'})"
    meu.scroll_into_view_if_needed()
    meu.hover()
    meu.locator("#action-menu button, #action-menu yt-icon-button").first.click()
    pg.wait_for_timeout(1500)
    fixar = pg.locator("ytd-menu-service-item-renderer:visible, tp-yt-paper-item:visible").filter(
        has_text=re.compile(r"^\s*(Fixar( no topo)?|Pin)\s*$", re.I)).first
    if not fixar.count():
        yw._shot(pg, "comentario_sem_fixar")
        pg.keyboard.press("Escape")
        return "aviso: comentário postado, mas o menu não tem 'Fixar'"
    fixar.click()
    pg.wait_for_timeout(2000)
    # canal em verificação: "Seu vídeo está sendo analisado ... 24 horas" e o comentário NÃO fica fixado (15/10)
    analise = pg.locator("tp-yt-paper-dialog:visible, ytd-popup-container [role=dialog]:visible").filter(
        has_text=re.compile(r"sendo analisad|being reviewed|verifica", re.I)).first

    def barrado():
        if not analise.count():
            return False
        _fechar_dialogo(analise, "verificacao do canal")
        return True

    if barrado():
        return "pendente: comentário postado; fixar libera depois da verificação do canal"
    bloqueio = _bloqueio_conta(pg, 3000)
    if bloqueio:
        return bloqueio  # o comentário fica postado, só não fixa
    yw._clicar_se_existe(pg, "yt-confirm-dialog-renderer #confirm-button, ytd-popup-container #confirm-button", 5000)
    pg.wait_for_timeout(3000)
    if barrado():
        return "pendente: comentário postado; fixar libera depois da verificação do canal"
    yw._shot(pg, "comentario_fixado")
    if re.search(r"Fixado por|Pinned by", meu.inner_text(), re.I):
        return "ok"
    return "aviso: cliquei em fixar, mas o comentário não mostra 'Fixado por' (ver print comentario_fixado)"


# ─────────────────────────── rascunhos presos ──────────────────────────────
def limpar_rascunhos(pg, channel_id, ensaio=False, maximo=40):
    """Apaga os rascunhos (linhas com "Editar rascunho") das abas Vídeos e Shorts. Roda dentro da trava do upload,
    então nenhum upload deste PC está no meio. Confere o título no diálogo antes de confirmar."""
    apagados, vistos = [], []
    for aba in ("upload", "short"):
        yw._abrir_studio(pg, channel_id, f"/videos/{aba}")
        pg.wait_for_timeout(6000)
        for _ in range(maximo):
            linha = pg.locator("ytcp-video-row").filter(has=pg.locator("ytcp-button", has_text=RASCUNHO)).first
            if not linha.count():
                break
            titulo = linha.locator("#video-title").first.inner_text().strip()
            # rascunho não tem link: o ID só aparece na miniatura (i9.ytimg.com/vi/<ID>/...)
            imgs = " ".join(linha.evaluate("el => Array.from(el.querySelectorAll('img')).map(i => i.src)"))
            alvo = (re.search(r"/vi/([\w-]{11})/", imgs) or [None, None])[1]
            if ensaio:
                vistos += [t.strip() for t in pg.locator("ytcp-video-row").filter(
                    has=pg.locator("ytcp-button", has_text=RASCUNHO)).locator("#video-title").all_inner_texts()]
                break
            linha.hover()
            # 23/10: envio que falhou ("Processamento interrompido") não tem o menu Opções — tem "Excluir vídeo" na linha
            direto = linha.locator("ytcp-button:visible, button:visible").filter(
                has_text=re.compile(r"^\s*(Excluir v[ií]deo|Delete video)\s*$", re.I)).first
            opcoes = linha.locator("ytcp-icon-button[aria-label='Opções'], ytcp-icon-button[aria-label='Options']").first
            if direto.count() and not opcoes.is_visible():
                direto.click()
            else:
                opcoes.click()
                pg.locator("tp-yt-paper-item[test-id=delete]:visible").first.click()
            dlg = pg.locator("tp-yt-paper-dialog:visible, ytcp-dialog:visible").last
            dlg.wait_for(state="visible", timeout=10000)
            if titulo[:20].lower() not in dlg.inner_text().lower():
                yw._shot(pg, "rascunho_dialogo_estranho")
                pg.keyboard.press("Escape")
                return f"aviso: o diálogo de exclusão não mostrou o rascunho '{titulo[:40]}'; parei ({len(apagados)} apagados)"
            marca = dlg.locator("ytcp-checkbox-lit:visible, tp-yt-paper-checkbox:visible, #confirm-checkbox:visible").first
            if marca.count():
                marca.click()
                pg.wait_for_timeout(500)
            # envio que falhou não tem miniatura: confere pelo título (23/10)
            esse = pg.locator(f"ytcp-video-row img[src*='/vi/{alvo}/']") if alvo else \
                (pg.locator("ytcp-video-row #video-title").filter(has_text=titulo) if titulo else None)
            dlg.locator("ytcp-button:visible, button:visible").filter(
                has_text=re.compile(r"Excluir v[ií]deo rascunho|Delete draft|Excluir para sempre|Delete forever|"
                                    r"^\s*Excluir( v[ií]deo)?\s*$|^\s*Delete( video)?\s*$", re.I)).last.click()
            for _ in range(20):
                pg.wait_for_timeout(1000)
                if esse is not None and not esse.count():  # a lista recarrega mais linhas: contar não serve
                    break
            else:
                yw._shot(pg, "rascunho_nao_sumiu")
                return f"aviso: o rascunho '{titulo[:40]}' não sumiu da lista ({len(apagados)} apagados)"
            apagados.append(titulo)
            log(f"  rascunho apagado: {titulo[:60]}")
    if ensaio:
        return f"ensaio: {len(vistos)} rascunho(s): " + "; ".join(vistos)[:300]
    return f"ok: {len(apagados)} rascunho(s) apagado(s)" if apagados else "ja"


# ─────────────────────────── trocar textos (nome da obra fora, 15/10) ──────
def _escrever(pg, sel, texto):
    """Troca o texto de uma caixa contenteditable do Studio (título/descrição). Devolve o texto que ficou."""
    tb = pg.locator(sel).first
    tb.click()
    pg.keyboard.press("Control+A")
    pg.keyboard.press("Delete")
    pg.wait_for_timeout(300)
    pg.keyboard.insert_text(texto)
    pg.wait_for_timeout(800)
    return tb.inner_text().strip()


def playlists(pg, channel_id):
    """[{titulo, id, videos}] das playlists do canal (aba Playlists do Conteúdo)."""
    pg.goto(f"https://studio.youtube.com/channel/{channel_id}/content/playlists", wait_until="domcontentloaded",
            timeout=90000)
    yw.esperar_assentar(pg)
    pg.locator("ytcp-playlist-row").first.wait_for(state="visible", timeout=45000)
    pg.wait_for_timeout(2500)
    out = []
    for r in pg.locator("ytcp-playlist-row").all():
        # linha: miniatura(nº) | título | descrição | tipo | visibilidade | data | nº de vídeos | visualizações
        txt = [x.strip() for x in (r.inner_text() or "").split("\n") if x.strip()]
        href = next((a.get_attribute("href") for a in r.locator("a[href*='/edit']").all()), "") or ""
        m = re.search(r"/playlist/([\w-]+)/edit", href)
        out.append({"titulo": txt[1] if len(txt) > 1 else "", "id": m.group(1) if m else "",
                    "videos": int(txt[-2]) if len(txt) >= 2 and txt[-2].isdigit() else None})
    return out


def ler_comentarios(pg, channel_id, maximo=30):
    """[{autor, quando, texto, video, chave}] dos comentários SEM RESPOSTA do canal (Comunidade > Comentários), mais
    recentes primeiro. Pros canais sem token da API (Noturnos, 21/10). chave = autor|texto|vídeo (dedupe)."""
    pg.goto(f"https://studio.youtube.com/channel/{channel_id}/comments/inbox", wait_until="domcontentloaded",
            timeout=90000)
    yw.esperar_assentar(pg)
    try:
        pg.locator("ytcp-comment-thread").first.wait_for(state="visible", timeout=30000)
    except Exception:  # noqa: BLE001  (nenhum comentário sem resposta)
        return []
    pg.wait_for_timeout(2000)
    out = []
    for th in pg.locator("ytcp-comment-thread").all()[:maximo]:
        linhas = [x.strip() for x in (th.inner_text() or "").split("\n") if x.strip()]
        if len(linhas) < 3:
            continue
        m = re.match(r"(@?\S+)\s*•\s*(.+)", linhas[0])
        autor, quando = (m.group(1), m.group(2)) if m else (linhas[0], "")
        fim = next((i for i, x in enumerate(linhas) if x == "Responder"), len(linhas))
        texto = " ".join(linhas[1:fim])
        video = linhas[-1] if fim < len(linhas) - 1 else ""
        out.append({"autor": autor, "quando": quando, "texto": texto, "video": video,
                    "chave": f"{autor}|{texto}|{video}"[:300]})
    return out


AVISOS_RUINS = ("Bloqueado", "Direitos autorais", "Restrito", "Restrição por idade", "Reivindicação de direitos autorais")


def avisos_conteudo(pg, channel_id, abas=("short", "upload"), maximo=40, ja_lidos=()):
    """[{video, titulo, aviso, abas}] dos vídeos com aviso ruim (Bloqueado / direitos autorais / restrito) na lista de
    Conteúdo do Studio — coluna "Avisos" (21/10: ~6% dos Shorts recentes de 3 canais estavam "Bloqueado" e o sistema
    contava como agendados)."""
    out = []
    for aba in abas:
        pg.goto(f"https://studio.youtube.com/channel/{channel_id}/videos/{aba}", wait_until="domcontentloaded",
                timeout=90000)
        yw.esperar_assentar(pg)
        try:
            pg.locator("ytcp-video-row").first.wait_for(state="visible", timeout=30000)
        except Exception:  # noqa: BLE001  (aba vazia)
            continue
        pg.wait_for_timeout(2500)
        vistos = set()
        for r in pg.locator("ytcp-video-row").all()[:maximo]:
            t = [x.strip() for x in (r.inner_text() or "").split("\n") if x.strip()]
            titulo = t[1] if len(t) > 1 else ""
            aviso = next((x for x in t if x in AVISOS_RUINS), None)
            # mesmo título 2x no canal = upload repetido (21/10: Dorama Noturno; o 1º estourou o tempo sem registro)
            if not aviso and titulo and titulo in vistos and aba == "short":
                aviso = "Duplicado"
            vistos.add(titulo)
            if not aviso:
                continue
            href = next((a.get_attribute("href") for a in r.locator("a[href*='/video/']").all()), "") or ""
            m = re.search(r"/video/([\w-]{11})", href)
            out.append({"video": m.group(1) if m else "", "titulo": titulo, "aviso": aviso, "aba": aba})
    # causa de cada bloqueio/direitos (tabela de reivindicações) — quem já foi lido antes vem de `ja_lidos`
    for x in out:
        if x["aviso"] != "Duplicado" and x["video"] and x["video"] not in ja_lidos:
            try:
                x["reivindicacoes"] = reivindicacoes(pg, x["video"])
            except Exception as e:  # noqa: BLE001
                x["reivindicacoes_erro"] = f"{type(e).__name__}: {str(e)[:80]}"
    return out


def views_lista(pg, channel_id, alvos=(), abas=("short", "upload"), paginas=4):
    """{video: {views, visibilidade, data}} lidos na lista de Conteúdo do Studio (colunas "Visualizações" e
    "Visibilidade"; conferido no print de 22/10, cartuchoreact). 1 página = 30 vídeos, os agendados vêm no topo: passa
    de página até achar todos os `alvos` (vazio = só a 1ª página de cada aba). M8 (22/10): o metricas() abre 3 páginas
    do Analytics por vídeo e o metricas_rede só dá conta de 3 por hora; aqui 1 canal inteiro sai em ~1 min."""
    out, falta = {}, set(alvos)
    for aba in abas:
        tem = False
        for tentativa in range(2):  # 22/10: no 1º teste do Manhwa Noturno a lista passou de 30 s e veio "vazia"
            pg.goto(f"https://studio.youtube.com/channel/{channel_id}/videos/{aba}", wait_until="domcontentloaded",
                    timeout=90000)
            yw.esperar_assentar(pg)
            try:
                pg.locator("ytcp-video-row").first.wait_for(state="visible", timeout=45000)
                tem = True
                break
            except Exception:  # noqa: BLE001  (aba vazia ou lenta: recarrega 1 vez)
                if tentativa:
                    yw._shot(pg, f"views_lista_{aba}_sem_linhas")
        if not tem:
            continue
        for _pagina in range(paginas):
            pg.wait_for_timeout(2500)
            primeiro = ""
            for r in pg.locator("ytcp-video-row").all():
                href = next((a.get_attribute("href") for a in r.locator("a[href*='/video/']").all()), "") or ""
                m = re.search(r"/video/([\w-]{11})", href)
                if not m:
                    continue
                primeiro = primeiro or m.group(1)

                def _cel(nome, r=r):
                    c = r.locator(f".tablecell-{nome}").first
                    return " ".join((c.inner_text() if c.count() else "").split())
                out[m.group(1)] = {"views": _numero(_cel("views")), "visibilidade": _cel("visibility"),
                                   "data": _cel("date"), "aba": aba}
                falta.discard(m.group(1))
            prox = pg.locator("#navigate-after").first
            if not falta or not prox.count() or (prox.get_attribute("aria-disabled") or "") == "true":
                break
            prox.click()
            for _ in range(20):  # a tabela troca no lugar: espera a 1ª linha mudar
                pg.wait_for_timeout(500)
                h = pg.locator("ytcp-video-row a[href*='/video/']").first
                if h.count() and primeiro not in (h.get_attribute("href") or ""):
                    break
        if not falta and alvos:
            break
    return out


JS_LINHAS_EXPLORE = r"""() => [...document.querySelectorAll('yta-explore-table-row:not(.total-row)')].map(r => {
  const img = r.querySelector('img[src*="/vi/"]');
  const m = img && img.src.match(/\/vi\/([\w-]{11})\//);
  return m ? [m[1], r.innerText.split('\n').map(x => x.trim()).filter(Boolean)] : null;
}).filter(Boolean)"""


def retencao_lista(pg, channel_id, alvos=(), periodo="4_weeks", rolagens=40):
    """{video: {dur_media (s), pct_media (%), continuaram (%), views_periodo, feed_impressoes, impressoes, ctr (%),
    intencionais}} do MODO AVANÇADO do Analytics do canal (tabela por vídeo; conferido em 23/10 no mundoquenaoexiste
    e em 29/10 no inovare_ita com as colunas novas: "Mostrados no feed", "Impressões de miniaturas", "Taxa de cliques
    na miniatura", "Visualizações intencionais"). 1 página pro canal inteiro em vez das 3 do metricas() por vídeo.
    ret30 (curva aos 0:30) não existe nessa tabela. Período 4 semanas cobre a vida toda dos alvos do lote (até 21
    dias). A tabela só desenha as linhas visíveis: rola até achar todos os `alvos` ou parar de aparecer linha nova.
    29/10 (Fable): "Mostrados no feed" vem "—" por vídeo (o YouTube só dá no total/série); fica no dicionário pra
    quando o Studio passar a mostrar. ANTES DE MUDAR as métricas/parsing: ler
    D:\\hipercool-materiais\\tarefas complexas para fable 5.1\\FABLE_DECISOES.md (D2) — dona 29/10."""
    mets = ("VIEWS", "SHORTS_FEED_IMPRESSIONS", "SHORTS_FEED_IMPRESSIONS_VTR", "VIDEO_THUMBNAIL_IMPRESSIONS",
            "VIDEO_THUMBNAIL_IMPRESSIONS_VTR", "AVERAGE_WATCH_TIME", "AVERAGE_WATCH_PERCENTAGE", "ENGAGED_VIEWS")
    url = (f"https://studio.youtube.com/channel/{channel_id}/analytics/tab-overview/period-default/explore?"
           f"entity_type=CHANNEL&entity_id={channel_id}&time_period={periodo}&explore_type=TABLE_AND_CHART"
           f"&metric=VIEWS&granularity=DAY&" + "&".join(f"t_metrics={m}" for m in mets) +
           "&dimension=VIDEO&o_column=VIEWS&o_direction=ANALYTICS_ORDER_DIRECTION_DESC")
    linhas = "yta-explore-table-row:not(.total-row)"
    for tentativa in range(2):  # 29/10: às 00:50 o Studio levou mais de 45 s pra desenhar a tabela (print mostrava
        pg.goto(url, wait_until="domcontentloaded", timeout=90000)  # ela pronta) e o lote ficou sem retenção
        yw.esperar_assentar(pg)
        try:
            pg.locator(linhas).first.wait_for(state="visible", timeout=90000)
            break
        except Exception:  # noqa: BLE001  (canal sem view no período, ou o Studio não abriu)
            if tentativa:
                yw._shot(pg, "retencao_lista_sem_linhas")
                return {}
    pg.wait_for_timeout(3000)
    out, falta, parado = {}, set(alvos), 0
    for _ in range(rolagens):
        antes = len(out)
        for vid, t in pg.evaluate(JS_LINHAS_EXPLORE):
            # [duração, título (1 ou 2 linhas), views, % das views, mostrados no feed, % deles, continuaram,
            # impressões de miniaturas, CTR, duração média, % assistida, intencionais, % delas]: lê do FIM, porque o
            # título pode quebrar; valor sem dado vem "—" (conta como coluna). Linha mais curta = tabela de outra
            # versão do Studio: pula em vez de ler coluna errada.
            if len(t) < 13:
                continue
            # views do período junto: com 3 views o "100% continuaram" não diz nada (o placar pesa pela amostra)
            out[vid] = {"dur_media": _numero(t[-4]), "pct_media": _numero(t[-3]), "continuaram": _numero(t[-7]),
                        "views_periodo": _numero(t[-11]), "feed_impressoes": _numero(t[-9]),
                        "impressoes": _numero(t[-6]), "ctr": _numero(t[-5]), "intencionais": _numero(t[-2])}
            falta.discard(vid)
        if alvos and not falta:
            break
        parado = parado + 1 if len(out) == antes else 0
        if parado >= 3:
            break
        try:  # 29/10: com mais colunas a linha virtual fica "instável" e o scroll_into_view estourava o tempo (teste
            pg.locator(linhas).last.scroll_into_view_if_needed(timeout=4000)  # inovare_ita); a roda sozinha basta
        except Exception:  # noqa: BLE001
            pass
        pg.mouse.move(900, 700)  # a roda só rola o que está debaixo do ponteiro
        pg.mouse.wheel(0, 1500)
        pg.wait_for_timeout(1200)
    return out


TIPOS_REIVINDICACAO = ("Áudio", "Vídeo", "Melodia", "Melodia ou letra", "Letra", "Composição", "Música", "Visual",
                       "Áudio e vídeo", "Audiovisual", "Audio", "Video", "Melody", "Lyrics", "Music")


def reivindicacoes(pg, vid):
    """[{conteudo, autor, tipo}] da tabela "Reivindicações" do vídeo no Studio (21/10: é ali que aparece a CAUSA do
    bloqueio — ex. "Cornfield Chase / Hans Zimmer · Áudio"; "deep space / Prod. Riddiman · Áudio", faixa que se dizia
    FREE FOR PROFIT). Linhas da tabela: título, autor, "Direitos autorais", tipo, efeito, botões."""
    pg.goto(f"https://studio.youtube.com/video/{vid}/copyright", wait_until="domcontentloaded", timeout=90000)
    yw.esperar_assentar(pg)
    pg.wait_for_timeout(6000)
    linhas = [x.strip() for x in pg.locator("ytcp-app").first.inner_text().split("\n") if x.strip()]
    out = []
    cabecalho = {"Tipo", "Reivindicar", "Reivindicações", "Type", "Claim"}
    for i, x in enumerate(linhas):
        if x == "Direitos autorais" and i >= 2 and i + 1 < len(linhas) and linhas[i + 1] in TIPOS_REIVINDICACAO:
            conteudo, autor = linhas[i - 2], linhas[i - 1]
            if conteudo in cabecalho:  # reivindicação de imagem (Visual/Audiovisual) não tem a linha do autor
                conteudo, autor = autor, ""
            if conteudo in cabecalho:  # nem o nome aparece (21/10, 5ocUB-tZbos: "Visual" sem título) — não é "Tipo"
                conteudo = ""
            out.append({"conteudo": conteudo, "autor": autor, "tipo": linhas[i + 1]})
    return out


def ler_inscritos(pg, channel_id):
    """Inscritos atuais do painel do canal no Studio (int) ou None."""
    pg.goto(f"https://studio.youtube.com/channel/{channel_id}", wait_until="domcontentloaded", timeout=90000)
    yw.esperar_assentar(pg)
    pg.wait_for_timeout(5000)
    linhas = [x.strip() for x in (pg.inner_text("body") or "").split("\n") if x.strip()]
    for i, x in enumerate(linhas):
        if x.lower().startswith("inscritos atuais") and i + 1 < len(linhas):
            return _numero(linhas[i + 1])
    return None


def renomear_playlist(pg, playlist_id, nome):
    """Troca o título da playlist pela página de edição do Studio e confere depois de recarregar."""
    pg.goto(f"https://studio.youtube.com/playlist/{playlist_id}/edit", wait_until="domcontentloaded", timeout=90000)
    yw.esperar_assentar(pg)
    sel = "ytcp-playlist-metadata-editor #title-textarea #textbox"
    pg.locator(sel).first.wait_for(state="visible", timeout=45000)
    pg.wait_for_timeout(1500)
    if pg.locator(sel).first.inner_text().strip() == nome:
        return "ja"
    _escrever(pg, sel, nome)
    bt = pg.locator("ytcp-button#save").first
    bt.click()
    pg.wait_for_timeout(5000)
    pg.reload(wait_until="domcontentloaded")
    yw.esperar_assentar(pg)
    pg.locator(sel).first.wait_for(state="visible", timeout=45000)
    pg.wait_for_timeout(1500)
    ficou = pg.locator(sel).first.inner_text().strip()
    if ficou != nome:
        yw._shot(pg, "playlist_renomear")
        return f"aviso: ficou '{ficou[:80]}'"
    return "ok"


def editar_metadados(pg, vid, titulo=None, descricao=None, tags=None):
    """Troca título/descrição/tags do vídeo (o que vier None fica como está) e confere depois de recarregar.
    tags = lista; as antigas saem todas (botão "Excluir todas")."""
    log(f"  metadados: abrindo edição de {vid}")
    _abrir_edicao(pg, vid)
    log(f"  metadados: página de edição carregada")
    if titulo is not None:
        log(f"  metadados: trocando título ({len(titulo)} chars)")
        _escrever(pg, "#title-textarea #textbox", titulo)
    if descricao is not None:
        log(f"  metadados: trocando descrição ({len(descricao)} chars)")
        _escrever(pg, "#description-textarea #textbox", descricao)
    if tags is not None:
        log(f"  metadados: trocando tags ({len(tags)} tags)")
        yw._clicar_se_existe(pg, "#toggle-button", 3000)
        pg.locator("#tags-container input#text-input").first.wait_for(state="visible", timeout=20000)
        if pg.locator("#tags-container ytcp-chip").count():
            pg.locator("#tags-container #clear-button").first.click()
            pg.wait_for_timeout(800)
        caixa = pg.locator("#tags-container input#text-input").first
        caixa.click()
        pg.keyboard.insert_text(",".join(t.replace(",", " ") for t in tags) + ",")
        pg.keyboard.press("Enter")
        pg.wait_for_timeout(1000)
    log(f"  metadados: clicando salvar")
    bt = pg.locator("ytcp-button#save").first
    if bt.get_attribute("aria-disabled", timeout=5000) != "true":
        bt.click()
        pg.wait_for_timeout(6000)
    log(f"  metadados: reabrindo para conferir")
    _abrir_edicao(pg, vid)  # confere o que ficou salvo
    falta = []
    if titulo is not None and pg.locator("#title-textarea #textbox").first.inner_text().strip() != titulo.strip():
        falta.append("título")
    if descricao is not None and pg.locator("#description-textarea #textbox").first.inner_text().strip()[:60] != \
            descricao.strip()[:60]:
        falta.append("descrição")
    if tags is not None:
        yw._clicar_se_existe(pg, "#toggle-button", 3000)
        pg.wait_for_timeout(1500)
        ficou = [c.strip() for c in pg.locator("#tags-container ytcp-chip").all_inner_texts()]
        if not ficou:
            falta.append("tags")
    if falta:
        yw._shot(pg, f"metadados_{vid}")
        return f"aviso: não ficou salvo: {', '.join(falta)}"
    log(f"  metadados: ok")
    return "ok"


# ─────────────────────────── visibilidade (tirar do ar sem apagar, 16/10) ──
VISIB_TXT = {"PRIVATE": re.compile(r"privad|private", re.I), "UNLISTED": re.compile(r"não listad|unlisted", re.I),
             "PUBLIC": re.compile(r"públic|public", re.I)}


def colaborar(pg, vid, handle):
    """02/11 dona (collab em todo vídeo, video-fila\\collabs.py escolhe o parceiro): convida o canal `handle` (@...)
    como colaborador. Detalhes > Mostrar mais > Colaboração > "Convidar um colaborador" > busca o @ > escolhe >
    "Criar link" > fecha o link > Salvar (diálogo) > Salvar (página). O link do convite tem formato fixo
    (studio.youtube.com/channel/<convidado>/collaboration/<dono>): o aceite é feito com aceitar_collab."""
    _abrir_edicao(pg, vid)
    pg.locator("ytcp-button#toggle-button, #toggle-button").filter(
        has_text=re.compile(r"mostrar mais|show more", re.I)).first.click(timeout=10000)
    pg.wait_for_timeout(2000)
    corpo = pg.inner_text("body")
    if re.search(r"Gerenciar colaboradores|Manage collaborators", corpo, re.I):
        return "ja"  # vídeo já tem colaborador (convite feito antes)
    bt = pg.get_by_text(re.compile(r"^\s*(Convidar um colaborador|Invite a collaborator)\s*$", re.I)).last
    if not bt.count():
        return "pendente: botão de colaboração não aparece neste canal/vídeo"
    bt.scroll_into_view_if_needed(timeout=5000)
    bt.click(timeout=10000)
    pg.wait_for_timeout(2500)
    dlg = pg.locator("tp-yt-paper-dialog:visible, ytcp-dialog:visible, [role=dialog]:visible").last
    inp = dlg.locator("input:visible").first
    inp.click()
    inp.type(handle, delay=60)
    # 05/11: 101 falhas "colaborar_sem_canal" com o canal NA TELA — o Studio mostra o @ com acento/maiúscula
    # ("@CódigoInteligente-n7j") e o filtro procurava "@codigointeligente-n7j". Compara sem acento e sem caixa.
    import unicodedata

    def _norm(s):
        return "".join(c for c in unicodedata.normalize("NFKD", s or "") if not unicodedata.combining(c)).casefold()
    itens = pg.locator("ytcp-channel-picker-list-item")
    item = None
    for _ in range(15):
        for i in range(itens.count()):
            if _norm(handle) in _norm(itens.nth(i).inner_text()) and itens.nth(i).is_visible():
                item = itens.nth(i)
                break
        if item:
            break
        pg.wait_for_timeout(1000)
    try:
        if item is None:
            raise TimeoutError("sem item")
    except Exception:  # noqa: BLE001
        yw._shot(pg, "colaborar_sem_canal")
        limite = pg.locator("#limit-reached-message:visible").count()
        pg.keyboard.press("Escape")
        return "aviso: limite de convites atingido" if limite else f"aviso: {handle} não apareceu na busca"
    item.click()
    pg.wait_for_timeout(2000)
    pg.locator("ytcp-button:visible, button:visible").filter(
        has_text=re.compile(r"^\s*(Criar link|Create link)\s*$", re.I)).last.click(timeout=10000)
    pg.wait_for_timeout(3500)
    inner = pg.locator("tp-yt-paper-dialog:visible, ytcp-dialog:visible, [role=dialog]:visible").filter(
        has_text=re.compile(r"Copiar e compartilhar o link|Copy and share", re.I)).last
    for sel in ("#close-button", "button[aria-label*='Fechar']", "[aria-label='Close']"):
        b = inner.locator(sel).first
        if b.count():
            b.click()
            break
    else:
        pg.keyboard.press("Escape")
    pg.wait_for_timeout(1500)
    outer = pg.locator("tp-yt-paper-dialog:visible, ytcp-dialog:visible, [role=dialog]:visible").filter(
        has_text=re.compile(r"Aceitação pendente|Pending", re.I)).last
    outer.locator("ytcp-button:visible, button:visible").filter(
        has_text=re.compile(r"^\s*(Salvar|Save)\s*$", re.I)).last.click(timeout=10000)
    pg.wait_for_timeout(3000)
    _salvar_pagina(pg)
    pg.wait_for_timeout(3000)
    if not re.search(r"Gerenciar colaboradores|Manage collaborators", pg.inner_text("body"), re.I):
        yw._shot(pg, "colaborar_nao_salvou")
        return "aviso: convite não ficou salvo"
    return "ok"


def aceitar_collab(pg, link):
    """Canal CONVIDADO abre o link do convite (aba Colaborações do Studio dele) e clica Aceitar. Vários convites do
    mesmo dono: aceita um por vez reabrindo o link (até 5)."""
    feitos = 0
    for _ in range(5):
        pg.goto(link, wait_until="domcontentloaded", timeout=90000)
        if yw.esperar_assentar(pg) == "login":
            raise yw.Falha("morto", "perfil do navegador não está logado (rode youtube_web_poster.py --logar)")
        dlg = pg.locator("tp-yt-paper-dialog:visible, ytcp-dialog:visible, [role=dialog]:visible").filter(
            has_text=re.compile(r"convite para colaborar|invited you to collaborate|invitation to collaborate", re.I))
        lista = pg.get_by_text(re.compile(r"^\s*(Conteúdo do canal|Channel content)\s*$", re.I)).first
        # 02/11: o Studio às vezes fica em BRANCO por >20 s — antes isso virava "ja" (sem aceitar). Agora espera até
        # 60 s pelo convite OU pela lista de conteúdo carregada; nada disso = recarrega 1x; ainda nada = pendente
        carregou = False
        for _tent in range(2):
            for _ in range(30):
                if dlg.count() or lista.is_visible():
                    carregou = True
                    break
                pg.wait_for_timeout(2000)
            if carregou:
                break
            pg.reload(wait_until="domcontentloaded", timeout=90000)
        if not carregou:
            yw._shot(pg, "aceitar_collab_studio_em_branco")
            return f"pendente: Studio não carregou{f' (aceitou {feitos})' if feitos else ''}"
        pg.wait_for_timeout(2500)
        if not dlg.count():
            break
        dlg.first.locator("ytcp-button:visible, button:visible").filter(
            has_text=re.compile(r"^\s*(Aceitar|Accept)\s*$", re.I)).last.click(timeout=10000)
        pg.wait_for_timeout(5000)
        feitos += 1
    if not feitos:
        yw._shot(pg, "aceitar_collab_sem_convite")
        return "ja"
    return "ok" if feitos == 1 else f"ok ({feitos} convites)"


def _visib_atual(pg):
    """Valor do seletor de visibilidade da página de edição ('Privado', 'Público', ...), sem o rótulo
    'Visibilidade' que vem na 1ª linha."""
    txt = (pg.locator("ytcp-video-metadata-visibility").first.inner_text(timeout=20000) or "").strip()
    return txt.split("\n")[-1].strip()


def visibilidade(pg, vid, nivel="private"):
    """Troca a visibilidade do vídeo (private|unlisted|public) pela página de edição e confere depois de recarregar.
    Serve pra tirar do ar um vídeo com problema sem apagar (dá pra voltar a público depois)."""
    nome = {"public": "PUBLIC", "unlisted": "UNLISTED", "private": "PRIVATE"}[nivel]
    _abrir_edicao(pg, vid)
    if VISIB_TXT[nome].search(_visib_atual(pg)):
        return "ja"
    if pg.locator("ytcp-video-metadata-visibility").first.get_attribute("disabled") is not None or \
            pg.get_by_text(re.compile(r"^\s*(Removido|Removed)\s*$")).count():
        return "removido: o YouTube já tirou o vídeo do ar (ver Avisos no Studio)"
    pg.locator("ytcp-video-metadata-visibility #select-button, ytcp-video-metadata-visibility").first.click()
    radio = pg.locator(f"#privacy-radios [name={nome}]").first
    try:
        radio.wait_for(state="visible", timeout=6000)
    except Exception:  # noqa: BLE001 — vídeo agendado: as opções ficam recolhidas em "Salvar ou publicar" (20/10)
        pg.locator("#first-container-expand-button").first.click()
    radio.wait_for(state="visible", timeout=20000)
    radio.click()
    pg.wait_for_timeout(800)
    # 30/10: ao marcar Público o Studio abre "Lembre-se de que todos podem ver o conteúdo público" com um "Ok" que fica
    # na frente do Concluir (print 20261030_111522_visibilidade_iIBHQv-ahlY_falhou.png)
    try:
        ok = pg.get_by_role("button", name=re.compile(r"^\s*(Ok|OK|Entendi|Got it)\s*$"))
        if ok.count():
            ok.first.click(timeout=5000)
            pg.wait_for_timeout(800)
    except Exception:  # noqa: BLE001
        pass
    if not yw._clicar_se_existe(pg, "ytcp-video-visibility-select #save-button, tp-yt-paper-dialog #save-button", 8000):
        yw._shot(pg, f"visibilidade_{vid}_sem_concluir")
        return "aviso: não achei o botão Concluído do seletor de visibilidade"
    pg.wait_for_timeout(1200)
    _salvar_pagina(pg)
    _abrir_edicao(pg, vid)
    ficou = _visib_atual(pg)
    if not VISIB_TXT[nome].search(ficou):
        yw._shot(pg, f"visibilidade_{vid}")
        return f"aviso: ficou '{ficou[:60]}'"
    return "ok"


# ─────────────────────────── métricas (Analytics do vídeo) ─────────────────
def _numero(txt):
    """'1,2 mil' -> 1200.0; '4,5%' -> 4.5; '1.234' -> 1234.0; '1:23' -> 83.0 (s); '—'/vazio -> None."""
    t = (txt or "").strip().lower().replace("\xa0", " ")
    m = re.match(r"^(\d+):(\d{2})(?::(\d{2}))?$", t)
    if m:
        p = [int(x) for x in m.groups() if x is not None]
        return float(p[0] * 3600 + p[1] * 60 + p[2]) if len(p) == 3 else float(p[0] * 60 + p[1])
    m = re.match(r"^([\d.,]+)\s*(mil|mi|k|m)?\b", t)
    if not m:
        return None
    s = m.group(1)
    # 23/10: o Chrome dos notebooks mostra o Studio em INGLÊS ("1,433" views, "44.8%"); antes "1,433" virava 1,433 e
    # "44.8%" virava 448. Grupo de 3 dígitos = milhar nos dois idiomas; com os dois sinais, o último é a decimal.
    if re.fullmatch(r"\d{1,3}([.,]\d{3})+", s):
        s = re.sub(r"[.,]", "", s)
    elif "," in s and "." in s:
        dec = max(s.rfind(","), s.rfind("."))
        s = re.sub(r"[.,]", "", s[:dec]) + "." + s[dec + 1:]
    else:
        s = s.replace(",", ".")
    try:
        n = float(s)
    except ValueError:
        return None
    return n * {"mil": 1e3, "k": 1e3, "mi": 1e6, "m": 1e6}.get(m.group(2) or "", 1)


def _valor_depois(linhas, rotulo):
    """Valor que vem logo depois da linha do rótulo (cartões do Analytics: 'Impressões' \\n '1,2 mil')."""
    for i, l in enumerate(linhas):
        if re.fullmatch(rotulo, l, re.I):
            for prox in linhas[i + 1:i + 4]:
                v = _numero(prox)
                if v is not None or prox.strip() in ("—", "-"):
                    return v
    return None


def _so_traco(linhas, rotulo):
    """O cartão do rótulo existe e mostra "—": o Studio não escreve 0 (22/10, print metricas_x4twHn3UYwU: todos os
    cartões "—" e o gráfico em 0)."""
    for i, l in enumerate(linhas):
        if re.search(rotulo, l, re.I):
            for prox in linhas[i + 1:i + 4]:
                if _numero(prox) is not None:
                    break
                if prox.strip() in ("—", "-"):
                    return True
    return False


JS_CURVA = r"""() => {
  // 29/10 (Fable, LONGOS_01): a curva "Retenção de público" da aba Engajamento é um SVG. Pega o path mais longo do
  // gráfico perto do título, os ticks de % (eixo y) e o fim do eixo x, e devolve pontos crus + calibração.
  const tudo = [...document.querySelectorAll('*')];
  const tit = tudo.find(e => e.children.length === 0 && /Retenção de público|Audience retention/i.test(e.textContent || ''));
  let raiz = tit; for (let i = 0; i < 8 && raiz && !raiz.querySelector('svg path'); i++) raiz = raiz.parentElement;
  if (!raiz) return null;
  const svgs = [...raiz.querySelectorAll('svg')];
  let melhor = null, nPts = 0, svgDe = null;
  for (const s of svgs) for (const p of s.querySelectorAll('path')) {
    const d = p.getAttribute('d') || ''; const n = (d.match(/[-\d.]+[ ,][-\d.]+/g) || []).length;
    if (n > nPts) { nPts = n; melhor = p; svgDe = s; }
  }
  if (!melhor || nPts < 10) return {erro: 'sem path', paths: svgs.length};
  const r0 = svgDe.getBoundingClientRect();
  const ticks = [...svgDe.querySelectorAll('text')].map(t => ({t: (t.textContent||'').trim(), b: t.getBoundingClientRect()}))
     .filter(x => /^\d+%$/.test(x.t)).map(x => ({pct: parseFloat(x.t), y: x.b.top + x.b.height/2 - r0.top}));
  const xs = [...svgDe.querySelectorAll('text')].map(t => ({t: (t.textContent||'').trim(), b: t.getBoundingClientRect()}))
     .filter(x => /^\d+:\d\d(:\d\d)?$/.test(x.t)).map(x => ({t: x.t, x: x.b.left + x.b.width/2 - r0.left}));
  // transforma os pontos do path pra coordenadas do svg (o path pode estar em <g transform>)
  const m = melhor.getScreenCTM(); const pts = [];
  const d = melhor.getAttribute('d');
  for (const mm of d.matchAll(/([ML])\s*([-\d.]+)[ ,]([-\d.]+)/g)) {
    const p = svgDe.createSVGPoint(); p.x = parseFloat(mm[2]); p.y = parseFloat(mm[3]);
    const q = p.matrixTransform(m); pts.push([q.x - r0.left, q.y - r0.top]);
  }
  return {pts, ticks, xs, n: pts.length};
}"""


def _curva_retencao(pg, dur_s=None):
    """[(fração 0..1, % de retenção)] com 50 pontos, calibrada pelos ticks do eixo y (0%…120%); None se o Studio não
    desenhou a curva ("Retenção média indisponível" aparece mas a curva do vídeo existe). ret_aos(curva, t/dur)."""
    try:
        r = pg.evaluate(JS_CURVA)
    except Exception:  # noqa: BLE001
        return None
    if not r or not r.get("pts") or len(r.get("ticks") or []) < 2:
        return None
    pts, ticks = r["pts"], sorted(r["ticks"], key=lambda t: t["pct"])
    # y(pixel) -> % : reta pelos dois ticks mais afastados
    (p0, y0), (p1, y1) = (ticks[0]["pct"], ticks[0]["y"]), (ticks[-1]["pct"], ticks[-1]["y"])
    if y1 == y0:
        return None
    a = (p1 - p0) / (y1 - y0)
    pct = lambda y: round(p0 + a * (y - y0), 1)  # noqa: E731
    xs = [p[0] for p in pts]
    x0, x1 = min(xs), max(xs)
    if x1 - x0 < 10:
        return None
    pts = sorted(pts)
    out = []
    for i in range(50):
        alvo = x0 + (x1 - x0) * i / 49
        # ponto do path mais próximo em x (a curva tem centenas de pontos)
        j = min(range(len(pts)), key=lambda k: abs(pts[k][0] - alvo))
        out.append((round(i / 49, 3), max(0.0, pct(pts[j][1]))))
    return out


def ret_aos(curva, fracao):
    """% ainda assistindo na fração do vídeo (ex.: 30 s / duração)."""
    if not curva:
        return None
    return min(curva, key=lambda p: abs(p[0] - fracao))[1]


def metricas(pg, vid):
    """Métricas do vídeo no Analytics do Studio (aba Visão geral, Alcance e Engajamento), período padrão:
    {views, impressoes, ctr (%), dur_media (s), ret30 (% ainda assistindo aos 0:30)}; None = sem dado."""
    out, textos = {}, {}
    for aba in ("tab-overview", "tab-reach_viewers", "tab-interest_viewers"):
        # 18/10: metade das falhas de 17/10 era o "Ops! Algo deu errado" do proprio Studio (prints em logs/yt_web), que
        # some ao recarregar - 1 nova tentativa por aba
        for _tentativa in range(2):
            pg.goto(f"https://studio.youtube.com/video/{vid}/analytics/{aba}/period-default",
                    wait_until="domcontentloaded", timeout=90000)
            yw.esperar_assentar(pg)
            pg.wait_for_timeout(9000)
            textos[aba] = pg.locator("ytcp-app").first.inner_text()
            if not re.search(r"Algo deu errado|Something went wrong", textos[aba]):
                if aba == "tab-interest_viewers":  # 29/10 (Fable, LONGOS_01): curva de retenção do SVG, mesma página
                    out["curva"] = _curva_retencao(pg)
                break
    linhas = [x.strip() for t in textos.values() for x in t.split("\n") if x.strip()]
    out["views"] = _valor_depois(linhas, r"visualizações|views")
    # 21/10: o Studio renomeou pra "Impressões de miniaturas" / "Taxa de cliques na miniatura" — com o nome antigo
    # a leitura dava None em todo longo (o placar de título do hipercool, por CTR, nunca recebia dado)
    out["impressoes"] = _valor_depois(linhas, r"impressões( de miniaturas)?|(thumbnail )?impressions")
    out["ctr"] = _valor_depois(linhas, r"taxa de cliques (de|das) impressões|taxa de cliques na miniatura|"
                                       r"(impressions|thumbnail) click-through rate")
    out["dur_media"] = _valor_depois(linhas, r"duração média (da|de) visualização|average view duration")
    eng = textos.get("tab-interest_viewers", "")
    m = re.search(r"([\d.,]+)\s*%[^%\n]{0,90}?\b0:30\b", eng) or re.search(r"\b0:30\b[^%\n]{0,90}?([\d.,]+)\s*%", eng)
    out["ret30"] = _numero(m.group(1)) if m else None
    # 29/10 (Fable): ret30 / ret60 / ret10min pela curva (fração = t / duração do vídeo, lida do "0:00 / 0:33")
    if out.get("curva"):
        md = re.search(r"0:00\s*/\s*(\d+):(\d\d)(?::(\d\d))?", eng)
        if md:
            p = [int(x) for x in md.groups() if x is not None]
            dur = p[0] * 3600 + p[1] * 60 + p[2] if len(p) == 3 else p[0] * 60 + p[1]
            out["dur_video"] = dur
            for nome, seg in (("ret30", 30), ("ret60", 60), ("ret10min", 600)):
                if dur > seg and (nome != "ret30" or out.get("ret30") is None):
                    out[nome] = ret_aos(out["curva"], seg / dur)
            out["ret_meio"], out["ret_fim"] = ret_aos(out["curva"], 0.5), ret_aos(out["curva"], 0.98)
    # Shorts (rotulos conferidos num Short real do CenaReact em 16/10): o card mostra "1,4 mil", mas a frase do topo tem o
    # numero exato; "Continuaram assistindo" = % que NAO deslizou (a metrica do feed de Shorts); "Visualizações
    # intencionais" = quem passou dos segundos iniciais.
    m = re.search(r"teve\s+([\d.]+)\s+visualiza", " ".join(textos.values()))  # \s: o Studio usa espaco nao separavel
    if m:
        out["views"] = _numero(m.group(1))
    out["continuaram"] = _valor_depois(linhas, r"continuaram assistindo|stayed to watch")  # notebooks: Studio em inglês
    out["intencionais"] = _valor_depois(linhas, r"visualizações intencionais|engaged views")
    # vídeo com 0 view caía como "nenhuma métrica" e sumia de todo placar (111 leituras ok, nenhuma com 0)
    if out["views"] is None and _so_traco(linhas, r"visualizações|views"):
        out["views"] = 0
    # 22/10: a frase "Este vídeo não teve nenhuma visualização desde a publicação" também é views=0
    # (caía no "aviso: nenhuma métrica achada" e o vídeo voltava pra fila de releitura pra sempre)
    if out["views"] is None and re.search(r"n[ãa]o teve nenhuma visualiza", " ".join(textos.values()), re.I):
        out["views"] = 0
    if all(v is None for v in out.values()):
        yw._shot(pg, f"metricas_{vid}")
        return {"aviso": "nenhuma métrica achada na página (ver print metricas_<id>)",
                "trecho": " | ".join(linhas[:40])[:600]}
    return out


# ─────────────────────────── uso por outros scripts ────────────────────────
def rodar(canal, video=None, tela_final=None, relacionado=None, titulo_relacionado=None, ab=None, comentario=None,
          limpar_rascunhos=False, timeout=900, metricas=False, curtir=False):
    """Chama este script num processo separado (o Playwright síncrono não convive com outro no mesmo processo) e
    devolve o dict do RESULTADO ({} se não rodou)."""
    cmd = [sys.executable, str(Path(__file__).resolve()), "--canal", canal]
    if video:
        cmd += ["--video", video]
    if tela_final:
        cmd += ["--tela-final", tela_final]
    if relacionado:
        cmd += ["--relacionado", relacionado] + (["--titulo-relacionado", titulo_relacionado] if titulo_relacionado else [])
    if ab:
        cmd += ["--ab", ",".join(str(c) for c in ab)]
    if comentario:
        cmd += ["--comentario", comentario]
    if curtir:
        cmd += ["--curtir"]
    if limpar_rascunhos:
        cmd += ["--limpar-rascunhos"]
    if metricas:
        cmd += ["--metricas"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace",
                           env={**__import__("os").environ, "PYTHONUTF8": "1"})
    except subprocess.TimeoutExpired:
        return {"erro": f"sem resposta em {timeout}s"}
    m = re.search(r"^RESULTADO: (\{.*\})\s*$", r.stdout or "", re.M)
    return json.loads(m.group(1)) if m else {"erro": ((r.stderr or r.stdout or "")[-300:]).strip()}


def main():
    if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--canal", required=True)
    ap.add_argument("--video", help="ID do vídeo (11 caracteres)")
    ap.add_argument("--tela-final", metavar="PLAYLIST")
    ap.add_argument("--relacionado", metavar="ID_COMPLETO", help="(Short) liga ao vídeo completo")
    ap.add_argument("--titulo-relacionado", default="", help="título do completo (ajuda a achar na lista)")
    ap.add_argument("--ab", help="2-3 capas separadas por vírgula")
    ap.add_argument("--capa", help="(com --video) troca a miniatura principal por este arquivo")
    ap.add_argument("--checar-ab", action="store_true", help="(com --video) checa no Studio se o teste A/B concluiu e quem venceu")
    ap.add_argument("--comentario", help="texto do comentário a fixar")
    ap.add_argument("--curtir", action="store_true", help="like do canal no próprio vídeo (só em vídeo público)")
    ap.add_argument("--limpar-rascunhos", action="store_true",
                    help="LISTA os rascunhos presos; so apaga com --apagar-mesmo (16/10: apaga TODOS do canal)")
    ap.add_argument("--apagar-mesmo", action="store_true", help="com --limpar-rascunhos: apaga de verdade")
    ap.add_argument("--ensaio", action="store_true", help="(rascunhos) só lista; (playlists/metadados) só mostra")
    ap.add_argument("--renomear-playlists", metavar="ARQ.json",
                    help='[{"id": "...", "novo": "..."} ou {"antigo": "título atual", "novo": "..."}]')
    ap.add_argument("--metadados", metavar="ARQ.json",
                    help='[{"video": ID, "titulo": "..."|null, "descricao": "..."|null, "tags": [...]|null}]')
    ap.add_argument("--metricas", action="store_true", help="(com --video) lê views/impressões/CTR/retenção 30 s")
    ap.add_argument("--ja-lidos", default="", help="(com --avisos) ids cuja causa já foi lida, separados por vírgula")
    ap.add_argument("--avisos", action="store_true",
                    help="vídeos/Shorts com aviso Bloqueado/direitos autorais/restrito na lista de Conteúdo")
    ap.add_argument("--recursos", action="store_true",
                    help="(12/11) lê o status dos recursos avançados (Configurações > Canal > Qualificação)")
    ap.add_argument("--ler-comentarios", action="store_true",
                    help="comentários sem resposta + inscritos do canal (canais sem token da API)")
    ap.add_argument("--visibilidade", choices=("private", "unlisted", "public"),
                    help="(com --video, aceita vários IDs separados por vírgula) troca a visibilidade")
    ap.add_argument("--colaborar", metavar="@HANDLE", help="(com --video) convida esse canal como colaborador (collab)")
    ap.add_argument("--aceitar-collab", metavar="LINK", help="aceita o convite de collab (link do Studio do convidado)")
    a = ap.parse_args()
    res = {}
    try:
        _canal, slug, e = yw._canal_e_mapa(a.canal)
        global _SLUG
        _SLUG = slug
        negado = negado_ate(slug)
        if negado is not None:  # 05/11: canal sem recursos avançados -> nem abre relacionado / teste A/B
            st = f"bloqueado: recursos avançados negados pelo YouTube (pedir de novo/contestar) até {negado}"
            for flag in ("relacionado", "ab"):
                if getattr(a, flag, None):
                    res[flag if flag != "ab" else "teste_ab"] = st
                    log(f"{flag}: pulado — {st}")
                    setattr(a, flag, None)
        acoes = []
        if a.renomear_playlists:
            pedidos = json.loads(Path(a.renomear_playlists).read_text(encoding="utf-8"))

            def _renomear(pg):
                pls, feito = playlists(pg, e["channel_id"]), {}
                log(f"playlists do canal: {pls}")
                for p in pedidos:
                    alvos = [x for x in pls if (p.get("id") and x["id"] == p["id"]) or
                             (p.get("antigo") and x["titulo"] == p["antigo"])]
                    for x in alvos:
                        feito[x["id"]] = "ensaio" if a.ensaio else renomear_playlist(pg, x["id"], p["novo"])
                        log(f"  playlist {x['id']} '{x['titulo']}' -> '{p['novo']}': {feito[x['id']]}")
                return feito or "nenhuma playlist com esse nome"
            acoes.append(("playlists", _renomear))
        if a.metadados:
            lista = json.loads(Path(a.metadados).read_text(encoding="utf-8"))

            def _metadados(pg):
                feito = {}
                for v in lista:
                    try:
                        feito[v["video"]] = "ensaio" if a.ensaio else editar_metadados(
                            pg, v["video"], v.get("titulo"), v.get("descricao"), v.get("tags"))
                    except yw.Falha:
                        raise
                    except Exception as ex:  # noqa: BLE001
                        yw._shot(pg, f"metadados_{v['video']}_falhou")
                        feito[v["video"]] = f"aviso: {type(ex).__name__}: {str(ex)[:120]}"
                    log(f"  {v['video']}: {feito[v['video']]}")
                return feito
            acoes.append(("metadados", _metadados))
        if a.avisos:
            ja = [x for x in (a.ja_lidos or "").split(",") if x]
            acoes.append(("avisos", lambda pg: avisos_conteudo(pg, e["channel_id"], ja_lidos=ja)))
        if a.recursos:  # 12/11 dona: "veja se os contestados já foram liberados" — lê a página de Recursos do Studio
            acoes.append(("recursos", lambda pg: ler_recursos(pg, e["channel_id"])))
        if a.ler_comentarios:
            acoes.append(("comentarios", lambda pg: ler_comentarios(pg, e["channel_id"])))
            acoes.append(("inscritos", lambda pg: ler_inscritos(pg, e["channel_id"])))
        if a.limpar_rascunhos:
            # 16/10: apagar exige --apagar-mesmo - um teste apagou junto um rascunho antigo de outro upload
            acoes.append(("rascunhos", lambda pg: limpar_rascunhos(pg, e["channel_id"], a.ensaio or not a.apagar_mesmo)))
        if a.video and a.tela_final:
            acoes.append(("tela_final", lambda pg: tela_final(pg, a.video, a.tela_final)))
        if a.video and a.relacionado:
            acoes.append(("relacionado", lambda pg: relacionado(pg, a.video, a.relacionado, a.titulo_relacionado)))
        if a.video and a.capa:  # 01/11: troca a miniatura de um vídeo já postado (capa aprovada pela dona)
            def _trocar_capa(pg):
                _abrir_edicao(pg, a.video)
                r = yw._capa(pg, a.capa)
                pg.wait_for_timeout(2500)
                # 03/11: Animescomia passou do limite diário de miniaturas sem a "verificação única" -> o Studio abre o
                # diálogo e a capa NÃO entra, mas yw._capa dizia "enviada" (print 20261103_151434_capa.png)
                if pg.get_by_text(re.compile(r"verificação única|one-time verification", re.I)).count():
                    yw._shot(pg, "capa_bloqueio_verificacao")
                    yw._clicar_se_existe(pg, "tp-yt-paper-dialog:visible ytcp-button:has-text('Cancelar')", 3000)
                    return "aviso: bloqueio de miniaturas — falta a verificação única do canal"
                if r.startswith("enviada"):
                    salvar = pg.get_by_role("button", name=re.compile(r"^\s*(Salvar|Save)\s*$", re.I)).first
                    try:
                        if salvar.is_disabled() or salvar.get_attribute("aria-disabled") == "true":
                            yw._shot(pg, "capa_nada_mudou")
                            return "aviso: a capa não mudou nada na página (Salvar continuou cinza)"
                    except Exception:  # noqa: BLE001
                        pass
                    if not _salvar_pagina(pg):
                        return "aviso: capa carregada mas o Salvar não confirmou"
                    yw._shot(pg, "capa_salva")
                return r
            acoes.append(("capa", _trocar_capa))
        if a.video and a.ab:
            acoes.append(("teste_ab", lambda pg: teste_ab(pg, a.video, a.ab.split(","))))
        if a.video and a.checar_ab:
            acoes.append(("checar_ab", lambda pg: checar_vencedor_ab(pg, a.video)))
        if a.video and a.comentario:
            try:  # 23/10: indicação do canal parceiro da dupla no fim do comentário fixado (config/indicacoes.json)
                import indicacoes
                a.comentario = indicacoes.no_comentario(a.canal, a.comentario, a.video)
            except Exception:  # noqa: BLE001
                pass
            acoes.append(("comentario", lambda pg: comentar_fixar(pg, a.video, a.comentario)))
        if a.video and a.curtir:
            acoes.append(("curtir", lambda pg: curtir(pg, a.video)))
        if a.video and a.metricas:
            acoes.append(("metricas", lambda pg: metricas(pg, a.video)))
        if a.video and a.visibilidade:
            def _visib(pg):
                feito = {}
                for v in a.video.split(","):
                    try:
                        feito[v] = visibilidade(pg, v.strip(), a.visibilidade)
                    except yw.Falha:
                        raise
                    except Exception as ex:  # noqa: BLE001
                        yw._shot(pg, f"visibilidade_{v}_falhou")
                        feito[v] = f"aviso: {type(ex).__name__}: {str(ex)[:120]}"
                    log(f"  {v}: {feito[v]}")
                return feito
            acoes.append(("visibilidade", _visib))
        if a.video and a.colaborar:
            acoes.append(("colaborar", lambda pg: colaborar(pg, a.video, a.colaborar)))
        if a.aceitar_collab:
            acoes.append(("aceitar_collab", lambda pg: aceitar_collab(pg, a.aceitar_collab)))
        if not acoes and res:  # tudo que foi pedido estava bloqueado: responde sem abrir o Chrome
            print("RESULTADO: " + json.dumps(res, ensure_ascii=False), flush=True)
            return
        if not acoes:
            ap.error("nada a fazer (use --video com --tela-final/--relacionado/--ab/--comentario/--curtir, --limpar-rascunhos, "
                     "--renomear-playlists ou --metadados)")
        with sessao(e) as pg:
            for nome, fn in acoes:
                try:
                    res[nome] = fn(pg)
                except yw.Falha:
                    raise
                except Exception as ex:  # noqa: BLE001
                    yw._shot(pg, f"{nome}_falhou")
                    res[nome] = f"aviso: {type(ex).__name__}: {str(ex)[:120]}"
                log(f"{nome}: {res[nome]}")
    except yw.Falha as f:
        res["erro"] = f"{f.status}: {f}"
    print("RESULTADO: " + json.dumps(res, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
