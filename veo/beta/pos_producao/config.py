"""Configuracao da esteira de pos-producao.

Edite este arquivo para ativar/desativar plugins ou mudar parametros.
O pipeline eh definido por uma lista ORDENADA de plugins; cada um eh aplicado
em sequencia, gerando saidas intermediarias ate chegar no mp4 final.

Arquivos:
  - produtos.json  : lista dos seus produtos de IA + peso + tema alvo
  - branding.json   : handles, cores, fontes, copies fixas
  - pipeline        : ordem dos plugins
"""

import os
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent  # D:\veo\beta

VIDEO_SRC_DIR = ROOT / "videos"
VIDEO_OUT_DIR = ROOT / "videos_pos"  # saida NAO destrutiva
ASSETS_DIR = BASE / "assets"
LOGOS_DIR = BASE / "logos"
AUDIOS_CACHE = BASE / "audios_cache"

# Caminho do ffmpeg central (vem do PATH do user, mas aqui a referencia explicita)
FFMPEG = os.environ.get("FFMPEG_PATH", r"D:\hipercool-materiais\bin\ffmpeg.exe")

CONFIG_PATH = BASE / "config.yaml"


def default_config():
    """Retorna a configuracao padrao. Plugins nao listados aqui ficam desligados."""
    return {
        "video_src": str(VIDEO_SRC_DIR),
        "video_out": str(VIDEO_OUT_DIR),
        "ffmpeg": FFMPEG,
        "pipeline": [
            # Ordem dos plugins aplicados a cada mp4 novo em videos/
            # "plugins.ffmpeg_loudnorm",        # mixar audio + normalizar loudness
            # "plugins.tts_gemini_or_edge",     # injeta fala PT-BR como faixa principal
            # "plugins.branding_watermark",     # CTA + handle fixo
            # "plugins.produto_rotativo",       # overlay do produto IA certo por tema
            # "plugins.crop_9_16",              # pad/crop 9:16 sem tarja preta
        ],
        # limites para a esteira nao virar mineradora de credito
        "max_videos_per_run": 5,
        "skip_if_output_exists": True,
    }


def load_config():
    """Le config.yaml se existir; senao retorna o padrao. Tolerante a I/O."""
    import yaml
    if not CONFIG_PATH.exists():
        return default_config()
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        merged = default_config()
        merged.update(data)
        return merged
    except Exception:
        return default_config()


def save_config(data):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    import yaml
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)
