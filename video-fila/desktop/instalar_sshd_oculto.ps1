Copy-Item D:\visualizador\sshd_desktop_oculto.py D:\ferramentas\sshd-usuario\sshd_desktop_oculto.py -Force
$acao = New-ScheduledTaskAction -Execute 'C:\Program Files\Python311\pythonw.exe' -Argument 'D:\ferramentas\sshd-usuario\sshd_desktop_oculto.py' -WorkingDirectory 'D:\ferramentas\sshd-usuario'
$gat = @((New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME), (New-ScheduledTaskTrigger -Once -At (Get-Date).AddSeconds(20) -RepetitionInterval (New-TimeSpan -Minutes 5)))
$quem = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive
$set = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew -ExecutionTimeLimit ([TimeSpan]::Zero)
Register-ScheduledTask -TaskName SSHD-Oculto -Action $acao -Trigger $gat -Principal $quem -Settings $set -Force | Out-Null
Start-ScheduledTask -TaskName SSHD-Oculto
Start-Sleep 6
Get-CimInstance Win32_Process -Filter "Name='sshd.exe'" | ForEach-Object { '{0} sessao {1} | {2}' -f $_.ProcessId, $_.SessionId, $_.CommandLine }
Get-Content D:\ferramentas\sshd-usuario\sshd_oculto.log -Tail 3 -ErrorAction SilentlyContinue
Get-Content D:\ferramentas\sshd-usuario\sshd_2223.log -Tail 3 -ErrorAction SilentlyContinue
