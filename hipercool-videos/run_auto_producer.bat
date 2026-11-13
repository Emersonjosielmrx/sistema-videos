@echo off
REM run_auto_producer.bat - Lanca o produtor autonomo destacado do chat.
REM Roda em loop infinito, sobrevive ao fechamento do Claude Code.
REM Log: D:\hipercool-videos\logs\auto-producer.md
REM Para parar: feche a janela ou mate o processo python via Gerenciador de Tarefas.

cd /d D:\hipercool-videos
set PYTHONUTF8=1
set FORCE_DIRECT_TTS=1

echo [%date% %time%] Iniciando auto_producer... >> logs\auto-producer-launcher.log
D:\hipercool-videos\venv\Scripts\python.exe D:\hipercool-videos\auto_producer.py %*
echo [%date% %time%] auto_producer encerrou (codigo %ERRORLEVEL%) >> logs\auto-producer-launcher.log
