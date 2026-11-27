@echo off
REM cron_postar_fb.bat — tarefa MSEnergy_PostarFB (11:05 e 20:05). 20/11/2026 dona: "comece a postar a da MS Energy".
REM Posta 1 Reel da MS Energy na Página do Facebook (mundosolarenergia) pelo Meta Business Suite (fb_reel_bs.py),
REM só o Facebook marcado (o Instagram tem horário próprio). Chrome msenergypara abre e fecha sozinho.
set PYTHONUTF8=1
set LOG=D:\ms-energy\videos\cron_postar_fb.log
set PY=D:\veo\venv\Scripts\python.exe
echo [%date% %time%] === Cron postagem Facebook === >> "%LOG%"
"%PY%" -u "D:\postador-de-videos\bin\postar_ms_energy.py" --um --so fb >> "%LOG%" 2>&1
echo [%date% %time%] exit=%ERRORLEVEL% >> "%LOG%"
echo. >> "%LOG%"
