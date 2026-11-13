# -*- coding: utf-8 -*-
"""hp_common.py — base compartilhada do pipeline hipercool.

Coisas que TODOS os pedaços do pipeline usam: caminhos do projeto, a função
log() e uns defaults. Fica separado pra evitar import circular entre
hiper-pipeline.py, narration.py e tts_stage.py.

Se você só quer achar uma pasta (videos, cache, tmp) ou mudar o watermark,
é AQUI. Não tem lógica de negócio, só constantes + log.
"""
import os
import sys
from datetime import datetime
from pathlib import Path

# Raiz do projeto = pai da pasta bin/. Todas as pastas derivam daqui.
PROJECT_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = PROJECT_DIR / "workspace" / "cache"
VIDEOS_DIR = PROJECT_DIR / "workspace" / "videos"
TMP_DIR = PROJECT_DIR / "workspace" / "tmp"

# Handle do canal pro watermark (configurável via env HIPERCOOL_WATERMARK).
WATERMARK_HANDLE = os.environ.get("HIPERCOOL_WATERMARK", "@InovareManhwaVerse")

# Garante que as pastas de saída existem antes de qualquer render.
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
TMP_DIR.mkdir(parents=True, exist_ok=True)

# Quantidade padrão de painéis processados quando --max-panels não é passado.
MAX_PANELS_DEFAULT = 50


def log(msg):
    """Log com timestamp no stderr (stdout fica livre pro pipe do vídeo)."""
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", file=sys.stderr)
