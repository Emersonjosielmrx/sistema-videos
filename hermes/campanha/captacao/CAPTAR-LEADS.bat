@echo off
chcp 65001 >nul
title Captacao Hermes - preparar lista de leads
cd /d "%~dp0"

rem Aceita o arquivo arrastado para cima deste .bat, ou pergunta.
set "ARQ=%~1"
if "%ARQ%"=="" (
  echo Arraste o seu arquivo de leads .csv para cima deste atalho,
  echo ou cole o caminho completo abaixo.
  echo.
  set /p "ARQ=Arquivo de leads: "
)
if not exist "%ARQ%" (
  echo.
  echo  Nao achei o arquivo: %ARQ%
  pause
  exit /b 1
)

echo.
echo  Segmento-alvo (ex.: imobiliaria, clinica, ecommerce) — ENTER para pular:
set /p "SEG=Segmento: "

set "EXTRA="
if not "%SEG%"=="" set "EXTRA=--segmento %SEG%"

echo.
echo  Processando...
python processar_leads.py "%ARQ%" %EXTRA% --saida saida
if errorlevel 1 (
  echo.
  echo  Deu erro acima. Confira se o arquivo tem uma coluna de telefone.
  pause
  exit /b 1
)

echo.
echo  Pronto. A lista para o Hermes esta em:  %~dp0saida\pronto-hermes.csv
echo  A lista completa para o CRM esta em:    %~dp0saida\leads-completo.csv
echo.
pause
