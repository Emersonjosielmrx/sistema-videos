@echo off
title Painel Engagement Bot
cd D:\projetos-navegador
start "" http://localhost:8850
start /B "Server" D:\hipercool-videos\venv\Scripts\python.exe D:\projetos-navegador\engage_server.py
echo Servidor iniciado. Para iniciar o bot, execute:
echo D:\hipercool-videos\venv\Scripts\python.exe D:\projetos-navegador\mega_engage.py
echo.
pause
