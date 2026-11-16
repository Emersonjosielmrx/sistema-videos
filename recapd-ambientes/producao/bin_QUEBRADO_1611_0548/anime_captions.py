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


def burn_captions(video_in, entries, video_out, orient="landscape"):
    """Queima legendas (1-2 palavras por vez) no vídeo.

    entries: [(texto, duracao_s), ...] na mesma ordem/tempo dos clipes.
    orient:  só informativo aqui (as dims já vêm do fx_assets via ANIME_ORIENT).

    Retorna True se queimou, False se falhou (o vídeo original continua válido).
    """
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

    if force_ass or (n_words >= ass_min and not force_png):
        logging.info(f"[captions] {n_words} cartões — usando libass (1 passada)")
        ok = burn_subtitles_ass(str(video_in), entries, str(video_out))
        if ok:
            return True
        logging.warning("[captions] libass falhou — tentando PNG overlay como fallback")

    tmp_dir = Path(video_out).parent
    subs = render_subtitles_short(entries, tmp_dir)
    if not subs:
        logging.warning("[captions] nenhuma legenda gerada")
        return False

    ok = burn_subtitles(str(video_in), subs, str(video_out))
    if not ok:
        logging.error("[captions] burn_subtitles falhou")
    return ok
