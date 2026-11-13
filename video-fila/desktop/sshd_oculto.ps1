# 01/11 dona ("aparece toda hora o PowerShell no desktop"): o sshd do usuÃ¡rio (2222, tarefa SSHD-Usuario) roda
# NA SESSÃƒO DA TELA, entÃ£o cada comando que chega por ssh abre uma janela. Este sobe uma 2Âª instÃ¢ncia (porta 2223)
# como o mesmo Emerson mas com logon S4U (fora da tela, sem senha): os comandos rodam sem janela. A 2222 fica de reserva.
$d = 'D:\ferramentas\sshd-usuario'
$cfg = Get-Content "$d\sshd_config"
$cfg = $cfg | ForEach-Object { if ($_ -match '^\s*Port\s') { 'Port 2223' } elseif ($_ -match '^\s*PidFile\s') { "PidFile $d/sshd_2223.pid" } else { $_ } }
if (-not ($cfg -match '^\s*Port\s')) { $cfg = @('Port 2223') + $cfg }
if (-not ($cfg -match '^\s*PidFile\s')) { $cfg += "PidFile $d/sshd_2223.pid" }
Set-Content -Encoding Ascii "$d\sshd_config_2223" $cfg
$acao = New-ScheduledTaskAction -Execute 'C:\Program Files\OpenSSH\sshd.exe' -Argument "-D -f $d\sshd_config_2223 -E $d\sshd_2223.log"
$gat = @((New-ScheduledTaskTrigger -AtStartup), (New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 5)))
$quem = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType S4U
$set = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew -ExecutionTimeLimit ([TimeSpan]::Zero) -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
Register-ScheduledTask -TaskName SSHD-Oculto -TaskPath '\CentralReservaBase\' -Action $acao -Trigger $gat -Principal $quem -Settings $set -Force | Out-Null
Start-ScheduledTask -TaskPath '\CentralReservaBase\' -TaskName SSHD-Oculto
Start-Sleep 4
Get-CimInstance Win32_Process -Filter "Name='sshd.exe'" | ForEach-Object { '{0} sessao {1} | {2}' -f $_.ProcessId, $_.SessionId, $_.CommandLine }
Get-Content "$d\sshd_2223.log" -Tail 5 -ErrorAction SilentlyContinue

