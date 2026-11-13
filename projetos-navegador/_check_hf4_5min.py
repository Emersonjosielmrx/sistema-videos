"""Check rapido 5 min do hotfix 4."""
import paramiko, time, re
from datetime import datetime

print("Aguardando 5 minutos...")
time.sleep(300)

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("100.108.160.85", username="Emerson-IA", password="<SEGREDO_REMOVIDO>", timeout=15)

cmd = r'powershell -c "Get-Content C:\projetos-navegador\bot_output.log -ErrorAction SilentlyContinue"'
_, stdout, _ = ssh.exec_command(cmd, timeout=30)
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

print(f"\n{'='*50}")
print(f"HOTFIX 4 — CHECK 5 MIN")
print(f"{'='*50}")
print(f"Tempo: {mins:.1f} min")
print(f"OKs: {oks}")
if mins > 0:
    print(f"Taxa: {oks/mins:.2f} OKs/min")
print(f"\nProxy blacklists: {proxy_bl}")
print(f"Proxy falhou: {proxy_falhou}")
print(f"Chrome morreu: {chrome_morreu}")
print(f"Context destroyed: {context_destroyed}")
print(f"Health cooldowns: {health_cd}")
print(f"\n{'='*50}")
if health_cd == 0:
    print("OK: 0 health cooldowns")
else:
    print(f"ALERTA: {health_cd} health cooldowns")

# Ultimas 10 linhas
print(f"\nUltimas 10 linhas:")
for l in lines[-10:]:
    try:
        print(l.strip())
    except UnicodeEncodeError:
        print(l.encode("ascii", errors="replace").decode().strip())

ssh.close()
