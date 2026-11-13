@echo off
rem Desfaz o INSTALAR.bat: volta os settings.json dos backups .bak-argon.
setlocal
set VS=%APPDATA%\Code\User\settings.json
if defined CLAUDE_CONFIG_DIR (set CC=%CLAUDE_CONFIG_DIR%\settings.json) else (set CC=%USERPROFILE%\.claude\settings.json)
if exist "%VS%.bak-argon" (copy /Y "%VS%.bak-argon" "%VS%" >nul & echo VS Code restaurado.) else (echo Sem backup do VS Code.)
if exist "%CC%.bak-argon" (copy /Y "%CC%.bak-argon" "%CC%" >nul & echo Claude Code restaurado.) else (echo Sem backup do Claude Code.)
echo Feche e abra o VS Code.
pause
