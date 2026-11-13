@echo off
chcp 65001 >nul
title Hermes Call - ligar o backup diario de todas as VPS
echo.
echo  LIGAR O BACKUP DIARIO DE TODAS AS VPS NO GOOGLE DRIVE
echo  -----------------------------------------------------
echo  Faz tres coisas, uma depois da outra:
echo    1. autoriza a producao a BUSCAR o backup na VPS de teste;
echo    2. o mesmo na VPS 157;
echo    3. agenda a copia para todo dia as 04:30 e dispara a primeira.
echo  A chave que e criada so serve para entregar o backup, e so para a producao.
echo  Detalhes: docs\BACKUP_TODAS_VPS.md
echo.
set /p OK=Digite SIM e aperte Enter para ligar:
if /I not "%OK%"=="SIM" (
  echo.
  echo  Cancelado. Nada foi alterado.
  echo.
  pause
  exit /b
)
echo.
echo  [1 de 3] VPS de teste...
ssh hermes-prod "/opt/hermes-call/ops/backup-vps.sh chave-publica" | ssh hermes-staging "bash /root/vps-backup-instalar.sh"
if errorlevel 1 goto erro
echo.
echo  [2 de 3] VPS 157...
ssh hermes-prod "/opt/hermes-call/ops/backup-vps.sh chave-publica" | ssh hermes-bloqueio "bash /root/vps-backup-instalar.sh"
if errorlevel 1 goto erro
echo.
echo  [3 de 3] agendando na producao...
ssh -t hermes-prod /opt/hermes-call/ops/backup-vps.sh instalar
if errorlevel 1 goto erro
echo.
echo  PRONTO. O backup de todas as VPS roda sozinho todo dia as 04:30.
echo  Avise o agente para ele conferir o que chegou no Drive.
pause
exit /b

:erro
echo.
echo  PAROU com erro no passo acima. Nada ficou pela metade que atrapalhe:
echo  copie o que apareceu na tela e mande para o agente.
pause
