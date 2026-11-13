@echo off
rem Inicia fila de caps do 26 ao 50 em background 
echo Iniciando do 26 ao 50...
set PYTHONUTF8=1
set GEMINI_TTS_PROXY_ENABLED=1
start /B "Queue Runner RW" "D:\recapd-ambientes\producao\venv\Scripts\python.exe" bin/queue-runner.py --caps 26-50 --obra "regressed-warriors" --titulo-base "O Guerreiro Regressou" > logs/rotina_rw_26_50.log 2>&1
echo Rodando em background!
