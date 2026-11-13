"""Diagnostico rapido: bot vivo? log completo? relançar se morreu."""
import paramiko, re
from datetime import datetime

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("100.108.160.85", username="Emerson-IA", password="<SEGREDO_REMOVIDO>", timeout=15)

# 1. Processo vivo?
_, stdout, _ = ssh.exec_command(
    'powershell -c "Get-Process python* -ErrorAction SilentlyContinue | Select-Object Id,CPU,WorkingSet64 | Format-Table -AutoSize"',
    timeout=10
)
procs = stdout.read().decode("utf-8", errors="replace").strip()
print("=== PROCESSOS PYTHON ===")
print(procs if procs else "(nenhum)")

# 2. Tamanho e ultima linha do log
_, stdout, _ = ssh.exec_command(
    r'powershell -c "$f=Get-Item C:\projetos-navegador\bot_output.log -EA SilentlyContinue; if($f){Write-Output \"Size: $($f.Length) bytes, Modified: $($f.LastWriteTime)\"} else {Write-Output \"Log nao existe\"}"',
    timeout=10
)
print(f"\n=== LOG ===")
print(stdout.read().decode("utf-8", errors="replace").strip())

# 3. Ultimas 30 linhas do log
_, stdout, _ = ssh.exec_command(
    r'powershell -c "Get-Content C:\projetos-navegador\bot_output.log -Tail 30 -EA SilentlyContinue"',
    timeout=10
)
tail = stdout.read().decode("utf-8", errors="replace").strip()
print(f"\n=== ULTIMAS 30 LINHAS ===")
for l in tail.splitlines():
    try:
        print(l)
    except UnicodeEncodeError:
        print(l.encode("ascii", errors="replace").decode())

# 4. Launcher output
_, stdout, _ = ssh.exec_command(
    r'powershell -c "Get-Content C:\projetos-navegador\launcher_output.log -Tail 15 -EA SilentlyContinue"',
    timeout=10
)
launcher = stdout.read().decode("utf-8", errors="replace").strip()
if launcher:
    print(f"\n=== LAUNCHER LOG ===")
    print(launcher)

# 5. Contar OKs no log completo
_, stdout, _ = ssh.exec_command(
    r'powershell -c "(Select-String -Path C:\projetos-navegador\bot_output.log -Pattern \"OK \[\" -EA SilentlyContinue).Count"',
    timeout=15
)
ok_count = stdout.read().decode("utf-8", errors="replace").strip()
print(f"\n=== TOTAL OKs NO LOG: {ok_count} ===")

ssh.close()
