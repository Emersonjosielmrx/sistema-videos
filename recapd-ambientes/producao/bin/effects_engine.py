# -*- coding: utf-8 -*-
"""effects_engine.py — FACHADA do motor de efeitos (split 2026-07-04).

NÃO tem mais o código: só RE-EXPORTA os fx_*.py, pra `effects_engine.X` seguir
funcionando (hiper-pipeline.py etc). Era 1 arquivo de 3515 linhas → 6 menores.
Pra consertar algo, abra SÓ o arquivo certo:

  fx_assets.py    dados crus (movimentos/transições/filtros/cores) + EffectsManager. W/H/FPS.
  fx_detect.py    detecção de cena + escolha de SFX/foley (pick_sfx_for_text, VRAA/REPROV) + mood/overlay.
  fx_foley.py     foley gap da cena + enhance_narration_audio.
  fx_subtitles.py legendas/karaokê/nametag/watermark + censura de vídeo legada + fontes.
  fx_clips.py     montagem ffmpeg: build_clip*, intro/outro, memes, concat_with_xfade, upscale.
  fx_music.py     trilha fixa e dinâmica por clima.

GRAFO (acíclico): fx_assets←(ninguém); fx_detect←fx_assets; fx_foley←fx_assets,fx_detect;
fx_subtitles←fx_assets; fx_clips←fx_assets,fx_detect,fx_subtitles; fx_music←fx_assets,fx_detect.
Backup do gigante: bin/_PRE_SPLIT_effects_engine.py.bak.
"""
from fx_assets import *      # noqa: F401,F403
from fx_detect import *      # noqa: F401,F403
from fx_foley import *       # noqa: F401,F403
from fx_subtitles import *   # noqa: F401,F403
from fx_clips import *       # noqa: F401,F403
from fx_music import *       # noqa: F401,F403

# nomes usados explicitamente por callers (import * já traz públicos; reforço):
from fx_assets import W, H, FPS, TRANSITION_DURATION   # noqa: F401
from fx_clips import W_FINAL, H_FINAL                   # noqa: F401
