@echo off
REM cron_postar_tiktok.bat - tarefa "MSEnergy_PostarTikTok" (12:10 e 19:10). Dono 19/10: o MS Energy posta todo dia
REM tambem no TikTok @energia.solar.da (conta msenergypara do cofre, internet de casa). 1 video por vez: primeiro os
REM novos (shorts_veo), depois os 49 antigos que so sairam no Instagram.
set PYTHONUTF8=1
set LOG=D:\ms-energy\videos\cron_postar_tiktok.log
echo [%date% %time%] === Cron postagem TikTok === >> "%LOG%"
D:\veo\venv\Scripts\python.exe D:\postador-de-videos\bin\etapa.py 20 "%LOG%" -- D:\veo\venv\Scripts\python.exe D:\postador-de-videos\bin\postar_ms_energy.py --um --so tiktok
echo [%date% %time%] exit=%ERRORLEVEL% >> "%LOG%"
