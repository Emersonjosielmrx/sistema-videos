"""
config.py — Caminhos de arquivos e configuração do bot.

OBJETIVO:
    Centraliza TODOS os caminhos e a leitura/escrita do engage_config.json.
    Qualquer módulo que precise de um caminho importa daqui.

COMO FUNCIONA:
    - Todos os Paths apontam pra D:/projetos-navegador/
    - load_config() lê o JSON de config ou retorna defaults seguros
    - Os defaults são: 5 workers, batch 500, sem pause, horário 0-23h

DEPENDENCIAS:
    - Nenhuma externa (só pathlib e json da stdlib)
"""
import json
from pathlib import Path


# ============================================================
# CAMINHOS FIXOS — não mudar sem ajustar engage_server.py também
# ============================================================

# Pasta raiz do projeto de engajamento
BASE_DIR = Path("D:/projetos-navegador")

# Arquivo JSON com o progresso (quais vídeos já foram engajados e por quem)
PROGRESS_FILE = BASE_DIR / "mega_engage_progress.json"

# Arquivo JSON com a lista de todos os vídeos dos canais alvo
VIDEOS_FILE = BASE_DIR / "all_channel_videos_full.json"

# Arquivo de log — cada linha tem [timestamp] mensagem
LOG_FILE = BASE_DIR / "mega_engage_log.txt"

# Arquivo de configuração editável pelo painel web (porta 8850)
CONFIG_FILE = BASE_DIR / "engage_config.json"

# Flags de controle: criar esses arquivos para/restart o bot
STOP_FLAG = BASE_DIR / "engage_stop.flag"
RESTART_FLAG = BASE_DIR / "engage_restart.flag"

# PID do processo principal (pra monitoramento externo)
PID_FILE = BASE_DIR / "engage_bot.pid"

# Caminho do Chrome no Windows
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

# Meta de engajamento total (1882 vídeos × 19 contas)
TARGET_TOTAL = 1882 * 19


# ============================================================
# DEFAULTS DO CONFIG — usados quando o arquivo não existe
# ============================================================

DEFAULT_CONFIG = {
    "workers": 5,          # Quantas threads simultâneas (max 19)
    "sleep_min": 2,        # Delay mínimo entre ações (segundos)
    "sleep_max": 8,        # Delay máximo entre ações (segundos)
    "batch": 500,          # Quantos vídeos por lote
    "priority": "",        # Canal prioritário (recebe 70% do batch)
    "mode": "both",        # "likes", "comments", ou "both"
    "active_hours": [0, 23],  # Horário de funcionamento [inicio, fim]
    "max_per_account_day": 200,  # Limite diário por conta (anti-ban)
    "max_per_channel_day": 80,   # Limite diário por canal (anti-brigading)
    "blacklist_channels": [],    # Canais ignorados
    "blacklist_videos": [],      # Vídeos ignorados
    "randomize_order": True,     # Embaralhar fila (anti-padrão)
    "comments_extra": {},        # Comentários extras por idioma
    "paused": False,             # Se True, bot fica parado
    "watch_time": [10, 30],      # Tempo de assistência simulado [min, max]
    "subscribe": False,          # Se deve se inscrever nos canais
    "fingerprint": True,         # Se deve variar user-agent/viewport
    "organic_mode": True,        # Se deve assistir vídeos aleatórios entre alvos
}


def load_config():
    """
    Lê a configuração do arquivo JSON.
    Se o arquivo não existir ou estiver corrompido, retorna defaults.

    Returns:
        dict com todas as configurações do bot
    """
    try:
        if CONFIG_FILE.exists():
            return json.loads(CONFIG_FILE.read_text("utf-8"))
    except Exception:
        pass
    return dict(DEFAULT_CONFIG)


def save_config(cfg):
    """
    Salva a configuração de volta no JSON.
    Usado pelo painel web (engage_server.py).

    Args:
        cfg: dict com a configuração a salvar
    """
    CONFIG_FILE.write_text(
        json.dumps(cfg, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
