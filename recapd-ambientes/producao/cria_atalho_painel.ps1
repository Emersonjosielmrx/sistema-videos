$WshShell = New-Object -comObject WScript.Shell
$DesktopPath = [System.Environment]::GetFolderPath('Desktop')
$Shortcut = $WshShell.CreateShortcut("$DesktopPath\Painel Hipercool.lnk")
$Shortcut.TargetPath = "D:\hipercool-inferior-fix\run_painel_html.bat"
$Shortcut.WorkingDirectory = "D:\hipercool-inferior-fix"
$Shortcut.IconLocation = "powershell.exe,0" 
$Shortcut.Save()
Write-Host "Atalho 'Painel Hipercool' criado na Área de Trabalho com sucesso!"
