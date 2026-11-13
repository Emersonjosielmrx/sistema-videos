# Liga o Claude Code (VS Code) DESTE PC no seu servidor (proxy :20133 da VPS) com TODOS os modelos grátis:
# Argon, Argon Pro, Sonnet web, Opus Genspark, Cline Opus e Gemini 3.8.
# Não leva senha: pede o endereço do servidor e a chave na hora. Faz backup de tudo que muda (*.bak-ia).
# Rodar:  clique com o direito > "Executar com o PowerShell"   (ou: powershell -ExecutionPolicy Bypass -File instalar_todos_modelos.ps1)
$ErrorActionPreference = "Stop"

Write-Host "`n=== Modelos grátis no Claude Code do VS Code ===" -ForegroundColor Cyan
$ip = (Read-Host "IP ou nome da sua VPS (ex.: 203.0.113.10)").Trim()
$SERVIDOR = "http://${ip}:20133"
$chave = (Read-Host "Chave do OmniRoute (começa com sk-)").Trim()
if (-not $chave.StartsWith("sk-")) { Write-Host "Chave inválida (tem que começar com sk-)." -ForegroundColor Red; Read-Host "Enter"; exit 1 }

Write-Host "`nTestando $SERVIDOR ..."
try {
    $corpo = @{ model = "agy/gemini-3.8-flash-high"; max_tokens = 20; messages = @(@{ role = "user"; content = "Responda so: ok" }) } | ConvertTo-Json -Depth 5
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
    if (Test-Path $arq) { Copy-Item $arq "$arq.bak-ia" -Force }
    [System.IO.File]::WriteAllText($arq, ($obj | ConvertTo-Json -Depth 20), (New-Object System.Text.UTF8Encoding($false)))
}
function Por($obj, $nome, $valor) {
    if ($obj.PSObject.Properties[$nome]) { $obj.$nome = $valor } else { $obj | Add-Member -NotePropertyName $nome -NotePropertyValue $valor }
}

$PADRAO = "argon-pro"
$vscode = Join-Path $env:APPDATA "Code\User\settings.json"
$s = Ler-Json $vscode
$vars = @(
    @{ name = "ANTHROPIC_BASE_URL"; value = $SERVIDOR },
    @{ name = "ANTHROPIC_API_KEY"; value = $chave },
    @{ name = "ANTHROPIC_AUTH_TOKEN"; value = $chave },
    @{ name = "ANTHROPIC_MODEL"; value = $PADRAO },
    @{ name = "ANTHROPIC_DEFAULT_OPUS_MODEL"; value = $PADRAO },
    @{ name = "ANTHROPIC_DEFAULT_SONNET_MODEL"; value = "agy/gemini-3.8-flash-high" },
    @{ name = "ANTHROPIC_DEFAULT_HAIKU_MODEL"; value = "agy/gemini-3.8-flash-high" },
    @{ name = "ANTHROPIC_SMALL_FAST_MODEL"; value = "agy/gemini-3.8-flash-high" }
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
    @{ model = "argon-pro"; label = "Argon Pro"; description = "Argon decide + Gemini 3.8 executa ferramentas (código)" },
    @{ model = "gemini-4-argon"; label = "Argon"; description = "Gemini 4 Argon puro, raciocínio alto (texto/análise)" },
    @{ model = "cw/claude-sonnet-5-5"; label = "Sonnet 5.5 web"; description = "Contas grátis do claude.ai (rápido; sem imagem nativa)" },
    @{ model = "genspark-opus-5-5"; label = "Opus 5.5 Genspark"; description = "Pool Genspark (100 créditos/dia por conta)" },
    @{ model = "cline-opus-5-5"; label = "Cline Opus 5.5"; description = "Pela cline-ponte (créditos Cline ou chave Anthropic)" },
    @{ model = "agy/gemini-3.8-flash-high"; label = "Gemini 3.8"; description = "Rápido; reserva quando os outros estão sem cota" }
)
Por $c "model" $PADRAO
Por $c "modelPicker" ([pscustomobject]@{ options = $opcoes; replaceBuiltInOptions = $true })
Gravar-Json $cc $c
Write-Host "Seletor configurado: $cc" -ForegroundColor Green
Write-Host "`nPRONTO. Feche TODAS as janelas do VS Code e abra de novo. Backups: *.bak-ia" -ForegroundColor Cyan
Read-Host "`nEnter para fechar"
