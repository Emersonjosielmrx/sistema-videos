param([switch]$Apagar)
$keep = 'final_anime_deitado.mp4','final_anime_deitado_ads.mp4','final_anime_short.mp4','roteiro.txt','_testes_usados.json'
$lim = (Get-Date).AddHours(-48); $tot = 0; $n = 0
foreach ($d in Get-ChildItem C:\recapd-e-animes\workspace\anime -Directory) {
  $novo = Get-ChildItem $d.FullName -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -gt $lim } | Select -First 1
  if ($novo) { continue }
  foreach ($i in Get-ChildItem $d.FullName -Force) {
    if ($keep -contains $i.Name) { continue }
    $s = if ($i.PSIsContainer) { (Get-ChildItem $i.FullName -Recurse -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum } else { $i.Length }
    $tot += $s; $n++
    if ($Apagar) { Remove-Item -LiteralPath $i.FullName -Recurse -Force -ErrorAction SilentlyContinue }
  }
}
'{0} itens, {1:N1} GB {2}' -f $n, ($tot/1GB), $(if ($Apagar) {'APAGADOS'} else {'(so medida)'})
'C livre: {0:N1} GB' -f ((Get-PSDrive C).Free/1GB)
