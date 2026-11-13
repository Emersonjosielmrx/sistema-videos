"""anime_captions.py — queima legendas no vídeo final.

Módulo isolado. Reusa o caminho COMPROVADO do motor hipercool (PNG via Pillow +
overlay ffmpeg), NÃO usa drawtext (que crasha no Windows por causa de fontfile).

A orientação (deitado/vertical) é decidida por ANIME_ORIENT no início do processo:
o fx_subtitles importa W/H do fx_assets já no tamanho certo, então aqui é só
gerar os PNGs e sobrepor — sem ajuste de dimensão.
"""
import logging
from pathlib import Path

from fx_subtitles import render_subtitles_short, burn_subtitles, burn_subtitles_ass


def burn_captions(video_in, entries, video_out, orient="landscape",
                  word_times=None, offsets=None, gancho="", gancho_barra=True, falantes=None, tarja=None):
    """Queima legendas (1-2 palavras por vez) no vídeo.

    entries:    [(texto, duracao_s), ...] na mesma ordem/tempo dos clipes.
    orient:     só informativo aqui (as dims já vêm do fx_assets via ANIME_ORIENT).
    word_times: [[[start_rel,end_rel,palavra],...] | None, ...] alinhado a entries —
                timing REAL por palavra do edge-tts (relativo ao clipe). Opcional.
    offsets:    [start_abs_s, ...] alinhado a entries — início absoluto de cada clipe
                no vídeo concatenado (corrige o drift do xfade). Opcional.
    falantes:   [(cor_rgb, nome), ...] alinhado a entries — Short de formato com várias vozes (23/10): a palavra
                acende na cor de quem fala e o nome vai pequeno em cima. None = legenda de sempre.
    tarja:      extra(vw, vh, dur) da tarja de capítulo do longo (anime_tarja_capitulo) — vai junto no libass.

    Retorna True se queimou, False se falhou (o vídeo original continua válido).
    """
    # SANITIZA as entries num ÚNICO ponto de entrada, ANTES de rotear pra
    # qualquer engine (libass/PNG). Remove pontuação órfã no início do texto de
    # cada frase (a vírgula solta ",Quem" que a segmentação por word-timing
    # arrasta pro começo de um fragmento). Ponto único = imune a qual rota rode.
    # char-agnostico: tira QUALQUER pontuacao/simbolo lider por categoria Unicode.
    from fx_subtitles import _strip_lead_punct
    entries = [(_strip_lead_punct(t or ""), d) for (t, d) in entries]

    # Espera RAM/CPU liberar antes de queimar (guarda contra OOM sob concorrência
    # com outro render pesado — veo3/hipercool).
    try:
        from fx_clips import _wait_for_ram
        _wait_for_ram()
    except Exception:
        pass

    # ROTA POR TAMANHO:
    #  - Vídeo longo (muitos cartões) => libass numa passada só. O overlay PNG
    #    re-encoda o vídeo inteiro a cada ~100 cartões: num recap de 40min isso
    #    vira dezenas de passadas (horas). O libass faz tudo numa passada.
    #  - Vídeo curto => mantém o PNG (estilo pixel-perfect já validado no v1).
    # Threshold configurável via ANIME_ASS_MIN_CARDS (default 400 ~ vídeo >5min).
    import os as _os
    n_words = sum(len((t or "").split()) for t, _ in entries)
    try:
        ass_min = int(_os.environ.get("ANIME_ASS_MIN_CARDS", "400"))
    except ValueError:
        ass_min = 400
    force_ass = _os.environ.get("ANIME_SUB_ENGINE", "").lower() == "ass"
    force_png = _os.environ.get("ANIME_SUB_ENGINE", "").lower() == "png"

    # 01/11 dona: legenda MIX + cartões animados + mascote muda no CTA também nos Shorts (só existem no libass) —
    # ANIME_SHORT_MIX=0 volta o Short pra legenda PNG antiga
    short_mix = _os.environ.get("ANIME_SHORT_MIX", "1") != "0"
    if force_ass or tarja or ((n_words >= ass_min or short_mix) and not force_png):  # a tarja só existe no libass
        logging.info(f"[captions] {n_words} cartões — usando libass (1 passada)")
        extra = None
        if gancho_barra:
            import anime_gancho
            extra = anime_gancho.extras(gancho, video_in, na_legenda=True)
        if tarja:
            import anime_tarja_capitulo
            extra = anime_tarja_capitulo.juntar(extra, tarja)
        ok = burn_subtitles_ass(str(video_in), entries, str(video_out),
                                word_times=word_times, offsets=offsets, extra=extra, falantes=falantes)
        if ok:
            return True
        logging.warning("[captions] libass falhou — tentando PNG overlay como fallback")

    tmp_dir = Path(video_out).parent
    try:
        subs = render_subtitles_short(entries, tmp_dir, word_times=word_times, offsets=offsets, falantes=falantes)
    except Exception as e:  # noqa: BLE001 — 23/10: a cor/nome por voz nunca derruba a legenda
        if not falantes:
            raise
        logging.warning(f"[captions] legenda com cor/nome por voz falhou ({type(e).__name__}: {e}) — legenda normal")
        falantes = None
        subs = render_subtitles_short(entries, tmp_dir, word_times=word_times, offsets=offsets)
    if not subs:
        logging.warning("[captions] nenhuma legenda gerada")
        return False

    # 28/10 teste T7: mascote num canto nas pausas da narração, ANTES da legenda (a legenda fica por cima dela)
    if _os.environ.get("CORTES_MASCOTE") == "B":  # sem tempos por palavra (clone) ela usa o volume do áudio
        try:
            import cortes_mascote
            from fx_subtitles import marcar_usado
            com = Path(video_out).with_name("_com_mascote.mp4")
            usou = cortes_mascote.aplicar(video_in, com, word_times, offsets or [])
            if usou:
                video_in = com
            marcar_usado(Path(video_out).parent, "mascote", "B" if usou else "A_falhou")
        except Exception as e:  # noqa: BLE001 — mascote é enfeite; nunca derruba a legenda
            logging.warning(f"[captions] mascote pulada ({type(e).__name__}: {e})")

    ok = burn_subtitles(str(video_in), subs, str(video_out))
    if not ok and not (force_ass or (n_words >= ass_min and not force_png)):
        # 21/10: PNG falhou e o libass ainda não foi tentado — tenta ele antes de sair sem legenda
        logging.warning("[captions] PNG overlay falhou — tentando libass como reserva")
        extra = None
        if gancho_barra:
            import anime_gancho
            extra = anime_gancho.extras(gancho, video_in, na_legenda=True)
        ok = burn_subtitles_ass(str(video_in), entries, str(video_out),
                                word_times=word_times, offsets=offsets, extra=extra, falantes=falantes)
        if ok:
            return True
    if not ok:
        logging.error("[captions] burn_subtitles falhou")
    elif gancho_barra:
        # legenda PNG (Short): gancho + barra numa passada curta à parte
        import anime_gancho
        tmp = Path(video_out).with_name(Path(video_out).stem + "_gancho.mp4")
        if anime_gancho.queimar(video_out, tmp, gancho):
            tmp.replace(video_out)
    return ok
