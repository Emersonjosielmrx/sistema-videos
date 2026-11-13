# ============================================================
#  Cria atalhos no Desktop pro PAINEL VEO (raiz D:\veo):
#   - VEO - PAINEL (ligar supervisor)
#   - VEO - DESLIGAR tudo
#  Rode uma vez:  powershell -ExecutionPolicy Bypass -File criar_atalhos_desktop.ps1
# ============================================================
$base    = $PSScriptRoot
$desktop = [Environment]::GetFolderPath('Desktop')
$ws      = New-Object -ComObject WScript.Shell

function Novo-Atalho($nome, $bat, $iconIndex) {
    $lnk = $ws.CreateShortcut((Join-Path $desktop "$nome.lnk"))
    $lnk.TargetPath       = (Join-Path $base $bat)
    $lnk.WorkingDirectory = $base
    $lnk.IconLocation     = "$env:SystemRoot\System32\shell32.dll,$iconIndex"
    $lnk.Description       = $nome
    $lnk.Save()
    Write-Host "  criado: $nome -> $bat"
}

Write-Host "Criando atalhos do PAINEL VEO no Desktop..."
Novo-Atalho "VEO - PAINEL"          "Veo_PAINEL.bat"          137
Novo-Atalho "VEO - DESLIGAR tudo"   "Veo_PAINEL_DESLIGAR.bat" 131
Write-Host "Pronto. Veja os 2 atalhos no seu Desktop."
