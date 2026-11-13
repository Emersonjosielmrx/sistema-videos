# tiktok_desktop_local.ps1 — login do TikTok SOZINHO, rodando NA PRÓPRIA máquina (dona 26/10: "faça ele fazer os login
# sozinho como foi no PC2"; "mandando o script de uma vez fica muito mais rápido, isso deve ser padrão"). Sem instalar
# nada: fala com o Chrome pela porta de controle (CDP) via WebSocket do próprio PowerShell. 5 janelas; em cada uma clica
# "Continuar com Google", escolhe a conta no popup e "Continuar/Permitir" (cliques de mouse de verdade). Saiu do /login
# pro feed sem popup = logada: 30 s (cookies), fecha, abre a próxima. Captcha/código = fica 6 min na tela pra dona.
$contas = 'aulacomia;aulasrevolution;canalanimescomia;canalhistoriacomia;comoseriasecomia;e4487017;emersongenc;emersongencshin;emersonjosiel0;emersonjosiel1995;emersonjosiel2026;emersonjosiel2027;emersonjosiel2029;emersonjosiel2030;emersonjosiel2031;emersonjosiel2032;emersonjosiel2033;emersonjosiel649;emersonjosielmrx1995;empressinovare;en1653964;entrevistacomia;fabiovideoseducativos;fabricadeautomacoes0;filmescomia1;gabriellyvitoriaisabelaaraujo;gameoftroneskingsroadbrasil;inovarecap;inovaremanhwabr;inovaremanhwaverse;inovaremanhwaverse2;inovaremanhwaverseesp;inovaremanhwaversefrench;inovaremanhwaversehindi;inovaremanhwaverseind;inovaremanhwaverseing;inovaremanhwaverseita;inovaremanhwaverserussian;inovaremanhwaversethai;inovaremanhwaverseviet;inovaremultiatendimento;jogoscomia;jornalcomia;maiteanajessicajesus;mentoriaiapro;mundosolar1995;murilodoctor192;revolutionemerson1;revolutionemerson2;revolutionemerson3;rezaulkarimul355;seebotsia;simonerebecaluizasilva;solarmundo195;vendeafiliados3'.Split(';')
$base = 'C:\postador-worker'; $feitas = "$base\tiktok_feitas.txt"
$chrome = 'C:\Program Files\Google\Chrome\Application\chrome.exe'
$ja = @(); if (Test-Path $feitas) { $ja = Get-Content $feitas }
$fila = New-Object System.Collections.Queue
foreach ($c in $contas) { if ($ja -notcontains $c) { $fila.Enqueue($c) } }
$livres = New-Object System.Collections.ArrayList; 9461..9463 | ForEach-Object { [void]$livres.Add($_) }
$abertas = @{}; $k = 0
$log = "$base\tiktok_log.txt"
function Log($m) { $l = (Get-Date -Format 'dd/MM HH:mm:ss') + ' ' + $m; Write-Host $l; Add-Content $log $l }

function Cdp($ws, $cmds) {
  # manda os comandos em ordem numa conexão só e devolve as respostas (pula eventos)
  $c = New-Object System.Net.WebSockets.ClientWebSocket; $ct = [Threading.CancellationToken]::None; $res = @()
  try {
    if (-not $c.ConnectAsync([Uri]$ws, $ct).Wait(10000)) { return $res }
    $id = 0
    foreach ($m in $cmds) {
      $id++; $msg = @{ id = $id; method = $m[0]; params = $m[1] } | ConvertTo-Json -Depth 8 -Compress
      $b = [Text.Encoding]::UTF8.GetBytes($msg)
      [void]$c.SendAsync((New-Object ArraySegment[byte] (,$b)), 'Text', $true, $ct).Wait(10000)
      while ($true) {
        $buf = New-Object byte[] 262144; $txt = ''
        do { $t = $c.ReceiveAsync((New-Object ArraySegment[byte] (,$buf)), $ct); if (-not $t.Wait(20000)) { return $res }
             $txt += [Text.Encoding]::UTF8.GetString($buf, 0, $t.Result.Count) } while (-not $t.Result.EndOfMessage)
        $r = $txt | ConvertFrom-Json
        if ($r.id -eq $id) { $res += $r; break }
      }
    }
  } catch {} finally { try { [void]$c.CloseAsync('NormalClosure', '', $ct).Wait(2000) } catch {}; $c.Dispose() }
  return $res
}
function Clicar($ws, $js) {
  # $js devolve "x,y" do centro do alvo (ou ""): clique de mouse real ali
  $r = Cdp $ws @(,@('Runtime.evaluate', @{ expression = $js; returnByValue = $true }))
  $v = "$($r[0].result.result.value)"
  if ($v -notmatch '^(\d+(\.\d+)?),(\d+(\.\d+)?)$') { return $false }
  $x = [double]$Matches[1]; $y = [double]$Matches[3]
  [void](Cdp $ws @(@('Input.dispatchMouseEvent', @{ type = 'mouseMoved'; x = $x; y = $y }),
                   @('Input.dispatchMouseEvent', @{ type = 'mousePressed'; x = $x; y = $y; button = 'left'; clickCount = 1 }),
                   @('Input.dispatchMouseEvent', @{ type = 'mouseReleased'; x = $x; y = $y; button = 'left'; clickCount = 1 })))
  return $true
}
$JS_GOOGLE = @'
(() => { const els = [...document.querySelectorAll('div,button,a,span,p')].filter(e => /Continu\w* com (o )?Google|Continue with Google/i.test(e.textContent || '') && (e.textContent || '').length < 60);
  if (!els.length) return ''; const el = els.sort((a, b) => a.textContent.length - b.textContent.length)[0];
  el.scrollIntoView({block: 'center'}); const r = el.getBoundingClientRect(); return (r.width ? (r.x + r.width / 2) + ',' + (r.y + r.height / 2) : ''); })()
'@
function JsConta($email) { return @"
(() => { let el = [...document.querySelectorAll('[data-identifier]')].find(x => (x.getAttribute('data-identifier') || '').toLowerCase() === '$email');
  if (!el) el = [...document.querySelectorAll('button,div[role=button],span')].find(x => /^(Continuar|Continue|Permitir|Allow)$/i.test((x.innerText || '').trim()));
  if (!el) return ''; el.scrollIntoView({block: 'center'}); const r = el.getBoundingClientRect(); return (r.width ? (r.x + r.width / 2) + ',' + (r.y + r.height / 2) : ''); })()
"@ }
function Fechar($porta) {
  Get-CimInstance Win32_Process -Filter "name='chrome.exe'" | Where-Object { $_.CommandLine -like "*--remote-debugging-port=$porta *" -and $_.CommandLine -notlike '*--type=*' } |
    ForEach-Object { try { (Get-Process -Id $_.ProcessId).CloseMainWindow() | Out-Null } catch {} }
}
function Soltar($p, $porta) { [void]$livres.Add($porta); $abertas.Remove($p) }
function Js($ws, $expr) {
  $r = Cdp $ws @(,@('Runtime.evaluate', @{ expression = $expr; returnByValue = $true; awaitPromise = $true }))
  return "$($r[0].result.result.value)"
}
function JsTexto($rx) { return @"
(() => { const el = [...document.querySelectorAll('div,button,span,p,a,li')].filter(e => /$rx/i.test((e.innerText || '').trim()) && (e.innerText || '').length < 40)
  .sort((a, b) => a.innerText.length - b.innerText.length)[0];
  if (!el) return ''; el.scrollIntoView({block: 'center'}); const r = el.getBoundingClientRect(); return (r.width ? (r.x + r.width / 2) + ',' + (r.y + r.height / 2) : ''); })()
"@ }
$JS_VERIFICA = "/verifi(que se é|ca que és)|verify it'?s you|verifique sua identidade|verification code|código de verificação/i.test(document.body.innerText)"
$JS_CAMPO = @'
(() => { const i = [...document.querySelectorAll('input')].find(x => x.offsetParent && x.type !== 'hidden' && x.type !== 'checkbox');
  if (!i) return ''; i.scrollIntoView({block: 'center'}); i.focus(); const r = i.getBoundingClientRect(); return (r.x + r.width / 2) + ',' + (r.y + r.height / 2); })()
'@
function CodigoGmail($porta) {
  # 24/10 (PC2): o código do TikTok chega no Gmail do MESMO perfil — abre uma aba, lê a busca (ou o e-mail mais novo)
  $codigos = @()
  try {
    $aba = Invoke-RestMethod -Method Put "http://127.0.0.1:$porta/json/new?https://mail.google.com/mail/u/0/" -TimeoutSec 20
    Start-Sleep 8
    [void](Js $aba.webSocketDebuggerUrl "location.href = 'https://mail.google.com/mail/u/0/#search/from%3Atiktok+newer_than%3A1h'")
    for ($i = 0; $i -lt 8 -and -not $codigos.Count; $i++) {
      Start-Sleep 5
      $linhas = Js $aba.webSocketDebuggerUrl "[...document.querySelectorAll('tr.zA')].filter(r => r.offsetParent).slice(0, 5).map(r => r.innerText).join(' | ')"
      $codigos = @([regex]::Matches($linhas, '\b\d{6}\b') | ForEach-Object { $_.Value })
      if (-not $codigos.Count -and $linhas) {
        [void](Clicar $aba.webSocketDebuggerUrl "(() => { const r = [...document.querySelectorAll('tr.zA')].find(x => x.offsetParent); if (!r) return ''; const b = r.getBoundingClientRect(); return (b.x + b.width / 2) + ',' + (b.y + b.height / 2); })()")
        Start-Sleep 6
        $corpo = Js $aba.webSocketDebuggerUrl "[...document.querySelectorAll('div.a3s')].map(d => d.innerText).join(' ')"
        $codigos = @([regex]::Matches($corpo, '\b\d{6}\b') | ForEach-Object { $_.Value })
      }
    }
    Invoke-RestMethod "http://127.0.0.1:$porta/json/close/$($aba.id)" -TimeoutSec 10 | Out-Null
  } catch {}
  return $codigos
}

Log "$($fila.Count) contas pra logar no TikTok, 3 de cada vez (sozinho)"
while ($fila.Count -or $abertas.Count) {
  while ($livres.Count -and $fila.Count) {
    $p = $fila.Dequeue(); $porta = $livres[0]; $livres.RemoveAt(0)
    $x = 40 + 60 * ($k % 5); $y = 20 + 40 * ($k % 5); $k++
    Start-Process $chrome -ArgumentList "`"--user-data-dir=$base\perfis\$p`"", "--remote-debugging-port=$porta", '--remote-allow-origins=*', '--no-first-run', '--no-default-browser-check', '--disable-sync', '--mute-audio', '--window-size=1100,900', "--window-position=$x,$y", 'https://www.tiktok.com/login'
    $abertas[$p] = @{ porta = $porta; t = Get-Date; ok = $null; clique = [datetime]::MinValue; aviso = $false }; Log "ABRIU $p"; Start-Sleep 3
  }
  Start-Sleep 4
  foreach ($p in @($abertas.Keys)) {
    $a = $abertas[$p]; $idade = ((Get-Date) - $a.t).TotalSeconds
    $tabs = $null; try { $tabs = Invoke-RestMethod "http://127.0.0.1:$($a.porta)/json" -TimeoutSec 5 } catch {}
    if (-not $tabs) {
      if ($a.ok) { Add-Content $feitas $p; Soltar $p $a.porta; Log "LOGADA (janela fechou depois de entrar): $p"; continue }
      if ($idade -gt 180) { Log "FECHADA SEM LOGIN (Chrome não respondeu em 3 min): $p"; Add-Content "$base\tiktok_falhas.txt" $p; Soltar $p $a.porta }
      continue
    }
    $pags = @($tabs | Where-Object { $_.type -eq 'page' })
    $tt = @($pags | Where-Object { $_.url -like '*tiktok.com*' })
    $login = @($tt | Where-Object { $_.url -like '*tiktok.com/login*' })
    $google = @($pags | Where-Object { $_.url -like '*accounts.google.com*' })
    if ($tt.Count -and -not $login.Count -and -not $google.Count -and $idade -gt 15) {
      if (-not $a.ok) { $a.ok = Get-Date; Log "ENTROU: $p (fecho em 30 s)" }
      elseif (((Get-Date) - $a.ok).TotalSeconds -gt 30) { Fechar $a.porta; Add-Content $feitas $p; Soltar $p $a.porta; Log "LOGADA: $p" }
      continue
    }
    $a.ok = $null
    $verifica = $false
    if ($login.Count -and -not $google.Count) { $verifica = (Js $login[0].webSocketDebuggerUrl $JS_VERIFICA) -eq 'True' }
    if ($verifica) {
      # TikTok pediu o código: escolhe E-mail, pede o código, lê no Gmail do perfil e digita (como o robô do PC2)
      $ws = $login[0].webSocketDebuggerUrl
      if (-not $a.fase) {
        Log "PEDIU CODIGO: $p (vou ler no Gmail)"
        [void](Clicar $ws (JsTexto '^E-?mail$')); Start-Sleep 3
        [void](Clicar $ws (JsTexto '^(Enviar código|Enviar|Send code)$'))
        $a.fase = 1; $a.pediu = Get-Date; $a.usados = @()
      } elseif ($a.fase -eq 1 -and ((Get-Date) - $a.pediu).TotalSeconds -gt 20) {
        $cod = @(CodigoGmail $a.porta | Where-Object { $a.usados -notcontains $_ }) | Select-Object -First 1
        if ($cod) {
          if (Clicar $ws $JS_CAMPO) {
            [void](Cdp $ws @(,@('Input.insertText', @{ text = $cod }))); Start-Sleep 2
            [void](Clicar $ws (JsTexto '^(Verificar|Avançar|Next|Confirmar|Enviar)$'))
            $a.usados += $cod; Log "CODIGO DIGITADO: $p"
          }
        }
        $a.pediu = Get-Date  # próxima leitura em 20 s (código novo, se este não valeu)
      }
    }
    elseif ($google.Count) { [void](Clicar $google[0].webSocketDebuggerUrl (JsConta "$p@gmail.com")) }
    elseif ($login.Count -and $idade -gt 8 -and ((Get-Date) - $a.clique).TotalSeconds -gt 25) {
      if (Clicar $login[0].webSocketDebuggerUrl $JS_GOOGLE) { $a.clique = Get-Date }
    }
    if ($idade -gt 360 -and -not ($a.fase -and $idade -lt 720)) {
      if (-not $a.aviso) { $a.aviso = $true; Log ("PRECISA DE VOCE: $p (captcha/codigo na janela) - fecho em 4 min | abas: " + (($pags | ForEach-Object { $_.url.Substring(0, [Math]::Min(70, $_.url.Length)) }) -join " ; ")) }
      if ($idade -gt 600) { Fechar $a.porta; Add-Content "$base\tiktok_falhas.txt" $p; Soltar $p $a.porta; Log "DESISTI: $p" }
    }
  }
}
Log 'FIM: TikTok. Feitas em C:\postador-worker\tiktok_feitas.txt'
