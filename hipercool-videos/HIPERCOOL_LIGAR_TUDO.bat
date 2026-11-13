@echo off
REM HIPERCOOL_LIGAR_TUDO.bat — Liga produção + painel web (8080)
title HIPERCOOL — Ligar TUDO
set PATH=D:\hipercool-materiais\bin;%PATH%
cd /d D:\hipercool-videos
echo ============================================
echo   HIPERCOOL — LIGAR TUDO
echo   (producao + painel web na porta 8080)
echo ============================================
echo.
echo [1/2] Ligando produção autônoma...
D:\hipercool-videos\venv\Scripts\python.exe D:\hipercool-videos\launch_daemon.py
echo.
echo [2/2] Subindo painel de controle (http://localhost:8080)...
start "HIPERCOOL Painel" /min D:\hipercool-videos\venv\Scripts\pythonw.exe D:\hipercool-videos\painel_html.py
echo.
echo Tudo LIGADO:
echo   - Producao: ver logs/auto-producer.md
echo   - Painel:   http://localhost:8080
echo.
echo Esta janela fecha em 8s...
timeout /t 8 >nul
