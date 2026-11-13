"""anime_captions.py — queima legendas no vídeo final.

Módulo isolado. Reusa o caminho COMPROVADO do motor hipercool (PNG via Pillow +
overlay ffmpeg), NÃO usa drawtext (que crasha no Windows por causa de fontfile).

A orientação (deitado/vertical) é decidida por ANIME_ORIENT no início do processo:
o fx_subtitles importa W/H do fx_assets já no tamanho certo, então aqui é só
gerar os PNGs e sobrepor — sem ajuste de dimensão.
"""
import logging
from pathlib import Path

from fx_subtitles import render_subtitles_short, burn_subtitles


def burn_captions(video_in, entries, video_out, orient="landscape"):
    """Queima legendas (1-2 palavras por vez) no vídeo.

    entries: [(texto, duracao_s), ...] na mesma ordem/tempo dos clipes.
    orient:  só informativo aqui (as dims já vêm do fx_assets via ANIME_ORIENT).

    Retorna True se queimou, False se falhou (o vídeo original continua válido).
    """
    # Espera RAM livre antes de gerar os PNGs de legenda (Pillow) e queimá-los
    # (ffmpeg). Sob concorrência com outro render pesado, o Image.new estoura
    # MemoryError; esperar a janela abrir faz a etapa "caber" em vez de falhar.
    try:
        from fx_clips import _wait_for_ram
        _wait_for_ram()
    except Exception:
        pass

    tmp_dir = Path(video_out).parent
    subs = render_subtitles_short(entries, tmp_dir)
    if not subs:
        logging.warning("[captions] nenhuma legenda gerada")
        return False

    ok = burn_subtitles(str(video_in), subs, str(video_out))
    if not ok:
        logging.error("[captions] burn_subtitles falhou")
    return ok
