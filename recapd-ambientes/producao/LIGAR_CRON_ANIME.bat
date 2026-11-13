@echo off
REM LIGAR_CRON_ANIME.bat — registra o cron noturno de anime no Agendador do Windows.
REM A tarefa roda de hora em hora, mas o cron_anime_noturno.bat so executa
REM de fato entre 00:00 e 06:00 (madrugada). Fora disso ele so loga e sai.
title Ligar Cron Anime (madrugada)

echo ============================================
echo   LIGANDO CRON NOTURNO DE ANIME
echo ============================================
echo.

schtasks /Create /F /TN "AnimeRecapNoturno" ^
  /TR "D:\recapd-ambientes\producao\cron_anime_noturno.bat" ^
  /SC HOURLY /ST 00:03 ^
  /RL LIMITED

if %ERRORLEVEL% EQU 0 (
  echo.
  echo Cron LIGADO. Roda de hora em hora; so liga o supervisor entre 0h e 6h.
  echo Log: D:\recapd-ambientes\producao\logs\cron_anime_noturno.log
) else (
  echo.
  echo FALHOU ao registrar a tarefa. Rode como Administrador se necessario.
)
echo.
echo Esta janela fecha em 10 segundos...
timeout /t 10 >nul
