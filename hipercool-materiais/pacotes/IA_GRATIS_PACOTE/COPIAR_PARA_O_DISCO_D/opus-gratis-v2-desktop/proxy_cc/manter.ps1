# manter.ps1 (31/10/2026, v2) — sobe o que estiver fora: ponte genspark_http.py (:20165) e proxy_genspark.mjs (:20166).
# Roda pela tarefa agendada GensparkProxyManter (ao entrar e a cada 5 min) e pelo trocar.ps1 genspark.
# Não reinicia o que já está escutando (pedido em andamento não cai).
$ErrorActionPreference = 'SilentlyContinue'
$pasta = 'D:\opus-gratis-v2-desktop\proxy_cc'
$log = Join-Path $pasta 'manter.log'
function Escutando($porta) { [bool](Get-NetTCPConnection -LocalPort $porta -State Listen -ErrorAction SilentlyContinue) }
function Anotar($t) { Add-Content -Path $log -Value "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $t" -Encoding UTF8 }

if (-not (Escutando 20165)) {
  $env:GENSPARK_PORTA = '20165'; $env:GENSPARK_VAGAS = '2'; Remove-Item Env:GENSPARK_DEBUG
  Start-Process python -ArgumentList '-X','utf8','D:\opus-gratis-v2-desktop\genspark_http.py' -WorkingDirectory 'D:\opus-gratis-v2-desktop' -WindowStyle Hidden `
    -RedirectStandardOutput (Join-Path $pasta 'ponte.out.log') -RedirectStandardError (Join-Path $pasta 'ponte.err.log')
  Anotar 'ponte :20165 estava fora -> subi'
}
if (-not (Escutando 20166)) {
  Start-Process node -ArgumentList (Join-Path $pasta 'proxy_genspark.mjs') -WorkingDirectory $pasta -WindowStyle Hidden `
    -RedirectStandardOutput (Join-Path $pasta 'proxy.out.log') -RedirectStandardError (Join-Path $pasta 'proxy.err.log')
  Anotar 'proxy :20166 estava fora -> subi'
}


