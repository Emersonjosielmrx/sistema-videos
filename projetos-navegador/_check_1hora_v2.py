"""Relanca bot no PC3 + monitora 1 hora real."""
import paramiko, time, re, os
from datetime import datetime
from scp import SCPClient

PC3_IP = "100.108.160.85"
PC3_USER = "Emerson-IA"
PC3_PASS = "Ssh@2026"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(PC3_IP, username=PC3_USER, password=PC3_PASS, timeout=15)

# 1. Matar qualquer processo python
print("Matando processos python...")
ssh.exec_command('powershell -c "Stop-Process -Name python* -Force -ErrorAction SilentlyContinue"')
time.sleep(3)

# 2. Limpar logs antigos
print("Limpando logs...")
ssh.exec_command(r'powershell -c "Remove-Item C:\projetos-navegador\bot_output.log,C:\projetos-navegador\launcher_output.log -Force -ErrorAction SilentlyContinue"')
time.sleep(1)

# 3. Relancar via Invoke-WmiMethod
print("Relancando bot...")
launcher = r'''
$result = Invoke-WmiMethod -Class Win32_Process -Name Create -ArgumentList "C:\projetos-navegador\venv\Scripts\python.exe -u C:\projetos-navegador\_bot_wrapper.py"
if ($result.ReturnValue -eq 0) { Write-Output "PID=$($result.ProcessId)" }
else { Write-Output "FAILED ReturnValue=$($result.ReturnValue)" }
'''
tmp_ps1 = os.path.join(os.environ.get("TEMP", "/tmp"), "_launch.ps1")
with open(tmp_ps1, "w", encoding="utf-8") as f:
    f.write(launcher)

scp = SCPClient(ssh.get_transport(), socket_timeout=60)
scp.put(tmp_ps1, "C:/projetos-navegador/_launch.ps1")
scp.close()

_, stdout, _ = ssh.exec_command(
    r'powershell -ExecutionPolicy Bypass -File C:\projetos-navegador\_launch.ps1',
    timeout=20
)
result = stdout.read().decode('utf-8', errors='replace').strip()
print(f"  {result}")

try: os.unlink(tmp_ps1)
except: pass

# 4. Confirmar que subiu (30s)
print("Esperando 30s pra confirmar...")
time.sleep(30)

_, stdout, _ = ssh.exec_command(
    r'powershell -c "Get-Content C:\projetos-navegador\bot_output.log -Tail 5 -ErrorAction SilentlyContinue"',
    timeout=10
)
check = stdout.read().decode('utf-8', errors='replace').strip()
if "OK [" in check or "ERRO" in check or "health" in check.lower():
    print("Bot esta rodando!")
else:
    print(f"Log ainda curto, mas bot lancado. Tail:\n{check}")

ssh.close()

# 5. Esperar 1 HORA
print("\n=== Aguardando 1 hora (3600s) ===")
time.sleep(3600)

# 6. Reconectar e puxar stats
print("\nReconectando pra puxar resultado...")
ssh2 = paramiko.SSHClient()
ssh2.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh2.connect(PC3_IP, username=PC3_USER, password=PC3_PASS, timeout=15)

# Processo vivo?
_, stdout, _ = ssh2.exec_command(
    'powershell -c "Get-Process python* -ErrorAction SilentlyContinue | Select-Object Id | Format-Table -AutoSize"',
    timeout=10
)
procs = stdout.read().decode("utf-8", errors="replace").strip()
bot_alive = bool(procs and "Id" in procs)

# Log completo
_, stdout, _ = ssh2.exec_command(
    r'powershell -c "Get-Content C:\projetos-navegador\bot_output.log -ErrorAction SilentlyContinue"',
    timeout=60
)
raw = stdout.read().decode("utf-8", errors="replace")
lines = raw.splitlines()

timestamps = []
for l in lines:
    m = re.match(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]', l)
    if m:
        timestamps.append(m.group(1))

if len(timestamps) >= 2:
    t0 = datetime.strptime(timestamps[0], "%Y-%m-%d %H:%M:%S")
    t1 = datetime.strptime(timestamps[-1], "%Y-%m-%d %H:%M:%S")
    mins = (t1 - t0).total_seconds() / 60
else:
    mins = 0

oks = sum(1 for l in lines if "OK [" in l)
health_cd = sum(1 for l in lines if "[HEALTH]" in l and "cooldown" in l)
proxy_bl = sum(1 for l in lines if "PROXY BLACKLIST" in l)
proxy_falhou = sum(1 for l in lines if "Proxy falhou" in l)
chrome_morreu = sum(1 for l in lines if "Chrome morreu" in l)
context_destroyed = sum(1 for l in lines if "Execution context was destroyed" in l)
epipe = sum(1 for l in lines if "EPIPE" in l)

print(f"\n{'='*60}")
print(f"  RESULTADO 1 HORA — MEGA ENGAGE V3")
print(f"{'='*60}")
print(f"Bot ainda vivo: {'SIM' if bot_alive else 'NAO (crashou)'}")
print(f"Tempo real de log: {mins:.1f} min")
print(f"")
print(f"  OKs totais:        {oks}")
if mins > 0:
    print(f"  Taxa media:        {oks/mins:.2f} OKs/min")
    print(f"  Projecao horaria:  {oks/mins * 60:.0f} OKs/hora")
print(f"")
print(f"  Erros classificados:")
print(f"    Proxy blacklists:   {proxy_bl}")
print(f"    Proxy falhou:       {proxy_falhou}")
print(f"    Chrome morreu:      {chrome_morreu}")
print(f"    Context destroyed:  {context_destroyed}")
print(f"    EPIPE crashes:      {epipe}")
print(f"    Health cooldowns:   {health_cd}")
print(f"")
print(f"{'='*60}")
if health_cd == 0:
    print("0 health cooldowns injustos")
else:
    print(f"ALERTA: {health_cd} health cooldowns")
if not bot_alive:
    print("BOT MORREU durante a hora — considerar auto-restart")

# Últimas 20 linhas
print(f"\nUltimas 20 linhas:")
for l in lines[-20:]:
    try:
        print(l.strip())
    except UnicodeEncodeError:
        print(l.encode("ascii", errors="replace").decode().strip())

ssh2.close()
