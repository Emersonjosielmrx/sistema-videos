@echo off
REM DESLIGAR_SUPERVISOR_AMBIENTES.bat — para o loop do supervisor dos 3 ambientes.
REM NAO mata os workers em si (PROD segue rodando); so encerra o supervisor que
REM decide quem roda. Pra parar tudo, feche tambem os workers.
title Desligar Supervisor Ambientes

echo ============================================
echo   DESLIGANDO SUPERVISOR DOS 3 AMBIENTES
echo ============================================
echo.

REM mata so o processo do supervisor (linha de comando contem ambientes_supervisor.py)
for /f "tokens=2" %%p in ('wmic process where "commandline like '%%ambientes_supervisor.py%%' and name='python.exe'" get processid ^| findstr /r "[0-9]"') do (
  echo Encerrando supervisor pid %%p...
  taskkill /PID %%p /F >nul 2>&1
)

echo.
echo Supervisor DESLIGADO. O PROD que ja estava rodando continua ate terminar.
echo Esta janela fecha em 8 segundos...
timeout /t 8 >nul
