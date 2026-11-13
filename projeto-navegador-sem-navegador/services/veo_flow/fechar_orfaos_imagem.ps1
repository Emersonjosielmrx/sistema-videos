# Fecha os Chromes de IMAGEM do caminho antigo (portas 9470-9479 do chrome_conta) que ficaram sem dono
# (pedido interrompido do lado do PC1). Nao mexe na 9460 (Veo/postagem), nas 9461-9469 (TikTok) nem nas 9480+ (fabrica).
$py = "C:\postador-worker\nsn\venv\Scripts\python.exe"
foreach ($p in 9470..9479) {
    $ocup = "C:\postador-worker\ocupado_$p"
    $vivo = netstat -ano -p TCP | Select-String ":$p .*LISTENING"
    if ($vivo) {
        $idade = if (Test-Path $ocup) { ((Get-Date) - (Get-Item $ocup).LastWriteTime).TotalMinutes } else { 999 }
        if ($idade -gt 15) { & $py C:\postador-worker\chrome_conta.py fechar $p | Out-Null; "fechei $p (aberto ha $([int]$idade) min)" }
        else { "$p em uso ha $([int]$idade) min - deixei" }
    }
}
