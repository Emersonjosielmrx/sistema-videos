@echo off
REM cron_facebook_inteligencia.bat - tarefa FacebookInteligencia (1x/dia 08:30). 20/11/2026 dona: escada + inteligencia no Facebook.
REM 1) mede views/seguidores das Paginas (fb_medir.py, pela saida fixa da conta)  2) escada sobe/segura (fb_escada.py)
set PYTHONUTF8=1
set LOG=D:\postador-de-videos\logs\facebook_inteligencia.log
set PY=D:\hipercool-videos\venv\Scripts\python.exe
echo [%date% %time%] === medir + escada === >> "%LOG%"
REM 20/11 (FB sem navegador): mede por HTTP (services\facebook\medir.py, ~7 s, mesmo fb_views.jsonl); so se nao
REM medir nenhuma Pagina cai no fb_medir.py com Chrome. Voltar ao antigo: .bak_antes_http_20nov
pushd D:\projeto-navegador-sem-navegador
"%PY%" -u -m services.facebook.medir >> "%LOG%" 2>&1
set MEDIU=%ERRORLEVEL%
popd
if not "%MEDIU%"=="0" "%PY%" -u "D:\postador-de-videos\bin\fb_medir.py" >> "%LOG%" 2>&1
"%PY%" -u "D:\postador-de-videos\bin\fb_escada.py" >> "%LOG%" 2>&1
REM 20/11 dona: ate quantas Paginas vale a pena no mesmo perfil -> para de criar se os Reels novos cairem
"%PY%" -u "D:\postador-de-videos\bin\fb_saturacao.py" >> "%LOG%" 2>&1
echo [%date% %time%] fim >> "%LOG%"
