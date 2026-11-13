@echo off
REM cron_postar_insta.bat — chamado pelo Agendador (tarefa MSEnergy_PostarInsta, 10:17 e 19:37).
REM Renova o token do Instagram se passou 1 semana (sem isso ele vence em 60 dias e a postagem para) e
REM posta 1 video pendente no Instagram (Feed + Stories).
set PYTHONUTF8=1
set LOG=D:\ms-energy\videos\cron_postar_insta.log
set PY=D:\hipercool-videos\venv\Scripts\python.exe
set SCRIPT=D:\postador-de-videos\bin\postar_ms_energy.py

echo [%date% %time%] === Cron postagem Instagram === >> "%LOG%"

"%PY%" "D:\postador-de-videos\bin\renovar_token_insta.py" msenergycap >> "%LOG%" 2>&1
"%PY%" "%SCRIPT%" --um --so insta >> "%LOG%" 2>&1

echo [%date% %time%] exit=%ERRORLEVEL% >> "%LOG%"
echo. >> "%LOG%"
