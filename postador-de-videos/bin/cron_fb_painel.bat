@echo off
REM cron_fb_painel.bat - tarefa PainelFacebookViews (de hora em hora). 23/11/2026 dona: painel de views do Facebook
REM sempre atualizado. 1) mede por HTTP (services.facebook.medir, cada conta pela SAIDA FIXA dela, sem navegador)
REM 2) gera D:\video-fila\painel_web\fb_views.json (fb_painel_dados.py, so le arquivos). O botao do painel roda esta tarefa.
set PYTHONUTF8=1
set LOG=D:\postador-de-videos\logs\fb_painel.log
set PY=D:\veo\venv\Scripts\python.exe
echo [%date% %time%] === medir + painel === >> "%LOG%"
pushd D:\projeto-navegador-sem-navegador
"%PY%" -u -m services.facebook.medir >> "%LOG%" 2>&1
popd
REM 25/11: views pela API (read_insights) - cada conta pela saida dela; o painel so usa se vier de insights
"%PY%" -u "D:\postador-de-videos\bin\fb_medir_api.py" >> "%LOG%" 2>&1
"%PY%" -u "D:\postador-de-videos\bin\fb_painel_dados.py" >> "%LOG%" 2>&1
echo [%date% %time%] fim >> "%LOG%"
