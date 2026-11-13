# camada_opus_botao.ps1 — botão da dona pra 3ª camada (Opus juiz) das melhorias contínuas (24/10).
#   ON  = liga: apaga estado\opus_camada_DESLIGADA (não força nada; o gatilho do motor continua valendo)
#   OFF = desliga: o lote rodando para no próximo pedaço, os já decididos valem, nada é morto
# Atalho: powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File camada_opus_botao.ps1 ON|OFF
# -SemJanela (testes): escreve na tela em vez da janelinha. -Script: outro .py (testes com pasta temporária).
param(
    [Parameter(Mandatory = $true, Position = 0)][ValidateSet('ON', 'OFF')][string]$Modo,
    [switch]$SemJanela,
    [string]$Script = 'D:\video-fila\camada_opus.py'
)

$py = 'D:\veo\venv\Scripts\python.exe'
$acao = if ($Modo -eq 'ON') { 'ligar' } else { 'desligar' }
$titulo = 'Opus 3ª camada'

try {
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $py
    $psi.Arguments = "`"$Script`" $acao"
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.StandardOutputEncoding = [System.Text.Encoding]::UTF8
    $psi.StandardErrorEncoding = [System.Text.Encoding]::UTF8
    $psi.EnvironmentVariables['PYTHONIOENCODING'] = 'utf-8'
    $p = [System.Diagnostics.Process]::Start($psi)
    $saida = $p.StandardOutput.ReadToEnd()
    $erro = $p.StandardError.ReadToEnd()
    $p.WaitForExit()
    $codigo = $p.ExitCode
    $msg = $saida.Trim()
    if (-not $msg) { $msg = "Não veio resposta (código $codigo). $($erro.Trim())" }
} catch {
    $codigo = 1
    $msg = "Não consegui rodar o camada_opus.py: $($_.Exception.Message)"
}

if ($SemJanela) {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    Write-Output $msg
    exit $codigo
}

Add-Type -AssemblyName System.Windows.Forms
$icone = if ($codigo -eq 0) { [System.Windows.Forms.MessageBoxIcon]::Information } else { [System.Windows.Forms.MessageBoxIcon]::Warning }
[System.Windows.Forms.MessageBox]::Show($msg, $titulo, [System.Windows.Forms.MessageBoxButtons]::OK, $icone) | Out-Null
exit $codigo
