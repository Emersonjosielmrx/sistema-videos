# vigia_chats.ps1 — 24/11 dona ("tá lento de novo ... faça os scripts pra não acontecer de novo"): 10 chats do Claude
# abertos (8 parados há ~8 h) + VS Code somavam ~40% da CPU e ~3 GB no PC1. NÃO fecha chat (pode ter trabalho da
# dona): só AVISA com notificação quando há muitos chats E o PC está apertado, no máximo 1x por hora.
# Tarefa VigiaChats a cada 15 min (oculta). Desligar: criar D:\video-fila\VIGIA_CHATS_OFF.
param([int]$MaxChats = 6, [double]$MinGB = 4, [int]$Intervalo = 60, [switch]$Simular)
if (Test-Path 'D:\video-fila\VIGIA_CHATS_OFF') { exit }
$log = 'D:\video-fila\logs\vigia_chats.log'
$arq = 'D:\video-fila\estado\vigia_chats.json'
function L($m) { Add-Content -Path $log -Value ("{0:yyyy-MM-dd HH:mm:ss} {1}" -f (Get-Date), $m) -Encoding UTF8 }

$cl = @(Get-Process claude -ErrorAction SilentlyContinue)
$code = @(Get-Process Code -ErrorAction SilentlyContinue)
# cada chat = 1 processo claude "principal" (os outros são filhos). Conta pelo uso de memória > 60 MB.
$chats = @($cl | Where-Object { $_.WorkingSet64 -gt 60MB })
$mbClaude = [int](($cl | Measure-Object WorkingSet64 -Sum).Sum / 1MB)
$mbCode = [int](($code | Measure-Object WorkingSet64 -Sum).Sum / 1MB)
Add-Type -AssemblyName Microsoft.VisualBasic
$livre = [math]::Round((New-Object Microsoft.VisualBasic.Devices.ComputerInfo).AvailablePhysicalMemory / 1GB, 1)
# CPU dos chats em 5 s
$a = @{}; $cl + $code | ForEach-Object { $a[$_.Id] = $_.CPU }
Start-Sleep 5
$cpu = 0; Get-Process claude, Code -ErrorAction SilentlyContinue | ForEach-Object { if ($a.ContainsKey($_.Id)) { $cpu += ($_.CPU - $a[$_.Id]) } }
$pct = [math]::Round($cpu / 5 / [Environment]::ProcessorCount * 100)

$linha = "{0} chats, Claude {1} MB + VS Code {2} MB, {3}% CPU, RAM livre {4} GB" -f $chats.Count, $mbClaude, $mbCode, $pct, $livre
if ($chats.Count -le $MaxChats -or ($livre -ge $MinGB -and $pct -lt 20)) { exit }

$ult = $null; if (Test-Path $arq) { try { $ult = [datetime](Get-Content $arq -Raw | ConvertFrom-Json).ultimo } catch {} }
if ($ult -and ((Get-Date) - $ult).TotalMinutes -lt $Intervalo) { exit }
L "AVISO: $linha"
if ($Simular) { "[simular] avisaria: $linha"; exit }
@{ ultimo = (Get-Date).ToString('o') } | ConvertTo-Json | Set-Content $arq -Encoding UTF8
try {
    [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
    [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
    $t = [Security.SecurityElement]::Escape("PC lento: $($chats.Count) chats do Claude abertos")
    $x = [Security.SecurityElement]::Escape("Usam $([math]::Round(($mbClaude + $mbCode)/1024,1)) GB e $pct% da CPU (RAM livre $livre GB). Feche os chats parados no VS Code.")
    $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
    $xml.LoadXml("<toast><visual><binding template='ToastGeneric'><text>$t</text><text>$x</text></binding></visual></toast>")
    [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\WindowsPowerShell\v1.0\powershell.exe').Show([Windows.UI.Notifications.ToastNotification]::new($xml))
} catch { L "toast falhou: $_" }
