@echo off
REM Rodada extra do TikTok (tarefa "TikTokRodadaExtra", 14:05 e 19:35). Dono 19/10: todas as contas ate 3/dia; com 50
REM contas (~150 posts, ~4 min cada) a etapa de 135 min do PostadorDeVideos (06:40, TikTok acaba ate ~12:50) nao da.
REM Prazo 240 min: a das 14:05 acaba antes da das 19:35, e a das 19:35 antes do ciclo do dia seguinte (sem trava entre
REM rodadas: duas ao mesmo tempo gravariam o tiktok_auto_posted.json uma por cima da outra).
set PYTHONUTF8=1
if exist D:\postador-de-videos\config\POSTAGEM_DESLIGADA.json exit /b 0
D:\veo\venv\Scripts\python.exe D:\postador-de-videos\bin\etapa.py 240 D:\postador-de-videos\logs\tiktok_%date:~6,4%%date:~3,2%%date:~0,2%.log -- D:\veo\venv\Scripts\python.exe D:\postador-de-videos\bin\postar_tiktok_auto.py --ate-min 225
REM 23/10 (dono): Instagram tambem tem 2a/3a chance aqui, DEPOIS do TikTok (nunca os dois Chromes juntos). So posta o
REM que faltou no dia (max_por_conta_dia): em 21/10 a rodada da manha quebrou e o Instagram ficou o dia inteiro parado.
REM 01/11: 90 -> 150 min (a rodada das 19:51 de 31/10 foi cortada aos 89 min no inovareclone e 10 contas ficaram sem post)
D:\veo\venv\Scripts\python.exe D:\postador-de-videos\bin\etapa.py 150 D:\postador-de-videos\logs\instagram_%date:~6,4%%date:~3,2%%date:~0,2%.log -- D:\veo\venv\Scripts\python.exe D:\postador-de-videos\bin\postar_insta_auto.py
