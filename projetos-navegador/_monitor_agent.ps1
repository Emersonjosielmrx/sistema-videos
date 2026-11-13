# ============================================================
# _monitor_agent.ps1 — Monitor/supervisor do MegaEngage
# ============================================================
# Roda a cada 12 min via Task Scheduler "MegaEngageMonitor".
# É a ÚNICA tarefa que cuida do bot (não deve haver outra tarefa relançando,
# senão sobem instâncias duplicadas).
#
# O QUE FAZ, em ordem:
#   1. Vê se o bot (mega_engage.py) está vivo.
#   2. Vê se o painel (engage_server.py) está vivo.
#   3. Se houver DUPLICATAS, mata as extras (mantém 1 de cada).
#   4. Lê o fim do log e detecta problemas (fila vazia, dead_accounts, cota).
#   5. Se o bot está MORTO -> relança.
#   6. Se a fila está vazia por dead_accounts.txt (falso ban por proxy) -> limpa.
#   7. Se o server está morto -> relança.
#   8. Registra 1 linha em _monitor_agente.log.
#
# COMO MEXER (coisas pequenas e seguras):
#   - Mudar a frequência: alterar o RepetitionInterval na tarefa (_criar_tarefa.ps1).
#   - Não relançar por um tempo: Disable-ScheduledTask -TaskName 'MegaEngageMonitor'.
#   - Ver histórico: abrir _monitor_agente.log.
# ============================================================

$ErrorActionPreference = "SilentlyContinue"

# ---- Caminhos (não mudar sem ajustar o resto do projeto) ----
$BOT_DIR     = "D:\projetos-navegador"
$PYTHON      = "D:\hipercool-videos\venv\Scripts\python.exe"
$LOG         = "$BOT_DIR\mega_engage_log.txt"
$DEAD        = "$BOT_DIR\dead_accounts.txt"
$LOCK        = "$BOT_DIR\engage_bot.lock"
$MONITOR_LOG = "$BOT_DIR\_monitor_agente.log"

$ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$action = "OK"

# ------------------------------------------------------------
# 1. Bot vivo? (conta processos python rodando mega_engage.py)
# ------------------------------------------------------------
$botProcs = Get-WmiObject Win32_Process -Filter "Name='python.exe'" |
    Where-Object { $_.CommandLine -like "*mega_engage.py*" -and $_.CommandLine -notlike "* -c *" }
$botAlive = ($botProcs -ne $null -and @($botProcs).Count -gt 0)

# ------------------------------------------------------------
# 2. Server (painel) vivo?
# ------------------------------------------------------------
$serverProcs = Get-WmiObject Win32_Process -Filter "Name='python.exe'" |
    Where-Object { $_.CommandLine -like "*engage_server.py*" }
$serverAlive = ($serverProcs -ne $null -and @($serverProcs).Count -gt 0)

# ------------------------------------------------------------
# 3. Matar duplicatas (mantém só a de maior PID = mais nova)
# ------------------------------------------------------------
if ($botAlive -and @($botProcs).Count -gt 1) {
    $sorted = @($botProcs) | Sort-Object -Property ProcessId -Descending
    foreach ($p in $sorted[1..($sorted.Count-1)]) { Stop-Process -Id $p.ProcessId -Force 2>$null }
    $action = "DEDUP_BOT"
}
if ($serverAlive -and @($serverProcs).Count -gt 1) {
    $sorted = @($serverProcs) | Sort-Object -Property ProcessId -Descending
    foreach ($p in $sorted[1..($sorted.Count-1)]) { Stop-Process -Id $p.ProcessId -Force 2>$null }
    $action += "+DEDUP_SERVER"
}

# ------------------------------------------------------------
# 4. Ler fim do log e detectar sintomas
# ------------------------------------------------------------
$logLines = @()
if (Test-Path $LOG) { $logLines = @(Get-Content $LOG -Tail 25) }

$hasEmptyQueue = ($logLines | Where-Object { $_ -match '0 tarefas \| 0 contas' }).Count -gt 0
$hasQuotaGone  = ($logLines | Where-Object { $_ -match 'COTA WEBSHARE ESGOTADA' }).Count -gt 0
$okCount  = ($logLines | Where-Object { $_ -match 'OK \[' }).Count
$errCount = ($logLines | Where-Object { $_ -match 'ERRO ' }).Count

# dead_accounts.txt tem quantas linhas?
$deadCount = 0
if (Test-Path $DEAD) { $deadCount = @(Get-Content $DEAD).Count }

# ------------------------------------------------------------
# 5/6. Decidir ações (SÓ relança se bot morto)
# ------------------------------------------------------------
$needsRestart   = $false
$needsDeadClean = $false

if (-not $botAlive) {
    $action = "RESTART_BOT_DOWN"
    $needsRestart = $true
}
elseif ($hasEmptyQueue -and $deadCount -gt 0) {
    # Fila vazia + dead_accounts cheio = falso ban por proxy. Limpar reabilita.
    $action = "CLEAN_DEAD_ACCOUNTS"
    $needsDeadClean = $true
}

if ($needsDeadClean -and (Test-Path $DEAD)) { Remove-Item $DEAD -Force }

if ($needsRestart) {
    # Limpa Chrome órfão antes de relançar (evita acúmulo -> OOM)
    taskkill /F /IM chrome.exe /T 2>$null
    Start-Sleep -Seconds 3
    # Lock órfão só é removido quando NÃO há bot vivo (aqui é o caso).
    if (Test-Path $LOCK) { Remove-Item $LOCK -Force }

    $env:PYTHONUTF8 = "1"
    Start-Process -FilePath $PYTHON -ArgumentList "mega_engage.py" `
        -WorkingDirectory $BOT_DIR -WindowStyle Hidden | Out-Null
    Start-Sleep -Seconds 10

    $verify = Get-WmiObject Win32_Process -Filter "Name='python.exe'" |
        Where-Object { $_.CommandLine -like "*mega_engage.py*" -and $_.CommandLine -notlike "* -c *" }
    if ($verify -ne $null -and @($verify).Count -gt 0) { $action += "_CONFIRMED" }
    else { $action += "_FAILED" }
}

# ------------------------------------------------------------
# 7. Server morto -> relança
# ------------------------------------------------------------
if (-not $serverAlive) {
    $env:PYTHONUTF8 = "1"
    Start-Process -FilePath $PYTHON -ArgumentList "engage_server.py" `
        -WorkingDirectory $BOT_DIR -WindowStyle Hidden | Out-Null
    $action += "+SERVER_STARTED"
}

# Se a cota do Webshare acabou, registra bem visível (reiniciar não resolve).
if ($hasQuotaGone) { $action += "+QUOTA_WEBSHARE_ESGOTADA" }

# ------------------------------------------------------------
# 8. Registrar 1 linha
# ------------------------------------------------------------
$chromeNow = @(Get-WmiObject Win32_Process -Filter "Name='chrome.exe'").Count
$logEntry = "$ts | alive=$botAlive server=$serverAlive dead=$deadCount ok=$okCount err=$errCount chrome=$chromeNow | $action"
Add-Content -Path $MONITOR_LOG -Value $logEntry -Encoding UTF8
Write-Output $logEntry
