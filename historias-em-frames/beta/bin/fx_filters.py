# -*- coding: utf-8 -*-
"""fx_filters.py — FILTROS ffmpeg PUROS (sem estado, sem I/O).

Fragmentos de filtro reutilizáveis: glitch, letterbox, rewind, pagetear e o
pacing (gap por mood). Extraído de fx_clips.py em 2026-07-11 pra reduzir o
tamanho do arquivo principal. fx_clips.py re-exporta tudo isto (fachada), então
nenhum import externo precisou mudar.
"""
from fx_assets import H, W

# ══════════════════════════════════════════════════════════════════════════
# PACING DINAMICO — gap entre clips baseado no mood da cena
# ══════════════════════════════════════════════════════════════════════════
MOOD_PACING = {
    "action": 0.1,
    "tense": 0.1,
    "impact": 0.1,
    "terror": 0.15,
    "suspense": 0.2,
    "neutral": 0.3,
    "calm": 0.3,
    "happy": 0.25,
    "comedy": 0.2,
    "sad": 0.5,
    "emotional": 0.5,
    "romantic": 0.4,
    "epic": 0.15,
    "mystery": 0.25,
}
DEFAULT_GAP = 0.3


def get_gap_for_mood(mood):
    """Retorna gap/padding em segundos baseado no mood da cena.

    Cenas de acao/tensao usam gap curto (ritmo rapido).
    Cenas emocionais/tristes usam gap longo (deixar respirar).
    """
    if not mood:
        return DEFAULT_GAP
    return MOOD_PACING.get(mood.lower(), DEFAULT_GAP)


def build_glitch_filter(duration=0.08):
    """Gera filtro de glitch RGB split (deslocamento de canais R/G/B).

    Efeito moderno usado em transições de tensão/revelação.
    Duração curtíssima (0.08s = 2-3 frames) pra não enjoar.
    """
    # RGB split: desloca o canal R pra direita e B pra esquerda
    return (
        f"rgbashift=rh=-4:bh=4:rv=2:bv=-2,"
        f"noise=alls=30:allf=t+u,"
        f"eq=contrast=1.3:brightness=-0.05"
    )


def build_letterbox_filter():
    """Adiciona barras cinematográficas (letterbox 2.39:1 dentro de 9:16).

    Usado em momentos dramáticos pra dar clima de cinema.
    """
    # Barras pretas top/bottom (120px cada = ~12.5% do frame)
    bar_h = 120
    return f"drawbox=x=0:y=0:w={W}:h={bar_h}:color=black:t=fill,drawbox=x=0:y={H-bar_h}:w={W}:h={bar_h}:color=black:t=fill"


def build_rewind_filter():
    """Gera um efeito de rebobinar retrô com scanlines, chromatic aberration e ruído."""
    return (
        "rgbashift=rh=-8:bh=8:rv=4:bv=-4,"
        "noise=alls=40:allf=t+u,"
        "eq=contrast=1.35:brightness=-0.08"
    )


def _build_pagetear_filter():
    """Simula o efeito de rasgar página: wipe diagonal rápido com distorção.

    Combina um scale acelerado + deslocamento horizontal que simula
    a página sendo arrancada para o lado com um leve twist.
    """
    # Wipe lateral acelerado com distorção horizontal (simula rasgar)
    return (
        f"scale={W}:{H}:force_original_aspect_ratio=decrease,"
        f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,"
        f"avgblur=sizeX=30:sizeY=1"
    )
