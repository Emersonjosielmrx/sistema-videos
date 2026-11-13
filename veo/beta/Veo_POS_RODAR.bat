@echo off
REM Roda uma passada do pipeline agora (independente do cron).
REM Uso: Veo_POS_RODAR.bat [incremental|retroativo] [limite]

set BASE=D:\veo\beta
set PYEXE=D:\veo\venv\Scripts\python.exe

set Modo=%1
if "%Modo%"=="" set Modo=incremental
set Limite=%2
if "%Limite%"=="" set Limite=5

if "%Modo%"=="retroativo" (
    "%PYEXE%" "%BASE%\cron_pos_producao.py" --retro --limite %Limite%
) else (
    "%PYEXE%" "%BASE%\cron_pos_producao.py" --incremental --limite %Limite%
)
echo.
pause