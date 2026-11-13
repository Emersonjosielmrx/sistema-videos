# Instala o telão + medidor no desktop puxando os arquivos do PC1 por HTTP (o ssh do desktop só aguenta comando curto).
# Usado pelo D:\video-fila\desktop_vigia.py (troca __URL__ pelo servidor temporário dele). Idempotente.
New-Item -ItemType Directory -Force C:\vitrine | Out-Null
foreach ($f in "telao_win.py","moldura_desktop.html","painel.html") {
  try { Invoke-WebRequest -UseBasicParsing -TimeoutSec 60 ("__URL__/" + $f) -OutFile ("C:\vitrine\" + $f) } catch { "ERRO " + $f + " " + $_.Exception.Message }
}
Set-Content -NoNewline C:\vitrine\maquina.txt desktop
$py = (Get-Command pythonw -EA SilentlyContinue).Source
if (-not $py) { $py = (Get-ChildItem C:\Python3*\pythonw.exe, "$env:LOCALAPPDATA\Programs\Python\*\pythonw.exe" -EA SilentlyContinue | Select-Object -First 1).FullName }
if (-not $py) { "SEM_PYTHON" } else {
  $area = [Environment]::GetFolderPath("Desktop")
  Set-Content -Path (Join-Path $area "DESLIGAR TELAO.bat") -Value ("@echo off`r`necho desligado > C:\vitrine\desligado.txt`r`necho Telao desligado. O desktop segue trabalhando.`r`ntimeout /t 3")
  Set-Content -Path (Join-Path $area "LIGAR TELAO.bat") -Value ("@echo off`r`ndel C:\vitrine\desligado.txt 2>nul`r`necho Telao volta em ate 1 minuto.`r`ntimeout /t 3")
  # cmdlets em vez de schtasks /tr: o python do desktop fica em "C:\Program Files\..." e o PowerShell 5 tira as aspas
  # do argumento do schtasks (29/10 23:49: "Argumento inválido - 'Files\Python..."). Interativo = aparece na tela dela.
  $acao = New-ScheduledTaskAction -Execute $py -Argument "C:\vitrine\telao_win.py" -WorkingDirectory "C:\vitrine"
  $gat = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
  $quem = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive
  $cfg = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit ([TimeSpan]::Zero)
  Register-ScheduledTask -TaskName Desktop_Telao -Action $acao -Trigger $gat -Principal $quem -Settings $cfg -Force | Out-Null
  Stop-ScheduledTask -TaskName Desktop_Telao -EA SilentlyContinue
  Start-ScheduledTask -TaskName Desktop_Telao
  "TAREFA " + (Get-ScheduledTask -TaskName Desktop_Telao).State
  "PY=" + $py
}
Get-ChildItem C:\vitrine -File | ForEach-Object { "ARQ " + $_.Name + " " + $_.Length }
"FIM"
