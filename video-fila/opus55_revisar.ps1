# opus55_revisar.ps1 — botão "Opus 5.5 REVISAR AGORA" (24/10, plano D:\video-fila\PLANO_OPUS55_CAMADAS.md, modo 1).
#   (sem parâmetro) = monta o dossiê das melhorias desde a última revisão e abre o Opus 5.5 (esforço máximo) nesta
#                     janela: ele revisa, mostra o relatório e fica esperando as perguntas da dona.
#   -Continuar      = volta pra última conversa de revisão (sem montar dossiê novo).
# Revisa e CORRIGE sozinho (pedido da dona 24/10), sem pedir permissão; guarda de comandos e backup de cada edição
# valem (a sessão é um pedido "chat" do painel: dá pra desfazer pelo painel). A chave vem do settings do VS Code
# (settings_5) na hora e só fica na memória deste processo.
param([switch]$Continuar)

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$Host.UI.RawUI.WindowTitle = 'Opus 5.5 — revisão das melhorias'
$py = 'D:\veo\venv\Scripts\python.exe'
$claude = 'D:\hipercool-videos\tools\claude\claude.exe'
$pasta = 'D:\video-fila\estado\opus55'
$settings = 'C:\Users\Haylla\Desktop\Claude VS Code - Trocar Modelo\settings_5_OPUS-5.5_NORMAL.json'

try {
    $cfg = Get-Content -Raw -Encoding UTF8 $settings | ConvertFrom-Json
    foreach ($v in $cfg.'claudeCode.environmentVariables') {
        if ($v.name -in @('ANTHROPIC_BASE_URL', 'ANTHROPIC_AUTH_TOKEN')) { Set-Item -Path "Env:$($v.name)" -Value $v.value }
    }
    Remove-Item Env:ANTHROPIC_API_KEY -ErrorAction SilentlyContinue
    $env:PYTHONUTF8 = '1'
    New-Item -ItemType Directory -Force $pasta | Out-Null
    Set-Location $pasta  # o --continue acha a conversa por esta pasta

    # 24/10 (dona): revisa E corrige sozinho, sem pedir permissão; a guarda e o backup (hooks do painel) valem
    $comum = @('--model', 'cc/claude-opus-5-5', '--effort', 'max', '--setting-sources', 'project,local',
               '--dangerously-skip-permissions')
    if ($Continuar) {
        $ult = Get-ChildItem $pasta -Filter '*_op55_hooks.json' | Sort-Object LastWriteTime | Select-Object -Last 1
        if ($ult) { $env:PAINEL_IA_JOB = $ult.Name -replace '_hooks\.json$', ''; $comum += @('--settings', $ult.FullName) }
        & $claude --continue @comum
        exit $LASTEXITCODE
    }
    Write-Host 'Montando o dossiê das melhorias desde a última revisão...'
    $saida = (& $py 'D:\video-fila\revisao_opus55.py' preparar | Select-Object -Last 1)
    $arq, $n, $tam, $jid, $hooks = $saida -split '\|'
    $env:PAINEL_IA_JOB = $jid
    $comum += @('--settings', $hooks)
    Write-Host "Dossiê: $arq ($n aplicação(ões)). Abrindo o Opus 5.5..."
    $prompt = "Leia o arquivo $arq inteiro (é o dossiê) e faça exatamente o que ele pede no começo: revise e corrija sozinho, sem me pedir permissão. Escreva em pt-BR simples. Depois do relatório, espere minhas perguntas."
    & $claude @comum $prompt
} catch {
    Write-Host "Não consegui abrir a revisão: $($_.Exception.Message)" -ForegroundColor Red
    Read-Host 'Enter pra fechar'
}
