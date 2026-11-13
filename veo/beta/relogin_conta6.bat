@echo off
echo ============================================
echo  Re-login no Google Flow - Conta NOVA (conta6)
echo ============================================
echo.
echo Abrindo Chrome com perfil conta6 na porta 9300...
echo Faca login no Google NA CONTA NOVA e navegue ate:
echo   https://labs.google/fx/pt/tools/flow
echo.
echo Quando a pagina do Flow carregar COM a caixa de prompt visivel,
echo FECHE O CHROME (o bot vai reabrir ja conectado).
echo.
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" ^
  --no-first-run ^
  --disable-session-crashed-bubble ^
  --remote-debugging-port=9300 ^
  "--user-data-dir=D:\veo\beta\chrome_gen_conta6" ^
  "https://labs.google/fx/pt/tools/flow"
echo.
echo Chrome aberto. Faca login e FECHE a janela quando terminar.
pause
