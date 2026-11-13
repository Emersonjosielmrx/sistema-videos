@echo off
chcp 65001 >nul
set PYTHONUTF8=1
cd /d D:\manhwa-react
title ManhwaReact - vigiando inbox
.venv\Scripts\python.exe manhwareact.py watch %*
