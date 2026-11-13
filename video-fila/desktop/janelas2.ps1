foreach ($n in 'KiroAbrir','PostadorLoginDesktop','PostadorTiktokDesktop2','PostadorTiktokFaltantes','PostadorLogar') {
  $t = Get-ScheduledTask -TaskName $n -ErrorAction SilentlyContinue; if (-not $t) { continue }
  $i = Get-ScheduledTaskInfo -TaskName $n
  $tr = ($t.Triggers | ForEach-Object { '{0} rep={1}' -f $_.CimClass.CimClassName, $_.Repetition.Interval }) -join '; '
  '{0} | ultima {1} | proxima {2} | {3}' -f $n, $i.LastRunTime, $i.NextRunTime, $tr
}
'--- tarefas em subpastas com powershell/cmd sem Hidden ---'
Get-ScheduledTask | Where-Object { $_.State -ne 'Disabled' -and $_.TaskPath -notlike '\Microsoft*' } | ForEach-Object {
  $a = $_.Actions[0]; $txt = '{0} {1}' -f $a.Execute, $a.Arguments
  if ($txt -match 'powershell|cmd|\.bat|\.cmd|python\.exe' -and $txt -notmatch 'Hidden|pythonw|wscript') {
    $i = Get-ScheduledTaskInfo -TaskName $_.TaskName -TaskPath $_.TaskPath
    '{0}{1} | ultima {2} | {3}' -f $_.TaskPath, $_.TaskName, $i.LastRunTime, $txt.Substring(0, [Math]::Min(150, $txt.Length)) } }
'--- pai do espelhar ---'
Get-CimInstance Win32_Process -Filter 'ProcessId=17768' | ForEach-Object { $_.Name + ' ' + $_.CommandLine }
