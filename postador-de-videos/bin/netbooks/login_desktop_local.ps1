# login_desktop_local.ps1 — login Google em lote RODANDO NO PRÓPRIO DESKTOP (26/10: o ssh do desktop cai depois do login,
# o PC1 não consegue comandar). Mesmo esquema do login_em_lote: 5 janelas, e-mail já no campo; chegou no YouTube =
# logada -> fecha e abre a próxima. Retoma de onde parou (C:\postador-worker\login_feitas.txt). Colar no PowerShell.
$contas = 'inovaremanhwaversethai|Inovaremanhwaversethai@gmail.com;inovaremanhwaverseviet|Inovaremanhwaverseviet@gmail.com;inovaremanhwaversehindi|Inovaremanhwaversehindi@gmail.com;inovaremanhwaverserussian|Inovaremanhwaverserussian@gmail.com;inovaremanhwaversefrench|Inovaremanhwaversefrench@gmail.com;inovaremanhwaverseita|Inovaremanhwaverseita@gmail.com;inovaremanhwaverseesp|inovaremanhwaverseesp@gmail.com;inovaremanhwaverseind|inovaremanhwaverseind@gmail.com;inovaremanhwaverseing|inovaremanhwaverseing@gmail.com;inovaremanhwaverse|inovaremanhwaverse@gmail.com;inovaremanhwabr|inovaremanhwabr@gmail.com;mentoriaiapro|mentoriaiapro@gmail.com;jogoscomia|jogoscomia@gmail.com;entrevistacomia|entrevistacomia@gmail.com;jornalcomia|jornalcomia@gmail.com;canalhistoriacomia|canalhistoriacomia@gmail.com;aulacomia|aulacomia@gmail.com;comoseriasecomia|comoseriasecomia@gmail.com;revolutionemerson1|revolutionemerson1@gmail.com;revolutionemerson2|revolutionemerson2@gmail.com;revolutionemerson3|revolutionemerson3@gmail.com;rezaulkarimul355|rezaulkarimul355@gmail.com;emersonjosiel2026|emersonjosiel2026@gmail.com;emersonjosiel2027|emersonjosiel2027@gmail.com;emersonjosiel2029|emersonjosiel2029@gmail.com;emersonjosiel2030|emersonjosiel2030@gmail.com;emersonjosiel2031|emersonjosiel2031@gmail.com;emersonjosiel2032|emersonjosiel2032@gmail.com;aulasrevolution|aulasrevolution@gmail.com;canalanimescomia|canalanimescomia@gmail.com;e4487017|e4487017@gmail.com;emersongenc|emersongenc@gmail.com;emersongencshin|emersongencshin@gmail.com;emersonjosiel0|emersonjosiel0@gmail.com;emersonjosiel1995|emersonjosiel1995@gmail.com;emersonjosiel2033|emersonjosiel2033@gmail.com;emersonjosiel649|emersonjosiel649@gmail.com;emersonjosielmrx1995|emersonjosielmrx1995@gmail.com;empressinovare|empressinovare@gmail.com;en1653964|en1653964@gmail.com;fabiovideoseducativos|fabiovideoseducativos@gmail.com;fabricadeautomacoes0|fabricadeautomacoes0@gmail.com;fabricadeautomacoesia|fabricadeautomacoesia@gmail.com;filmescomia1|filmescomia1@gmail.com;gabriellyvitoriaisabelaaraujo|gabriellyvitoriaisabelaaraujo@gmail.com;gameoftroneskingsroadbrasil|gameoftroneskingsroadbrasil@gmail.com;inovarecap|inovarecap@gmail.com;inovaremanhwaverse2|inovaremanhwaverse2@gmail.com;inovaremultiatendimento|inovaremultiatendimento@gmail.com;maiteanajessicajesus|maiteanajessicajesus@gmail.com;mundosolar1995|mundosolar1995@gmail.com;murilodoctor192|murilodoctor192@gmail.com;seebotsia|seebotsia@gmail.com;simonerebecaluizasilva|simonerebecaluizasilva@gmail.com;solarmundo195|solarmundo195@gmail.com;vendeafiliados3|vendeafiliados3@gmail.com'.Split(';')
$base = 'C:\postador-worker'; $feitas = "$base\login_feitas.txt"; New-Item -ItemType Directory -Force "$base\perfis" | Out-Null
$chrome = 'C:\Program Files\Google\Chrome\Application\chrome.exe'
$ja = @(); if (Test-Path $feitas) { $ja = Get-Content $feitas }
$fila = New-Object System.Collections.Queue
foreach ($c in $contas) { if ($ja -notcontains $c.Split('|')[0]) { $fila.Enqueue($c) } }
$abertas = @{}; $k = 0
Write-Host "$($fila.Count) contas pra logar, 5 de cada vez"
while ($fila.Count -or $abertas.Count) {
  while ($abertas.Count -lt 5 -and $fila.Count) {
    $p, $e = $fila.Dequeue().Split('|')
    $url = 'https://accounts.google.com/ServiceLogin?Email=' + [uri]::EscapeDataString($e) + '&continue=https%3A%2F%2Fwww.youtube.com%2F'
    $x = 40 + 60 * ($k % 5); $y = 20 + 40 * ($k % 5); $k++
    Start-Process $chrome -ArgumentList "`"--user-data-dir=$base\perfis\$p`"", '--no-first-run', '--no-default-browser-check', '--disable-sync', '--window-size=1000,800', "--window-position=$x,$y", "`"$url`""
    $abertas[$p] = Get-Date; Write-Host "ABRIU $e"; Start-Sleep 3
  }
  Start-Sleep 5
  $procs = Get-CimInstance Win32_Process -Filter "name='chrome.exe'" | Where-Object { $_.CommandLine -like '*postador-worker\perfis\*' -and $_.CommandLine -notlike '*--type=*' }
  foreach ($p in @($abertas.Keys)) {
    $pr = $procs | Where-Object { $_.CommandLine -like "*perfis\$p`"*" } | Select-Object -First 1
    if (-not $pr) {
      if (((Get-Date) - $abertas[$p]).TotalSeconds -gt 60) { Write-Host "FECHADA SEM LOGIN: $p"; Add-Content "$base\login_falhas.txt" $p; $abertas.Remove($p) }
      continue
    }
    if ((Get-Process -Id $pr.ProcessId -ErrorAction SilentlyContinue).MainWindowTitle -like '*YouTube*') {
      (Get-Process -Id $pr.ProcessId).CloseMainWindow() | Out-Null
      Add-Content $feitas $p; $abertas.Remove($p); Write-Host "LOGADA: $p"
    }
  }
}
Write-Host 'FIM: todas abertas. Feitas em C:\postador-worker\login_feitas.txt'
