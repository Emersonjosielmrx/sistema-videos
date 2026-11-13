<#
Sobe o kit vps-redroid numa VPS (acesso por chave SSH ja configurado) e testa.
Rode no PowerShell, dentro desta pasta:

  .\implantar.ps1 -Vps hermes-bloqueio                    copia o kit e o APK, diagnostico, kernel.
                                                          PARA se a VPS precisar reiniciar.
  .\implantar.ps1 -Vps hermes-bloqueio -Etapa reiniciar   SO depois do "pode reiniciar" da dona.
  .\implantar.ps1 -Vps hermes-bloqueio -Etapa android     Android + WhatsApp + testes (passo 8).
  .\implantar.ps1 -Vps hermes-bloqueio -Etapa testar      so os testes do passo 8 (gera tela.png).

Etapas soltas: copiar, diagnostico, kernel, reiniciar, android, testar. Padrao: ate-kernel.
Nunca pede senha: se a chave nao entrar, para e avisa.
#>
param(
  [Parameter(Mandatory = $true)][string]$Vps,
  [ValidateSet('ate-kernel', 'copiar', 'diagnostico', 'kernel', 'reiniciar', 'android', 'testar')]
  [string]$Etapa = 'ate-kernel'
)

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$kit = $PSScriptRoot
$remoto = '/opt/vps-redroid'
$apk = Join-Path (Split-Path $kit -Parent) 'apk\WhatsApp.apk'
$arquivos = 'LEIA.md', 'comum.sh', '0-diagnostico.sh', '1-preparar-kernel.sh', '2-instalar-android.sh',
            'manter-vivo.sh', 'docker-compose.yml', 'config.env'
$sshOpts = @('-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15')

function Titulo($t) { Write-Host ''; Write-Host "=== $t ===" -ForegroundColor Cyan }
function Falha($m) { Write-Host ''; Write-Host "ERRO: $m" -ForegroundColor Red; exit 1 }
function Remoto([string]$cmd) {
  # roda um comando na VPS e devolve a saida (stdout+stderr juntos); codigo em $script:rc
  $saida = ssh @sshOpts $Vps "$cmd 2>&1"
  $script:rc = $LASTEXITCODE
  return $saida
}

function PortaAdb {
  $p = 5555
  Get-Content (Join-Path $kit 'config.env') | ForEach-Object { if ($_ -match '^ADB_PORT=(\d+)') { $p = [int]$Matches[1] } }
  return $p
}

function Etapa-Acesso {
  Titulo "acesso a $Vps (so chave)"
  $h = Remoto 'hostname; uptime'
  if ($rc -ne 0) { $h; Falha "nao consegui entrar em '$Vps' por chave. Nao tente senha: avise a dona." }
  $h
}

function Etapa-Copiar {
  Titulo 'fim de linha dos arquivos do kit'
  foreach ($f in $arquivos) {
    $b = [System.IO.File]::ReadAllBytes((Join-Path $kit $f))
    if ([Array]::IndexOf($b, [byte]13) -ge 0) { Falha "$f tem CRLF. Converta para LF antes de copiar." }
  }
  Write-Host 'OK: todos em LF'

  Titulo "copiando o kit para ${Vps}:$remoto"
  Remoto "mkdir -p $remoto" | Out-Null
  if ($rc -ne 0) { Falha "nao consegui criar $remoto na VPS" }
  $lista = $arquivos | ForEach-Object { Join-Path $kit $_ }
  scp -o BatchMode=yes -q $lista "${Vps}:$remoto/"
  if ($LASTEXITCODE -ne 0) { Falha 'scp do kit falhou (mensagem acima)' }
  Write-Host "OK: $($arquivos.Count) arquivos copiados"

  Titulo 'WhatsApp.apk'
  if (-not (Test-Path $apk)) { Falha "nao achei $apk" }
  $tam = (Get-Item $apk).Length
  $la = (Remoto "stat -c %s $remoto/WhatsApp.apk 2>/dev/null; true")
  if ("$la".Trim() -eq "$tam") {
    Write-Host "OK: WhatsApp.apk ja esta na VPS com o mesmo tamanho ($tam bytes)"
  } else {
    Write-Host "enviando WhatsApp.apk ($([math]::Round($tam / 1MB)) MB)..."
    scp -o BatchMode=yes -q $apk "${Vps}:$remoto/"
    if ($LASTEXITCODE -ne 0) { Falha 'scp do APK falhou (mensagem acima)' }
    Write-Host 'OK: APK enviado'
  }
}

function Etapa-Diagnostico {
  Titulo 'diagnostico (so leitura)'
  Remoto "bash $remoto/0-diagnostico.sh"
  if ($rc -ne 0) { Falha '0-diagnostico.sh nao rodou' }

  Titulo 'conferencias automaticas'
  $virt = "$(Remoto 'systemd-detect-virt; true')".Trim()
  if ($virt -match '^(lxc|lxc-libvirt|openvz|systemd-nspawn|docker|podman|wsl)$') {
    Falha "esta VPS e um conteiner ($virt): nao da para trocar o kernel. Precisa de VPS KVM."
  }
  Write-Host "OK: virtualizacao = $virt"

  $grub = "$(Remoto 'test -f /boot/grub/grub.cfg && echo sim || echo nao')".Trim()
  if ($grub -ne 'sim') { Falha 'nao existe /boot/grub/grub.cfg: o kernel e escolhido pelo provedor.' }
  Write-Host 'OK: /boot/grub/grub.cfg existe'

  $memMB = [int]"$(Remoto 'free -m | awk ''/^Mem:/{print $7}''')".Trim()
  $discoGB = [int]"$(Remoto 'df -BG --output=avail / | tail -1 | tr -dc 0-9')".Trim()
  Write-Host "memoria disponivel: $memMB MB   disco livre em /: $discoGB GB"
  if ($memMB -lt 2048) { Write-Host "AVISO: menos de 2 GB disponiveis. O Android usa ~1,5 GB; vai ficar apertado." -ForegroundColor Yellow }
  if ($discoGB -lt 6) { Falha "menos de 6 GB livres em /. Libere espaco antes." }

  $compose = "$(Remoto 'docker compose version >/dev/null 2>&1 && echo sim || echo nao')".Trim()
  if ($compose -ne 'sim') { Falha "falta o 'docker compose' na VPS (pacote docker-compose-plugin)." }
  Write-Host 'OK: docker compose presente'

  $porta = PortaAdb
  $uso = "$(Remoto "ss -ltn | grep -w ':$porta' ; true")".Trim()
  if ($uso) { Falha "a porta $porta ja esta em uso na VPS:`n$uso`nTroque ADB_PORT no config.env e PORTA_VPS no conectar.bat, e rode de novo." }
  Write-Host "OK: porta $porta livre"
}

function Etapa-Kernel {
  Titulo 'kernel com binder (1-preparar-kernel.sh)'
  $saida = Remoto "bash $remoto/1-preparar-kernel.sh"
  $saida | ForEach-Object { Write-Host $_ }
  if ($rc -ne 0) { Falha "1-preparar-kernel.sh falhou (codigo $rc). Mande a saida acima." }
  if ("$saida" -match 'OK: o kernel atual') {
    Write-Host ''
    Write-Host 'O kernel atual ja tem binder: NAO precisa reiniciar. Proximo: -Etapa android' -ForegroundColor Green
    return
  }
  Write-Host ''
  Write-Host 'A VPS PRECISA REINICIAR para usar o kernel novo.' -ForegroundColor Yellow
  Write-Host 'Pare aqui e peca o "pode reiniciar" da dona. Depois: -Etapa reiniciar' -ForegroundColor Yellow
}

function Etapa-Reiniciar {
  Titulo "reiniciando $Vps (com autorizacao da dona)"
  $antes = "$(Remoto 'uname -r')".Trim()
  Write-Host "kernel antes: $antes"
  ssh @sshOpts $Vps 'reboot' 2>$null
  $inicio = Get-Date
  Write-Host 'esperando a VPS voltar (tento a cada 30 s, ate 10 min)...'
  Start-Sleep -Seconds 30
  $k = ''
  while (((Get-Date) - $inicio).TotalMinutes -lt 10) {
    $k = "$(ssh -o BatchMode=yes -o ConnectTimeout=10 $Vps 'uname -r' 2>$null)".Trim()
    if ($LASTEXITCODE -eq 0 -and $k) { break }
    $k = ''
    Start-Sleep -Seconds 30
  }
  if (-not $k) { Falha 'a VPS nao voltou em 10 min. Force o reinicio pelo painel do provedor: ela volta sozinha ao kernel antigo.' }
  Write-Host "voltou em $([int]((Get-Date) - $inicio).TotalSeconds) s com o kernel: $k"
  if ($k -match 'cloud') { Falha "ligou com o kernel 'cloud' ($k), que nao tem binder. Confira o GRUB (grub-reboot) e rode 1-preparar-kernel.sh de novo." }
  if ($k -eq $antes) { Falha "ligou com o mesmo kernel de antes ($k)." }
  Write-Host 'OK: kernel sem "cloud"' -ForegroundColor Green

  Titulo 'servicos que nao subiram (systemctl --failed)'
  $f = Remoto 'systemctl --failed --no-legend --plain'
  if ("$f".Trim()) { $f; Write-Host 'AVISO: ha servicos em falha. Avise a dona antes de seguir.' -ForegroundColor Yellow } else { Write-Host 'nenhum' }
}

function Etapa-Android {
  Titulo 'Android + WhatsApp (2-instalar-android.sh)'
  $saida = Remoto "bash $remoto/2-instalar-android.sh"
  $saida
  if ($rc -ne 0) { Falha "2-instalar-android.sh falhou (codigo $rc). Mande a saida acima." }
}

function Etapa-Testar {
  $porta = PortaAdb
  $serial = "127.0.0.1:$porta"
  $falhas = 0
  Titulo "testes do passo 8 (adb -s $serial)"

  Remoto "adb connect $serial" | Out-Null
  $boot = "$(Remoto "adb -s $serial shell getprop sys.boot_completed")".Trim()
  if ($boot -eq '1') { Write-Host 'PASSOU: sys.boot_completed = 1' } else { Write-Host "FALHOU: sys.boot_completed = '$boot'" -ForegroundColor Red; $falhas++ }

  $pm = "$(Remoto "adb -s $serial shell pm path com.whatsapp")".Trim()
  if ($pm -match '^package:') { Write-Host "PASSOU: $pm" } else { Write-Host "FALHOU: pm path com.whatsapp -> '$pm'" -ForegroundColor Red; $falhas++ }

  $tela = Join-Path $kit 'tela.png'
  Remoto "adb -s $serial exec-out screencap -p > /tmp/tela.png && ls -l /tmp/tela.png" | Out-Null
  scp -o BatchMode=yes -q "${Vps}:/tmp/tela.png" $tela
  if ($LASTEXITCODE -eq 0 -and (Test-Path $tela) -and (Get-Item $tela).Length -gt 1000) {
    Write-Host "PASSOU: tela salva em $tela ($((Get-Item $tela).Length) bytes). Abra e confira se mostra o WhatsApp."
  } else { Write-Host 'FALHOU: nao consegui trazer a tela (tela.png)' -ForegroundColor Red; $falhas++ }

  Titulo 'manutencao agendada'
  Remoto 'systemctl list-timers redroid-manter-vivo.timer --no-pager'
  Titulo 'memoria e consumo do conteiner'
  Remoto 'free -h; docker stats --no-stream redroid'

  Write-Host ''
  if ($falhas -eq 0) { Write-Host 'TUDO PASSOU. Agora: conectar.bat no PC para ver a tela e cadastrar o numero.' -ForegroundColor Green }
  else { Falha "$falhas teste(s) falharam. Veja acima; para investigar: docker logs --tail 80 redroid" }
}

Etapa-Acesso
switch ($Etapa) {
  'copiar'      { Etapa-Copiar }
  'diagnostico' { Etapa-Diagnostico }
  'kernel'      { Etapa-Kernel }
  'reiniciar'   { Etapa-Reiniciar }
  'android'     { Etapa-Android; Etapa-Testar }
  'testar'      { Etapa-Testar }
  'ate-kernel'  { Etapa-Copiar; Etapa-Diagnostico; Etapa-Kernel }
}
