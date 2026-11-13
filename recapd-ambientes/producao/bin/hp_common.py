# -*- coding: utf-8 -*-
"""hp_common.py — base compartilhada do pipeline hipercool (-fix).

Caminhos do projeto + log() + defaults. Separado pra evitar import circular
entre hiper-pipeline.py, narration.py e tts_stage.py.
NOTA: workspace/* e material/tts_cache são JUNCTIONS pra D:\\hipercool-materiais.
"""
import os
import sys
from datetime import datetime
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = PROJECT_DIR / "workspace" / "cache"
VIDEOS_DIR = PROJECT_DIR / "workspace" / "videos"
TMP_DIR = PROJECT_DIR / "workspace" / "tmp"
WATERMARK_HANDLE = os.environ.get("HIPERCOOL_WATERMARK", "@InovareManhwaVerse")
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
TMP_DIR.mkdir(parents=True, exist_ok=True)
MAX_PANELS_DEFAULT = 50
TEST_MODE = int(os.environ.get("TEST_MODE", "0"))
_ERR_MARKERS = ("erro", "error", "falha", "fail", "\u26a0", "\u2717", "traceback", "exception")


def log(msg):
    """Log com timestamp no stderr (stdout fica livre pro pipe do vídeo)."""
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", file=sys.stderr)
