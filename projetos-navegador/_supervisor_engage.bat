@echo off
REM Supervisor do MEGA ENGAGE — relanca o bot se ele nao estiver rodando.
REM Chamado pela Tarefa Agendada "MegaEngageBot" (logon + a cada 15min).
REM O lock file (engage_bot.lock) impede 2 instancias, entao e seguro chamar sempre.

set PYEXE=D:\hipercool-videos\venv\Scripts\python.exe
set BOTDIR=D:\projetos-navegador

REM Ja esta rodando? Se sim, sai.
wmic process where "name='python.exe'" get commandline 2>nul | findstr /I "mega_engage.py" >nul
if %ERRORLEVEL%==0 (
    echo [%DATE% %TIME%] Bot ja rodando. >> "%BOTDIR%\_supervisor.log"
    goto :server
)

echo [%DATE% %TIME%] Bot parado. Relancando... >> "%BOTDIR%\_supervisor.log"
cd /d "%BOTDIR%"
set PYTHONUTF8=1
start "" /b "%PYEXE%" mega_engage.py

:server
REM Garante que o painel (porta 8850) tambem esteja no ar.
wmic process where "name='python.exe'" get commandline 2>nul | findstr /I "engage_server.py" >nul
if %ERRORLEVEL%==0 goto :eof
cd /d "%BOTDIR%"
set PYTHONUTF8=1
start "" /b "%PYEXE%" engage_server.py
