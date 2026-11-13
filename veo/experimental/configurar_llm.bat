@echo off
REM Configura variaveis de ambiente para usar Gemini Flash Lite como LLM barata.
REM
REM Como usar:
REM   1. Pegue uma chave em: https://aistudio.google.com/apikey (gratis)
REM   2. Edite este arquivo e cole sua chave em GOOGLE_API_KEY=...
REM   3. Rode este .bat antes de executar o cron

set PYTHONUTF8=1
set LLM_MODEL=gemini-flash-lite-latest
set LLM_TIMEOUT=30

REM >>> EDITE AQUI - cole sua chave do Google AI Studio <<<
REM Se vazio, o bot carrega chaves de ..\secrets\gemini_keys.json (D:\veo\secrets)
REM e rotaciona entre elas automaticamente quando uma da rate limit.
set GOOGLE_API_KEY=
REM <<<

REM Fallback automatico: se a chave estiver vazia, o bot usa lista estatica.
REM Para desligar a LLM completamente: set LLM_DISABLED=1

echo Configuracao LLM:
echo   LLM_MODEL     = %LLM_MODEL%
echo   LLM_TIMEOUT   = %LLM_TIMEOUT%
echo   GOOGLE_API_KEY = %GOOGLE_API_KEY:~0,8%*** (tamanho %GOOGLE_API_KEY:~0,0% chars)

if "%GOOGLE_API_KEY%"=="" (
    echo AVISO: GOOGLE_API_KEY vazia. Bot vai usar lista estatica.
) else if "%GOOGLE_API_KEY%"=="AIzaSyColeSuaChaveAqui" (
    echo AVISO: Voce esqueceu de editar a chave. Bot vai usar lista estatica.
) else (
    echo LLM ATIVA - vai gerar falas e cenarios com Gemini Flash Lite
)