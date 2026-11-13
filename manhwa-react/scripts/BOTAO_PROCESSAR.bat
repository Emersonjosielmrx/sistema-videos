@echo off
chcp 65001 >nul
set PYTHONUTF8=1
cd /d D:\manhwa-react
title ManhwaReact - processando videos de 1-COLOQUE-AQUI
echo ============================================================
echo  ManhwaReact - processando tudo que estiver em:
echo    D:\manhwa-react\1-COLOQUE-AQUI
echo  Os videos prontos vao para:
echo    D:\hipercool-materiais\manhwa-react\shorts  (e cortes\ / grandes\ para reacts grandes)
echo ============================================================
.venv\Scripts\python.exe manhwareact.py batch
echo.
echo Pronto. Abrindo a pasta dos videos prontos...
start "" "D:\hipercool-materiais\manhwa-react"
pause
