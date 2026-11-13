"""Hotfix 2: reenvia worker.py corrigido pro PC3 e reinicia bot."""
import paramiko, os, time
from scp import SCPClient

PC3_IP = "100.108.160.85"
PC3_USER = "Emerson-IA"
PC3_PASS = "Ssh@2026"

base = os.path.dirname(os.path.abspath(__file__))

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(PC3_IP, username=PC3_USER, password=PC3_PASS, timeout=15)

# 1. Matar
print("Matando bot...")
ssh.exec_command('powershell -c "Stop-Process -Name python* -Force -ErrorAction SilentlyContinue"')
time.sleep(3)

# 2. Upload worker.py corrigido
print("Enviando worker.py...")
local_path = os.path.join(base, "engage_modules", "worker.py")
with open(local_path, "r", encoding="utf-8") as f:
    content = f.read()
for old, new in [("D:\\\\projetos-navegador","C:\\\\projetos-navegador"),("D:/projetos-navegador","C:/projetos-navegador"),("D:\\projetos-navegador","C:\\projetos-navegador")]:
    content = content.replace(old, new)
tmp = os.path.join(os.environ.get("TEMP", "/tmp"), "worker.py")
with open(tmp, "w", encoding="utf-8") as f:
    f.write(content)
scp = SCPClient(ssh.get_transport(), socket_timeout=60)
scp.put(tmp, "C:/projetos-navegador/engage_modules/worker.py")

# 3. Reset health novamente
print("Resetando health...")
reset_cmd = 'powershell -c "if(Test-Path C:\\projetos-navegador\\data\\account_health.json){Remove-Item C:\\projetos-navegador\\data\\account_health.json -Force; Write-Output \'Resetado\'} else {Write-Output \'Nao existia\'}"'
_, stdout, _ = ssh.exec_command(reset_cmd, timeout=10)
print(f"  {stdout.read().decode('utf-8', errors='replace').strip()}")

# 4. Limpar logs
ssh.exec_command('powershell -c "Remove-Item C:\\projetos-navegador\\bot_output.log,C:\\projetos-navegador\\launcher_output.log -Force -ErrorAction SilentlyContinue"')
time.sleep(1)

# 5. Relançar
print("Relançando...")
launcher = r'''
$result = Invoke-WmiMethod -Class Win32_Process -Name Create -ArgumentList "C:\projetos-navegador\venv\Scripts\python.exe -u C:\projetos-navegador\_bot_wrapper.py"
if ($result.ReturnValue -eq 0) { Write-Output "PID=$($result.ProcessId)" }
else { Write-Output "FAILED ReturnValue=$($result.ReturnValue)" }
'''
tmp_ps1 = os.path.join(os.environ.get("TEMP", "/tmp"), "_launch.ps1")
with open(tmp_ps1, "w", encoding="utf-8") as f:
    f.write(launcher)
scp.put(tmp_ps1, "C:/projetos-navegador/_launch.ps1")
scp.close()

_, stdout, _ = ssh.exec_command(
    'powershell -ExecutionPolicy Bypass -File C:\\projetos-navegador\\_launch.ps1',
    timeout=20
)
print(f"  {stdout.read().decode('utf-8', errors='replace').strip()}")
os.unlink(tmp)
os.unlink(tmp_ps1)

# 6. Esperar e verificar
print("Esperando 30s...")
time.sleep(30)

_, stdout, _ = ssh.exec_command(
    'powershell -c "Get-Content C:\\projetos-navegador\\bot_output.log -Tail 25 -ErrorAction SilentlyContinue"',
    timeout=10
)
print(f"\nLog:\n{stdout.read().decode('utf-8', errors='replace').strip()}")

ssh.close()
print("\nHotfix 2 concluido!")
