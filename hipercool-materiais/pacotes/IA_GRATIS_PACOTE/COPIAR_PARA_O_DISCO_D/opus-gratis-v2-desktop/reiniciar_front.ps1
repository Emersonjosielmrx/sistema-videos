# Reinicia o genspark_http (:20165) do pc1 SEM cortar pedido em andamento (31/10, pc1).
# Espera não haver nenhuma conexão estabelecida na 20165, derruba o servidor e sobe de novo pelo og_manter.py.
# Use SEMPRE este script (pc1 ou o agente do desktop por ssh) em vez de matar/subir o servidor à mão.
#   powershell -NoProfile -File D:\opus-gratis-v2-desktop\reiniciar_front.ps1
$ErrorActionPreference = 'Stop'
$aqui = Split-Path -Parent $MyInvocation.MyCommand.Path
& python -m py_compile (Join-Path $aqui 'genspark_http.py')
if ($LASTEXITCODE -ne 0) { Write-Output 'genspark_http.py com erro de sintaxe: NAO reiniciei'; exit 1 }
for ($i = 1; $i -le 120; $i++) {
    $ocupado = @(Get-NetTCPConnection -LocalPort 20165 -State Established -ErrorAction SilentlyContinue).Count
    if ($ocupado -eq 0) {
        $pids = @(Get-NetTCPConnection -LocalPort 20165 -State Listen -ErrorAction SilentlyContinue).OwningProcess | Sort-Object -Unique
        foreach ($p in $pids) { Stop-Process -Id $p -Force -ErrorAction SilentlyContinue }
        Set-Location $aqui
        & python og_manter.py | Select-Object -Last 1
        Write-Output "reiniciado na volta $i (havia $($pids.Count) servidor(es) na porta)"
        exit 0
    }
    Start-Sleep -Seconds 3
}
Write-Output 'ocupado por 6 min: NAO reiniciei'
exit 2
