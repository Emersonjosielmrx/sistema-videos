@echo off
REM LIGAR_PRODUCAO.bat - Liga o produtor autonomo de videos (destacado).
title Ligar Producao de Videos
set PATH=D:\hipercool-materiais\bin;%PATH%
cd /d D:\hipercool-videos

echo ============================================
echo   LIGANDO PRODUCAO AUTONOMA DE VIDEOS
echo ============================================
echo.

D:\hipercool-videos\venv\Scripts\python.exe D:\hipercool-videos\launch_daemon.py

echo.
echo Producao LIGADA. Roda em segundo plano (sem janela).
echo Log: D:\hipercool-videos\logs\auto-producer.md
echo.
echo Esta janela fecha em 8 segundos...
timeout /t 8 >nul
