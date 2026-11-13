@echo off
chcp 65001 >nul
set PYTHONUTF8=1
cd /d D:\manhwa-react
title Postagem automatica - LIGAR
echo ============================================================
echo  Ligando a postagem automatica da rede de canais.
echo  Agora: todo canal com video para hoje publica ja,
echo  20 min entre canais (o navegador pode abrir).
echo  Depois: segue a agenda sozinha nos proximos dias.
echo ============================================================
REM Apaga POSTAGEM_DESLIGADA.json e roda a rede com recuperar+ja: todo canal com vaga hoje e video aprovado publica
REM agora (1 canal a cada 20 min); os proximos dias seguem a agenda normal (tarefa ManhwaReact-Rede).
.venv\Scripts\python.exe manhwareact.py rede --ligar
echo.
pause
