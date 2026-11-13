@echo off
REM cron_anime_noturno.bat — liga o SUPERVISOR dos 3 ambientes SO de madrugada.
REM Janela permitida: 00:00 as 06:00 (quando ninguem esta usando o PC).
REM Agende no Agendador de Tarefas pra rodar de hora em hora; este script
REM checa a hora e so liga o supervisor dentro da janela. O supervisor aplica
REM a regra permanente (PROD nunca para; sob pressao mata TESTE, depois BETA)
REM e escolhe sozinho o trabalho via anime_night_shift.py.

setlocal
set H=%time:~0,2%
set H=%H: =0%
set BASE=D:\recapd-ambientes\producao

if %H% GEQ 6 goto :skip

echo [%date% %time%] JANELA DE MADRUGADA (%H%h) - ligando supervisor >> "%BASE%\logs\cron_anime_noturno.log"
cd /d %BASE%
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
REM --once: 1 ciclo por disparo do agendador (evita 2 loops sobrepostos).
"%BASE%\venv\Scripts\python.exe" bin\ambientes_supervisor.py --loop --once >> "%BASE%\logs\cron_anime_noturno.log" 2>&1
echo [%date% %time%] ciclo do supervisor encerrou (codigo %ERRORLEVEL%) >> "%BASE%\logs\cron_anime_noturno.log"
goto :eof

:skip
echo [%date% %time%] FORA DA JANELA (%H%h) - nao roda >> "%BASE%\logs\cron_anime_noturno.log"
