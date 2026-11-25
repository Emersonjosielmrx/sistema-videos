# liberar_ram.ps1 — libera RAM/CPU do PC1 sem tocar no VS Code (dona 24/11: "ao sobrecarregar faça isso, botão no
# desktop e notificação como a do Wise").
#   -Vigia  (tarefa LiberarRamVigia, 2/2 min): mede; se RAM livre < -MinGB ou CPU >= -MaxCpu, limpa (no máx. 1x/15 min)
#   -Agora  (botão "Liberar RAM" no Desktop): limpa já e mostra a notificação
#   -Simular: só registra o que faria
# O que limpa:
#   1. limpeza_chrome.ps1 (Chrome de automação esquecido/travado; ffmpeg parado há 1 h+)
#   2. árvore TRAVADA: cmd .bat, bash ou powershell -Command cuja árvore inteira não gastou CPU por -MinParado min
#      (medido entre rodadas do vigia, no estado) — nunca se algum processo da árvore escuta porta (servidor/ponte)
#   3. tira da RAM a memória parada dos processos (EmptyWorkingSet, o mesmo que o Wise faz), menos VS Code/Claude
# Nunca toca: Code, claude, chrome pessoal (sem porta), python solto que não é filho de .bat/bash/powershell.
param([switch]$Vigia, [switch]$Agora, [switch]$Simular, [double]$MinGB = 1.2, [int]$MaxCpu = 95,
      [int]$MinParado = 45, [int]$Intervalo = 15)
$ErrorActionPreference = 'SilentlyContinue'
$base = 'D:\video-fila'
$log = "$base\logs\liberar_ram.log"
$arqEst = "$base\estado\liberar_ram.json"
New-Item -ItemType Directory -Force "$base\logs", "$base\estado" | Out-Null
function L($m) { Add-Content -Path $log -Value ("{0:yyyy-MM-dd HH:mm:ss} {1}" -f (Get-Date), $m) -Encoding UTF8 }
function LivreGB { [math]::Round((Get-CimInstance Win32_OperatingSystem -OperationTimeoutSec 20).FreePhysicalMemory / 1MB, 2) }
# 24/11: WMI sem prazo prendia a rodada com o PC1 a 100% (e a tarefa não começa outra enquanto uma vive)
Get-Process powershell | ? { $_.Id -ne $PID -and $_.StartTime -and ((Get-Date) - $_.StartTime).TotalMinutes -gt 6 } | % {
    if ("$((Get-CimInstance Win32_Process -Filter "ProcessId=$($_.Id)" -OperationTimeoutSec 10).CommandLine)" -match 'liberar_ram\.ps1') { Stop-Process -Id $_.Id -Force } }
$Excluir = 'painel_controlador|vibe-voz|ponte_proxy|genspark_http|omniroute|recapd|sentinela|PrioridadeVSCode|prioridade_vscode|liberar_ram'

# ---------- estado (CPU das árvores entre rodadas) ----------
$est = @{ ultima = ''; arvores = @{} }
try { $j = Get-Content $arqEst -Raw | ConvertFrom-Json; $est.ultima = $j.ultima
      $j.arvores.PSObject.Properties | % { $est.arvores[$_.Name] = $_.Value } } catch {}

# 24/11: vigia barata — sem sobrecarga e com varredura feita há < 10 min, sai já (a varredura completa custava ~11 s de CPU)
if ($Vigia -and -not $Agora) {
    $l0 = LivreGB
    $c0 = (Get-CimInstance Win32_Processor -OperationTimeoutSec 20 | Measure-Object LoadPercentage -Average).Average
    $sob0 = ($l0 -lt $MinGB) -or (($c0 -ge $MaxCpu) -and ($l0 -lt 2 * $MinGB))
    $idadeVarr = 999; try { $idadeVarr = ((Get-Date) - (Get-Item $arqEst).LastWriteTime).TotalMinutes } catch {}
    if (-not $sob0 -and $idadeVarr -lt 10) { exit 0 }
}

$procs = Get-CimInstance Win32_Process -OperationTimeoutSec 60
if (-not $procs) { L "WMI nao respondeu em 60 s - pulo esta rodada"; exit 0 }
$porPai = @{}; foreach ($p in $procs) { $k = [int]$p.ParentProcessId; if (-not $porPai[$k]) { $porPai[$k] = @() }; $porPai[$k] += $p }
$porId = @{}; foreach ($p in $procs) { $porId[[int]$p.ProcessId] = $p }
$escuta = @{}; Get-NetTCPConnection -State Listen | % { $escuta[[int]$_.OwningProcess] = 1 }
$cpuDe = @{}; Get-Process | % { $cpuDe[$_.Id] = $_.CPU }
function Arvore($id) { $r = @($id); foreach ($f in @($porPai[[int]$id])) { if ($f -and $f.ProcessId -ne $id) { $r += Arvore $f.ProcessId } }; $r }

$raizes = $procs | ? {
    $cl = "$($_.CommandLine)"; $pai = $porId[[int]$_.ParentProcessId]
    (($_.Name -eq 'cmd.exe' -and $cl -match '\.bat') -or
     ($_.Name -eq 'bash.exe' -and -not ($pai -and $pai.Name -eq 'bash.exe')) -or
     ($_.Name -eq 'powershell.exe' -and $cl -match ' -Command ' -and $cl -notmatch '__claudeCodeScript|noexit' -and -not ($pai -and $pai.Name -eq 'powershell.exe'))) -and
    $cl -notmatch $Excluir
}
$novoEst = @{}; $travadas = @()
foreach ($r in $raizes) {
    $ids = Arvore $r.ProcessId
    $chave = "<SEGREDO_REMOVIDO>'yyyyMMddHHmmss'))"
    $cpu = 0.0; foreach ($i in $ids) { $cpu += [double]$cpuDe[[int]$i] }
    $servidor = @($ids | ? { $escuta[[int]$_] }).Count -gt 0
    $todosCmd = ($ids | % { "$($porId[[int]$_].CommandLine)" }) -join ' '
    if ($servidor -or $todosCmd -match $Excluir) { continue }
    $ant = $est.arvores[$chave]
    if ($ant -and [math]::Abs($cpu - [double]$ant.cpu) -lt 0.3) { $desde = [datetime]$ant.desde } else { $desde = Get-Date }
    $novoEst[$chave] = @{ cpu = $cpu; desde = $desde.ToString('o') }
    $parado = ((Get-Date) - $desde).TotalMinutes
    $idade = ((Get-Date) - $r.CreationDate).TotalMinutes
    if ($parado -ge $MinParado -and $idade -ge 60) {
        $desc = "$($r.CommandLine)"; if ($desc.Length -gt 140) { $desc = $desc.Substring(0, 140) }
        $travadas += [pscustomobject]@{ Id = $r.ProcessId; Ids = $ids; Parado = [int]$parado; Idade = [int]$idade; Desc = $desc }
    }
}

# ---------- decide ----------
$livre = LivreGB
$cpuAgora = (Get-CimInstance Win32_Processor -OperationTimeoutSec 20 | Measure-Object LoadPercentage -Average).Average
# CPU em 100% é normal no PC1 (render); só conta junto com RAM apertada (< 2x o mínimo), senão a notificação não parava
$sobrecarga = ($livre -lt $MinGB) -or (($cpuAgora -ge $MaxCpu) -and ($livre -lt 2 * $MinGB))
$podeAgir = $Agora -or ($sobrecarga -and (-not $est.ultima -or ((Get-Date) - [datetime]$est.ultima).TotalMinutes -ge $Intervalo))
if (-not $podeAgir) {
    if (-not $Simular) { @{ ultima = $est.ultima; arvores = $novoEst } | ConvertTo-Json -Depth 4 | Set-Content $arqEst -Encoding UTF8 }
    exit 0
}

$antes = $livre; $fechou = @()
L ("--- {0}: RAM livre {1} GB, CPU {2}%, {3} arvore(s) travada(s)" -f $(if ($Agora) { 'botao' } else { 'sobrecarga' }), $livre, $cpuAgora, $travadas.Count)

# 1. Chrome de automação + ffmpeg parado
$argsLC = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "$base\limpeza_chrome.ps1", '-Horas', '3', '-HorasFfmpeg', '1', '-MinOrfao', '15')
if ($Simular) { $argsLC += '-Simular' }
$tamLog = (Get-Item "$base\logs\limpeza_chrome.log").Length
& powershell.exe @argsLC | Out-Null
$novo = Get-Content "$base\logs\limpeza_chrome.log" -Raw -Encoding UTF8
if ($novo.Length -gt $tamLog) { $n = ([regex]::Matches($novo.Substring([math]::Min($tamLog, $novo.Length)), 'fechou ')).Count; if ($n) { $fechou += "$n Chrome/ffmpeg" } }

# 2. árvores travadas
$nArv = 0
foreach ($t in $travadas) {
    if ($Simular) { L ("[simular] mataria arvore {0} (parada ha {1} min, aberta ha {2} min): {3}" -f $t.Id, $t.Parado, $t.Idade, $t.Desc); continue }
    taskkill /PID $t.Id /T /F 2>&1 | Out-Null
    foreach ($i in $t.Ids) { Stop-Process -Id $i -Force }
    L ("matou arvore {0} ({1} proc, parada ha {2} min): {3}" -f $t.Id, $t.Ids.Count, $t.Parado, $t.Desc); $nArv++
}
if ($nArv) { $fechou += "$nArv tarefa(s) travada(s)" }

# 3. esvaziar memória parada (como o Wise), menos VS Code / Claude
if (-not $Simular) {
    if (-not ('Psapi.Mem' -as [type])) {
        Add-Type -Namespace Psapi -Name Mem -MemberDefinition '[DllImport("psapi.dll")] public static extern bool EmptyWorkingSet(IntPtr h);'
    }
    $nT = 0
    foreach ($p in Get-Process) {
        if ($p.ProcessName -match '^(Code|claude|System|Idle|Registry|Memory Compression|csrss|smss|wininit|lsass|dwm)$') { continue }
        try { if ([Psapi.Mem]::EmptyWorkingSet($p.Handle)) { $nT++ } } catch {}
    }
}

Start-Sleep 3
$depois = LivreGB
L ("RAM livre {0} -> {1} GB; {2}" -f $antes, $depois, $(if ($fechou) { $fechou -join ', ' } else { 'nada travado' }))
if (-not $Simular) { @{ ultima = (Get-Date).ToString('o'); arvores = $novoEst } | ConvertTo-Json -Depth 4 | Set-Content $arqEst -Encoding UTF8 }  # 24/11: simulação não pode gravar "ultima" (travaria a limpeza real por 15 min)

# ---------- notificação (toast do Windows) ----------
$titulo = "RAM liberada: {0:N1} -> {1:N1} GB livres" -f $antes, $depois
$texto = if ($fechou) { "Fechei " + ($fechou -join ', ') + "." } else { "Nada travado; memória parada esvaziada." }
if (-not $Agora) { $texto = "PC sobrecarregado (CPU $cpuAgora%). " + $texto }
if ($Simular) { $titulo = "[simulação] " + $titulo }
try {
    [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
    [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
    $esc = { param($s) [Security.SecurityElement]::Escape($s) }
    $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
    $xml.LoadXml("<toast><visual><binding template='ToastGeneric'><text>$(& $esc $titulo)</text><text>$(& $esc $texto)</text></binding></visual></toast>")
    $app = '{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\WindowsPowerShell\v1.0\powershell.exe'
    [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($app).Show([Windows.UI.Notifications.ToastNotification]::new($xml))
} catch { L "toast falhou: $_" }
