@echo off
chcp 65001 >nul
set PYTHONUTF8=1
cd /d D:\manhwa-react
title Postagem automatica - DESLIGAR
REM Cria D:\postador-de-videos\config\POSTAGEM_DESLIGADA.json: a rede (de hora em hora), os comentarios, o ciclo
REM das 06:40 e o agendador VO3 param de postar e de abrir navegador. Os videos continuam na fila.
.venv\Scripts\python.exe manhwareact.py rede --desligar
echo.
echo  Para voltar: botao "5 - POSTAGEM AUTOMATICA - LIGAR"
echo  (ele faz as pendentes de hoje e volta a agenda).
echo.
pause
