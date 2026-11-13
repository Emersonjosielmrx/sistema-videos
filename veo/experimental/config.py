# Roteador VEO API-Fake — config
# Transforma o labs.google/fx (Flow / VideoFX) em "API" via automacao de navegador.
# Nao usa token OAuth (o Google barra por scope); usa a sessao logada do navegador (cookies).

import os

BASE = os.path.dirname(os.path.abspath(__file__))
SESSIONS_DIR = os.path.join(BASE, "sessions")   # storage_state por conta
OUTPUT_DIR = os.path.join(BASE, "videos")        # mp4 gerados
LOG_DIR = os.path.join(BASE, "logs")

FLOW_URL = "https://labs.google/fx/tools/flow"
# alternativa (VideoFX antigo): "https://labs.google/fx/tools/video-fx"

# porta do servidor API-fake
API_HOST = "127.0.0.1"
API_PORT = 8790

# quanto esperar (segundos) um video renderizar no site
GEN_TIMEOUT_S = 1800
POLL_S = 5

# roda o navegador visivel (False) ou escondido/headless (True).
# Pra capturar login precisa ser visivel; pra gerar pode ser headless.
# Pode ser sobrescrito por sessao via env FLOW_HEADLESS=1/0.
HEADLESS_GEN = False

# -------------------------------------------------------------------
# RESILIENCIA A CARGA (usados por recursos.py / pool adaptativo / fila)
# -------------------------------------------------------------------
# Quantos MB de RAM cada Chrome+worker consome (pra calcular quantos abrir).
RAM_POR_CHROME_MB = 1500
# Folga de RAM que nunca ocupamos (deixa o Windows respirar).
RAM_RESERVA_MB = 2000
# Maximo de workers em paralelo (subir p/ 10 quando tiver 50 contas).
TETO_WORKERS = 4
# Acima deste % de CPU, corta 1 worker do calculo.
CPU_ALTA_PCT = 85
# Abaixo deste espaco em disco (GB), nao gera video (evita encher o HD).
DISCO_MIN_GB = 5

# Fila de prompts prontos (buffer pra nao desperdicar trabalho do Gemini).
FILA_MIN = 5     # abaixo disso, gera prompts em lote quando a maquina esta livre
FILA_ALVO = 10   # ate quanto encher
FILA_MAX = 30    # teto duro

# Quantos videos um worker faz numa conta antes de liberar e pegar outra.
BATCH_POR_CLAIM = 5

for d in (SESSIONS_DIR, OUTPUT_DIR, LOG_DIR):
    os.makedirs(d, exist_ok=True)
