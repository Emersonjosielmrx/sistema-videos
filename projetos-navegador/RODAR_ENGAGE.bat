@echo off
title Cross-Engagement Bot
cd /d D:\projetos-navegador

echo Matando Chromes zumbis...
taskkill /F /IM chrome.exe >nul 2>&1

echo Iniciando proxy forwarder...
start "Proxy" /MIN "D:\hipercool-videos\venv\Scripts\python.exe" local_proxy.py
timeout /t 4 /nobreak >nul

echo Iniciando painel server (porta 8850)...
start "Server" /MIN "D:\hipercool-videos\venv\Scripts\python.exe" engage_server.py
timeout /t 2 /nobreak >nul

:loop
echo [%date% %time%] Iniciando mega_engage.py...
"D:\hipercool-videos\venv\Scripts\python.exe" mega_engage.py
echo [%date% %time%] mega_engage caiu. Reiniciando em 10s...
taskkill /F /IM chrome.exe >nul 2>&1
timeout /t 10 /nobreak >nul
goto loop
