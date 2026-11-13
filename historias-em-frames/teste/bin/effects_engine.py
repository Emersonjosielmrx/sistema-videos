# -*- coding: utf-8 -*-
"""effects_engine.py — Fachada re-exporta fx_*.py (mesmo padrão do hipercool-fix)."""
from fx_assets import *      # noqa: F401,F403
from fx_detect import *      # noqa: F401,F403
from fx_foley import *       # noqa: F401,F403
from fx_subtitles import *   # noqa: F401,F403
from fx_clips import *       # noqa: F401,F403
from fx_music import *       # noqa: F401,F403

from fx_assets import W, H, FPS, TRANSITION_DURATION   # noqa: F401
from fx_clips import W_FINAL, H_FINAL                   # noqa: F401
