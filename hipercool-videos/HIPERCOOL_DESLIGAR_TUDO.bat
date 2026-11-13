@echo off
REM HIPERCOOL_DESLIGAR_TUDO.bat — Para produção + painel web
title HIPERCOOL — Desligar TUDO
set PATH=D:\hipercool-materiais\bin;%PATH%
cd /d D:\hipercool-videos
echo ============================================
echo   HIPERCOOL — DESLIGAR TUDO
echo   (producao + painel web 8080)
echo ============================================
echo.
echo [1/2] Parando produção autônoma...
D:\hipercool-videos\venv\Scripts\python.exe D:\hipercool-videos\stop_auto_producer.py
echo.
echo [2/2] Matando painel de controle (8080)...
for /f "tokens=5" %%p in ('netstat -aon ^| findstr :8080 ^| findstr LISTENING') do taskkill /PID %%p /F >nul 2>&1
echo.
echo Tudo DESLIGADO.
echo Esta janela fecha em 8s...
timeout /t 8 >nul
