@echo off
REM ============================================================
REM  VEO — DESLIGAR TUDO
REM  Para o supervisor E os 3 ambientes (loops, cron, gera_auto).
REM  Cria PAUSE_SYSTEM em cada ambiente pra nada reabrir Chrome.
REM  Tambem mata _producao_10h.bat (CMD /k) que NAO casa nos padroes
REM  anteriores e sobrevivia como orfao.
REM ============================================================
title VEO-DESLIGAR-tudo
set PYTHONUTF8=1
cd /d "%~dp0"

echo Parando supervisor e todos os ambientes...
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'supervisor\.py' -or $_.CommandLine -match 'run_cron_loop_3contas' -or $_.CommandLine -match 'cron_gerar_video_llm' -or $_.CommandLine -match 'gera_auto' -or $_.CommandLine -match '_producao_10h\.bat' -or $_.CommandLine -match 'Veo_PAINEL' } | ForEach-Object { taskkill /PID $_.ProcessId /T /F 2>&1 | Out-Null }"

REM mata QUALQUER cmd /k filho de nossos bats (caso _producao_10h tenha sido renomeado)
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match '\\veo\\(prod|beta|experimental)\\.*\.bat' } | ForEach-Object { taskkill /PID $_.ProcessId /T /F 2>&1 | Out-Null }"

REM mata todos os chromes do escopo veo (deixa intacto o que NAO casa D:\veo\)
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'D:\\veo\\' -or $_.CommandLine -match '\\veo\\.lock|\\veo\\(prod|beta|experimental)\\perfis' } | ForEach-Object { taskkill /PID $_.ProcessId /T /F 2>&1 | Out-Null }"

REM marca pausa em cada ambiente
for %%A in (prod beta experimental) do (
  if exist "%~dp0%%A\logs" (
    echo {"until":null,"motivo":"desligar_manual"} > "%~dp0%%A\logs\PAUSE_SYSTEM"
  )
)
echo.
echo Tudo parado. Feche esta janela.
timeout /t 5 /nobreak >nul
