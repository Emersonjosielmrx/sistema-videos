"""Checa versão dos módulos no PC3 — busca cooldown e report_failure."""
import paramiko, os
from scp import SCPClient

PS1 = r'''
$out = ""

$out += "=== WORKER.PY report_failure ===`n"
Select-String -Path "C:\projetos-navegador\engage_modules\worker.py" -Pattern "report_failure" | ForEach-Object { $out += $_.Line.Trim() + "`n" }

$out += "`n=== ACCOUNT_HEALTH.PY cooldown ===`n"
if (Test-Path "C:\projetos-navegador\engage_modules\account_health.py") {
    Select-String -Path "C:\projetos-navegador\engage_modules\account_health.py" -Pattern "cooldown|3600|900" | ForEach-Object { $out += $_.Line.Trim() + "`n" }
} else { $out += "ARQUIVO NAO EXISTE`n" }

$out += "`n=== CONFIG.PY cooldown ===`n"
Select-String -Path "C:\projetos-navegador\engage_modules\config.py" -Pattern "cooldown|COOLDOWN|3600|900" -CaseSensitive:$false | ForEach-Object { $out += $_.Line.Trim() + "`n" }

$out += "`n=== BOT LOG RESUMO ===`n"
$lines = Get-Content "C:\projetos-navegador\bot_output.log" -ErrorAction SilentlyContinue
$ok = ($lines | Select-String "^.*OK \[" | Measure-Object).Count
$erros = ($lines | Select-String "^.*ERRO " | Measure-Object).Count
$cooldowns = ($lines | Select-String "cooldown 1h" | Measure-Object).Count
$cooldowns15 = ($lines | Select-String "cooldown 15m" | Measure-Object).Count
$total = $lines.Count
$out += "Total linhas: $total`n"
$out += "OKs: $ok`n"
$out += "Erros: $erros`n"
$out += "Cooldown 1h: $cooldowns`n"
$out += "Cooldown 15m: $cooldowns15`n"

$out += "`n=== PRIMEIRO/ULTIMO ===`n"
if ($lines.Count -gt 0) {
    $out += "PRIMEIRO: $($lines[0])`n"
    $out += "ULTIMO: $($lines[-1])`n"
}

$out | Out-File "C:\projetos-navegador\_diag_result3.txt" -Encoding UTF8
Write-Output "DONE"
'''

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('100.108.160.85', username='Emerson-IA', password='<SEGREDO_REMOVIDO>', timeout=15)
scp = SCPClient(ssh.get_transport(), socket_timeout=60)

tmp = os.path.join(os.environ.get("TEMP", "/tmp"), "_diag3.ps1")
with open(tmp, "w", encoding="utf-8") as f:
    f.write(PS1)
scp.put(tmp, "C:/projetos-navegador/_diag3.ps1")
scp.close()

_, stdout, stderr = ssh.exec_command(
    'powershell -ExecutionPolicy Bypass -File C:\\projetos-navegador\\_diag3.ps1',
    timeout=20
)
print(stdout.read().decode("utf-8", errors="replace").strip())

import time; time.sleep(1)
scp2 = SCPClient(ssh.get_transport(), socket_timeout=60)
scp2.get("C:/projetos-navegador/_diag_result3.txt", os.path.join(os.path.dirname(os.path.abspath(__file__)), "_diag_result3.txt"))
scp2.close()

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_diag_result3.txt"), "r", encoding="utf-8") as f:
    print(f.read())

ssh.close()
os.unlink(tmp)
