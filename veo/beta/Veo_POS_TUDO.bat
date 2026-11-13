@echo off
REM Liga/desliga pos-producao de uma vez (todos os flags pos_producao).
REM Uso: pos_producao_TUDO.bat [on|off]

set BASE=D:\veo\beta
set PYEXE=D:\veo\venv\Scripts\python.exe

set Acao=%1
if "%Acao%"=="" set Acao=on

call :toggle_flag cron_video %Acao%
call :toggle_flag pos_video %Acao%
call :toggle_flag cron_pos_retro %Acao%
call :toggle_flag voz_whatsapp %Acao%

echo.
echo ============================================================
echo   pos_producao  TODOS os flags: %Acao%
echo ============================================================
"%PYEXE%" "%BASE%\pos_producao\flags.py" list
echo ============================================================
echo.
pause
exit /b 0

:toggle_flag
"%PYEXE%" "%BASE%\pos_producao\flags.py" %1 %2 >nul 2>&1
goto :eof