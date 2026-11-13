$WshShell = New-Object -comObject WScript.Shell
$DesktopPath = [Environment]::GetFolderPath("Desktop")
$Shortcut = $WshShell.CreateShortcut("$DesktopPath\Painel Hipercool.lnk")
$Shortcut.TargetPath = "D:\hipercool-inferior-fix\start_painel.bat"
$Shortcut.WorkingDirectory = "D:\hipercool-inferior-fix\"
$Shortcut.Save()
