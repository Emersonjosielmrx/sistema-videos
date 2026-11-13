@echo off
REM Perfis com sessao TikTok ativa (2026-07-07)
REM IMPORTANTE: --remote-allow-origins=* necessario pro CDP puro funcionar
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="D:\logins-google\chrome-profiles\canalalucinaai" --no-first-run --no-default-browser-check --remote-allow-origins=*
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9271 --user-data-dir="D:\logins-google\chrome-profiles\jornalcomia" --no-first-run --no-default-browser-check --remote-allow-origins=*
