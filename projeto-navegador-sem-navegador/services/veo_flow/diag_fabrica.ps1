# Diagnostico da fabrica de tokens nesta maquina (Chromes dos perfis quentes, portas 9480+).
Get-CimInstance Win32_Process -Filter "Name='chrome.exe'" | Where-Object { $_.CommandLine -like '*remote-debugging-port=948*' -and $_.CommandLine -notlike '*--type=*' } |
    ForEach-Object { "$($_.ProcessId) " + ($_.CommandLine -replace '.*user-data-dir=([^ ]+).*remote-debugging-port=(\d+).*', '$1 porta $2') }
"--- todos os Chromes principais (perfil):"
Get-CimInstance Win32_Process -Filter "Name='chrome.exe'" | Where-Object { $_.CommandLine -notlike '*--type=*' } |
    ForEach-Object { "$($_.ProcessId) " + ($_.CommandLine -replace '.*user-data-dir=("?[^" ]+).*', '$1') }
netstat -ano -p TCP | Select-String ":948[0-9] .*LISTENING"
Get-CimInstance Win32_Process -Filter "Name like 'python%'" | Where-Object { $_.CommandLine -like '*fabrica_tokens*' } | ForEach-Object { "fabrica pid $($_.ProcessId) sessao $($_.SessionId)" }
Get-Content C:\postador-worker\fabrica_tokens.log -Tail 8
try { (Invoke-WebRequest -UseBasicParsing http://127.0.0.1:9399/estado -TimeoutSec 5).Content } catch { "FORA" }
