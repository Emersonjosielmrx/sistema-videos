'--- processos de console na sessao da tela (SessionId 1) ---'
Get-CimInstance Win32_Process | Where-Object { $_.SessionId -eq 1 -and $_.Name -in 'powershell.exe','cmd.exe','conhost.exe','python.exe','wscript.exe','ssh.exe' } |
  ForEach-Object { $c = [string]$_.CommandLine; '{0} pai {1} {2} {3} | {4}' -f $_.ProcessId, $_.ParentProcessId, $_.Name, $_.CreationDate, $c.Substring(0, [Math]::Min(160, $c.Length)) }
'--- janelas visiveis ---'
Get-Process | Where-Object { $_.MainWindowTitle -and $_.SessionId -eq 1 } | Select-Object Id, ProcessName, MainWindowTitle | Format-Table -AutoSize | Out-String -Width 200
'--- ultimos eventos de processo criado (4688) ---'
try { Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4688; StartTime=(Get-Date).AddMinutes(-15)} -MaxEvents 40 -ErrorAction Stop |
  ForEach-Object { $_.TimeCreated.ToString('HH:mm:ss') + ' ' + $_.Properties[5].Value } } catch { 'sem auditoria de processos' }
