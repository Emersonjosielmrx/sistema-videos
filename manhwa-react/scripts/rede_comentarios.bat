@echo off
REM Posta o 1o comentario do canal nos videos da rede que ja abriram (tarefa ManhwaReact-Comentarios, a cada 30 min)
set PYTHONUTF8=1
D:\manhwa-react\.venv\Scripts\python.exe D:\manhwa-react\manhwareact.py rede --comentarios >> D:\manhwa-react\logs\rede_comentarios.log 2>&1
