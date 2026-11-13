"""Checa log resumido do bot no PC3."""
import paramiko, os
from scp import SCPClient

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('100.108.160.85', username='Emerson-IA', password='<SEGREDO_REMOVIDO>', timeout=15)

PS1 = r'''
$out = ""
$lines = Get-Content "C:\projetos-navegador\bot_output.log" -ErrorAction SilentlyContinue
$ok = ($lines | Select-String "^.*OK \[" | Measure-Object).Count
$erros = ($lines | Select-String "^.*ERRO " | Measure-Object).Count
$cd_old = ($lines | Select-String "cooldown 1h" | Measure-Object).Count
$cd_new = ($lines | Select-String "cooldown \d+min" | Measure-Object).Count
$proxy = ($lines | Select-String "Proxy falhou|nao conta como falha" | Measure-Object).Count
$dead = ($lines | Select-String "dead_accounts" | Measure-Object).Count
$total = $lines.Count

$out += "Total linhas: $total`n"
$out += "OKs: $ok`n"
$out += "Erros: $erros`n"
$out += "Cooldown antigo (1h): $cd_old`n"
$out += "Cooldown novo (Nmin): $cd_new`n"
$out += "Proxy errors (nao conta): $proxy`n"
$out += "Dead accounts: $dead`n"
$out += "`n=== ULTIMAS 30 LINHAS ===`n"
$tail = $lines | Select-Object -Last 30
$out += ($tail -join "`n")

$out | Out-File "C:\projetos-navegador\_check_result.txt" -Encoding UTF8
Write-Output "DONE"
'''

tmp = os.path.join(os.environ.get("TEMP", "/tmp"), "_check.ps1")
with open(tmp, "w", encoding="utf-8") as f:
    f.write(PS1)
scp = SCPClient(ssh.get_transport(), socket_timeout=60)
scp.put(tmp, "C:/projetos-navegador/_check.ps1")
scp.close()

_, stdout, _ = ssh.exec_command(
    'powershell -ExecutionPolicy Bypass -File C:\projetos-navegador\_check.ps1',
    timeout=15
)
stdout.read()

import time; time.sleep(1)
scp2 = SCPClient(ssh.get_transport(), socket_timeout=60)
scp2.get("C:/projetos-navegador/_check_result.txt", os.path.join(os.path.dirname(os.path.abspath(__file__)), "_check_result.txt"))
scp2.close()

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_check_result.txt"), "r", encoding="utf-8") as f:
    print(f.read())

ssh.close()
os.unlink(tmp)
