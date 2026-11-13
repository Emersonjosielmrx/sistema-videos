# -*- coding: utf-8 -*-
"""effects_engine.py — FACHADA (mapa do motor de efeitos).

════════════════════════════════════════════════════════════════════════════
LEIA ISTO PRIMEIRO (feito pra modelo grátis / manutenção rápida)
════════════════════════════════════════════════════════════════════════════
Este arquivo NÃO tem mais o código dos efeitos. Ele só RE-EXPORTA os módulos
fx_*.py, pra que quem já usa `effects_engine.X` continue funcionando sem mudar
nada (hiper-pipeline.py, patch-video.py, etc).

O motor foi dividido em 6 arquivos menores (era 1 de 2186 linhas). Se você
precisa consertar/editar algo, abra SÓ o arquivo certo abaixo — não precisa
ler o resto. Isso economiza token e deixa o conserto cirúrgico.

┌─────────────────┬──────────────────────────────────────────────────────────┐
│ ARQUIVO         │ O QUE VIVE LÁ (abra este pra mexer no assunto)             │
├─────────────────┼──────────────────────────────────────────────────────────┤
│ fx_assets.py    │ Dados crus: bancos de MOVIMENTOS (zoompan), TRANSITIONS,   │
│                 │ COLOR_FILTERS, VIGNETTE_FILTERS + classe EffectsManager    │
│                 │ (rotaciona efeitos sem repetir). W/H/FPS moram aqui.       │
│                 │ -> mexa aqui pra: novo movimento de câmera, nova transição, │
│                 │   mudar resolução de render (W,H).                         │
├─────────────────┼──────────────────────────────────────────────────────────┤
│ fx_detect.py    │ "Que tipo de cena é este painel?": is_impact/tension/      │
│                 │ sensual_panel, pick_sfx, get_transition_and_sfx,           │
│                 │ get_event_package, overlay_for_mood, detect_mood_from_text.│
│                 │ Listas de KEYWORDS + EVENT_PACKAGES ficam aqui.            │
│                 │ -> mexa aqui pra: ajustar quando entra shake/glitch/sfx,    │
│                 │   adicionar palavra-gatilho, mudar overlay por clima.      │
├─────────────────┼──────────────────────────────────────────────────────────┤
│ fx_foley.py     │ Som do que ACONTECE na cena (campainha, porta, passos,     │
│                 │ soco): FOLEY_MAP, pick_foley, prepare_foley_audio.         │
│                 │ -> mexa aqui pra: novo som de cena, timing do foley (gap).  │
├─────────────────┼──────────────────────────────────────────────────────────┤
│ fx_clips.py     │ Monta cada clip com ffmpeg: build_clip, build_clip_with_   │
│                 │ shake, build_flash_clip, build_clip_animated, intro/outro, │
│                 │ concat_with_transitions, upscale_to_fullhd, filtros de     │
│                 │ glitch/letterbox/rewind. É o arquivo MAIOR (o coração).    │
│                 │ -> mexa aqui pra: como o vídeo é montado/concatenado.       │
├─────────────────┼──────────────────────────────────────────────────────────┤
│ fx_subtitles.py │ Texto na tela: legendas (render_subtitles/_progressive),   │
│                 │ karaokê, name tag, watermark, burn_subtitles, censura      │
│                 │ (censurar_video). Fontes (_load_font) moram aqui.          │
│                 │ -> mexa aqui pra: estilo/tamanho de legenda, watermark.     │
├─────────────────┼──────────────────────────────────────────────────────────┤
│ fx_music.py     │ Trilha sonora: add_background_music, add_dynamic_music     │
│                 │ (troca trilha conforme o clima da cena).                   │
│                 │ -> mexa aqui pra: volume de trilha, regra de troca de mood. │
└─────────────────┴──────────────────────────────────────────────────────────┘

GRAFO DE DEPENDÊNCIA (quem importa quem — é acíclico, não há import circular):
    fx_assets ← (ninguém)
    fx_detect ← (ninguém)
    fx_foley  ← (ninguém)
    fx_subtitles ← fx_assets (W,H)
    fx_clips  ← fx_assets (W,H,FPS,TRANSITION_DURATION) + fx_subtitles (fontes)
    fx_music  ← fx_detect (SFX_DIR, detect_mood_from_text)

REGRA DE OURO ao editar: mexa DENTRO de um fx_*.py. NÃO mova função de um
arquivo pro outro sem checar o grafo acima (senão cria import circular).
O backup do arquivo gigante original está em bin/_PRE_SPLIT_effects_engine.py.bak.
════════════════════════════════════════════════════════════════════════════
"""

# Re-exporta TUDO de cada módulo. A ordem respeita o grafo de dependência.
from fx_assets import *      # noqa: F401,F403  — dados + EffectsManager
from fx_detect import *      # noqa: F401,F403  — detecção de cena + sfx/overlay
from fx_foley import *       # noqa: F401,F403  — som de cena
from fx_subtitles import *   # noqa: F401,F403  — legendas/nametag/watermark/censura
from fx_clips import *       # noqa: F401,F403  — montagem dos clips (ffmpeg)
from fx_music import *       # noqa: F401,F403  — trilha sonora

# `from X import *` NÃO traz nomes que começam com "_" nem constantes que o
# módulo não lista em __all__. Alguns callers usam nomes específicos, então
# re-importamos explicitamente o que precisa ficar visível como effects_engine.X:
from fx_assets import W, H, FPS, TRANSITION_DURATION
from fx_clips import W_FINAL, H_FINAL
