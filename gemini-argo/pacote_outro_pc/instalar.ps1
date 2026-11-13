# Instala o Argon (Gemini 4 Argon) e o Argon Pro no Claude Code do VS Code deste PC.
# Nao leva senha nem cookie: pede a chave do OmniRoute na hora. Faz backup de tudo que muda (*.bak-argon).
$ErrorActionPreference = "Stop"
$SERVIDOR = "http://157.173.207.22:20133"

Write-Host ""
Write-Host "=== Instalar Argon no VS Code ===" -ForegroundColor Cyan
Write-Host "Cole a chave do OmniRoute (comeca com sk-) e aperte Enter."
Write-Host "Onde achar no PC principal: Area de Trabalho > 'Claude VS Code - Trocar Modelo' > settings_1_*.json, linha ANTHROPIC_AUTH_TOKEN"
$chave = (Read-Host "Chave").Trim()
if (-not $chave.StartsWith("sk-")) { Write-Host "Chave invalida (tem que comecar com sk-)." -ForegroundColor Red; Read-Host "Enter para sair"; exit 1 }

# 1) teste rapido: o servidor responde com essa chave? (Gemini 3.8, segundos)
Write-Host "`nTestando o servidor..."
try {
    $corpo = @{ model = "agy/gemini-3.8-flash-high"; max_tokens = 20; messages = @(@{ role = "user"; content = "Responda so: ok" }) } | ConvertTo-Json -Depth 5
    $r = Invoke-RestMethod -Uri "$SERVIDOR/v1/messages" -Method Post -Body $corpo -ContentType "application/json" `
        -Headers @{ "x-api-key" = $chave; "anthropic-version" = "2023-06-01" } -TimeoutSec 120
    Write-Host ("Servidor OK: " + (($r.content | Where-Object { $_.type -eq "text" } | Select-Object -First 1).text)) -ForegroundColor Green
} catch {
    Write-Host "O servidor nao respondeu ($($_.Exception.Message)). Confira a chave e a internet. Sigo instalando assim mesmo." -ForegroundColor Yellow
}

function Ler-Json($arq) {
    if (-not (Test-Path $arq)) { return [pscustomobject]@{} }
    $txt = Get-Content $arq -Raw -Encoding UTF8
    if (-not $txt.Trim()) { return [pscustomobject]@{} }
    # o settings do VS Code aceita comentarios // que o ConvertFrom-Json nao entende
    $semComentario = ($txt -split "`n" | ForEach-Object { $_ -replace '^\s*//.*$', '' }) -join "`n"
    return $semComentario | ConvertFrom-Json
}

function Gravar-Json($arq, $obj) {
    $dir = Split-Path $arq
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force $dir | Out-Null }
    if (Test-Path $arq) { Copy-Item $arq "$arq.bak-argon" -Force }
    $json = $obj | ConvertTo-Json -Depth 20
    [System.IO.File]::WriteAllText($arq, $json, (New-Object System.Text.UTF8Encoding($false)))
}

function Por($obj, $nome, $valor) {
    if ($obj.PSObject.Properties[$nome]) { $obj.$nome = $valor } else { $obj | Add-Member -NotePropertyName $nome -NotePropertyValue $valor }
}

# 2) VS Code: variaveis da extensao Claude Code (servidor, chave e modelos padrao)
$vscode = Join-Path $env:APPDATA "Code\User\settings.json"
try { $s = Ler-Json $vscode } catch {
    Write-Host "Nao consegui ler $vscode (JSON com erro). Abra o arquivo, corrija e rode de novo." -ForegroundColor Red
    Read-Host "Enter para sair"; exit 1
}
$vars = @(
    @{ name = "ANTHROPIC_BASE_URL"; value = $SERVIDOR },
    @{ name = "ANTHROPIC_API_KEY"; value = $chave },
    @{ name = "ANTHROPIC_AUTH_TOKEN"; value = $chave },
    @{ name = "ANTHROPIC_MODEL"; value = "argon-pro" },
    @{ name = "ANTHROPIC_DEFAULT_OPUS_MODEL"; value = "argon-pro" },
    @{ name = "ANTHROPIC_DEFAULT_SONNET_MODEL"; value = "agy/gemini-3.8-flash-high" },
    @{ name = "ANTHROPIC_DEFAULT_HAIKU_MODEL"; value = "agy/gemini-3.8-flash-high" },
    @{ name = "ANTHROPIC_SMALL_FAST_MODEL"; value = "agy/gemini-3.8-flash-high" }
)
# mantem variaveis que ja existiam e nao sao destas
$antigas = @()
if ($s.PSObject.Properties["claudeCode.environmentVariables"]) {
    $nomes = $vars | ForEach-Object { $_.name }
    $antigas = @($s."claudeCode.environmentVariables" | Where-Object { $nomes -notcontains $_.name })
}
Por $s "claudeCode.environmentVariables" (@($antigas) + $vars)
Gravar-Json $vscode $s
Write-Host "VS Code configurado: $vscode" -ForegroundColor Green

# 3) Claude Code: seletor de modelos com o Argon Pro e o Argon puro
$pasta = if ($env:CLAUDE_CONFIG_DIR) { $env:CLAUDE_CONFIG_DIR } else { Join-Path $env:USERPROFILE ".claude" }
$cc = Join-Path $pasta "settings.json"
try { $c = Ler-Json $cc } catch { $c = [pscustomobject]@{} }
$opcoes = @(
    @{ model = "argon-pro"; label = "Argon Pro"; description = "Argon decide + Gemini 3.8 executa as ferramentas (melhor para codigo)" },
    @{ model = "gemini-4-argon"; label = "Argon"; description = "Gemini 4 Argon puro, raciocinio alto (melhor para texto: roteiro, analise)" },
    @{ model = "argon-gemini"; label = "Argon + Gemini 3.8"; description = "Argon faz tudo; Gemini 3.8 so socorre quando ele nao chama ferramenta" },
    @{ model = "agy/gemini-3.8-flash-high"; label = "Gemini 3.8"; description = "Gemini 3.8 Flash (rapido; reserva quando o Argon esta sem cota)" },
    @{ model = "antigravity/claude-opus-4-6-thinking"; label = "Opus 4.6"; description = "Opus 4.6 (Antigravity)" },
    @{ model = "cc/claude-opus-5-5"; label = "Opus 5.5"; description = "Opus 5.5 (conta paga)" }
)
Por $c "model" "argon-pro"
Por $c "modelPicker" ([pscustomobject]@{ options = $opcoes; replaceBuiltInOptions = $true })
Gravar-Json $cc $c
Write-Host "Seletor do Claude Code configurado: $cc" -ForegroundColor Green

Write-Host "`nPRONTO. Feche TODAS as janelas do VS Code e abra de novo." -ForegroundColor Cyan
Write-Host "No chat do Claude Code, o modelo ja comeca no 'Argon Pro'; troque pelo seletor ou com /model gemini-4-argon."
Write-Host "Backups do que mudou: arquivos .bak-argon ao lado de cada settings.json."
Read-Host "`nEnter para fechar"
