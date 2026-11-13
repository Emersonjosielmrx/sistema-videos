@echo off
REM ============================================================
REM  ATIVAR_CLEANUP_PC2.bat  -- RODAR NO PC2 (REVISION-PC)
REM ============================================================
REM  Ativa o fix "transferir + apaga": leva o daemon novo (com os
REM  endpoints /disk e /cleanup) pro PC2 e reinicia o daemon.
REM  Sem isso o PC2 continua rodando o daemon VELHO e o disco enche
REM  de novo (videos nunca sao apagados de la).
REM
REM  Pega o arquivo direto do share do PC1 (\\192.168.18.36\D$).
REM  NAO precisa do server 8080 (que esta fora do ar).
REM
REM  ATENCAO: isto REINICIA o daemon. Rode quando NAO houver render
REM  em andamento (senao mata o job no meio).
REM ============================================================
title Ativar Cleanup PC2
setlocal

set PC1=\\192.168.18.36\D$\recapd-ambientes\producao\bin
set BIN=C:\recapd-e-animes\bin
set PROJ=C:\recapd-e-animes

echo.
echo [1/4] Copiando daemon novo do PC1...
copy /Y "%PC1%\anime_worker_daemon.py" "%BIN%\anime_worker_daemon.py"
copy /Y "%PC1%\anime_worker_client.py" "%BIN%\anime_worker_client.py"
if errorlevel 1 (
  echo   FALHOU a copia. O PC1 esta ligado? O share \\192.168.18.36\D$ acessivel?
  pause
  goto :eof
)

echo.
echo [2/4] Parando o daemon antigo (porta 8772)...
REM acha o PID que escuta na 8772 e mata so ele
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8772" ^| findstr LISTENING') do (
  echo   matando PID %%p
  taskkill /F /PID %%p 2>nul
)

echo.
echo [3/4] Subindo o daemon novo...
cd /d %PROJ%
start "AnimeWorkerDaemon" /min "%PROJ%\venv\Scripts\python.exe" bin\anime_worker_daemon.py --port 8772
echo   aguardando o daemon subir...
timeout /t 5 >nul

echo.
echo [4/4] Testando os endpoints novos (/disk deve responder)...
powershell -Command "try { $r = Invoke-RestMethod -Uri 'http://localhost:8772/disk' -TimeoutSec 8; Write-Host ('   OK /disk -> livre_gb=' + $r.livre_gb + ' critico=' + $r.critico) } catch { Write-Host '   /disk ainda nao responde -- veja o log em workspace\anime_worker_daemon.log' }"

echo.
echo ============================================================
echo   PRONTO. Se /disk respondeu, o cleanup esta ATIVO.
echo   Daqui pra frente cada video e baixado pro PC1 e apagado do PC2.
echo ============================================================
echo.
pause
