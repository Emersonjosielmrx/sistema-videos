@echo off
set PYTHONUTF8=1
set PYTHONUNBUFFERED=1
set GEMINI_TTS_PROXY_ENABLED=1
D:\recapd-ambientes\producao\venv\Scripts\python.exe D:\hipercool-inferior\bin\hiper-pipeline.py --panels-dir D:\hipercool-inferior\workspace\panels\the-meek-cat-cap01 --titulo "The Meek Cat - Capitulo 1" --max-panels 120 --subtitles --karaoke --skip-notify --output-suffix _NORMAL > D:\hipercool-inferior\cap01_full.log 2>&1
