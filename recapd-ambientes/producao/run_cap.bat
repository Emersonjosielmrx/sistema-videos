@echo off
REM ============================================================
REM  run_cap.bat — 1 comando pra renderizar um capitulo certo.
REM  Liga TODOS os efeitos via --preset (nao precisa setar env a mao).
REM
REM  Uso:
REM    run_cap.bat ^<pasta-paineis^> "^<titulo^>" [teste^|final]
REM
REM  Exemplos:
REM    run_cap.bat the-warrior-disappointed-cap11 "The Warrior - Cap 11" teste
REM    run_cap.bat the-meek-cat-cap06 "The Meek Cat - Capitulo 6" final
REM
REM  teste = 720p rapido (edge TTS gratis, do cache).
REM  final = 1080p (use TTS_ENGINE=gemini antes se quiser voz premium).
REM ============================================================
setlocal
set PYTHONUTF8=1
set GEMINI_TTS_PROXY_ENABLED=1
set PY=D:\recapd-ambientes\producao\venv\Scripts\python.exe
set PANELS=%~1
set TITULO=%~2
set PRESET=%~3
if "%PANELS%"=="" echo Falta a pasta de paineis. Ex: run_cap.bat the-meek-cat-cap06 "The Meek Cat - Cap 6" teste & exit /b 1
if "%TITULO%"=="" echo Falta o titulo (entre aspas). & exit /b 1
if "%PRESET%"=="" set PRESET=teste

echo [run_cap] %PANELS% ^| "%TITULO%" ^| preset=%PRESET%
"%PY%" D:\hipercool-inferior-fix\bin\hiper-pipeline.py ^
  --panels-dir D:\hipercool-inferior-fix\workspace\panels\%PANELS% ^
  --titulo "%TITULO%" ^
  --max-panels 120 --subtitles --karaoke --censura --skip-notify ^
  --preset %PRESET% --output-suffix _%PRESET%
endlocal
