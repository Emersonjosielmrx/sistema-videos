@echo off
REM LIGAR_SUPERVISOR_AMBIENTES.bat — inicia o supervisor dos 3 ambientes em loop.
REM Aplica a REGRA PERMANENTE (ver AMBIENTES.md): PROD nunca para; sob pressao
REM de recurso mata TESTE, depois BETA; PROD e o default.
title Ligar Supervisor Ambientes

echo ============================================
echo   LIGANDO SUPERVISOR DOS 3 AMBIENTES
echo ============================================
echo.
echo Regra: PROD nunca para. Sob pressao mata TESTE, depois BETA.
echo Log: D:\recapd-ambientes\producao\logs\ambientes_supervisor.log
echo.

start "SupervisorAmbientes" /MIN "D:\recapd-ambientes\producao\venv\Scripts\python.exe" ^
  "D:\recapd-ambientes\producao\bin\ambientes_supervisor.py" --loop --intervalo 30

echo Supervisor LIGADO (janela minimizada).
echo Esta janela fecha em 8 segundos...
timeout /t 8 >nul
