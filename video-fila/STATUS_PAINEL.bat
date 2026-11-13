@echo off
rem Painel dos projetos de video (22/10/2026): gera e abre painel_web\status.html.
rem So LEITURA: nao posta, nao renderiza, nao mexe em nada.
set PYTHONUTF8=1
"D:\hipercool-videos\venv\Scripts\python.exe" "D:\video-fila\status_videos.py" html
start "" "D:\video-fila\painel_web\status.html"
