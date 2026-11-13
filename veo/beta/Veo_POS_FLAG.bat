@echo off
REM Liga/desliga um flag especifico do pos_producao.
REM Uso: Veo_POS_FLAG.bat <nome_flag> [on|off]
REM      Veo_POS_FLAG.bat list     (mostra todos)

set BASE=D:\veo\beta
set PYEXE=D:\veo\venv\Scripts\python.exe

if "%1"=="" goto :uso
if "%1"=="list" goto :listar
if "%2"=="" goto :toggle
goto :set

:listar
"%PYEXE%" "%BASE%\pos_producao\flags.py" list
echo.
pause
exit /b 0

:toggle
"%PYEXE%" "%BASE%\pos_producao\flags.py" toggle %1
"%PYEXE%" "%BASE%\pos_producao\flags.py" list
echo.
pause
exit /b 0

:set
"%PYEXE%" "%BASE%\pos_producao\flags.py" %2 %1
"%PYEXE%" "%BASE%\pos_producao\flags.py" list
echo.
pause
exit /b 0

:uso
echo Uso:
echo   Veo_POS_FLAG.bat list                  mostra todos os flags
echo   Veo_POS_FLAG.bat ^<nome^>               alterna esse flag
echo   Veo_POS_FLAG.bat ^<nome^> on/off        seta o estado
echo.
echo Flags conhecidos:
echo   cron_video      - gera novos videos Veo
echo   pos_video       - pos-producao incremental
echo   cron_pos_retro  - retroativo (processa backlog em videos/)
echo   voz_whatsapp    - injeta voz PT-BR no audio
pause
exit /b 0