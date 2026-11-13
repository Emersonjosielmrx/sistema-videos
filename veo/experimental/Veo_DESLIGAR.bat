@echo off
REM ============================================================
REM  Veo — DESLIGAR
REM  Pausa DE VERDADE: cria PAUSE_SYSTEM, mata os Chromes do bot
REM  e encerra o loop. Nao fica reabrindo Chrome.
REM  Pra religar depois: use um dos botoes LIGAR.
REM ============================================================
title Veo-DESLIGAR
set PYTHONUTF8=1
cd /d "%~dp0"

"%~dp0..\venv\Scripts\python.exe" -u desligar.py

echo.
echo Producao desligada. Feche esta janela.
timeout /t 5 /nobreak >nul
