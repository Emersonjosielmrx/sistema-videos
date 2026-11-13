# limpeza_chrome.ps1 — fecha Chromes de AUTOMAÇÃO esquecidos e ffmpeg parado (dona 02/11: "muita coisa que abre não
# fecha; pode fechar e limpar e deixar automação pra fechar e limpar").
# Fecha SÓ Chrome com --remote-debugging-port (automação: cofre, Flow, TikTok, postadores) aberto há mais de
# -Horas e cuja porta nenhum python/pythonw/node em execução cita na linha de comando. Fecha pelo CDP (Browser.close
# grava os cookies); se não sair em 10 s, taskkill na árvore dele. Chrome sem porta (o pessoal da dona) NUNCA.
# ffmpeg com mais de -HorasFfmpeg e que não gastou CPU em 30 s = parado -> fecha. Nunca toca em python/pythonw.
#   powershell -File limpeza_chrome.ps1 [-Horas 3] [-HorasFfmpeg 6] [-Simular]
param([double]$Horas = 3, [double]$HorasFfmpeg = 6, [double]$MinTravado = 15, [switch]$Simular)
$log = Join-Path $PSScriptRoot "logs\limpeza_chrome.log"
New-Item -ItemType Directory -Force (Split-Path $log) | Out-Null
function L($m) { $l = "{0:yyyy-MM-dd HH:mm:ss} {1} {2}" -f (Get-Date), $env:COMPUTERNAME, $m; Add-Content -Path $log -Value $l -Encoding UTF8; $l }

$procs = Get-CimInstance Win32_Process
$usos = ($procs | Where-Object { $_.Name -match '^(python|pythonw|node|pwsh|powershell)\.exe$' } | ForEach-Object { $_.CommandLine }) -join ' '
$livreAntes = [math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1MB, 1)
$fechados = 0
# 03/11 (dona: "no PC2 fica um cemitério de Chromes, dezenas abertos"): lá havia 15 Chromes de 31/10-01/11 na MESMA
# porta 9470. Só 1 escuta a porta (o dono); os outros são restos que nenhum script alcança, mas eram poupados porque
# um script vivo cita a 9470. Resto = fecha direto pelo PID (o CDP da porta fecharia o dono, não ele).
$gerentes = @($procs | Where-Object { $_.Name -match '^(python|pythonw|node)\.exe$' } | ForEach-Object { $_.ProcessId })
$donoDaPorta = @{}
Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | ForEach-Object { $donoDaPorta["$($_.LocalPort)"] = $_.OwningProcess }
function Fechar-Chrome($c, $porta, $motivo) {
    try {
        $ws = (Invoke-RestMethod "http://127.0.0.1:$porta/json/version" -TimeoutSec 5).webSocketDebuggerUrl
        $cli = New-Object System.Net.WebSockets.ClientWebSocket
        $cli.ConnectAsync([Uri]$ws, [Threading.CancellationToken]::None).Wait(5000) | Out-Null
        $msg = [Text.Encoding]::UTF8.GetBytes('{"id":1,"method":"Browser.close"}')
        $cli.SendAsync([ArraySegment[byte]]$msg, 'Text', $true, [Threading.CancellationToken]::None).Wait(5000) | Out-Null
    } catch { }
    Start-Sleep 5
    if (Get-Process -Id $c.ProcessId -ErrorAction SilentlyContinue) { taskkill /PID $c.ProcessId /T /F | Out-Null }
    L ("fechou Chrome porta {0} pid {1}: {2}" -f $porta, $c.ProcessId, $motivo)
}
# 03/11 (dona: "muitos navegadores travam antes de colocar a URL, ficam na aba nova e ficam lá sem serem eliminados nem
# ir pra frente — não pode acontecer em nenhum PC"): Chrome de automação com >= -MinTravado min e TODAS as abas em
# branco (about:blank / nova aba), ou que não responde mais pela porta, travou — fecha já, sem esperar as -Horas.
$feitos = @{}
# 04/11: Chromes que não responderam numa volta anterior (pid -> quando) — fecha só se continuar assim 20+ min depois
$arqSR = 'D:\video-fila\estado\limpeza_chrome_sem_resposta.json'
$semResp = @{}; $mudouSR = $false
try { (Get-Content $arqSR -Raw -ErrorAction Stop | ConvertFrom-Json).PSObject.Properties | ForEach-Object { $semResp[$_.Name] = $_.Value } } catch {}
$branco ='^(about:blank|chrome://newtab/?|chrome://new-tab-page/?|chrome-search://local-ntp.*|)$'
foreach ($c in ($procs | Where-Object { $_.Name -eq 'chrome.exe' -and $_.CommandLine -match 'remote-debugging-port=(\d+)' -and $_.CommandLine -notmatch '--type=' })) {
    $porta = [regex]::Match($c.CommandLine, 'remote-debugging-port=(\d+)').Groups[1].Value
    if (((Get-Date) - $c.CreationDate).TotalMinutes -lt $MinTravado) { continue }
    if ($donoDaPorta.ContainsKey($porta) -and $donoDaPorta[$porta] -ne $c.ProcessId) { continue }  # resto: regra abaixo
    $abas = $null
    foreach ($t in 1..2) { try { $abas = @(Invoke-RestMethod "http://127.0.0.1:$porta/json/list" -TimeoutSec 8 | Where-Object { $_.type -eq 'page' }); break } catch { Start-Sleep 3 } }
    $min = [int]((Get-Date) - $c.CreationDate).TotalMinutes
    if ($null -eq $abas) {
        if ($min -lt 30) { continue }
        # 04/11: com o PC1 em 100% de CPU, Chrome OCUPADO trabalhando (Veo, Studio) não respondia em 8 s e era fechado no
        # meio ("TargetClosedError: browser has been closed" no extras_ledger). Agora só fecha se (a) já não respondia
        # numa volta anterior há >= 20 min e (b) não gastou CPU em 20 s (travado de verdade fica parado).
        $chaveSR = "<SEGREDO_REMOVIDO>"
        $desde = $semResp[$chaveSR]
        if (-not $desde) { $semResp[$chaveSR] = (Get-Date).ToString('o'); $mudouSR = $true; continue }
        if (((Get-Date) - [datetime]$desde).TotalMinutes -lt 20) { continue }
        $cpuIds = @($c.ProcessId) + @($procs | Where-Object { $_.ParentProcessId -eq $c.ProcessId } | ForEach-Object { $_.ProcessId })
        $cpuA = (Get-Process -Id $cpuIds -ErrorAction SilentlyContinue | Measure-Object CPU -Sum).Sum
        Start-Sleep 20
        $cpuB = (Get-Process -Id $cpuIds -ErrorAction SilentlyContinue | Measure-Object CPU -Sum).Sum
        if (($cpuB - $cpuA) -gt 1) { L ("Chrome porta {0} sem resposta mas trabalhando ({1:N1} s de CPU em 20 s) - deixo" -f $porta, ($cpuB - $cpuA)); continue }
        if ($Simular) { L ("[simular] fecharia Chrome porta {0}: nao responde pela porta (aberto ha {1} min)" -f $porta, $min); continue }
        Fechar-Chrome $c $porta ("travado: nao responde pela porta ha 20+ min e sem CPU (aberto ha {0} min)" -f $min); $fechados++; $feitos[$c.ProcessId] = 1; $semResp.Remove($chaveSR); $mudouSR = $true; continue
    }
    if ($semResp.ContainsKey("$($c.ProcessId)")) { $semResp.Remove("$($c.ProcessId)"); $mudouSR = $true }  # voltou a responder
    if ($abas.Count -and -not ($abas | Where-Object { $_.url -notmatch $branco })) {
        if ($Simular) { L ("[simular] fecharia Chrome porta {0}: {1} aba(s) em branco ha {2} min" -f $porta, $abas.Count, $min); continue }
        Fechar-Chrome $c $porta ("travado na aba nova: {0} aba(s) em branco, aberto ha {1} min" -f $abas.Count, $min); $fechados++
        $feitos[$c.ProcessId] = 1
    }
}
if ($mudouSR -and -not $Simular) {
    # só os pids que ainda existem (Chrome que sumiu sozinho sai do estado)
    $vivosSR = @{}; foreach ($k in @($semResp.Keys)) { if (Get-Process -Id ([int]$k) -ErrorAction SilentlyContinue) { $vivosSR[$k] = $semResp[$k] } }
    try { $vivosSR | ConvertTo-Json | Set-Content -Path $arqSR -Encoding UTF8 } catch {}
}
foreach ($c in ($procs | Where-Object { $_.Name -eq 'chrome.exe' -and $_.CommandLine -match 'remote-debugging-port=(\d+)' -and $_.CommandLine -notmatch '--type=' -and -not $feitos.ContainsKey($_.ProcessId) })) {
    if (-not (Get-Process -Id $c.ProcessId -ErrorAction SilentlyContinue)) { continue }
    $porta = [regex]::Match($c.CommandLine, 'remote-debugging-port=(\d+)').Groups[1].Value
    $h = ((Get-Date) - $c.CreationDate).TotalHours
    if ($h -lt $Horas) { continue }
    $perfil = [regex]::Match($c.CommandLine, 'user-data-dir="?([^"]+?)"?( --|$)').Groups[1].Value -replace '.*\\', ''
    if ($donoDaPorta.ContainsKey($porta) -and $donoDaPorta[$porta] -ne $c.ProcessId) {
        if ($Simular) { L ("[simular] fecharia Chrome RESTO porta {0} (dono e outro) aberto ha {1:N1} h" -f $porta, $h); continue }
        taskkill /PID $c.ProcessId /T /F | Out-Null
        $fechados++
        L ("fechou Chrome RESTO porta {0} pid {1} (a porta e de outro Chrome) aberto ha {2:N1} h" -f $porta, $c.ProcessId, $h)
        continue
    }
    if ($usos -match "(?<!\d)$porta(?!\d)") { continue }  # algum script em execução usa esta porta
    # quem abriu ainda vive e cuida dele (fabrica_tokens: até 10 quentes) — 07/11: mas só até 12 h; um processo-pai de
    # vida longa (laço/daemon) segurava o Chrome do cofre do revolutionemerson2 há 19 h e o TikTok travou 2 rodadas
    if ($gerentes -contains $c.ParentProcessId -and $h -lt 12) { continue }
    if ($Simular) { L ("[simular] fecharia Chrome porta {0} ({1}) aberto ha {2:N1} h" -f $porta, $perfil, $h); continue }
    try {
        $ws = (Invoke-RestMethod "http://127.0.0.1:$porta/json/version" -TimeoutSec 5).webSocketDebuggerUrl
        $cli = New-Object System.Net.WebSockets.ClientWebSocket
        $cli.ConnectAsync([Uri]$ws, [Threading.CancellationToken]::None).Wait(5000) | Out-Null
        $msg = [Text.Encoding]::UTF8.GetBytes('{"id":1,"method":"Browser.close"}')
        $cli.SendAsync([ArraySegment[byte]]$msg, 'Text', $true, [Threading.CancellationToken]::None).Wait(5000) | Out-Null
    } catch { }
    Start-Sleep 10
    if (Get-Process -Id $c.ProcessId -ErrorAction SilentlyContinue) { taskkill /PID $c.ProcessId /T /F | Out-Null }
    $fechados++
    L ("fechou Chrome porta {0} ({1}) aberto ha {2:N1} h" -f $porta, $perfil, $h)
}
foreach ($f in ($procs | Where-Object { $_.Name -eq 'ffmpeg.exe' })) {
    if (((Get-Date) - $f.CreationDate).TotalHours -lt $HorasFfmpeg) { continue }
    $p = Get-Process -Id $f.ProcessId -ErrorAction SilentlyContinue; if (-not $p) { continue }
    $cpu0 = $p.CPU; Start-Sleep 30; $p.Refresh()
    if ($p.CPU - $cpu0 -gt 0.5) { continue }  # ainda trabalhando
    if ($Simular) { L ("[simular] fecharia ffmpeg parado {0}" -f $f.ProcessId); continue }
    Stop-Process -Id $f.ProcessId -Force -ErrorAction SilentlyContinue
    $fechados++
    L ("fechou ffmpeg parado {0} (aberto ha {1:N1} h, 0 CPU em 30 s)" -f $f.ProcessId, ((Get-Date) - $f.CreationDate).TotalHours)
}
if ($fechados) { L ("RAM livre {0} -> {1} GB" -f $livreAntes, [math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1MB, 1)) }
