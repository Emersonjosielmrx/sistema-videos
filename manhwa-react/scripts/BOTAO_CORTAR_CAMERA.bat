@echo off
chcp 65001 >nul
set PYTHONUTF8=1
cd /d D:\manhwa-react
title ManhwaReact - cortar so a camera
echo ============================================================
echo  CORTAR SO A CAMERA (tira o video/desenho de baixo, entrega 1920x1080)
echo  Arraste o(s) video(s) ou uma pasta em cima deste botao, ou cole o caminho abaixo.
echo  Saida: D:\hipercool-materiais\manhwa-react\camera
echo  (junto sai uma _area.jpg com o retangulo vermelho do corte, para conferir)
echo ============================================================
if not "%~1"=="" goto arrastado
set /p ALVO=Caminho do video ou pasta:
set ALVO=%ALVO:"=%
.venv\Scripts\python.exe manhwareact.py camera "%ALVO%"
goto fim
:arrastado
for %%F in (%*) do .venv\Scripts\python.exe manhwareact.py camera "%%~F"
:fim
echo.
echo Pronto. Abrindo a pasta da saida...
start "" "D:\hipercool-materiais\manhwa-react\camera"
pause
