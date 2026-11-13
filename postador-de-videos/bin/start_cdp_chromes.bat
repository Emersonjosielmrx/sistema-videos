@echo off
REM Lanca 4 Chromes CDP com sessoes TikTok ativas (offscreen)
REM Perfis validados: canalalucinaai, jornalcomia, 3dfabricadeautomacoesia, inovaremanhwaverseita

start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="D:\logins-google\chrome-profiles\canalalucinaai" --no-first-run --no-default-browser-check --remote-allow-origins=* --window-size=1280,800 --window-position=-2000,0 about:blank

start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9251 --user-data-dir="D:\logins-google\chrome-profiles\3dfabricadeautomacoesia" --no-first-run --no-default-browser-check --remote-allow-origins=* --window-size=1280,800 --window-position=-2000,0 about:blank

start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9261 --user-data-dir="D:\logins-google\chrome-profiles\inovaremanhwaverseita" --no-first-run --no-default-browser-check --remote-allow-origins=* --window-size=1280,800 --window-position=-2000,0 about:blank

start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9271 --user-data-dir="D:\logins-google\chrome-profiles\jornalcomia" --no-first-run --no-default-browser-check --remote-allow-origins=* --window-size=1280,800 --window-position=-2000,0 about:blank

echo 4 Chromes CDP iniciados nas portas 9222, 9251, 9261, 9271
