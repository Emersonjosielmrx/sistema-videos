@echo off
rem 25/10 (dono): videos PROFISSIONAIS de produto (bin\produto\diario.py) - 1 por conta de produto quando a fila
rem tem menos de 3 prontos. Python do Veo (precisa da escada de contas do Veo para a cena comercial).
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
set FLOW_HEADLESS=1
call "D:\veo\beta\configurar_llm.bat" >nul 2>&1
set FLOW_ASPECT=9:16
set FLOW_MODEL=Veo 3.1 - Fast
set FLOW_DURATION=8S
cd /d D:\postador-de-videos\bin
echo [%date% %time%] inicio >> D:\postador-de-videos\logs\produto_videos.log
D:\veo\venv\Scripts\python.exe -u -m produto.diario >> D:\postador-de-videos\logs\produto_videos.log 2>&1
echo [%date% %time%] fim (exit %errorlevel%) >> D:\postador-de-videos\logs\produto_videos.log
