@echo off
rem 28/10 (dona): monitoramento de erros do desktop a cada 30 min (vigia_desktop.py)
set PYTHONUTF8=1
cd /d D:\video-fila
D:\veo\venv\Scripts\python.exe -u vigia_desktop.py >> D:\video-fila\estado\vigia_desktop.log 2>&1
