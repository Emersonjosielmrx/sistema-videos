# rede_vigia.ps1 - vigia da placa de rede do PC2 (dona 23/10/2026: "a placa de rede dele as vezes para de funcionar,
# ai tem que ser desativada e ativada de novo; faca um script pra isso e coloque no PC2 pra que, ao ficar sem conexao,
# ele faca isso sozinho").
#
# Roda como SYSTEM pela tarefa agendada PC2_RedeVigia (no boot; o instalador e D:\video-fila\pc2\instalar_rede_vigia.ps1
# no PC1). A cada 10 min testa a internet; na 1a falha passa a testar de minuto em minuto e 3 falhas seguidas (~2 min) = desativa e reativa a placa Wi-Fi.
# Nao voltou: reconecta na rede Wi-Fi salva e repete com espera crescente (2, 5, 10 min...). Tudo vai pro
# C:\pc2-rede\rede_vigia.log e o estado pro C:\pc2-rede\estado.json; o PC1 (vigia_mutuo) le esse estado quando o PC2
# volta e conta no Telegram quantas vezes a placa foi reiniciada. O AVISO de PC2 fora do ar sai do PC1/notebooks
# (daqui, sem rede, nao tem como avisar).

$ErrorActionPreference = "Continue"
$Pasta = "C:\pc2-rede"
$Log = Join-Path $Pasta "rede_vigia.log"
$Estado = Join-Path $Pasta "estado.json"
$Placa = "Wi-Fi"
$Externos = @("1.1.1.1", "8.8.8.8", "208.67.222.222")
$IntervaloS = 600        # dona 23/10: "não precisa ser a cada 30 s, pode ser uns 10 min" - com a rede boa, confere a cada 10 min
$IntervaloFalhaS = 60    # depois da 1a falha confere de minuto em minuto (nao reinicia por um ping perdido)
$FalhasParaReiniciar = 3
$Esperas = @(0, 120, 300, 600)   # depois de cada reinicio que nao resolveu (o ultimo valor se repete)

New-Item -ItemType Directory -Force -Path $Pasta | Out-Null

# uma instancia so (a tarefa de boot e um "Executar agora" do instalador nao brigam pela placa)
$mutex = New-Object System.Threading.Mutex($false, "Global\PC2_RedeVigia")
if (-not $mutex.WaitOne(0)) { exit 0 }

function Escrever($msg) {
    $linha = "[{0}] {1}" -f (Get-Date -Format "dd/MM HH:mm:ss"), $msg
    Add-Content -Path $Log -Value $linha -Encoding UTF8
    # log nao cresce sem fim: passou de 2 MB, fica so a metade final
    if ((Get-Item $Log).Length -gt 2MB) {
        $l = Get-Content $Log -Encoding UTF8
        $l[([int]($l.Count / 2))..($l.Count - 1)] | Set-Content $Log -Encoding UTF8
    }
}

function Ler-Estado {
    try { return Get-Content $Estado -Raw -Encoding UTF8 | ConvertFrom-Json } catch { return $null }
}

function Gravar-Estado($e) {
    $e | ConvertTo-Json -Depth 4 | Set-Content -Path $Estado -Encoding UTF8
}

function Roteador {
    try { return (Get-NetRoute -DestinationPrefix "0.0.0.0/0" -ErrorAction Stop | Sort-Object RouteMetric | Select-Object -First 1).NextHop } catch { return $null }
}

function Tem-Internet {
    foreach ($h in $Externos) {
        if (Test-Connection -ComputerName $h -Count 1 -Quiet -ErrorAction SilentlyContinue) { return $true }
    }
    return $false
}

function Rede-Salva {
    # SSID da rede em que o Wi-Fi esta (guardado enquanto funciona, pra reconectar depois)
    $s = (netsh wlan show interfaces) | Select-String -Pattern "^\s*SSID\s*:\s*(.+)$" | Select-Object -First 1
    if ($s) { return $s.Matches[0].Groups[1].Value.Trim() }
    return $null
}

function Reiniciar-Placa($tentativa) {
    Escrever "SEM CONEXAO - reiniciando a placa '$Placa' (tentativa $tentativa)"
    try {
        Disable-NetAdapter -Name $Placa -Confirm:$false -ErrorAction Stop
        Start-Sleep -Seconds 6
        Enable-NetAdapter -Name $Placa -Confirm:$false -ErrorAction Stop
    } catch {
        # o WMI do PC2 tem classes quebradas (23/10: as de tarefa agendada davam "Classe invalida"): plano B pelo netsh
        Escrever "  Disable/Enable-NetAdapter falhou ($($_.Exception.Message)) - usando netsh"
        netsh interface set interface name="$Placa" admin=disabled | Out-Null
        Start-Sleep -Seconds 6
        netsh interface set interface name="$Placa" admin=enabled | Out-Null
    }
    if ($tentativa -ge 2 -and $script:Ssid) {
        Start-Sleep -Seconds 10
        Escrever "  reconectando na rede salva '$($script:Ssid)'"
        netsh wlan connect name="$($script:Ssid)" | Out-Null
    }
    # ate 75 s pro Wi-Fi associar e pegar IP
    for ($i = 0; $i -lt 15; $i++) {
        Start-Sleep -Seconds 5
        if (Tem-Internet) { return $true }
    }
    return $false
}

$script:Ssid = Rede-Salva
Escrever "vigia iniciado (placa '$Placa', rede '$($script:Ssid)', roteador $(Roteador))"
$falhas = 0
$tentativa = 0
$caiuEm = $null

while ($true) {
    if (Tem-Internet) {
        if ($caiuEm) {
            $min = [math]::Round(((Get-Date) - $caiuEm).TotalMinutes, 1)
            Escrever "CONEXAO VOLTOU depois de $min min ($tentativa reinicio(s) da placa)"
            $e = Ler-Estado
            $hist = @()
            if ($e -and $e.historico) { $hist = @($e.historico) }
            $hist += [pscustomobject]@{ caiu = $caiuEm.ToString("s"); voltou = (Get-Date).ToString("s"); minutos = $min; reinicios = $tentativa }
            if ($hist.Count -gt 50) { $hist = $hist[($hist.Count - 50)..($hist.Count - 1)] }
            Gravar-Estado ([pscustomobject]@{ situacao = "ok"; desde = (Get-Date).ToString("s"); historico = $hist })
        }
        $s = Rede-Salva
        if ($s) { $script:Ssid = $s }
        $falhas = 0; $tentativa = 0; $caiuEm = $null
        Start-Sleep -Seconds $IntervaloS
        continue
    }

    $falhas++
    if (-not $caiuEm) {
        $caiuEm = Get-Date
        Escrever "sem internet (roteador $(Roteador) $(if ((Roteador) -and (Test-Connection -ComputerName (Roteador) -Count 1 -Quiet -ErrorAction SilentlyContinue)) {'responde'} else {'NAO responde'}))"
    }
    if ($falhas -lt $FalhasParaReiniciar) { Start-Sleep -Seconds $IntervaloFalhaS; continue }

    $tentativa++
    $e = Ler-Estado
    $hist = @(); if ($e -and $e.historico) { $hist = @($e.historico) }
    Gravar-Estado ([pscustomobject]@{ situacao = "sem_conexao"; desde = $caiuEm.ToString("s"); reinicios = $tentativa; historico = $hist })
    if (Reiniciar-Placa $tentativa) {
        $falhas = 0
        continue   # o "voltou" e anotado na proxima volta do laco
    }
    $espera = $Esperas[[math]::Min($tentativa, $Esperas.Count - 1)]
    Escrever "  ainda sem conexao - proxima tentativa em $([math]::Round($espera / 60)) min"
    Start-Sleep -Seconds $espera
}
