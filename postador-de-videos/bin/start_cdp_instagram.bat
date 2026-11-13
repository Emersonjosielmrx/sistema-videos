@echo off
REM Lanca Chrome CDP com perfil logado no Instagram (MS Energy Solar)
REM Porta 9401 = Instagram msenergypara

start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9401 --user-data-dir="D:\logins-google\chrome-profiles\msenergypara" --no-first-run --no-default-browser-check --remote-allow-origins=* --window-size=1280,900 about:blank

echo Chrome CDP Instagram iniciado na porta 9401 (msenergypara)
echo.
echo IMPORTANTE: Se for a primeira vez, faca login no Instagram manualmente:
echo   1. Abra a janela do Chrome que apareceu
echo   2. Va em instagram.com e faca login
echo   3. Depois feche este terminal e rode o poster
