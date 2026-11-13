# -*- coding: utf-8 -*-
"""Configuracao central da Fabrica Viral."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "db" / "fabrica.db"
LOGS_DIR = BASE_DIR / "logs"
VIDEOS_DIR = BASE_DIR / "videos"

# LLM Proxy
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "http://157.173.207.22:20128")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "<SEGREDO_REMOVIDO>")
LLM_MODEL = os.environ.get("LLM_MODEL", "auto/best-chat")
LLM_MODEL_FAST = os.environ.get("LLM_MODEL_FAST", "antigravity/gemini-2.5-flash-lite")

# YouTube Data API
YT_API_KEY = os.environ.get("YT_API_KEY", "<SEGREDO_REMOVIDO>")

# SerpAPI
SERP_API_KEY = os.environ.get("SERP_API_KEY", "365f405039587e0e04566aedab2dddb4e8d027fb589301b72bb39f2a8b2ffe25")

# Veo API local
VEO_API_URL = os.environ.get("VEO_API_URL", "http://127.0.0.1:8799")
VEO_API_TOKEN = os.environ.get("VEO_API_TOKEN", "")

# Ler token do Veo se nao setado
if not VEO_API_TOKEN:
    tf = Path("D:/hipercool-inferior-fix/roteador-veo-api-fake/.api_token")
    if tf.exists():
        VEO_API_TOKEN = tf.read_text().strip()

# Painel
PAINEL_PORT = int(os.environ.get("PAINEL_PORT", "8800"))

# Canais (29 da fabrica viral)
CANAIS_JSON = Path("D:/credenciais-canais/youtube_canais.json")

# Intervalo entre geracoes (segundos)
INTERVALO_GERACAO = int(os.environ.get("INTERVALO_GERACAO", "180"))
