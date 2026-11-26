$T = "D:\video-fila\memes_melhoria\teste\humor"
$py = (Get-Command python).Source
$a1 = "`"$T\teste_humor.py`" `"D:\hipercool-materiais\animes recap\na_nuvem\e2nIzNGXvmA_xtts_momo\roteiro.txt`" momo 100"
$a2 = "`"$T\teste_humor.py`" `"D:\hipercool-materiais\animes recap\na_nuvem\kxohroSbgS8_She_Cheated_On_Him_With_3_Other_Guys_But\roteiro.txt`" kkvirjao 250"
$p1 = Start-Process $py -ArgumentList $a1 -WindowStyle Hidden -PassThru -RedirectStandardOutput "$T\saida_momo.log" -RedirectStandardError "$T\erro_momo.log"
$p1.PriorityClass = 'BelowNormal'
$p2 = Start-Process $py -ArgumentList $a2 -WindowStyle Hidden -PassThru -RedirectStandardOutput "$T\saida_virjao.log" -RedirectStandardError "$T\erro_virjao.log"
$p2.PriorityClass = 'BelowNormal'
"pids $($p1.Id) $($p2.Id)"
