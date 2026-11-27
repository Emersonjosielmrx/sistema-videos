$a = New-ScheduledTaskAction -Execute 'wscript.exe' -Argument 'D:\rodar_oculto.vbs D:\veo\venv\Scripts\pythonw.exe -X utf8 D:\sistema\catalogo\limpar_scripts.py --rede'
$t = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(2) -RepetitionInterval (New-TimeSpan -Minutes 10)
$s = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 8) -StartWhenAvailable
Register-ScheduledTask -TaskName 'RedeLimpeza' -Action $a -Trigger $t -Settings $s -User 'Haylla' -RunLevel Limited -Force | Select TaskName,State
