"""
MEGA ENGAGE v3 — Entry point.

Este arquivo SÓ importa e roda o módulo principal.
Toda a lógica está em engage_modules/ (dividida e comentada).

Estrutura dos módulos:
    engage_modules/
        __init__.py    → Documentação geral
        config.py      → Caminhos e configuração
        comments.py    → Comentários por idioma
        progress.py    → Carregar/salvar progresso
        logger.py      → Função de log
        flags.py       → Stop/restart via arquivo
        browser.py     → Chrome headless + fingerprint
        engagement.py  → Like/comment/subscribe (1 vídeo)
        worker.py      → Worker (1 conta, N vídeos)
        scheduler.py   → Fila de tarefas + ThreadPool
        main.py        → Loop principal

Para IAs que forem dar manutenção:
    - Cada arquivo tem docstring explicando o que faz
    - Comece por config.py pra entender os caminhos
    - O fluxo é: main → scheduler → worker → engagement
    - Se algo crashar, olhe logger.py (tem try/except pro PermissionError)
"""
import sys
import os

# Garante que o diretório do script é o cwd (pro RODAR_ENGAGE.bat funcionar)
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Adiciona o path do shared/ pra importar google_session
sys.path.insert(0, "D:/projetos-navegador/shared")

from engage_modules.main import main

if __name__ == "__main__":
    main()
