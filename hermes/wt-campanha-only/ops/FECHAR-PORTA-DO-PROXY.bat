@echo off
chcp 65001 >nul
title Hermes Call - fechar a porta do proxy no firewall
echo.
echo  FECHAR A PORTA DO PROXY (8888) NO FIREWALL DA PRODUCAO
echo  ------------------------------------------------------
echo  O proxy ja recusa quem nao e uma das suas VPS (desde 05/10 21:32).
echo  Isto fecha tambem a porta no firewall, para os estranhos nem chegarem nele.
echo  Nao mexe no Hermes nem nas ligacoes.
echo.
set /p OK=Digite SIM e aperte Enter para fechar:
if /I not "%OK%"=="SIM" (
  echo.
  echo  Cancelado. Nada foi alterado.
  echo.
  pause
  exit /b
)
ssh -t hermes-prod /opt/hermes-call/ops/trancar-proxy.sh
echo.
echo  Se apareceu "TRANCADO" e o teste deu 403 ou "sem resposta", terminou.
echo  Pode fechar esta janela.
pause
