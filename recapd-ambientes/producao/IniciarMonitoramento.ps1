# -*- coding: utf-8 -*-
# IniciarMonitoramento.ps1 - Script principal que inicia todos os monitoramentos

param(
    [switch]$Background
)

$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "=== INICIANDO SISTEMA DE MONITORAMENTO DE VÍDEOS ===" -ForegroundColor Cyan
Write-Host ""

# Scripts de monitoramento
$scripts = @(
    @{
        Nome = "MonitorarVideos.ps1"
        Descricao = "Monitora pastas especiais (camera_isolada, corte_tematico)"
        Path = Join-Path $SCRIPT_DIR "MonitorarVideos.ps1"
    },
    @{
        Nome = "MonitorarTodasPastas.ps1"
        Descricao = "Monitora pastas gerais (com_minha_foto, baixados_agora, etc)"
        Path = Join-Path $SCRIPT_DIR "MonitorarTodasPastas.ps1"
    }
)

# Verifica se os scripts existem
foreach ($script in $scripts) {
    if (-not (Test-Path $script.Path)) {
        Write-Host "✗ Script não encontrado: $($script.Nome)" -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ $($script.Nome) - $($script.Descricao)" -ForegroundColor Green
}

Write-Host ""

if ($Background) {
    Write-Host "Iniciando em background (jobs)..." -ForegroundColor Yellow

    foreach ($script in $scripts) {
        $job = Start-Job -FilePath $script.Path -Name $script.Nome
        Write-Host "  Job iniciado: $($script.Nome) (ID: $($job.Id))" -ForegroundColor Cyan
    }

    Write-Host ""
    Write-Host "Para ver status dos jobs:" -ForegroundColor Yellow
    Write-Host "  Get-Job"
    Write-Host ""
    Write-Host "Para ver logs de um job:" -ForegroundColor Yellow
    Write-Host "  Receive-Job -Id <ID> -Keep"
    Write-Host ""
    Write-Host "Para parar todos os jobs:" -ForegroundColor Yellow
    Write-Host "  Get-Job | Stop-Job"
    Write-Host "  Get-Job | Remove-Job"

} else {
    Write-Host "Iniciando em foreground (múltiplas janelas)..." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Uma nova janela será aberta para cada script de monitoramento." -ForegroundColor Yellow
    Write-Host "Feche as janelas ou pressione Ctrl+C nelas para parar." -ForegroundColor Yellow
    Write-Host ""

    foreach ($script in $scripts) {
        $cmd = "powershell.exe -NoExit -ExecutionPolicy Bypass -File `"$($script.Path)`""
        Write-Host "  Abrindo janela para: $($script.Nome)" -ForegroundColor Cyan
        Start-Process powershell.exe -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", "`"$($script.Path)`""
        Start-Sleep -Seconds 1
    }

    Write-Host ""
    Write-Host "✓ Todos os monitoramentos foram iniciados em janelas separadas" -ForegroundColor Green
    Write-Host ""
    Write-Host "Logs disponíveis em:" -ForegroundColor Yellow
    Write-Host "  D:\recapd-ambientes\producao\logs\monitoramento\"
}
