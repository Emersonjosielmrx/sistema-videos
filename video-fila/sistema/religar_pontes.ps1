$ErrorActionPreference='SilentlyContinue'
$salvo = Get-Content -Raw D:\sistema\mapa\pontes_salvas.json | ConvertFrom-Json
$vivos = @(Get-CimInstance Win32_Process | %{ "$($_.CommandLine)".Trim() })
$n=0; $f=@()
foreach($s in $salvo){
  $cmd = "$($s.cmd)".Trim()
  if($vivos -contains $cmd){ continue }
  $m = [regex]::Match($cmd, '^"?([^"]+?\.exe)"?\s+(.*)$')
  if(-not $m.Success){ $f += $cmd; continue }
  $exe = $m.Groups[1].Value; $arg = $m.Groups[2].Value
  $wd = if($cmd -match 'ponte\.mjs'){ 'D:\cline-ponte' } else { 'D:\' }
  Start-Process -FilePath $exe -ArgumentList $arg -WorkingDirectory $wd -WindowStyle Hidden
  $n++; Start-Sleep -Milliseconds 200
}
Start-Sleep 12
"iniciados: $n | sem parse: $($f.Count)"
'pontes vivas: ' + @(Get-CimInstance Win32_Process | ?{ $_.CommandLine -match 'ponte_proxy_fixo|gemini_http_proxy|genspark_http|tunel_painel|ponte\.mjs' }).Count
foreach($p in 18558,18569,18310,18316,18347,18383){ $r=& curl.exe -s -m 10 -x "http://127.0.0.1:$p" http://api.ipify.org; "  porta ${p}: $r" }
