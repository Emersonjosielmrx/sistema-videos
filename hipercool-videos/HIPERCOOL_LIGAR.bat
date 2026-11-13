@echo off
REM HIPERCOOL_LIGAR.bat — Liga apenas a produção autônoma de vídeos
title HIPERCOOL — Ligar Produção
set PATH=D:\hipercool-materiais\bin;%PATH%
cd /d D:\hipercool-videos
echo ============================================
echo   HIPERCOOL — LIGAR PRODUCAO
echo ============================================
D:\hipercool-videos\venv\Scripts\python.exe D:\hipercool-videos\launch_daemon.py
echo.
echo Producao LIGADA (daemon destacado, sem janela).
echo Log: D:\hipercool-videos\logs\auto-producer.md
echo.
echo Esta janela fecha em 8s...
timeout /t 8 >nul
