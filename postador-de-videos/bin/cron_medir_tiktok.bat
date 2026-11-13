@echo off
REM cron_medir_tiktok.bat - tarefa TikTok_MedirViews (todo dia 07:23): views de todas as contas do TikTok com @ conhecido
REM (bin\medir_tiktok.py) -> TIKTOK_VISUALIZACOES.md + resumo no Telegram. Usa o Chrome do cofre msenergypara
REM (o mesmo da postagem do MS Energy no TikTok 12:10/19:10: horario longe de proposito).
set PYTHONUTF8=1
set LOG=D:\postador-de-videos\logs\medir_tiktok.log
echo [%date% %time%] === medir tiktok === >> "%LOG%"
D:\veo\venv\Scripts\python.exe D:\postador-de-videos\bin\medir_tiktok.py >> "%LOG%" 2>&1
echo [%date% %time%] exit=%ERRORLEVEL% >> "%LOG%"
