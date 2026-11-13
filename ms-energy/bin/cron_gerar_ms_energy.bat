@echo off
REM cron_gerar_ms_energy.bat - tarefa "MSEnergy_Gerar" (todo dia 07:20). Dono 19/10: "o MS Energy deve continuar
REM produzindo; o conteudo dele e diferente pois e um produto real; deve gerar e postar todo dia".
REM Gera N shorts (padrao 2) e sai - no lugar do loop infinito (run_loop_ms_energy.bat), que gastava os creditos do
REM Flow sem parar. Mesmas contas/variaveis do loop; prazo de 150 min (etapa.py).
set PYTHONUTF8=1
set GEMINI_TTS_PROXY_ENABLED=1
set FLOW_HEADLESS=1
call "D:\veo\beta\configurar_llm.bat" >nul 2>&1
set FLOW_SESSION=seebotsia
set FLOW_PROJ=https://labs.google/fx/pt/tools/flow
set FLOW_ASPECT=9:16
set FLOW_MODEL=Veo 3.1 - Fast
set FLOW_DURATION=8S
set FLOW_PORT=9250
set FLOW_PROFILE=chrome_gen_seebotsia
set LOTE=%1
if "%LOTE%"=="" set LOTE=2
cd /d "D:\ms-energy"
echo [%date% %time%] === MS Energy - gerar %LOTE% === >> D:\ms-energy\logs\gerar_diario.log
D:\veo\venv\Scripts\python.exe D:\postador-de-videos\bin\etapa.py 150 D:\ms-energy\logs\gerar_diario.log -- D:\veo\venv\Scripts\python.exe -u bin\gerar_short_veo.py --tipo misto --lote %LOTE%
echo [%date% %time%] fim (exit %ERRORLEVEL%) >> D:\ms-energy\logs\gerar_diario.log
