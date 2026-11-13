@echo off
REM DESLIGAR postagem Instagram MS Energy — remove tarefa do Agendador.
title Desligar Postagem Instagram - MS Energy

echo ============================================
echo   DESLIGANDO POSTAGEM INSTAGRAM (MS Energy)
echo ============================================
echo.

schtasks /Delete /F /TN "MSEnergy_PostarInsta"

if %ERRORLEVEL% EQU 0 (
  echo.
  echo Postagem Instagram DESLIGADA. Nenhum video sera postado automaticamente.
) else (
  echo.
  echo Nada pra remover ^(a tarefa pode ja estar desligada^).
)
echo.
echo Esta janela fecha em 10 segundos...
timeout /t 10 >nul
