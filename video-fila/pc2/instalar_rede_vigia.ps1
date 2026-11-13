# instalar_rede_vigia.ps1 - roda NO PC2 (como admin), mandado pelo PC1 por ssh:
#   scp D:\video-fila\pc2\rede_vigia.ps1 D:\video-fila\pc2\PC2_RedeVigia.xml D:\video-fila\pc2\instalar_rede_vigia.ps1 pc2:C:/pc2-rede/
#   ssh pc2 powershell -ExecutionPolicy Bypass -File C:\pc2-rede\instalar_rede_vigia.ps1
# Cria a tarefa PC2_RedeVigia (SYSTEM, no boot + a cada hora; o script tem trava de instancia unica) e ja inicia.
# Pelo schtasks + XML: no PC2 os cmdlets *-ScheduledTask dao "Classe invalida" (WMI quebrado, 23/10).
$xml = "C:\pc2-rede\PC2_RedeVigia.xml"
# o schtasks quer o XML em UTF-16
$txt = Get-Content $xml -Raw -Encoding UTF8
[System.IO.File]::WriteAllText($xml, $txt, [System.Text.Encoding]::Unicode)
schtasks /create /tn "PC2_RedeVigia" /xml $xml /f
schtasks /run /tn "PC2_RedeVigia"
Start-Sleep -Seconds 10
schtasks /query /tn "PC2_RedeVigia" /fo list | Select-String "Status|Estado|Pr.xima|Next"
if (Test-Path "C:\pc2-rede\rede_vigia.log") { Get-Content "C:\pc2-rede\rede_vigia.log" -Tail 3 }
