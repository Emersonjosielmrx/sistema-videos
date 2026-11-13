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

# -------------------------------------------------------------------
# FLOW POR HTTP NAS MAQUINAS (29/10, D30 em FABLE_DECISOES.md)
# -------------------------------------------------------------------
# Nos notebooks/PC2 o video e pedido ao Flow por HTTP (nsn_worker de la): o Chrome de la so fabrica o token do
# reCAPTCHA e e fechado assim que o Flow aceita o pedido (segundos de Chrome em vez de ~33 min). Falhou/recusou =
# cai no Chrome como antes (nunca sem producao). Desligar tudo: FLOW_HTTP_REMOTO=0. Por conta: contas.SEM_HTTP.
# 12/11 15h (dona: "deixe funcionando do jeito que funciona e da melhor maneira"): DESLIGADO por padrão — o HTTP do
# Flow volta vazio (~2% ok; 875 min de máquina perdidos em 12/11) desde que o Flow virou "agente". Tudo vai direto pela
# tela (Chrome), que é o que funciona. Religar quando o flow_gerar.py estiver refeito com o pedido novo (captura
# capturas\passivo_flow_20261112.jsonl, RPC ogiZ0b): FLOW_HTTP_REMOTO=1 ou trocar o "0" abaixo.
FLOW_HTTP_REMOTO = os.environ.get("FLOW_HTTP_REMOTO", "0") != "0"
# 12/11 16h: IMAGEM por HTTP religada — pedido novo BELUGA (ogiZ0b) testado no STI: 4 imagens ok (9:16/1:1/16:9/3:4,
# com e sem referência) em ~40 s cada. FLOW_HTTP_IMAGEM=0 volta pra tela.
FLOW_HTTP_IMAGEM = os.environ.get("FLOW_HTTP_IMAGEM", "1") != "0"
# False = o Chrome fica aberto ate o fim (so para diagnostico; a RAM do notebook fica presa os ~10 min da geracao)
FLOW_HTTP_FECHAR_CHROME = os.environ.get("FLOW_HTTP_FECHAR_CHROME", "1") != "0"
# Video em 2 fases nas maquinas (29/10): pede (Chrome ~40 s), solta a vez da maquina, baixa depois sem Chrome.
# FLOW_HTTP_2_FASES=0 volta ao jeito de 1 chamada (a maquina fica reservada ate o mp4 chegar).
FLOW_HTTP_2_FASES = os.environ.get("FLOW_HTTP_2_FASES", "1") != "0"

for d in (SESSIONS_DIR, OUTPUT_DIR, LOG_DIR):
    os.makedirs(d, exist_ok=True)
