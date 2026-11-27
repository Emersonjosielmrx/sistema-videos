# Para SO os servicos permanentes que seguram as pastas, move, e religa CADA UM com a MESMA linha de comando (mesmo IP).
$ErrorActionPreference='SilentlyContinue'
$LOG='D:\sistema\mapa\mudanca.log'; function L($m){ Add-Content -Encoding UTF8 $LOG ((Get-Date -f 'dd/MM HH:mm:ss')+' '+$m) }
$pad = 'ponte_proxy_fixo\.py|gemini_http_proxy\.py|genspark_http\.py|tunel_painel\.py|ponte\.mjs'
$todos = Get-CimInstance Win32_Process | ?{ $_.CommandLine -match $pad -and $_.Name -match 'python|node' }
# pais (python do venv que lanca o filho) + filhos: guarda so a linha do processo "de cima" de cada par
$ids = $todos | %{ $_.ProcessId }
$topo = $todos | ?{ $ids -notcontains $_.ParentProcessId }
$salvo = $topo | %{ [pscustomobject]@{ exe=$_.ExecutablePath; cmd=$_.CommandLine; dir=(Split-Path ($_.CommandLine -replace '^"?[^"]+\.exe"?\s*','' -split '\s+')[0] -EA 0) } }
$salvo | ConvertTo-Json | Set-Content -Encoding UTF8 D:\sistema\mapa\pontes_salvas.json
L ("pontes/servicos permanentes salvos: " + @($salvo).Count + " (de " + @($todos).Count + " processos)")
$todos | %{ Stop-Process -Id $_.ProcessId -Force }
Stop-Process -Name cmd -EA 0 -Force:$false 2>$null | Out-Null
Get-CimInstance Win32_Process -Filter "Name='cmd.exe'" | ?{ $_.CommandLine -match 'cline-ponte' } | %{ Stop-Process -Id $_.ProcessId -Force }
Start-Sleep 3
$env:SISTEMA_USO='0'
$saida = & 'C:\Users\Haylla\AppData\Local\Programs\Python\Python313\python.exe' -X utf8 D:\sistema\catalogo\mudar_para_sistema.py --aplicar 2>&1
$saida | ?{ $_ -match 'MOVIDA|movidas:|presa:' } | %{ L ("  " + $_) }
# religa cada um com a MESMA linha (sem janela)
$sh = New-Object -ComObject WScript.Shell
foreach($s in $salvo){ $sh.Run($s.cmd, 0, $false) | Out-Null; Start-Sleep -Milliseconds 300 }
Start-ScheduledTask ClinePonte; Start-ScheduledTask PainelTunel; Start-ScheduledTask ArgonManter; Start-ScheduledTask OpusGratisManter
Start-Sleep 15
$depois = @(Get-CimInstance Win32_Process | ?{ $_.CommandLine -match $pad }).Count
L ("pontes/servicos religados: " + $depois + " processos (antes " + @($todos).Count + ")")
"antes $(@($todos).Count) | depois $depois"
$saida | ?{ $_ -match 'movidas:' }
