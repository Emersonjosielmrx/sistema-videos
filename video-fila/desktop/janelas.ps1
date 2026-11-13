Get-CimInstance Win32_Process | Where-Object { $_.Name -in 'powershell.exe','pwsh.exe','cmd.exe','python.exe','conhost.exe' } |
  ForEach-Object { $c = [string]$_.CommandLine; '{0} | pai {1} | {2} | {3}' -f $_.ProcessId, $_.ParentProcessId, $_.Name, $c.Substring(0, [Math]::Min(170, $c.Length)) }
'--- tarefas ---'
Get-ScheduledTask | Where-Object { $_.State -ne 'Disabled' -and $_.TaskPath -eq '\' } | ForEach-Object {
  $a = $_.Actions[0]; '{0} | {1} {2}' -f $_.TaskName, $a.Execute, $a.Arguments }
