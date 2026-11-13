# Liga o Claude Code (VS Code) DESTE PC no seu servidor com o modelo Sonnet 5.5 web (contas gratuitas do claude.ai).
# Não leva senha: pede o endereço do servidor, a porta e a chave na hora. Faz backup de tudo que muda (*.bak-sonnet).
# Rodar:  clique com o direito > "Executar com o PowerShell"   (ou: powershell -ExecutionPolicy Bypass -File instalar_sonnet_web.ps1)
$ErrorActionPreference = "Stop"

Write-Host "`n=== Sonnet 5.5 web no Claude Code do VS Code ===" -ForegroundColor Cyan
$ip = (Read-Host "IP ou nome da sua VPS (ex.: 203.0.113.10)").Trim()
$porta = (Read-Host "Porta (Enter = 20133 do proxy; use 20128 se for direto no OmniRoute)").Trim()
if (-not $porta) { $porta = "20133" }
$SERVIDOR = "http://${ip}:${porta}"
$seguro = Read-Host "Chave do OmniRoute (começa com sk-)" -AsSecureString
$chave = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($seguro)).Trim()
if (-not $chave.StartsWith("sk-")) { Write-Host "Chave inválida (tem que começar com sk-)." -ForegroundColor Red; Read-Host "Enter"; exit 1 }

$MODELO = "cw/claude-sonnet-5-5"

Write-Host "`nTestando $SERVIDOR ..."
try {
    $corpo = @{ model = $MODELO; max_tokens = 20; messages = @(@{ role = "user"; content = "Responda so: ok" }) } | ConvertTo-Json -Depth 5
    $r = Invoke-RestMethod -Uri "$SERVIDOR/v1/messages" -Method Post -Body $corpo -ContentType "application/json" `
        -Headers @{ "x-api-key" = $chave; "anthropic-version" = "2023-06-01" } -TimeoutSec 120
    Write-Host ("Servidor OK: " + (($r.content | Where-Object { $_.type -eq "text" } | Select-Object -First 1).text)) -ForegroundColor Green
} catch { Write-Host "Servidor não respondeu ($($_.Exception.Message)). Sigo instalando." -ForegroundColor Yellow }

function Ler-Json($arq) {
    if (-not (Test-Path $arq)) { return [pscustomobject]@{} }
    $txt = Get-Content $arq -Raw -Encoding UTF8
    if (-not $txt.Trim()) { return [pscustomobject]@{} }
    $sem = ($txt -split "`n" | ForEach-Object { $_ -replace '^\s*//.*$', '' }) -join "`n"
    return $sem | ConvertFrom-Json
}
function Gravar-Json($arq, $obj) {
    $dir = Split-Path $arq
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force $dir | Out-Null }
    if (Test-Path $arq) { Copy-Item $arq "$arq.bak-sonnet" -Force }
    [System.IO.File]::WriteAllText($arq, ($obj | ConvertTo-Json -Depth 20), (New-Object System.Text.UTF8Encoding($false)))
}
function Por($obj, $nome, $valor) {
    if ($obj.PSObject.Properties[$nome]) { $obj.$nome = $valor } else { $obj | Add-Member -NotePropertyName $nome -NotePropertyValue $valor }
}

$vscode = Join-Path $env:APPDATA "Code\User\settings.json"
$s = Ler-Json $vscode
$vars = @(
    @{ name = "ANTHROPIC_BASE_URL"; value = $SERVIDOR },
    @{ name = "ANTHROPIC_API_KEY"; value = $chave },
    @{ name = "ANTHROPIC_AUTH_TOKEN"; value = $chave },
    @{ name = "ANTHROPIC_MODEL"; value = $MODELO },
    @{ name = "ANTHROPIC_DEFAULT_OPUS_MODEL"; value = $MODELO },
    @{ name = "ANTHROPIC_DEFAULT_SONNET_MODEL"; value = $MODELO },
    @{ name = "ANTHROPIC_DEFAULT_HAIKU_MODEL"; value = $MODELO },
    @{ name = "ANTHROPIC_SMALL_FAST_MODEL"; value = $MODELO }
)
$antigas = @()
if ($s.PSObject.Properties["claudeCode.environmentVariables"]) {
    $nomes = $vars | ForEach-Object { $_.name }
    $antigas = @($s."claudeCode.environmentVariables" | Where-Object { $nomes -notcontains $_.name })
}
Por $s "claudeCode.environmentVariables" (@($antigas) + $vars)
Gravar-Json $vscode $s
Write-Host "VS Code configurado: $vscode" -ForegroundColor Green

$pasta = if ($env:CLAUDE_CONFIG_DIR) { $env:CLAUDE_CONFIG_DIR } else { Join-Path $env:USERPROFILE ".claude" }
$cc = Join-Path $pasta "settings.json"
try { $c = Ler-Json $cc } catch { $c = [pscustomobject]@{} }
$opcoes = @(
    @{ model = $MODELO; label = "Sonnet 5.5 web"; description = "Contas gratuitas do claude.ai (rápido; sem imagem nativa)" }
)
Por $c "model" $MODELO
Por $c "modelPicker" ([pscustomobject]@{ options = $opcoes; replaceBuiltInOptions = $true })
Gravar-Json $cc $c
Write-Host "Seletor configurado: $cc" -ForegroundColor Green
Write-Host "`nPRONTO. Feche TODAS as janelas do VS Code e abra de novo. Backups: *.bak-sonnet" -ForegroundColor Cyan
Read-Host "`nEnter para fechar"
