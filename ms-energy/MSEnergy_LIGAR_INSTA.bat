@echo off
REM LIGAR postagem Instagram MS Energy — registra a tarefa no Agendador: 2 por dia (10:17 e 19:37), sem janela.
REM 22/10: o MS Energy gera 2 shorts por dia; com 1 post por dia a fila crescia 1 por dia.
title Ligar Postagem Instagram - MS Energy

echo ============================================
echo   LIGANDO POSTAGEM INSTAGRAM (MS Energy)
echo ============================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command "$a = New-ScheduledTaskAction -Execute 'wscript.exe' -Argument '\"D:\rodar_oculto.vbs\" \"D:\ms-energy\bin\cron_postar_insta.bat\"'; $t = @((New-ScheduledTaskTrigger -Daily -At '10:17'), (New-ScheduledTaskTrigger -Daily -At '19:37')); Register-ScheduledTask -TaskName 'MSEnergy_PostarInsta' -Action $a -Trigger $t -Force | Out-Null"

if %ERRORLEVEL% EQU 0 (
  echo.
  echo Postagem LIGADA. Posta 2 videos por DIA no Instagram ^(Feed + Stories^), as 10:17 e 19:37.
  echo Conta: msenergycap
  echo Log: D:\ms-energy\videos\cron_postar_insta.log
) else (
  echo.
  echo FALHOU ao registrar a tarefa.
)
echo.
echo Esta janela fecha em 10 segundos...
timeout /t 10 >nul
