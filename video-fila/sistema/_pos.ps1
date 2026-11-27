"boot: " + (Get-CimInstance Win32_OperatingSystem).LastBootUpTime
"flow juncao: " + [bool]((Get-Item D:\flow-imagens -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)
$i = Get-ScheduledTaskInfo MudarNoBoot; "MudarNoBoot: $($i.LastRunTime) rc=$($i.LastTaskResult)"
"pontes: " + @(Get-CimInstance Win32_Process | ?{ $_.CommandLine -match 'ponte_proxy_fixo' }).Count
"pythons: " + @(Get-Process python*,pythonw* -ErrorAction SilentlyContinue).Count
"logado: " + (Get-CimInstance Win32_ComputerSystem).UserName
