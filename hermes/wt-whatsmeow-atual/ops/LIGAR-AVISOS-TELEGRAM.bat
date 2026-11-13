@echo off
chcp 65001 >nul
title Hermes Call - ligar os avisos de operacao no Telegram
echo.
echo  LIGAR OS AVISOS DE OPERACAO DO HERMES NO TELEGRAM
echo  -------------------------------------------------
echo  Hoje nenhum aviso chega (o arquivo de configuracao esta vazio desde 03/10):
echo  backup com falha, servico caido e disco cheio avisam ninguem.
echo  Vai pedir o token do bot (nao aparece ao digitar) e o chat id. Nada mais muda.
echo.
set /p OK=Digite SIM e aperte Enter para continuar:
if /I not "%OK%"=="SIM" (
  echo.
  echo  Cancelado. Nada foi alterado.
  echo.
  pause
  exit /b
)
scp "%~dp0vps\configurar-alertas.sh" hermes-prod:/opt/hermes-call/ops/configurar-alertas.sh
ssh -t hermes-prod "chmod 755 /opt/hermes-call/ops/configurar-alertas.sh && /opt/hermes-call/ops/configurar-alertas.sh"
echo.
echo  Se apareceu "AVISO DE TESTE ENVIADO", confira no Telegram e pode fechar esta janela.
pause
