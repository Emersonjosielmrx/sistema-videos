# D:\sistema\catalogo\janela_madrugada.ps1 - OBRA: 2a janela (03:10) para as pastas que ficaram presas de dia por
# Chrome do cofre, pontes e Python principal em uso. Fecha o Chrome do cofre pelo jeito normal (grava cookies) antes.
# Nao mexe em postagem em andamento. Religa tudo no maximo as 04:30. Log: D:\sistema\mapa\mudanca.log
$ErrorActionPreference = 'SilentlyContinue'
$PY = 'C:\Users\Haylla\AppData\Local\Programs\Python\Python313\python.exe'
$LOG = 'D:\sistema\mapa\mudanca.log'
function L($m){ Add-Content -Encoding UTF8 $LOG ((Get-Date -f 'dd/MM HH:mm:ss') + ' ' + $m) }
L '===== JANELA MADRUGADA: inicio'
# Chrome do cofre: fechamento normal (CloseMainWindow) para gravar cookies; so depois de 20 s, forca o que sobrar
Get-CimInstance Win32_Process -Filter "Name='chrome.exe'" | ?{ $_.CommandLine -match 'logins-google' -and $_.CommandLine -notmatch '--type=' } | %{ (Get-Process -Id $_.ProcessId).CloseMainWindow() | Out-Null }
Start-Sleep 20
L ('Chrome do cofre fechado normalmente; restantes: ' + @(Get-CimInstance Win32_Process -Filter "Name='chrome.exe'" | ?{ $_.CommandLine -match 'logins-google' }).Count)
# reaproveita a janela de dia com limite 04:30
& powershell -NoProfile -ExecutionPolicy Bypass -File D:\sistema\catalogo\janela_mudanca.ps1
L '===== JANELA MADRUGADA: fim'
