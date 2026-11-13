$dir = 'C:\Users\Emerson\RustDesk'
New-Item -ItemType Directory -Force $dir | Out-Null
Move-Item -Force 'C:\Users\Emerson\AppData\Local\Temp\rustdesk-portatil.exe' "$dir\rustdesk.exe"
$exe = "$dir\rustdesk.exe"
Remove-Item 'C:\Users\Emerson\AppData\Local\Temp\rustdesk-1.5.1-x86_64.msi' -ErrorAction SilentlyContinue
$ws = New-Object -ComObject WScript.Shell
$lnk = $ws.CreateShortcut('C:\Users\Emerson\Desktop\Tela do PC1.lnk')
$lnk.TargetPath = $exe
$lnk.Arguments = '--connect 100.118.234.102 --password zMQVUd8astNY'
$lnk.WorkingDirectory = $dir
$lnk.IconLocation = "$exe,0"
$lnk.Description = 'Abre a tela do Revision-PC (PC1) pela Tailscale'
$lnk.Save()
"exe=$(Test-Path $exe) atalho=$(Test-Path 'C:\Users\Emerson\Desktop\Tela do PC1.lnk')"
