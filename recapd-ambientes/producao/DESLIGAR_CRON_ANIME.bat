@echo off
REM DESLIGAR_CRON_ANIME.bat — remove o cron noturno de anime do Agendador do Windows.
title Desligar Cron Anime

echo ============================================
echo   DESLIGANDO CRON NOTURNO DE ANIME
echo ============================================
echo.

schtasks /Delete /F /TN "AnimeRecapNoturno"

if %ERRORLEVEL% EQU 0 (
  echo.
  echo Cron DESLIGADO. O pipeline nao sera mais disparado automaticamente.
) else (
  echo.
  echo Nada pra remover (a tarefa pode ja estar desligada).
)
echo.
echo Esta janela fecha em 10 segundos...
timeout /t 10 >nul
