# Instala/religa a fabrica de tokens (fabrica_tokens.py) nesta maquina: tarefa FabricaTokens na sessao da tela, oculta.
$py = "C:\postador-worker\nsn\venv\Scripts\pythonw.exe"
$sc = "C:\postador-worker\nsn\services\veo_flow\fabrica_tokens.py"
schtasks /create /tn FabricaTokens /tr "$py $sc" /sc once /st 00:00 /it /f 2>$null | Out-Null
# reinicia sempre (codigo novo); a fabrica nova fecha os Chromes orfaos das portas 9480-9489
Get-CimInstance Win32_Process -Filter "Name like 'python%'" | Where-Object { $_.CommandLine -like '*fabrica_tokens*' } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Start-Sleep 2
schtasks /run /tn FabricaTokens | Out-Null
foreach ($i in 1..30) { Start-Sleep 2; try { Invoke-WebRequest -UseBasicParsing http://127.0.0.1:9399/estado -TimeoutSec 2 | Out-Null; break } catch {} }
try { (Invoke-WebRequest -UseBasicParsing http://127.0.0.1:9399/estado -TimeoutSec 5).Content } catch {
    "FORA: $_"
    # mostra o erro de quem nao subiu (roda 8 s com o python de console, saida em arquivo)
    $err = "C:\postador-worker\fabrica_erro.txt"
    $p = Start-Process "C:\postador-worker\nsn\venv\Scripts\python.exe" -ArgumentList $sc -RedirectStandardError $err -WindowStyle Hidden -PassThru
    Start-Sleep 8
    if (-not $p.HasExited) { "SUBIU NO TESTE (o problema e a tarefa)"; Stop-Process $p.Id -Force }
    Get-Content $err -Tail 15
}
if (Test-Path C:\postador-worker\fabrica_tokens.log) { Get-Content C:\postador-worker\fabrica_tokens.log -Tail 5 }
