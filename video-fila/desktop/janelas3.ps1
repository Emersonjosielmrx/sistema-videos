Get-ScheduledTask | ForEach-Object {
  foreach ($a in $_.Actions) {
    $txt = '{0} {1}' -f $a.Execute, $a.Arguments
    if ($txt -match 'espelhar|downloads_para_drive|limpeza-cache|central-reserva') {
      $i = Get-ScheduledTaskInfo -TaskName $_.TaskName -TaskPath $_.TaskPath
      $rep = ($_.Triggers | ForEach-Object { $_.Repetition.Interval }) -join ','
      '{0}{1} | {2} | ultima {3} | rep {4} | {5}' -f $_.TaskPath, $_.TaskName, $_.State, $i.LastRunTime, $rep, $txt } } }
Get-Content D:\ferramentas\central-reserva\espelhar_pc1.ps1 -TotalCount 12
