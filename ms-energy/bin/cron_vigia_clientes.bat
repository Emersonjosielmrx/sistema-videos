@echo off
REM cron_vigia_clientes.bat - tarefa MSEnergy_VigiaClientes (a cada 15 min): comentario novo ou mensagem nova no
REM Direct do @msenergycap avisa na hora no Telegram (bin\vigia_clientes_insta.py).
set PYTHONUTF8=1
D:\veo\venv\Scripts\python.exe D:\ms-energy\bin\vigia_clientes_insta.py >> D:\ms-energy\logs\vigia_clientes.log 2>&1
