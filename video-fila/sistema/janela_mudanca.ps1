# D:\sistema\catalogo\janela_mudanca.ps1 - OBRA 26/11: janela completa e AUTONOMA da mudanca fisica (roda como tarefa
# JanelaMudanca, sem depender do chat). 1) pausa  2) move o que estiver livre, tenta de novo a cada 2 min conforme as
# postagens em andamento terminam  3) RELIGA TUDO no maximo as 17:30 (ou antes, se nada mais destravar). Log: mapa\mudanca.log
$ErrorActionPreference = 'SilentlyContinue'
$PY = 'C:\Users\Haylla\AppData\Local\Programs\Python\Python313\python.exe'
$LOG = 'D:\sistema\mapa\mudanca.log'
function L($m){ Add-Content -Encoding UTF8 $LOG ((Get-Date -f 'dd/MM HH:mm:ss') + ' ' + $m) }
$env:SISTEMA_USO = '0'
$limite = (Get-Date).Date.AddHours(17).AddMinutes(30)
L '===== JANELA DE MUDANCA: inicio'
try {
  & powershell -NoProfile -ExecutionPolicy Bypass -File D:\sistema\catalogo\pausa.ps1 -Pausar | Out-Null
  $semMudar = 0
  while((Get-Date) -lt $limite){
    $saida = & $PY -X utf8 D:\sistema\catalogo\mudar_para_sistema.py --aplicar 2>&1
    $saida | ?{ $_ -match 'MOVIDA|movidas:|presa:' } | %{ L ("  " + $_) }
    $mov = 0; $m = [regex]::Match(($saida -join "`n"), 'movidas: (\d+)'); if($m.Success){ $mov = [int]$m.Groups[1].Value }
    $presas = @($saida | ?{ $_ -match 'presa:' }).Count
    if($presas -eq 0){ L 'nada preso: fim'; break }
    $postando = @(Get-CimInstance Win32_Process | ?{ $_.CommandLine -match 'postar_|_poster\.py|youtube_web|postar_celular|postar_facebook|trocar_marca' }).Count
    if($mov -eq 0){ $semMudar++ } else { $semMudar = 0 }
    if($postando -eq 0 -and $semMudar -ge 2){ L "presas restantes sao de processo permanente (pontes/Chrome): fim ($presas)"; break }
    L "aguardando: $presas presas, $postando postagem(ns) em andamento"
    Start-Sleep 120
  }
} finally {
  & powershell -NoProfile -ExecutionPolicy Bypass -File D:\sistema\catalogo\pausa.ps1 -Retomar | Out-Null
  & $PY -X utf8 D:\sistema\catalogo\montar_pasta_unica.py 2>&1 | %{ L ("  montar: " + $_) }
  & $PY -X utf8 D:\sistema\catalogo\catalogo.py validar 2>&1 | select -last 1 | %{ L ("  catalogo: " + $_) }
  L '===== JANELA DE MUDANCA: fim (tudo religado)'
}
