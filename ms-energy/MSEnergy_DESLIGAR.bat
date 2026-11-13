@echo off
REM ============================================================
REM  MS Energy — DESLIGAR
REM  Pausa a geração de shorts solares e mata o loop.
REM  NÃO afeta o Veo principal (rodam independentes).
REM ============================================================
title MS-Energy-DESLIGAR
set PYTHONUTF8=1
cd /d "D:\ms-energy"

echo.
echo ========================================
echo   MS ENERGY — DESLIGANDO PRODUCAO
echo ========================================
echo.

REM Mata o loop do MS Energy (pelo title da janela e pelo script)
powershell -NoProfile -Command ^
  "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'run_loop_ms_energy|MS-Energy-Loop|gerar_short_veo' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"

echo Producao MS Energy desligada.
echo (O Veo principal NAO foi afetado.)
echo.
timeout /t 5 /nobreak >nul
