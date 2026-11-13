@echo off
REM Tarefa ManhwaReact-Rede (de hora em hora, minuto 17): sobe so os videos que publicam nas proximas 3 h
REM (cada upload sai 1-3 h antes de abrir, espalhado no dia - sem rajada). Comentarios do canal na mesma rodada.
set PYTHONUTF8=1
REM Antes da rede: Veo novo do gerador (D:\veo\beta\videos\cron_shorts) vira limpo e passa pelos detectores (16/10:
REM sem isso o Veo religado nunca chegava na rede). So os que ainda nao tem json nos limpos; no maximo 3 por rodada.
D:\manhwa-react\.venv\Scripts\python.exe D:\postador-de-videos\bin\limpar_veo.py --max 3 >> D:\manhwa-react\logs\rede_%date:~6,4%%date:~3,2%%date:~0,2%.log 2>&1
D:\manhwa-react\.venv\Scripts\python.exe D:\manhwa-react\manhwareact.py rede >> D:\manhwa-react\logs\rede_%date:~6,4%%date:~3,2%%date:~0,2%.log 2>&1
REM Depois da rede (mesmo Chrome, sem disputa): acabamento no Studio - Short de react ganha o "video relacionado" (o
REM completo do canal). No maximo 2 por rodada; log em D:\postador-de-videos\logs\extras_rede.log (dono aprovou 16/10).
D:\manhwa-react\.venv\Scripts\python.exe D:\postador-de-videos\bin\extras_rede.py --max 2 >> D:\manhwa-react\logs\rede_%date:~6,4%%date:~3,2%%date:~0,2%.log 2>&1
REM Metricas do Studio pelo navegador (Onda 3.1, 16/10): "continuaram assistindo" dos Shorts e CTR dos completos viram
REM nota do gancho/titulo no aprendizado da rede. 3 videos por rodada; log em D:\postador-de-videos\logs\metricas_rede.log
D:\manhwa-react\.venv\Scripts\python.exe D:\postador-de-videos\bin\metricas_rede.py --max 3 --por-canal 3 >> D:\manhwa-react\logs\rede_%date:~6,4%%date:~3,2%%date:~0,2%.log 2>&1
