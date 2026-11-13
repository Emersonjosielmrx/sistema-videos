$ErrorActionPreference = 'Continue'
$msi = Join-Path $env:TEMP 'rustdesk-1.5.1-x86_64.msi'
$exe = 'C:\Program Files\RustDesk\rustdesk.exe'
if (-not (Test-Path $exe)) {
    $p = Start-Process msiexec -ArgumentList "/i `"$msi`" /qn /norestart" -Wait -PassThru -WindowStyle Hidden
    "msi=$($p.ExitCode)"
}
"instalado=$(Test-Path $exe)"
$ws = New-Object -ComObject WScript.Shell
foreach ($d in @("$env:PUBLIC\Desktop", [Environment]::GetFolderPath('Desktop'))) {
    if (-not (Test-Path $d)) { continue }
    $lnk = $ws.CreateShortcut((Join-Path $d 'Tela do PC1.lnk'))
    $lnk.TargetPath = $exe
    $lnk.Arguments = '--connect 100.118.234.102 --password zMQVUd8astNY'
    $lnk.IconLocation = "$exe,0"
    $lnk.Description = 'Abre a tela do Revision-PC (PC1) pela Tailscale'
    $lnk.Save()
    "atalho=$d"
}
Remove-Item $msi -ErrorAction SilentlyContinue
