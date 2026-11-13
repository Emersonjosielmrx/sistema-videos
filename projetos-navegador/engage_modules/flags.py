"""
flags.py — Controle de fluxo via arquivos-flag (stop/restart).

OBJETIVO:
    O painel web ou o usuário pode criar arquivos especiais
    na pasta do projeto pra controlar o bot:
    - engage_stop.flag    → bot para imediatamente
    - engage_restart.flag → bot reinicia o processo

COMO FUNCIONA:
    check_flags() é chamada a cada iteração do loop principal.
    Se encontrar a flag, executa a ação e apaga o arquivo.

DEPENDENCIAS:
    - config.py (STOP_FLAG, RESTART_FLAG paths)
    - logger.py (log)
    - sys, os (stdlib)
"""
import sys

from .config import STOP_FLAG, RESTART_FLAG
from .logger import log


def check_flags():
    """
    Verifica se existem flags de controle e age:
    - STOP_FLAG  → encerra o bot (sys.exit)
    - RESTART_FLAG → encerra o bot (o RODAR_ENGAGE.bat relança automaticamente)

    Deve ser chamada no início de cada ciclo/lote.
    """
    if STOP_FLAG.exists():
        STOP_FLAG.unlink()
        log("STOP flag detectada. Encerrando.")
        sys.exit(0)

    if RESTART_FLAG.exists():
        RESTART_FLAG.unlink()
        log("RESTART flag detectada. Saindo para relaunch pelo bat...")
        sys.exit(0)
