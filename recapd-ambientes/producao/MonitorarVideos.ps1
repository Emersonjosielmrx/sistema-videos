# -*- coding: utf-8 -*-
# MonitorarVideos.ps1 - Monitora pastas de vídeo e processa automaticamente

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
    Add-Content -Path "$LOG_DIR\monitor.log" -Value $linha -Encoding UTF8
}

function Processar-CameraIsolada {
    param([string]$VideoPath)

    Write-Log "=== CAMERA ISOLADA: $VideoPath ==="

    $videoFile = Get-Item $VideoPath
    $pastaDestino = $videoFile.Directory.FullName
    $nomeBase = $videoFile.BaseName
    $videoSaida = Join-Path $pastaDestino "${nomeBase}_fullhd.mp4"

    # Já processado?
    if (Test-Path $videoSaida) {
        Write-Log "Já processado: $videoSaida"
        return $videoSaida
    }

    # Processa com crop/upscale
    Write-Log "Processando câmera isolada..."
    & $PYTHON "$BIN_DIR\processar_camera.py" $VideoPath $videoSaida 2>&1 | Write-Log

    if ($LASTEXITCODE -eq 0 -and (Test-Path $videoSaida)) {
        Write-Log "✓ Processado: $videoSaida"

        # Postagem/agendamento do vídeo processado
        # Detecta canal do nome do arquivo (padrão: CanalNome_titulo_id.mp4)
        $canal = $null
        if ($nomeBase -match '^(.+?)_[a-zA-Z0-9]{8,}$') {
            $canalSlug = $Matches[1]
            $canal = $canalSlug -replace '_', ' '
            Write-Log "Canal detectado (com ID): $canal"
        }
        elseif ($nomeBase -match '^([^_]+)_') {
            $canalSlug = $Matches[1]
            $canal = $canalSlug -replace '_', ' '
            Write-Log "Canal detectado (primeiro segmento): $canal"
        }

        if ($canal) {
            $titulo = $nomeBase -replace '^[^_]+_', '' -replace '_', ' '
            if ($titulo.Length -gt 80) {
                $titulo = $titulo.Substring(0, 80)
            }

            $descricao = "Vídeo com câmera isolada processado automaticamente. #shorts"
            $tags = "camera,fullhd,shorts"

            Write-Log "Postando/agendando vídeo processado..."
            try {
                $sucesso = Postar-Ou-Agendar `
                    -VideoPath $videoSaida `
                    -Canal $canal `
                    -Titulo $titulo `
                    -Descricao $descricao `
                    -Tags $tags

                if (-not $sucesso) {
                    Write-Log "⚠ Vídeo processado mas não foi postado (verificar canal)"
                }
            } catch {
                Write-Log "⚠ Vídeo processado mas erro ao postar: $_"
            }
        } else {
            Write-Log "⚠ Vídeo processado mas canal não detectado no nome do arquivo"
            Write-Log "  Formato esperado: CanalNome_titulo_id.mp4"
        }

        return $videoSaida
    } else {
        Write-Log "✗ Falha ao processar câmera (exit code $LASTEXITCODE)"
        return $null
    }
}

function Processar-CorteTematico {
    param([string]$VideoPath)

    Write-Log "=== CORTE TEMATICO: $VideoPath ==="

    $videoFile = Get-Item $VideoPath
    $pastaBase = $videoFile.Directory.FullName
    $nomeBase = $videoFile.BaseName

    # Cria pasta de trabalho
    $pastaTrabalho = Join-Path $pastaBase "${nomeBase}_processamento"
    if (-not (Test-Path $pastaTrabalho)) {
        New-Item -ItemType Directory -Path $pastaTrabalho -Force | Out-Null
    }

    # 1. Transcrição
    Write-Log "1/5 Transcrevendo áudio..."
    $transcricaoJson = Join-Path $pastaTrabalho "transcricao.json"
    $transcricaoOutput = & $PYTHON "$BIN_DIR\transcricao_video.py" $VideoPath "base" "pt" 2>&1

    if ($LASTEXITCODE -ne 0) {
        Write-Log "✗ Falha na transcrição (exit code $LASTEXITCODE)"
        Write-Log "  Saída: $transcricaoOutput"
        return
    }

    # Salva stdout como JSON
    $transcricaoOutput | Out-File -FilePath $transcricaoJson -Encoding UTF8

    if (-not (Test-Path $transcricaoJson)) {
        Write-Log "✗ Arquivo de transcrição não foi criado"
        return
    }
    Write-Log "✓ Transcrição concluída"

    # 2. Classificação de tema
    Write-Log "2/5 Classificando temas..."
    $temasJson = Join-Path $pastaTrabalho "temas.json"
    $temasOutput = & $PYTHON "$BIN_DIR\classificar_tema.py" $transcricaoJson 2>&1

    if ($LASTEXITCODE -ne 0) {
        Write-Log "✗ Falha na classificação (exit code $LASTEXITCODE)"
        Write-Log "  Saída: $temasOutput"
        return
    }

    $temasOutput | Out-File -FilePath $temasJson -Encoding UTF8

    if (-not (Test-Path $temasJson)) {
        Write-Log "✗ Arquivo de temas não foi criado"
        return
    }
    Write-Log "✓ Temas classificados"

    # 3. Segmentação
    Write-Log "3/5 Segmentando vídeo..."
    $segmentosJson = Join-Path $pastaTrabalho "segmentos.json"
    $segmentosOutput = & $PYTHON "$BIN_DIR\segmentar_video.py" $VideoPath $temasJson 2>&1

    if ($LASTEXITCODE -ne 0) {
        Write-Log "✗ Falha na segmentação (exit code $LASTEXITCODE)"
        Write-Log "  Saída: $segmentosOutput"
        return
    }

    $segmentosOutput | Out-File -FilePath $segmentosJson -Encoding UTF8

    if (-not (Test-Path $segmentosJson)) {
        Write-Log "✗ Arquivo de segmentos não foi criado"
        return
    }
    Write-Log "✓ Vídeo segmentado"

    # 4. Gerar shorts
    Write-Log "4/5 Gerando shorts..."
    $pastaShortsBase = Join-Path $pastaBase "shorts"
    & $PYTHON "$BIN_DIR\gerar_shorts.py" $VideoPath $segmentosJson $pastaShortsBase 2>&1 | Write-Log

    if ($LASTEXITCODE -ne 0) {
        Write-Log "✗ Falha ao gerar shorts (exit code $LASTEXITCODE)"
        return
    }
    Write-Log "✓ Shorts gerados"

    # 5. Postar/agendar
    Write-Log "5/5 Postando vídeos..."
    $shortsJson = Join-Path $pastaShortsBase "shorts_gerados.json"

    if (Test-Path $shortsJson) {
        $dados = Get-Content $shortsJson -Raw -Encoding UTF8 | ConvertFrom-Json

        foreach ($short in $dados.shorts) {
            $shortPath = $short.path
            $canal = $short.canal
            $categoria = $short.categoria

            if (-not $canal) {
                Write-Log "✗ Short sem canal definido: $shortPath"
                continue
            }

            Write-Log "Postando/agendando: $categoria -> $canal"

            # Posta ou agenda conforme status do canal
            $titulo = "Short $categoria - Tema do Dia"
            $descricao = "Conteúdo sobre $categoria. #shorts"
            $tags = "$categoria,shorts,viral"

            try {
                $sucesso = Postar-Ou-Agendar `
                    -VideoPath $shortPath `
                    -Canal $canal `
                    -Titulo $titulo `
                    -Descricao $descricao `
                    -Tags $tags

                if (-not $sucesso) {
                    Write-Log "✗ Falha ao processar: $shortPath"
                    Write-Log "  Canal: $canal (verifique se existe em youtube_canais.json)"
                }
            } catch {
                Write-Log "✗ Erro ao processar short: $_"
            }

            # Espera entre postagens
            Start-Sleep -Seconds 5
        }
    }

    Write-Log "=== PROCESSAMENTO COMPLETO ==="
}

function Verificar-PostagemHoje {
    param([string]$Canal)

    if (-not $Canal) {
        Write-Log "✗ Canal não especificado para verificação"
        return $false
    }

    # Chama script Python que verifica via YouTube Data API
    & $PYTHON "$BIN_DIR\verificar_postagem_canal.py" $Canal 2>&1 | Out-Null

    # Exit code 0 = já postou, 1 = não postou
    return ($LASTEXITCODE -eq 0)
}

function Calcular-ProximoHorario {
    param([int]$OffsetHoras = 2)

    # Chama script Python que calcula próximo horário em BRT
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

    # Verifica se já postou hoje
    $jaPostou = Verificar-PostagemHoje -Canal $Canal

    if ($jaPostou) {
        # Agendar para daqui a 2 horas
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
        # Postar imediatamente
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

# Monitoramento das pastas
Write-Log "Iniciando monitoramento de pastas..."
Write-Log "Pasta raiz: $PastaRaiz"

$pastaCameraIsolada = Join-Path $PastaRaiz "camera_isolada"
$pastaCorteTematico = Join-Path $PastaRaiz "corte_tematico"

# Cria pastas se não existem
@($pastaCameraIsolada, $pastaCorteTematico) | ForEach-Object {
    if (-not (Test-Path $_)) {
        New-Item -ItemType Directory -Path $_ -Force | Out-Null
        Write-Log "Pasta criada: $_"
    }
}

# FileSystemWatcher para camera_isolada
$watcherCamera = New-Object System.IO.FileSystemWatcher
$watcherCamera.Path = $pastaCameraIsolada
$watcherCamera.Filter = "*.mp4"
$watcherCamera.IncludeSubdirectories = $false
$watcherCamera.EnableRaisingEvents = $true

$actionCamera = {
    $path = $Event.SourceEventArgs.FullPath
    $name = $Event.SourceEventArgs.Name
    $changeType = $Event.SourceEventArgs.ChangeType

    if ($changeType -eq "Created") {
        Start-Sleep -Seconds 2  # Aguarda arquivo terminar de ser copiado

        Write-Log "Novo vídeo detectado (camera_isolada): $name"
        Processar-CameraIsolada -VideoPath $path
    }
}

Register-ObjectEvent -InputObject $watcherCamera -EventName Created -Action $actionCamera

# FileSystemWatcher para corte_tematico
$watcherCorte = New-Object System.IO.FileSystemWatcher
$watcherCorte.Path = $pastaCorteTematico
$watcherCorte.Filter = "*.mp4"
$watcherCorte.IncludeSubdirectories = $false
$watcherCorte.EnableRaisingEvents = $true

$actionCorte = {
    $path = $Event.SourceEventArgs.FullPath
    $name = $Event.SourceEventArgs.Name
    $changeType = $Event.SourceEventArgs.ChangeType

    if ($changeType -eq "Created") {
        Start-Sleep -Seconds 2

        Write-Log "Novo vídeo detectado (corte_tematico): $name"
        Processar-CorteTematico -VideoPath $path
    }
}

Register-ObjectEvent -InputObject $watcherCorte -EventName Created -Action $actionCorte

Write-Log "Monitoramento ativo. Pressione Ctrl+C para parar."
Write-Log "  - Camera isolada: $pastaCameraIsolada"
Write-Log "  - Corte temático: $pastaCorteTematico"

# Loop infinito
try {
    while ($true) {
        Start-Sleep -Seconds 60
    }
} finally {
    Write-Log "Encerrando monitoramento..."
    $watcherCamera.EnableRaisingEvents = $false
    $watcherCorte.EnableRaisingEvents = $false
    $watcherCamera.Dispose()
    $watcherCorte.Dispose()
}
