"""Espera 10 min e verifica sustentabilidade do hotfix 3."""
import paramiko, time, re
from datetime import datetime

print("Aguardando 10 minutos...")
time.sleep(600)

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("100.108.160.85", username="Emerson-IA", password="<SEGREDO_REMOVIDO>", timeout=15)

# Log completo pra calcular taxa real
cmd = r'powershell -c "Get-Content C:\projetos-navegador\bot_output.log -ErrorAction SilentlyContinue"'
_, stdout, _ = ssh.exec_command(cmd, timeout=30)
raw = stdout.read().decode("utf-8", errors="replace")
lines = raw.splitlines()

# Health
cmd2 = r'powershell -c "Get-Content C:\projetos-navegador\data\account_health.json -ErrorAction SilentlyContinue"'
_, stdout2, _ = ssh.exec_command(cmd2, timeout=10)
health_raw = stdout2.read().decode("utf-8", errors="replace")
import json
try:
    health = json.loads(health_raw)
except:
    health = {}

# Calcular janela de tempo
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
health_cooldowns = sum(1 for l in lines if "[HEALTH]" in l and "cooldown" in l)
context_destroyed = sum(1 for l in lines if "Context destroyed" in l or "Execution context was destroyed" in l)
navigation_to = sum(1 for l in lines if "Navigation to" in l and "ERRO" in l)
chrome_morreu = sum(1 for l in lines if "Chrome morreu" in l)
proxy_falhou = sum(1 for l in lines if "Proxy falhou" in l)

# Contas em cooldown
cooldown_contas = [acc for acc, data in health.items() if data.get("cooldown_until")]

print(f"\n{'='*60}")
print(f"CHECK 10 MIN — HOTFIX 3")
print(f"{'='*60}")
print(f"Tempo total: {mins:.1f} min")
print(f"OKs: {oks}")
print(f"Taxa: {oks/mins:.2f} OKs/min" if mins > 0 else "Taxa: N/A")
print(f"\nErros classificados:")
print(f"  Context destroyed: {context_destroyed}")
print(f"  Navigation to (proxy): {navigation_to}")
print(f"  Chrome morreu (infra): {chrome_morreu}")
print(f"  Proxy falhou (correto): {proxy_falhou}")
print(f"  Health cooldown (penaliza conta): {health_cooldowns}")
print(f"\nContas em cooldown: {len(cooldown_contas)}")
if cooldown_contas:
    for acc in cooldown_contas[:5]:
        cd = health[acc].get("cooldown_until", "?")
        fails = health[acc].get("consecutive_fails", 0)
        print(f"  {acc}: ate {cd[:16]}, {fails} fails")

print(f"\n{'='*60}")
if health_cooldowns == 0:
    print("✅ PERFEITO: 0 health cooldowns — fix funcionando")
else:
    print(f"⚠️  {health_cooldowns} health cooldowns — investigar")

ssh.close()
