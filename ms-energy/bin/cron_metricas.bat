@echo off
REM cron_metricas.bat - tarefa MSEnergy_Metricas (toda segunda 09:07): mede os Reels do @msenergycap (formato novo
REM x antigo, por pauta), grava docs\METRICAS_INSTAGRAM.md e manda o resumo no Telegram (resumo da rotina).
set PYTHONUTF8=1
set LOG=D:\ms-energy\logs\metricas.log
echo [%date% %time%] === metricas === >> "%LOG%"
D:\veo\venv\Scripts\python.exe D:\ms-energy\bin\metricas_insta.py >> "%LOG%" 2>&1
echo [%date% %time%] exit=%ERRORLEVEL% >> "%LOG%"
