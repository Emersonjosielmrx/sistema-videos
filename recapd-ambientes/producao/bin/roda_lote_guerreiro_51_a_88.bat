@echo off
rem Inicia fila de caps do 51 ao 88 em background
echo Iniciando do 51 ao 88...
set PYTHONUTF8=1
set GEMINI_TTS_PROXY_ENABLED=1
start /B "Queue Runner RW 51-88" "D:\recapd-ambientes\producao\venv\Scripts\python.exe" bin/queue-runner.py --caps 51-88 --obra "regressed-warriors" --titulo-base "O Guerreiro Regressou" > logs/rotina_rw_51_88.log 2>&1
echo Rodando em background!
