@echo off
chcp 65001 >nul
title Hermes Call - voltar para a versao estavel
echo.
echo  HERMES CALL - VOLTAR PARA A VERSAO ESTAVEL
echo  ------------------------------------------
echo  Isto coloca no ar a ultima versao que funcionava bem (a "estavel").
echo  Os dados (contatos, conversas, ligacoes) NAO sao apagados.
echo.
set /p OK=Digite SIM e aperte Enter para voltar: 
if /I not "%OK%"=="SIM" (
  echo.
  echo  Cancelado. Nada foi alterado.
  echo.
  pause
  exit /b
)
cd /d "%~dp0.."
"C:\Program Files\Git\bin\bash.exe" ops/voltar-estavel.sh
echo.
echo  Se apareceu "Pronto", terminou.
echo  IMPORTANTE: recarregue o painel (Ctrl+F5) em TODAS as abas abertas,
echo  no computador e no celular, antes de salvar qualquer configuracao.
echo  Depois pode fechar esta janela.
pause
