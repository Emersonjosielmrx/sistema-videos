# ============================================================
#  Cria 3 atalhos no Desktop pros botoes do bot Veo/Flow:
#   - Veo - LIGAR (visivel)
#   - Veo - LIGAR (invisivel, economico)
#   - Veo - DESLIGAR
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

Write-Host "Criando atalhos no Desktop..."
Novo-Atalho "Veo - LIGAR (visivel)"                "Veo_LIGAR_visivel.bat"          137
Novo-Atalho "Veo - LIGAR (invisivel-economico)"    "Veo_LIGAR_invisivel.bat"        41
Novo-Atalho "Veo - DESLIGAR"                       "Veo_DESLIGAR.bat"               131
Novo-Atalho "Veo - ACESSO TOTAL (ligar)"           "Veo_ACESSO_TOTAL_LIGAR.bat"     46
Novo-Atalho "Veo - ACESSO TOTAL (desligar)"        "Veo_ACESSO_TOTAL_DESLIGAR.bat"  27
Write-Host "Pronto. Veja os 5 atalhos no seu Desktop."
