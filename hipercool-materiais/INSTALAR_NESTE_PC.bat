@echo off
REM PC novo: copie D:\hipercool-materiais e as pastas de codigo dos projetos, depois rode este arquivo UMA vez.
REM Ele religa tudo a esta pasta e baixa o que e descartavel (Python, modelos):
REM  - atalhos (junction) assets/models/venv de cada projeto -> hipercool-materiais
REM  - HF_HOME -> models\huggingface (modelo que faltar baixa sozinho no 1o uso)
REM  - python\venv recriado do requirements.txt (precisa do Python 3.13 instalado)
set M=D:\hipercool-materiais
setx HF_HOME "%M%\models\huggingface" >nul
if not exist "%M%\python\venv\Scripts\python.exe" call "%M%\python\recriar_venv.bat"

call :liga "D:\hipercool-videos\assets" "%M%\assets"
call :liga "D:\manhwa-react\assets" "%M%\assets"
call :liga "D:\manhwa-react\models" "%M%\models\whisper"
call :liga "%M%\assets\models" "%M%\models"
call :liga "D:\.cache\huggingface" "%M%\models\huggingface"
call :liga "D:\manhwa-react\.venv" "%M%\python\venv"
call :liga "D:\veo\venv" "%M%\python\venv"
call :liga "D:\historias-em-frames\venv" "%M%\python\venv"
call :liga "D:\hipercool-videos\venv" "%M%\python\venv"
echo pronto. Whisper medium e demais modelos baixam sozinhos quando forem usados.
goto :eof

:liga
if exist "%~1" (echo ja existe: %~1 & goto :eof)
if not exist "%~dp1" goto :eof
mklink /J "%~1" "%~2" >nul && echo ligado: %~1 -^> %~2
goto :eof
