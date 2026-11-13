@echo off
REM cron_anime_monitor.bat — roda o monitor de saude do recap de anime.
REM Agendado de hora em hora. Detecta problemas, auto-corrige o que e seguro
REM (re-registrar o cron), e avisa o resto no Telegram (se houver token).
setlocal
set BASE=D:\recapd-ambientes\producao
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d %BASE%
"%BASE%\venv\Scripts\python.exe" bin\anime_health_monitor.py --auto-fix >> "%BASE%\logs\anime_health_monitor.log" 2>&1
