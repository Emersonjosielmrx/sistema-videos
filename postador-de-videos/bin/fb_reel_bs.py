"""Posta Reel numa Página do Facebook pelo Meta Business Suite (business.facebook.com/latest/reels_composer).
20/11/2026 — o facebook_cdp_poster (botão 'Criar reel' da página) parou: o layout novo não tem mais o botão.

Regras:
  - Só o FACEBOOK fica marcado em "Postar em" (o Instagram ligado à página é DESMARCADO; ele tem postador próprio).
  - Grupos nunca são marcados.
  - O Chrome tem que já estar aberto na saída da conta (fb_contas.abrir confere isso).
  - Confirma a postagem no fim (tela "Compartilhar"/sucesso) e devolve (ok, motivo).

Uso direto:  python fb_reel_bs.py <conta> <asset_id_da_pagina> <video.mp4> "<texto>"
"""
import sys, time
from pathlib import Path

LOG = Path(__file__).resolve().parent.parent / "logs"
COMPOSER = "https://business.facebook.com/latest/reels_composer?asset_id={}"


def _fechar_avisos(pg):
    for _ in range(3):
        pg.keyboard.press("Escape")
        time.sleep(0.8)
        for e in pg.query_selector_all('[aria-label="Fechar"], [aria-label="Close"]'):
            try:
                if e.is_visible():
                    e.click(); time.sleep(0.8)
            except Exception:
                pass


def _botao(pg, *nomes):
    """Botão visível com o nome. Com vários (20/11: a setinha das miniaturas também se chama 'Avançar'), fica com o
    MAIOR/mais embaixo — o do rodapé."""
    for n in nomes:
        loc = pg.get_by_role("button", name=n, exact=True)
        vis = []
        for i in range(loc.count()):
            el = loc.nth(i)
            if el.is_visible():
                bb = el.bounding_box() or {"width": 0, "y": 0}
                vis.append((bb["width"] >= 60, bb["y"], el))
        if vis:
            return max(vis, key=lambda t: (t[0], t[1]))[2]
    return None


def _so_facebook(pg, nome_pagina):
    """Abre 'Postar em' e deixa marcado só a página do Facebook (desmarca Instagram e grupos)."""
    caixa = pg.locator("text=Postar em").locator("xpath=following::div[@role='combobox' or @aria-haspopup][1]").first
    if not caixa.count():
        caixa = pg.locator("div[role=combobox]").first
    # 20/11: às vezes um aviso cobre a caixa e o clique estoura; se ela já mostra SÓ a página, segue
    rotulo0 = " ".join((caixa.inner_text(timeout=15000) or "").replace("​", " ").split())
    if nome_pagina and rotulo0.casefold() == nome_pagina.casefold():
        return True, [], rotulo0
    try:
        caixa.click(timeout=15000)
    except Exception:
        _fechar_avisos(pg)
        caixa.click(force=True, timeout=15000)
    time.sleep(2.5)
    itens = pg.locator("[role=listbox] [role=option], [role=option]")
    marcados_fb, desmarcou = False, []
    for i in range(itens.count()):
        it = itens.nth(i)
        if not it.is_visible():
            continue
        txt = (it.inner_text() or "").strip()
        sel = (it.get_attribute("aria-selected") or it.get_attribute("aria-checked") or "").lower() == "true"
        tem_ig = it.locator("img[src*='instagram'], svg").count() and "Grupo" not in txt
        e_pagina = txt.split("\n")[0].strip().casefold() == nome_pagina.casefold()
        if e_pagina:
            if not sel:
                it.click(); time.sleep(1)
            marcados_fb = True
        elif sel:
            it.click(); time.sleep(1); desmarcou.append(txt.split("\n")[0])
    pg.keyboard.press("Escape")
    time.sleep(1.5)
    rotulo = " ".join((caixa.inner_text() or "").replace("​", " ").split())
    return marcados_fb, desmarcou, rotulo


def postar(ctx, asset_id, nome_pagina, video, texto, tag="fb"):
    pg = ctx.new_page()
    pg.set_viewport_size({"width": 1366, "height": 900})
    try:
        for tent in range(2):  # pelo proxy o Business Suite às vezes demora a abrir
            try:
                pg.goto(COMPOSER.format(asset_id), wait_until="domcontentloaded", timeout=120000)
                break
            except Exception:
                if tent:
                    raise
                time.sleep(10)
        time.sleep(12)
        if "login" in pg.url:
            return False, "não logado"
        _fechar_avisos(pg)
        ok_fb, desm, rotulo = _so_facebook(pg, nome_pagina)
        print(f"  postar em: '{rotulo}' (desmarcou {desm})", flush=True)
        if not ok_fb or rotulo.casefold() != nome_pagina.casefold():
            pg.screenshot(path=str(LOG / f"{tag}_erro_postar_em.png"))
            return False, f"'Postar em' ficou '{rotulo}' — esperado só '{nome_pagina}'"
        # upload: o botão abre o seletor de arquivo nativo
        with pg.expect_file_chooser(timeout=20000) as fc:
            _botao(pg, "Adicionar vídeo").click()
        fc.value.set_files(str(Path(video).resolve()), timeout=300000)  # pelo proxy o envio do arquivo demora
        print("  vídeo enviado ao seletor", flush=True)
        # texto
        caixa = pg.locator("[contenteditable=true][role=textbox]").first
        caixa.click(); time.sleep(0.5)
        pg.keyboard.insert_text(texto)
        time.sleep(1)
        # espera o upload terminar (Avançar habilita)
        for i in range(120):
            b = _botao(pg, "Avançar")
            if b and (b.get_attribute("aria-disabled") or "false") == "false":
                break
            time.sleep(5)
        else:
            pg.screenshot(path=str(LOG / f"{tag}_erro_upload.png"))
            return False, "upload não terminou em 10 min"
        pg.screenshot(path=str(LOG / f"{tag}_1_criar.png"))
        # Avançar até aparecer Compartilhar/Publicar
        for passo in range(5):  # Criar -> Editar -> Compartilhar: clica Avançar enquanto existir
            b = _botao(pg, "Avançar")
            if not b:
                break
            for _ in range(30):
                if (b.get_attribute("aria-disabled") or "false") == "false":
                    break
                time.sleep(3)
            b.click(); time.sleep(8)
        pg.screenshot(path=str(LOG / f"{tag}_2_final.png"))
        fim = _botao(pg, "Compartilhar", "Publicar", "Compartilhar agora")
        if not fim:
            return False, "botão Compartilhar não apareceu"
        for _ in range(60):  # espera habilitar (processamento)
            if (fim.get_attribute("aria-disabled") or "false") == "false":
                break
            time.sleep(5)
        fim.click()
        print("  Compartilhar clicado", flush=True)
        for i in range(60):
            time.sleep(3)
            corpo = (pg.inner_text("body") or "").lower()
            if any(x in corpo for x in ("reel compartilhado", "seu reel foi", "publicado", "foi compartilhado",
                                        "está sendo publicado", "sendo processado", "processando seu reel")) \
                    or "reels_composer" not in pg.url:
                pg.screenshot(path=str(LOG / f"{tag}_3_ok.png"))
                return True, "ok"
        pg.screenshot(path=str(LOG / f"{tag}_3_sem_confirmacao.png"))
        return False, "sem confirmação depois de Compartilhar (conferir na página)"
    except Exception as e:  # noqa: BLE001
        try:
            pg.screenshot(path=str(LOG / f"{tag}_erro.png"))
        except Exception:
            pass
        return False, f"erro: {e}"[:300]
    finally:
        try:
            pg.close()
        except Exception:
            pass


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from playwright.sync_api import sync_playwright
    import fb_contas
    conta, asset, video, texto = sys.argv[1:5]
    nome = sys.argv[5] if len(sys.argv) > 5 else None
    porta, proc = fb_contas.abrir(conta)
    try:
        with sync_playwright() as p:
            b = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
            print(postar(b.contexts[0], asset, nome, video, texto, tag=f"fb_{conta}"))
    finally:
        fb_contas.fechar(proc)
