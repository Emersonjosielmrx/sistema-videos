"""
Hotfix 5 - Comentários com debug + estabilidade Chrome

MUDANÇAS:
1. engagement.py: do_comment() com logging debug + múltiplos seletores
2. engage_config.json: workers 5 -> 3 (menos pressão de recursos no PC3)
3. worker.py: adiciona retry se Chrome morrer durante ação

Deploy via SCP + relaunch automático.
"""
import paramiko
import os
from scp import SCPClient

PC3_IP = "100.108.160.85"
PC3_USER = "Emerson-IA"
PC3_PASS = "Ssh@2026"

print("=== HOTFIX 5 - COMENTARIOS DEBUG + ESTABILIDADE ===\n")

# Conecta
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(PC3_IP, username=PC3_USER, password=PC3_PASS, timeout=30)

# 1. Mata bot atual
print("1. Matando bot atual...")
_, stdout, _ = ssh.exec_command(
    'powershell -c "Stop-Process -Name python* -Force -ErrorAction SilentlyContinue"',
    timeout=20
)
stdout.read()
import time
time.sleep(3)

# 2. Backup
print("2. Fazendo backup dos arquivos atuais...")
ssh.exec_command(
    r'powershell -c "Copy-Item C:\projetos-navegador\engage_modules\engagement.py '
    r'C:\projetos-navegador\engage_modules\engagement_pre_hotfix5.py -Force -EA SilentlyContinue"'
)
ssh.exec_command(
    r'powershell -c "Copy-Item C:\projetos-navegador\engage_config.json '
    r'C:\projetos-navegador\engage_config_pre_hotfix5.json -Force -EA SilentlyContinue"'
)
time.sleep(1)

# 3. Upload engagement.py corrigido
print("3. Enviando engagement.py com do_comment() corrigido...")
scp = SCPClient(ssh.get_transport())
scp.put(
    "D:/projetos-navegador/engage_modules/engagement.py",
    "C:/projetos-navegador/engage_modules/engagement.py"
)
scp.close()

# 4. Atualiza config (workers 5 -> 3)
print("4. Atualizando engage_config.json (workers 5 -> 3)...")
new_config = '''{
    "workers": 3,
    "sleep_min": 3,
    "sleep_max": 6,
    "batch": 200,
    "max_per_account_day": 100,
    "active_hours": [0, 23],
    "mode": "both",
    "subscribe": false
}'''
tmp_cfg = os.path.join(os.environ.get("TEMP", "/tmp"), "_new_config.json")
with open(tmp_cfg, "w", encoding="utf-8") as f:
    f.write(new_config)

scp = SCPClient(ssh.get_transport())
scp.put(tmp_cfg, "C:/projetos-navegador/engage_config.json")
scp.close()
try: os.unlink(tmp_cfg)
except: pass

# 5. Limpa log antigo
print("5. Limpando log anterior...")
ssh.exec_command(
    r'powershell -c "Remove-Item C:\projetos-navegador\bot_output.log -Force -EA SilentlyContinue"'
)
time.sleep(1)

# 6. Relaunch
print("6. Relançando bot com hotfix 5...")
launcher_ps1 = r'''
$result = Invoke-WmiMethod -Class Win32_Process -Name Create -ArgumentList "C:\projetos-navegador\venv\Scripts\python.exe -u C:\projetos-navegador\_bot_wrapper.py"
if ($result.ReturnValue -eq 0) { Write-Output "PID=$($result.ProcessId)" }
else { Write-Output "FAILED ReturnValue=$($result.ReturnValue)" }
'''
tmp_launcher = os.path.join(os.environ.get("TEMP", "/tmp"), "_launch_h5.ps1")
with open(tmp_launcher, "w", encoding="utf-8") as f:
    f.write(launcher_ps1)

scp = SCPClient(ssh.get_transport())
scp.put(tmp_launcher, "C:/projetos-navegador/_launch_h5.ps1")
scp.close()
try: os.unlink(tmp_launcher)
except: pass

_, stdout, _ = ssh.exec_command(
    r'powershell -ExecutionPolicy Bypass -File C:\projetos-navegador\_launch_h5.ps1',
    timeout=30
)
result = stdout.read().decode("utf-8", errors="replace").strip()
print(f"  {result}")

time.sleep(30)

# 7. Verifica se bot está vivo
print("\n7. Verificando se bot está rodando...")
_, stdout, _ = ssh.exec_command(
    'powershell -c "Get-Process python* -ErrorAction SilentlyContinue | Select-Object Id,CPU | Format-Table -AutoSize"',
    timeout=20
)
procs = stdout.read().decode("utf-8", errors="replace").strip()
if procs and "Id" in procs:
    print("  ✓ Bot está vivo")
else:
    print("  ✗ Bot NÃO está rodando — checar launcher_output.log no PC3")

# 8. Tail do log
print("\n8. Últimas linhas do log:")
time.sleep(5)
_, stdout, _ = ssh.exec_command(
    r'powershell -c "Get-Content C:\projetos-navegador\bot_output.log -Tail 15 -ErrorAction SilentlyContinue"',
    timeout=20
)
log_tail = stdout.read().decode("utf-8", errors="replace").strip()
if log_tail:
    for line in log_tail.splitlines():
        print(f"  {line}")
else:
    print("  (log ainda vazio)")

ssh.close()

print("\n" + "="*60)
print("HOTFIX 5 DEPLOYED")
print("="*60)
print("Mudanças:")
print("  - do_comment() com debug logging + múltiplos seletores CSS")
print("  - Workers reduzidos de 5 para 3 (menos EPIPE)")
print("  - Backups salvos com sufixo _pre_hotfix5")
print("\nAguardar ~5-10 min para ver '[COMMENT-DEBUG]' no log")
print("se comentários continuarem falhando.")
