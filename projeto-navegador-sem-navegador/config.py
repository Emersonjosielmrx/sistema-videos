# -*- coding: utf-8 -*-
"""
config.py — Configurações centrais do projeto-navegador-sem-navegador.
Define caminhos, portas, URLs base e parâmetros padrão de cada serviço.
"""
import os
from pathlib import Path

# Diretórios base
ROOT_DIR = Path(__file__).resolve().parent
COOKIES_DIR = ROOT_DIR / "cookies"
COOKIES_DIR.mkdir(exist_ok=True)

# Diretórios externos de referência (somente leitura)
COFRE_DIR = Path(r"D:\logins-google\cofre")
GEMINI_ARGO_COOKIES = Path(r"D:\gemini-argo\cookies")
GEMINI_ARGO_YT_COOKIES = Path(r"D:\gemini-argo\cookies_youtube")
POSTADOR_CONFIG = Path(r"D:\postador-de-videos\config")

# User-Agents padronizados (Desktop e Mobile)
UA_DESKTOP = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
UA_MOBILE = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1"
)

# URLs e Endpoints
URLS = {
    "google": "https://www.google.com",
    "youtube": "https://www.youtube.com",
    "youtube_studio": "https://studio.youtube.com",
    "google_photos": "https://photos.google.com",
    "flow_ai": "https://aisandbox-pa.googleapis.com",
    "instagram": "https://www.instagram.com",
    "tiktok": "https://www.tiktok.com",
}

# Cabeçalhos padrão
DEFAULT_TIMEOUT = 30
