# D:\sistema\catalogo\pausa.ps1 - OBRA: janela de mudanca. -Pausar / -Retomar. Estado em D:\sistema\mapa\pausa_tarefas.json
# Pausar: postagem geral OFF (controle.py), desliga TODAS as tarefas proprias ligadas (lista salva), encerra os processos
# que rodam DENTRO das pastas que vao mudar - EXCETO postagem em andamento (e sua arvore) e Chrome (perfis/cookies).
# Retomar: religa exatamente as tarefas da lista, postagem ON, dispara as tarefas que mantem processos vivos.
param([switch]$Pausar, [switch]$Retomar)
$ErrorActionPreference = 'SilentlyContinue'
$EST = 'D:\sistema\mapa\pausa_tarefas.json'; $LOG = 'D:\sistema\mapa\mudanca.log'
$PY = 'C:\Users\Haylla\AppData\Local\Programs\Python\Python313\python.exe'
function L($m){ $t = (Get-Date -f 'dd/MM HH:mm:ss') + ' ' + $m; Add-Content -Encoding UTF8 $LOG $t; $t }
$env:SISTEMA_USO = '0'
if($Pausar){
  & $PY -X utf8 D:\video-fila\controle.py desligar tudo postagem "mudanca de pastas obra 26/11" | Out-Null
  L 'postagem geral DESLIGADA (controle.py tudo postagem)'
  $lig = @(Get-ScheduledTask | ?{ $_.TaskPath -notlike '\Microsoft*' -and $_.State -ne 'Disabled' -and $_.TaskName -notmatch '^(HP |IObit|MicrosoftEdge|GoogleUpdater|RunPlatform|Wise|AtualizarChrome)' } | %{ $_.TaskName })
  $lig | ConvertTo-Json | Set-Content -Encoding UTF8 $EST
  foreach($n in $lig){ Disable-ScheduledTask -TaskName $n | Out-Null }
  L ("tarefas desligadas: " + $lig.Count + " (lista em " + $EST + ")")
  $todos = Get-CimInstance Win32_Process
  $postando = @($todos | ?{ $_.CommandLine -match 'postar_|_poster\.py|youtube_web|postar_celular|postar_facebook|trocar_marca|etapa\.py|ponte_proxy_fixo|proxy_tiktok|proxy_celular|gemini_http_proxy|genspark_http|ponte\.mjs|tunel_' } | %{ $_.ProcessId })
  # arvore da postagem (filhos e netos) fica intocada
  $prot = New-Object 'System.Collections.Generic.HashSet[int]'; foreach($x in $postando){ [void]$prot.Add([int]$x) }
  for($k=0;$k -lt 4;$k++){ foreach($x in $todos){ if($prot.Contains([int]$x.ParentProcessId)){ [void]$prot.Add([int]$x.ProcessId) } } }
  foreach($x in $todos){ if($prot.Contains([int]$x.ProcessId)){ $pp=[int]$x.ParentProcessId; $pai=$todos | ?{ $_.ProcessId -eq $pp }; if($pai -and $pai.Name -match 'python|cmd|wscript'){ [void]$prot.Add($pp) } } }
  $pastas = (Get-Content -Raw D:\sistema\mapa\mudanca_alvos.txt) -split "`r?`n" | ?{ $_ }
  $mortos = 0
  foreach($x in $todos){
    if($prot.Contains([int]$x.ProcessId) -or $x.Name -match '^(chrome|sshd|ssh|conhost|powershell|explorer|Code)\.exe$' -or $x.ProcessId -eq $PID){ continue }
    $c = ("$($x.CommandLine) $($x.ExecutablePath)").ToLower()
    foreach($a in $pastas){ if($c.Contains($a.ToLower())){ Stop-Process -Id $x.ProcessId -Force; $mortos++; break } }
  }
  L ("processos encerrados: $mortos | postagem em andamento preservada: " + $postando.Count)
}
if($Retomar){
  $lig = Get-Content -Raw $EST | ConvertFrom-Json
  foreach($n in $lig){ Enable-ScheduledTask -TaskName $n | Out-Null }
  L ("tarefas religadas: " + @($lig).Count)
  & $PY -X utf8 D:\video-fila\controle.py ligar tudo postagem | Out-Null
  L 'postagem geral LIGADA'
  foreach($n in 'CelularesEncher','PainelVideos','PainelTunel','MedidorPC1','ArgonManter','OpusGratisManter','ClinePonte','ProxyCelular','VigilanciaSistema','BuscasOLX','GuardaEstado','RondaCaoGuarda'){ Start-ScheduledTask -TaskName $n }
  L 'tarefas que mantem processos vivos disparadas'
}
