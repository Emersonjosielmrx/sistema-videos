# -*- coding: utf-8 -*-
# MonitorarTodasPastas.ps1 - Aplica auto-processamento a TODAS as pastas de videos_para_postar

param(
    [string]$PastaRaiz = "D:\recapd-ambientes\producao\fabrica-viral\videos_para_postar"
)

$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$PYTHON = "D:\recapd-ambientes\producao\venv\Scripts\python.exe"
$BIN_DIR = "D:\recapd-ambientes\producao\bin"

# Logs
$LOG_DIR = "D:\recapd-ambientes\producao\logs\monitoramento"
if (-not (Test-Path $LOG_DIR)) {
    New-Item -ItemType Directory -Path $LOG_DIR -Force | Out-Null
}

function Write-Log {
    param([string]$Mensagem)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $linha = "[$timestamp] $Mensagem"
    Write-Host $linha
    Add-Content -Path "$LOG_DIR\monitor_todas.log" -Value $linha -Encoding UTF8
}

function Verificar-PostagemHoje {
    param([string]$Canal)

    if (-not $Canal) {
        Write-Log "✗ Canal não especificado para verificação"
        return $false
    }

    & $PYTHON "$BIN_DIR\verificar_postagem_canal.py" $Canal 2>&1 | Out-Null
    return ($LASTEXITCODE -eq 0)
}

function Calcular-ProximoHorario {
    param([int]$OffsetHoras = 2)

    $rfc3339 = & $PYTHON "$BIN_DIR\calcular_proximo_horario.py" $OffsetHoras 2>&1 | Select-Object -Last 1
    return $rfc3339.Trim()
}

function Postar-Ou-Agendar {
    param(
        [string]$VideoPath,
        [string]$Canal,
        [string]$Titulo,
        [string]$Descricao,
        [string]$Tags
    )

    if (-not $Canal) {
        Write-Log "✗ Canal não especificado, pulando postagem"
        return $false
    }

    $jaPostou = Verificar-PostagemHoje -Canal $Canal

    if ($jaPostou) {
        Write-Log "Canal '$Canal' já postou hoje, agendando..."
        $publishAt = Calcular-ProximoHorario -OffsetHoras 2

        & $PYTHON "$BIN_DIR\youtube_poster.py" `
            --video $VideoPath `
            --titulo $Titulo `
            --descricao $Descricao `
            --tags $Tags `
            --canal $Canal `
            --publish-at $publishAt

        if ($LASTEXITCODE -eq 0) {
            Write-Log "✓ Agendado para: $publishAt"
            return $true
        } else {
            Write-Log "✗ Falha ao agendar"
            return $false
        }
    } else {
        Write-Log "Canal '$Canal' ainda não postou hoje, postando agora..."

        & $PYTHON "$BIN_DIR\youtube_poster.py" `
            --video $VideoPath `
            --titulo $Titulo `
            --descricao $Descricao `
            --tags $Tags `
            --canal $Canal

        if ($LASTEXITCODE -eq 0) {
            Write-Log "✓ Postado imediatamente"
            return $true
        } else {
            Write-Log "✗ Falha ao postar"
            return $false
        }
    }
}

function Processar-VideoPasta {
    param(
        [string]$VideoPath,
        [string]$NomePasta
    )

    Write-Log "=== PROCESSANDO: $NomePasta ==="
    Write-Log "Vídeo: $VideoPath"

    $videoFile = Get-Item $VideoPath
    $nomeBase = $videoFile.BaseName

    # Extrai canal do nome do arquivo (padrão: CanalNome_titulo_id.mp4 ou Canal_Nome_titulo_id.mp4)
    $canal = $null

    # Tenta capturar tudo até o último underscore antes de um provável ID (8+ chars alfanuméricos)
    if ($nomeBase -match '^(.+?)_[a-zA-Z0-9]{8,}$') {
        $canalSlug = $Matches[1]
        $canalNome = $canalSlug -replace '_', ' '
        Write-Log "Canal detectado (com ID): $canalNome"
        $canal = $canalNome
    }
    # Fallback: apenas primeiro segmento antes de underscore
    elseif ($nomeBase -match '^([^_]+)_') {
        $canalSlug = $Matches[1]
        $canalNome = $canalSlug -replace '_', ' '
        Write-Log "Canal detectado (primeiro segmento): $canalNome"
        $canal = $canalNome
    }

    if (-not $canal) {
        Write-Log "✗ Não foi possível detectar canal do nome do arquivo"
        Write-Log "  Formato esperado: CanalNome_titulo_id.mp4"
        Write-Log "  Ou: Canal_Nome_titulo_abc12345.mp4"
        return
    }

    # Valida se canal existe (tenta postar teste)
    Write-Log "Validando existência do canal '$canal'..."
    & $PYTHON "$BIN_DIR\youtube_poster.py" --listar-canais 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Log "✗ Erro ao validar canal (youtube_poster.py falhou)"
        return
    }

    # Título genérico baseado no nome do arquivo
    $titulo = $nomeBase -replace '^[^_]+_', '' -replace '_', ' '
    if ($titulo.Length -gt 80) {
        $titulo = $titulo.Substring(0, 80)
    }

    $descricao = "Conteúdo gerado automaticamente. #viral #shorts"
    $tags = "viral,shorts,ia"

    try {
        $sucesso = Postar-Ou-Agendar `
            -VideoPath $VideoPath `
            -Canal $canal `
            -Titulo $titulo `
            -Descricao $descricao `
            -Tags $tags

        if ($sucesso) {
            Write-Log "✓ Processado com sucesso: $VideoPath"
        } else {
            Write-Log "✗ Falha no processamento: $VideoPath"
            Write-Log "  Verifique se o canal '$canal' existe em youtube_canais.json"
        }
    } catch {
        Write-Log "✗ Erro durante processamento: $_"
    }
}

# Monitoramento das pastas existentes
Write-Log "=== INICIANDO MONITORAMENTO DE TODAS AS PASTAS ==="
Write-Log "Pasta raiz: $PastaRaiz"

# Pastas que já têm lógica específica (ignorar)
$pastasEspeciais = @("camera_isolada", "corte_tematico")

# Lista todas as pastas em videos_para_postar
$todasPastas = Get-ChildItem -Path $PastaRaiz -Directory | Where-Object {
    $_.Name -notin $pastasEspeciais
}

if ($todasPastas.Count -eq 0) {
    Write-Log "Nenhuma pasta adicional para monitorar (além das especiais)"
    exit 0
}

Write-Log "Pastas encontradas para monitoramento:"
foreach ($pasta in $todasPastas) {
    Write-Log "  - $($pasta.Name)"
}

# Cria watchers para cada pasta
$watchers = @()
$actions = @()

foreach ($pasta in $todasPastas) {
    $pastaPath = $pasta.FullName
    $pastaNome = $pasta.Name

    Write-Log "Configurando watcher para: $pastaNome"

    $watcher = New-Object System.IO.FileSystemWatcher
    $watcher.Path = $pastaPath
    $watcher.Filter = "*.mp4"
    $watcher.IncludeSubdirectories = $false
    $watcher.EnableRaisingEvents = $true

    $action = {
        $path = $Event.SourceEventArgs.FullPath
        $name = $Event.SourceEventArgs.Name
        $changeType = $Event.SourceEventArgs.ChangeType
        $pastaNome = $Event.MessageData

        if ($changeType -eq "Created") {
            Start-Sleep -Seconds 2  # Aguarda arquivo terminar de ser copiado

            Write-Log "Novo vídeo detectado em '$pastaNome': $name"
            Processar-VideoPasta -VideoPath $path -NomePasta $pastaNome
        }
    }

    $registration = Register-ObjectEvent `
        -InputObject $watcher `
        -EventName Created `
        -Action $action `
        -MessageData $pastaNome

    $watchers += $watcher
    $actions += $registration
}

Write-Log "Monitoramento ativo para $($watchers.Count) pastas"
Write-Log "Pressione Ctrl+C para parar"

# Loop infinito
try {
    while ($true) {
        Start-Sleep -Seconds 60
    }
} finally {
    Write-Log "Encerrando monitoramento..."
    foreach ($watcher in $watchers) {
        $watcher.EnableRaisingEvents = $false
        $watcher.Dispose()
    }
    foreach ($action in $actions) {
        Unregister-Event -SourceIdentifier $action.Name -ErrorAction SilentlyContinue
    }
}
