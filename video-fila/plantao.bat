@echo off
rem 01/11 (dona): Funcionário de Plantão no Telegram, lido a cada 1 min por conta própria (plantao.py)
set PYTHONUTF8=1
cd /d D:\video-fila
D:\veo\venv\Scripts\python.exe -u plantao.py >> D:\video-fila\estado\plantao_saida.log 2>&1
