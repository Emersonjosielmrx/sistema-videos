param([string]$Script, [string]$Out, [int]$Espera = 90)
$a = New-ScheduledTaskAction -Execute 'cmd.exe' -Argument "/c cd /d D:\logins-google && python -X utf8 $Script > $Out 2>&1"
$p = New-ScheduledTaskPrincipal -UserId 'Haylla' -LogonType Interactive
Register-ScheduledTask -TaskName 'ClaudeInterativo' -Action $a -Principal $p -Force | Out-Null
Start-ScheduledTask 'ClaudeInterativo'
$fim = (Get-Date).AddSeconds($Espera)
do { Start-Sleep 3; $st = (Get-ScheduledTask 'ClaudeInterativo').State } while ($st -eq 'Running' -and (Get-Date) -lt $fim)
Get-Content $Out
Unregister-ScheduledTask 'ClaudeInterativo' -Confirm:$false
