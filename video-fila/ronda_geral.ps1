# D:\video-fila\ronda_geral.ps1  (copia mestre: /mnt/win-bootcamp/claude-central/ronda/ronda_geral.ps1)
# RONDA GERAL - SOMENTE LEITURA. Junta num resumo curto o estado de todos os projetos do PC1.
# Nao roda nenhum script de conta, nao apaga nada. Chamado pela Omarchy via ronda.sh.
# Doc: /mnt/win-bootcamp/claude-central/PAINEL_PROJETOS_ATIVOS.md
$ErrorActionPreference = 'SilentlyContinue'
[Console]::OutputEncoding = [Text.Encoding]::UTF8
$agora = Get-Date
"RONDA PC1 " + $agora.ToString('dd/MM HH:mm')

# 1) Saude da maquina
$d = Get-PSDrive D; $c = Get-PSDrive C
$os = Get-CimInstance Win32_OperatingSystem
$commit = [math]::Round(($os.TotalVirtualMemorySize - $os.FreeVirtualMemory)/1MB,1)
$ramLivre = [math]::Round($os.FreePhysicalMemory/1MB,1)
$cpu = (Get-CimInstance Win32_Processor | Measure-Object LoadPercentage -Average).Average
"[MAQUINA] D livre {0} GB | C livre {1} GB | RAM livre {2} GB | commit {3} GB | CPU {4}%" -f [math]::Round($d.Free/1GB,1),[math]::Round($c.Free/1GB,1),$ramLivre,$commit,$cpu
if ($d.Free -lt 5GB) { "  !! DISCO D QUASE CHEIO (preparo de celular para abaixo de 3 GB)" }
if ($c.Free -lt 5GB) { "  !! DISCO C QUASE CHEIO" }

# 2) Postagem
if (Test-Path 'D:\postador-de-videos\config\POSTAGEM_DESLIGADA.json') { "[POSTAGEM] !! DESLIGADA (existe POSTAGEM_DESLIGADA.json)" } else { "[POSTAGEM] ligada" }

# 3) Tarefas agendadas com erro real na ultima execucao
# ignorados: 0 ok | 0x41301 rodando | 0x41303 nunca rodou | 0x800710E0 pulou porque ja estava rodando
$ok = @(0, 267009, 267011, -2147020576, 2147946720)
$ruins = @()
# janelas de mudanca (inicio..fim+5min) lidas do log, para nao culpar tarefa encerrada pela pausa
$janelas = @()
$ini = $null
foreach ($ln in (Get-Content D:\sistema\mapa\mudanca.log -ErrorAction SilentlyContinue)) {
  if ($ln -match '^(\d\d/\d\d \d\d:\d\d:\d\d) .*(JANELA (MADRUGADA|DE MUDANCA): inicio)') { $ini = [datetime]::ParseExact($agora.Year.ToString() + '/' + $matches[1], 'yyyy/dd/MM HH:mm:ss', $null) }
  elseif ($ini -and $ln -match '^(\d\d/\d\d \d\d:\d\d:\d\d) .*(fim|encerrada)') { $janelas += ,@($ini.AddMinutes(-2), [datetime]::ParseExact($agora.Year.ToString() + '/' + $matches[1], 'yyyy/dd/MM HH:mm:ss', $null).AddMinutes(5)); $ini = $null }
}
foreach ($t in (Get-ScheduledTask | Where-Object { $_.TaskPath -notlike '\Microsoft*' -and $_.State -ne 'Disabled' })) {
  if ($t.TaskName -match '^(HP |IObit|Microsoft|Google|RunPlatform|Wise)') { continue }
  $i = Get-ScheduledTaskInfo -TaskName $t.TaskName -TaskPath $t.TaskPath
  if (-not $i.LastRunTime -or $i.LastRunTime.Year -lt 2000) { continue }
  if (($agora - $i.LastRunTime).TotalHours -gt 48) { continue }
  # 27/11: 0xFFFFFFFF/0x8007042B = encerrada a forca (janela de mudanca / desligamento do PC). Se a tarefa ainda tem
  # proxima execucao e foi morta dentro de uma janela registrada em D:\sistema\mapa\mudanca.log, nao e defeito dela.
  $forca = @(-1, 4294967295, -2147023829, 2147943467)
  if ($forca -contains $i.LastTaskResult -and $janelas | Where-Object { $i.LastRunTime -ge $_[0] -and $i.LastRunTime -le $_[1] }) { continue }
  if ($ok -notcontains $i.LastTaskResult) { $ruins += ("{0} (0x{1:X}, {2})" -f $t.TaskName, $i.LastTaskResult, $i.LastRunTime.ToString('dd HH:mm')) }
}
"[TAREFAS COM ERRO] {0}" -f $ruins.Count
$ruins | ForEach-Object { "  - $_" }

# 4) Lacos que precisam estar vivos (processos)
$procs = Get-CimInstance Win32_Process | Where-Object { $_.Name -match 'python' } | ForEach-Object { $_.CommandLine }
$vivos = [ordered]@{
  'Celulares laco (noite_encher laco)'        = 'noite_encher.py" laco$|noite_encher.py laco$'
  'Celulares postar (laco_postar)'            = 'laco_postar'
  'Celulares conferir (laco_conferir)'        = 'laco_conferir'
  'Painel de videos (painel_controlador)'     = 'painel_controlador.py'
  'Proxy TikTok'                              = 'proxy_tiktok.py'
  'Proxy Gemini (gemini_http_proxy)'          = 'gemini_http_proxy.py'
  'Genspark (opus-gratis)'                    = 'genspark_http.py'
  'Medidor PC1'                               = 'medidor_pc1.py'
}
$faltam = @()
foreach ($k in $vivos.Keys) { if (-not ($procs | Where-Object { $_ -match $vivos[$k] })) { $faltam += $k } }
if ($faltam.Count) { "[LACOS PARADOS] " + ($faltam -join ', ') } else { "[LACOS] todos vivos" }
$pontes = ($procs | Where-Object { $_ -match 'ponte_proxy_fixo' } | ForEach-Object { ($_ -split '\s+')[-2] } | Sort-Object -Unique).Count
"[PONTES KAGGLE/COLAB] $pontes portas abertas"

# 5) Celulares
$adb = @((& 'D:\tools\platform-tools\adb.exe' devices 2>$null) | Where-Object { $_ -match '\tdevice$' } | ForEach-Object { ($_ -split '\t')[0] })
"[CELULARES adb] {0} conectados (esperado 5: A2 G20 A3 S20 S20U): {1}" -f $adb.Count, ($adb -join ' ')

# 6) Alarmes do vigilancia.py (ja calculados por ele)
$vig = 'D:\video-fila\VIGILANCIA.md'
if (Test-Path $vig) {
  $idade = [math]::Round(($agora - (Get-Item $vig).LastWriteTime).TotalMinutes)
  $linhas = Get-Content -Encoding UTF8 $vig
  $ini = ($linhas | Select-String -Pattern '^## Alarmes' | Select-Object -First 1).LineNumber
  $fim = ($linhas | Select-String -Pattern '^## Casos' | Select-Object -First 1).LineNumber
  "[ALARMES DO VIGIA] (relatorio de $idade min atras)"
  if ($ini -and $fim) { $linhas[$ini..($fim-2)] | Where-Object { $_ -match '^- ' } | ForEach-Object { "  $_" } }
  if ($idade -gt 60) { "  !! VIGILANCIA.md parado ha $idade min (tarefa VigilanciaSistema travou?)" }
}

# 7) Relatorios que devem estar frescos (nome, arquivo, horas maximas)
$frescos = @(
  @('Medico recuperacao', 'D:\video-fila\MEDICO.md', 26),
  @('Inventario videos',  'D:\video-fila\INVENTARIO_VIDEOS.md', 4),
  @('Diario supervisor',  'D:\video-fila\ARQUITETURA_PC1_SUPERVISOR.md', 6),
  @('Estado fila Facebook','D:\postador-de-videos\logs\fb_fila_estado.json', 3)
)
$velhos = @()
foreach ($f in $frescos) { if (Test-Path $f[1]) { $h = ($agora - (Get-Item $f[1]).LastWriteTime).TotalHours; if ($h -gt $f[2]) { $velhos += ("{0} ({1:N0} h)" -f $f[0], $h) } } else { $velhos += ($f[0] + ' (sumiu)') } }
if ($velhos.Count) { "[RELATORIOS VELHOS] " + ($velhos -join ', ') } else { "[RELATORIOS] todos frescos" }

# 8) Producao de anuncios (claude-code-video): ultimo trabalho
$ult = Get-ChildItem D:\claude-code-video\trabalhos -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($ult) { "[ANUNCIOS REMOTION] ultimo: {0} ({1:N1} h atras)" -f $ult.Name, ($agora - $ult.LastWriteTime).TotalHours }

# 9) Erros novos nos logs de hoje (Traceback na ultima hora)
$logs = Get-ChildItem D:\postador-de-videos\logs, D:\video-fila\logs, D:\recapd-ambientes\producao\logs, D:\hipercool-videos\logs, D:\ms-energy\logs, D:\manhwa-react\logs -Filter *.log -File |
  Where-Object { $_.LastWriteTime -gt $agora.AddHours(-1) }
$tb = @()
foreach ($l in $logs) { $n = (Get-Content $l.FullName -Tail 150 | Select-String -Pattern 'Traceback' -SimpleMatch | Measure-Object).Count; if ($n) { $tb += ("{0} ({1})" -f $l.Name, $n) } }
if ($tb.Count) { "[LOGS COM TRACEBACK no fim do log (mexidos na ultima hora)] " + ($tb -join ', ') } else { "[LOGS] sem Traceback recente" }

# 10) Checagens dos HANDOFFS de 26/11 (FACEBOOK, CELULARES, SUPERVISOR) - sem ninguem assumindo, a ronda vigia
#     Fonte: claude-central/HANDOFF_FACEBOOK_26NOV.md sec 4-5, HANDOFF_CELULARES_26NOV.md sec 1, HANDOFF_26NOV_0845.md sec 6
#     ASCII puro: PowerShell 5 le .ps1 sem BOM como ANSI e quebra com travessao/acento.
$fbE = Get-Content -Raw -Encoding UTF8 D:\postador-de-videos\logs\fb_fila_estado.json | ConvertFrom-Json
$p02 = "$($fbE.contas.emersonjosiel02.parada_ate)"
if ($agora -lt [datetime]'2026-11-27T12:08:05' -and $p02 -ne '2026-11-27T12:08:05') { "[FACEBOOK] !! trava de repouso da emersonjosiel02 MUDOU para [$p02] (deve ser 2026-11-27T12:08:05)" }
$n368 = (Get-ChildItem D:\postador-de-videos\logs\fb_*.log | Where-Object { $_.Name -ne 'fb_escada.log' -and $_.LastWriteTime -gt $agora.AddHours(-2) } | Select-String -Pattern '368/|Limitamos' | Measure-Object).Count
if ($n368 -gt 0) { "[FACEBOOK] !! $n368 bloqueio(s) 368 ou Limitamos nas ultimas 2 h. Regra: parar a conta 24 h e avisar a dona" }
$pontesFb = foreach ($p in 18558, 18569) { $r = & curl.exe -s -m 15 -x "http://127.0.0.1:$p" http://api.ipify.org; if ($r -match '^\d+\.\d+\.\d+\.\d+$') { "$p ok" } else { "$p !! CAIDA" } }
$mortas = @(Get-ChildItem D:\postador-de-videos\logs\fb_postando_*.lock | Where-Object { -not (Get-Process -Id ((Get-Content $_.FullName -Raw).Split('|')[0]) -ErrorAction SilentlyContinue) } | ForEach-Object { $_.Name })
'[FACEBOOK] pontes: ' + ($pontesFb -join ', ') + ' / travas de PID morto: ' + $mortas.Count + ' / bloqueios 368 em 2h: ' + $n368
if ($mortas.Count -gt 0) { '  !! travas mortas: ' + ($mortas -join ', ') }
$cel = 'D:\projeto celular sub controle\canal_pronto\noite_encher.log'
$linhasCel = Get-Content $cel -Tail 2000 | Select-String -Pattern ': PRONTO'
$prontosHoje = @($linhasCel | Where-Object { $_.Line.StartsWith($agora.ToString('dd/MM')) }).Count
$ultCel = ($linhasCel | Select-Object -Last 1).Line
'[CELULARES] posts PRONTO hoje: ' + $prontosHoje + ' / ultimo: ' + $(if ($ultCel) { $ultCel.Substring(0, [Math]::Min(55, $ultCel.Length)) } else { 'nenhum' })
if ($ultCel -and $agora.Hour -ge 10 -and $agora.Hour -lt 22) {
  $h = [datetime]::ParseExact($agora.Year.ToString() + '/' + $ultCel.Substring(0, 14), 'yyyy/dd/MM HH:mm:ss', $null)
  if (($agora - $h).TotalHours -gt 4) { '  !! nenhum post de celular ha mais de 4 h' }
}
$tt = @(Get-Content ('D:\postador-de-videos\logs\tiktok_' + $agora.ToString('yyyyMMdd') + '.log') | Select-String 'OK #').Count
$ag = @(Get-Content D:\recapd-ambientes\producao\logs\parceiro_postar.log -Tail 3000 | Select-String -Pattern ('\[' + $agora.ToString('yyyy-MM-dd') + '.*AGENDADO')).Count
'[SUPERVISOR] Shorts parceiro AGENDADO hoje: ' + $ag + ' / TikTok OK hoje: ' + $tt
if ($agora.Hour -ge 12 -and $tt -eq 0) { '  !! TikTok com 0 posts hoje depois do meio-dia' }

# 11) Lacunas achadas na conferencia de 26/11 11h (ASCII puro)
$ig = 'D:\postador-de-videos\logs\instagram_' + $agora.ToString('yyyyMMdd') + '.log'
$igOk = @(Select-String -Path $ig -Pattern '^\[\d\d:\d\d:\d\d\]\s+OK ')
$igErr = @(Select-String -Path $ig -Pattern 'nao subiu para link publico').Count
$igUlt = if ($igOk.Count) { $igOk[-1].Line.Substring(1,5) } else { 'nenhum' }
'[INSTAGRAM] OK hoje: ' + $igOk.Count + ' / falhas de link publico (uguu/litterbox): ' + $igErr + ' / ultimo OK: ' + $igUlt
if ($igOk.Count -and $agora.Hour -ge 9) { $hU = [datetime]::ParseExact($agora.ToString('yyyy-MM-dd ') + $igOk[-1].Line.Substring(1,8), 'yyyy-MM-dd HH:mm:ss', $null); if (($agora - $hU).TotalHours -gt 6) { '  !! Instagram sem post OK ha mais de 6 h' } }
$k3 = Get-Content D:\kit3d-producao\tools\diario.log -Tail 3 -ErrorAction SilentlyContinue
if (-not $k3) { $k3 = Get-ChildItem D:\kit3d-producao -Recurse -Depth 2 -Filter diario.log | Select-Object -First 1 | ForEach-Object { Get-Content $_.FullName -Tail 3 } }
if ($k3 -match 'sem tema novo') { '[KIT 3D] !! parado: fila de temas vazia (temas.json) - a dona precisa acrescentar temas' }

# 12) (OBRA etapa 1, 26/11) producao parada agora vem do CATALOGO (secao 17). Lista fixa antiga em ronda_geral.ps1.bak_obra_1

# 13) Tarefas atrasadas: proxima execucao ja passou ha mais de 90 min (o agendador nao rodou)
$atras = @()
foreach ($t in (Get-ScheduledTask | Where-Object { $_.TaskPath -notlike '\Microsoft*' -and $_.State -eq 'Ready' })) {
  if ($t.TaskName -match '^(HP |IObit|Microsoft|Google|RunPlatform|Wise)') { continue }
  $i = Get-ScheduledTaskInfo -TaskName $t.TaskName -TaskPath $t.TaskPath
  if ($i.NextRunTime -and $i.NextRunTime.Year -gt 2000 -and $i.NextRunTime -lt $agora.AddMinutes(-90)) { $atras += $t.TaskName }
}
if ($atras.Count) { '[TAREFAS ATRASADAS] ' + $atras.Count; $atras | ForEach-Object { '  !! nao rodou no horario: ' + $_ } } else { '[TAREFAS ATRASADAS] nenhuma' }

# 14) Inventario: tarefa agendada NOVA que ninguem acompanha ainda (1o aviso e entra na base)
$base = 'D:\video-fila\estado\ronda_tarefas_base.txt'
$atuais = @(Get-ScheduledTask | Where-Object { $_.TaskPath -notlike '\Microsoft*' } | ForEach-Object { $_.TaskName } | Sort-Object -Unique)
if (-not (Test-Path $base)) { $atuais | Set-Content -Encoding UTF8 $base; '[INVENTARIO] base criada com ' + $atuais.Count + ' tarefas' }
else {
  $conhecidas = Get-Content -Encoding UTF8 $base
  $novas = @($atuais | Where-Object { $conhecidas -notcontains $_ })
  $sumiram = @($conhecidas | Where-Object { $atuais -notcontains $_ })
  $novas | ForEach-Object { '  !! TAREFA NOVA no PC1 (incluir na lista mestra): ' + $_ }
  $sumiram | ForEach-Object { '  !! TAREFA SUMIU do PC1: ' + $_ }
  if ($novas.Count -or $sumiram.Count) { $atuais | Set-Content -Encoding UTF8 $base }
  '[INVENTARIO] ' + $atuais.Count + ' tarefas / novas: ' + $novas.Count + ' / sumiram: ' + $sumiram.Count
}

# 15) Handoffs: documento de passagem novo na pasta comum (sinal de chat encerrando e trabalho sem dono)
$hoAgora = @(Get-ChildItem 'D:\video-fila\HANDOFF_*.md','D:\projeto celular sub controle\canal_pronto\HANDOFF_*.md' -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -gt $agora.AddHours(-24) } | ForEach-Object { $_.Name })
'[HANDOFFS 24h no PC1] ' + ($hoAgora -join ', ')

# 16) Views por canal (24 h x 24 h antes) e Kaggle - feito em Python (ronda_extra.py, copiado pela ronda.sh)
& D:\veo\venv\Scripts\python.exe -X utf8 D:\video-fila\ronda_extra.py 2>&1 | ForEach-Object { "$_" }

# 17) CATALOGO UNICO (D:\video-fila\sistema\sistema.json): tarefas sem dono, incoerencias, producao parada por projeto
& D:\veo\venv\Scripts\python.exe -X utf8 D:\video-fila\sistema\catalogo.py ronda 2>&1 | ForEach-Object { "$_" }

# 18) OBRA sistema unico: uso real x catalogo (vivos, mortos candidatos, tarefas prontas para o Python unico)
$env:SISTEMA_USO = '0'
& D:\veo\venv\Scripts\python.exe -X utf8 D:\sistema\catalogo\analisar_uso.py --ronda 2>&1 | ForEach-Object { "$_" }

# 19) OBRA etapas 2-4: o que esta segurado (motivos.py), maquinas (lista unica), codigo comum (vinculos)
& D:\veo\venv\Scripts\python.exe -X utf8 D:\sistema\catalogo\motivos.py --resumo 2>&1 | ForEach-Object { "$_" }
& D:\veo\venv\Scripts\python.exe -X utf8 D:\sistema\catalogo\maquinas.py --conferir 2>&1 | ForEach-Object { "$_" }
& D:\veo\venv\Scripts\python.exe -X utf8 D:\sistema\catalogo\comum.py --conferir 2>&1 | ForEach-Object { "$_" }
