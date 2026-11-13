# ============================================================
#  Cria atalhos no Desktop pros botoes do bot Veo/Flow:
#   - Veo - LIGAR (visivel)
#   - Veo - LIGAR (invisivel, economico)
#   - Veo - DESLIGAR
#   - Veo - ACESSO TOTAL (ligar / desligar)
#   - Veo - POS (ligar/desligar todos)
#   - Veo - POS Flag (toggle de 1 flag)
#   - Veo - POS Rodar (incremental / retroativo)
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

# --- pos-producao (subsistemas independentes) ---
Novo-Atalho "Veo - POS (LIGAR tudo)"               "Veo_POS_TUDO.bat"               44
Novo-Atalho "Veo - POS (DESLIGAR tudo)"            "Veo_POS_TUDO.bat off"           131
Novo-Atalho "Veo - POS Flag"                       "Veo_POS_FLAG.bat"               13
Novo-Atalho "Veo - POS Rodar (incremental)"        "Veo_POS_RODAR.bat"              24
Novo-Atalho "Veo - POS Rodar (retroativo 5)"       "Veo_POS_RODAR.bat retroativo 5" 144

Write-Host "Pronto. Veja os atalhos no seu Desktop."
