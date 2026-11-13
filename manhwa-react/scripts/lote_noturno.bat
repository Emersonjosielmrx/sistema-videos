@echo off
REM Processa as gravacoes novas de 1-COLOQUE-AQUI (tarefa ManhwaReact-Lote, 02:00). O editorial ja distribui entre os 12 canais da rede.
set PYTHONUTF8=1
D:\manhwa-react\.venv\Scripts\python.exe D:\manhwa-react\manhwareact.py batch --max 20 >> D:\manhwa-react\logs\lote_noturno.log 2>&1
