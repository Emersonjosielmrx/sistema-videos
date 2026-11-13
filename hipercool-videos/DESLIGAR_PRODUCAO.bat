@echo off
REM DESLIGAR_PRODUCAO.bat - Para o produtor e todos os processos filhos.
title Desligar Producao de Videos
cd /d D:\hipercool-videos

echo ============================================
echo   DESLIGANDO PRODUCAO AUTONOMA DE VIDEOS
echo ============================================
echo.

D:\hipercool-videos\venv\Scripts\python.exe D:\hipercool-videos\stop_auto_producer.py

echo.
echo Esta janela fecha em 8 segundos...
timeout /t 8 >nul
