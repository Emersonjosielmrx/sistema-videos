# Tarefa VisualizadorLongos no desktop: a cada minuto, só com o usuário logado (abre o Chrome na tela dele)
$acao = New-ScheduledTaskAction -Execute 'C:\Program Files\Python311\pythonw.exe' -Argument 'D:\visualizador\visualizador_win.py' -WorkingDirectory 'D:\visualizador'
$gatilho = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 1)
$quem = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive
$cfg = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 5)
Register-ScheduledTask -TaskName VisualizadorLongos -Action $acao -Trigger $gatilho -Principal $quem -Settings $cfg -Force | Out-Null
(Get-ScheduledTask -TaskName VisualizadorLongos).State
