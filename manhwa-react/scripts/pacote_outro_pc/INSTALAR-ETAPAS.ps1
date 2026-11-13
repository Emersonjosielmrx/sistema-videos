# Atualizacao "videos dos 2 PCs no mesmo Google Drive" (16/10) - ver LEIA-ME-ETAPAS.txt
$ErrorActionPreference = "Stop"
$aqui = Split-Path -Parent $MyInvocation.MyCommand.Path
$data = Get-Date -Format "yyyyMMdd_HHmm"
Add-Type -AssemblyName System.IO.Compression.FileSystem

Write-Host "1/4 arquivos novos (copia .bkp_$data de cada um que ja existia)"
$zip = [System.IO.Compression.ZipFile]::OpenRead((Join-Path $aqui "etapas.zip"))
foreach ($e in $zip.Entries) {
    if ($e.FullName.EndsWith("/")) { continue }
    $dst = Join-Path "D:\" ($e.FullName -replace "/", "\")
    if (Test-Path $dst) { Copy-Item $dst "$dst.bkp_$data" }
    New-Item -ItemType Directory -Force (Split-Path $dst) | Out-Null
    [System.IO.Compression.ZipFileExtensions]::ExtractToFile($e, $dst, $true)
    Write-Host "   $dst"
}
$zip.Dispose()

Write-Host "2/4 rclone no mesmo Drive (remoto manhwa-drive)"
$conf = Join-Path $env:APPDATA "rclone\rclone.conf"
$tem = (Test-Path $conf) -and (Select-String -Path $conf -Pattern "^\[manhwa-drive\]" -Quiet)
if (-not $tem) {
    # mesmo app do rclone e mesma conta Google do PC principal (escopo drive.file): enxerga as mesmas pastas
    Write-Host "   vai abrir o navegador: entre na conta Google do Drive de backup (a mesma do PC principal)"
    Write-Host "   (se der erro 400, abra antes uma janela anonima do Chrome e rode este instalador de novo)"
    & D:\tools\rclone.exe config create manhwa-drive drive scope=drive.file
    if ($LASTEXITCODE -ne 0) { throw "a autorizacao do Drive nao terminou (erro $LASTEXITCODE)" }
} else {
    Write-Host "   ja estava em $conf"
}
& D:\tools\rclone.exe lsd manhwa-drive:videos-backup
if ($LASTEXITCODE -ne 0) { throw "o rclone nao abriu o Drive (erro $LASTEXITCODE). Rode: D:\tools\rclone.exe config reconnect manhwa-drive:" }

Write-Host "3/4 o que o backup faria (simulacao, nao mexe em nada)"
$env:PYTHONUTF8 = "1"
& D:\manhwa-react\.venv\Scripts\python.exe D:\manhwa-react\scripts\backup_drive.py --simular
if ($LASTEXITCODE -ne 0) { throw "a simulacao do backup deu erro (acima); a tarefa NAO foi agendada" }

Write-Host "4/4 tarefa BackupDriveVideos (todo dia 04:50)"
$acao = New-ScheduledTaskAction -Execute "wscript.exe" -Argument '"D:\rodar_oculto.vbs" "D:\manhwa-react\scripts\backup_drive.bat"'
$quando = New-ScheduledTaskTrigger -Daily -At "04:50"
$opcoes = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Hours 6) -StartWhenAvailable
Register-ScheduledTask -TaskName "BackupDriveVideos" -Action $acao -Trigger $quando -Settings $opcoes -Force | Out-Null
Write-Host ""
Write-Host "PRONTO. Para mandar ja: D:\manhwa-react\scripts\backup_drive.bat  (log: D:\manhwa-react\logs\backup_drive.log)"
