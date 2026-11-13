"""
logger.py — Função de log com timestamp pro mega_engage.

OBJETIVO:
    Uma única função log(msg) que:
    1. Imprime no console (stdout) com timestamp
    2. Grava no arquivo mega_engage_log.txt

CUIDADO:
    - O arquivo é aberto e fechado a cada chamada (não fica preso)
    - Se o arquivo estiver travado, o print() ainda funciona
    - NÃO redirecionar stdout pro arquivo (causa conflito no Windows)

DEPENDENCIAS:
    - config.py (LOG_FILE path)
    - datetime (stdlib)
"""
from datetime import datetime
from .config import LOG_FILE


def log(msg):
    """
    Registra uma mensagem com timestamp.

    Formato: [2026-07-07 12:30:45] Mensagem aqui

    Args:
        msg: string com a mensagem a registrar

    Comportamento:
        - Sempre imprime no stdout (visível no console)
        - Tenta gravar no arquivo de log
        - Se o arquivo estiver travado, só imprime (não crasha)
    """
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"

    # Sempre mostra no console
    print(line)

    # Tenta gravar no arquivo (com tratamento pro Windows não travar)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except PermissionError:
        # Arquivo travado por outro processo — ignora, não crasha
        pass
    except OSError:
        # Disco cheio ou outro erro de IO — ignora
        pass
