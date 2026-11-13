# cria_atalhos_controle.ps1 — cria atalhos no Desktop pra LIGAR/DESLIGAR
# o cron noturno de anime e a producao autonoma (veo3/hipercool).
$WshShell = New-Object -comObject WScript.Shell
$Desktop = [Environment]::GetFolderPath("Desktop")

function New-Atalho($nome, $alvo, $workdir) {
    $sc = $WshShell.CreateShortcut("$Desktop\$nome.lnk")
    $sc.TargetPath = $alvo
    $sc.WorkingDirectory = $workdir
    $sc.Save()
    Write-Host "  criado: $nome -> $alvo"
}

Write-Host "Criando atalhos de controle no Desktop..."
New-Atalho "LIGAR Cron Anime"     "D:\recapd-e-animes\LIGAR_CRON_ANIME.bat"    "D:\recapd-e-animes"
New-Atalho "DESLIGAR Cron Anime"  "D:\recapd-e-animes\DESLIGAR_CRON_ANIME.bat" "D:\recapd-e-animes"
New-Atalho "LIGAR Producao"       "D:\hipercool-videos\LIGAR_PRODUCAO.bat"     "D:\hipercool-videos"
New-Atalho "DESLIGAR Producao"    "D:\hipercool-videos\DESLIGAR_PRODUCAO.bat"  "D:\hipercool-videos"
Write-Host "Pronto. 4 atalhos no Desktop."
