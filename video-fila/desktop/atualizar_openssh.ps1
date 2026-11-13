# atualizar_openssh.ps1 - roda NO desktop (Emerson), solto da sessao ssh: o instalador para o sshd e derruba a conexao.
# Dono 23/10: "winget install Microsoft.OpenSSH.Preview" porque o sshd 7.7 (embutido) derrubava a conexao no login.
# Ordem: winget -> se nao instalou, MSI direto do GitHub -> se o servico sshd embutido atrapalha (1923), troca o
# servico e tenta de novo -> no fim o sshd SEMPRE volta ligado (novo ou o antigo), senao ninguem entra mais.
$ErrorActionPreference = 'Continue'
$log = 'C:\ProgramData\ssh\atualizar_openssh.log'
$novo = 'C:\Program Files\OpenSSH\sshd.exe'
$velho = 'C:\Windows\System32\OpenSSH\sshd.exe'
function L($m) { "$(Get-Date -Format 'dd/MM HH:mm:ss') $m" | Out-File $log -Append -Encoding utf8 }
function Caminho { (Get-CimInstance Win32_Service -Filter "Name='sshd'" -ErrorAction SilentlyContinue).PathName }
function Versao($exe) { if (Test-Path $exe) { ((& $exe -V 2>&1) | Out-String).Trim() } else { 'nao existe' } }

L '--- inicio'
L "antes: servico=$(Caminho) | embutido=$(Versao $velho) | novo=$(Versao $novo) | processos sshd=$(@(Get-Process sshd -ErrorAction SilentlyContinue).Count)"
try {
    Get-WinEvent -LogName 'OpenSSH/Operational' -MaxEvents 12 -ErrorAction Stop |
        ForEach-Object { L ("evento " + $_.TimeCreated.ToString('dd/MM HH:mm:ss') + ' ' + ($_.Message -replace '\s+', ' ')) }
} catch { L "sem eventos OpenSSH: $($_.Exception.Message)" }

# 1) winget (o pedido do dono)
$wg = Get-Command winget -ErrorAction SilentlyContinue
if (-not $wg) {
    $wg = Get-ChildItem 'C:\Program Files\WindowsApps\Microsoft.DesktopAppInstaller_*_x64__8wekyb3d8bbwe\winget.exe' -ErrorAction SilentlyContinue |
        Sort-Object FullName -Descending | Select-Object -First 1
}
if ($wg) {
    $exe = if ($wg.Source) { $wg.Source } else { $wg.FullName }
    L "winget: $exe"
    $out = & $exe install --id Microsoft.OpenSSH.Preview -e --silent --accept-package-agreements --accept-source-agreements --disable-interactivity 2>&1
    L ("winget saiu $LASTEXITCODE : " + (($out | Where-Object { "$_".Trim() -and "$_" -notmatch '^[\s\-\\|/]+$' } | Select-Object -Last 12) -join ' / '))
} else {
    L 'winget nao existe neste PC (LTSC sem App Installer)'
}

# 2) MSI direto, se o winget nao deixou o sshd novo instalado
function Msi($arq, $tag) {
    $mlog = "C:\ProgramData\ssh\openssh_msi_$tag.log"
    $p = Start-Process msiexec.exe -ArgumentList "/i `"$arq`" /qn /norestart /l*v `"$mlog`"" -Wait -PassThru
    L "msiexec ($tag) saiu $($p.ExitCode)"
    $erro1923 = (Test-Path $mlog) -and (Select-String -Path $mlog -Pattern 'Error 1923|Erro 1923' -Quiet)
    return @{ ok = ($p.ExitCode -in 0, 3010); s1923 = $erro1923 }
}
if (-not (Test-Path $novo)) {
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        $rels = Invoke-RestMethod 'https://api.github.com/repos/PowerShell/Win32-OpenSSH/releases?per_page=10' -UseBasicParsing
        $asset = $rels | ForEach-Object { $_.assets } | Where-Object { $_.name -match '^OpenSSH-Win64-v.*\.msi$' } | Select-Object -First 1
        $arq = Join-Path $env:TEMP $asset.name
        L "baixando $($asset.browser_download_url)"
        Invoke-WebRequest $asset.browser_download_url -OutFile $arq -UseBasicParsing
        $r = Msi $arq 'a'
        if (-not $r.ok -and $r.s1923) {
            L 'servico sshd embutido atrapalha (1923): removendo o servico (config/chaves em ProgramData ficam) e tentando de novo'
            Stop-Service sshd -Force -ErrorAction SilentlyContinue
            Stop-Service ssh-agent -Force -ErrorAction SilentlyContinue
            sc.exe delete sshd | Out-Null
            sc.exe delete ssh-agent | Out-Null
            Start-Sleep 3
            $r = Msi $arq 'b'
        }
    } catch { L "MSI falhou: $($_.Exception.Message)" }
}

# 3) sshd tem que voltar ligado, novo ou antigo
if (-not (Get-Service sshd -ErrorAction SilentlyContinue)) {
    L 'servico sshd sumiu: recriando o embutido pra nao perder o acesso'
    sc.exe create sshd binPath= "$velho" start= auto DisplayName= "OpenSSH SSH Server" | Out-Null
}
Set-Service sshd -StartupType Automatic -ErrorAction SilentlyContinue
Start-Service sshd -ErrorAction SilentlyContinue
Start-Sleep 3
if ((Get-Service sshd).Status -ne 'Running') {
    L 'sshd nao subiu: tentando de novo em 10 s'
    Start-Sleep 10
    Start-Service sshd -ErrorAction SilentlyContinue
}
L "depois: servico=$(Caminho) | status=$((Get-Service sshd -ErrorAction SilentlyContinue).Status) | novo=$(Versao $novo)"
L '--- fim'
