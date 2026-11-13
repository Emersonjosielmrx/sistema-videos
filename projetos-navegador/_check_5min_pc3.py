"""Espera 5 min e checa log completo do PC3."""
import paramiko, re, time

print("Esperando 5 minutos pra proxies recuperarem...")
time.sleep(300)

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("100.108.160.85", username="Emerson-IA", password="<SEGREDO_REMOVIDO>", timeout=15)

cmd = r'powershell -c "Get-Content C:\projetos-navegador\bot_output.log -ErrorAction SilentlyContinue"'
_, stdout, _ = ssh.exec_command(cmd, timeout=30)
raw = stdout.read().decode("utf-8", errors="replace")
lines = raw.splitlines()

oks = [l for l in lines if "OK [" in l]
proxy_errs = [l for l in lines if "Proxy falhou" in l]
health_cds = [l for l in lines if "[HEALTH]" in l and "cooldown" in l]
infra = [l for l in lines if "Chrome morreu" in l]
ban_signals = [l for l in lines if "BAN SIGNAL" in l or "BAN DETECTADO" in l]

# Tempo de execucao
timestamps = []
for l in lines:
    m = re.match(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]', l)
    if m:
        timestamps.append(m.group(1))

runtime = ""
if len(timestamps) >= 2:
    from datetime import datetime
    t0 = datetime.strptime(timestamps[0], "%Y-%m-%d %H:%M:%S")
    t1 = datetime.strptime(timestamps[-1], "%Y-%m-%d %H:%M:%S")
    diff = t1 - t0
    runtime = f"{diff.total_seconds()/60:.1f} min"

print(f"\nTotal linhas: {len(lines)}")
print(f"Tempo rodando: {runtime}")
print(f"OKs (acoes): {len(oks)}")
print(f"Proxy errors (NAO penaliza conta): {len(proxy_errs)}")
print(f"Chrome morreu (infra): {len(infra)}")
print(f"Health cooldowns (CONTA penalizada): {len(health_cds)}")
print(f"Ban signals: {len(ban_signals)}")

if oks:
    # Taxa por minuto
    if runtime:
        mins = diff.total_seconds() / 60
        if mins > 0:
            print(f"Taxa: {len(oks)/mins:.1f} OKs/min")

# Contas
accounts_ok = {}
for l in oks:
    m = re.search(r'<- (\S+)', l)
    if m:
        a = m.group(1)
        accounts_ok[a] = accounts_ok.get(a, 0) + 1

print(f"\nContas com OKs: {len(accounts_ok)}")
for a in sorted(accounts_ok, key=accounts_ok.get, reverse=True):
    try:
        print(f"  {a}: {accounts_ok[a]}")
    except UnicodeEncodeError:
        pass

# Bot ainda vivo?
_, stdout2, _ = ssh.exec_command(
    r'powershell -c "Get-Process python* -ErrorAction SilentlyContinue | Select-Object Id,CPU | Format-List"',
    timeout=10
)
procs = stdout2.read().decode("utf-8", errors="replace").strip()
print(f"\nProcessos Python: {'SIM' if procs else 'NAO (morreu!)'}")
if procs:
    print(procs[:200])

# Ultimas 10 linhas
print("\n=== ULTIMAS 10 LINHAS ===")
for l in lines[-10:]:
    try:
        print(l.strip())
    except UnicodeEncodeError:
        print(l.encode("ascii", errors="replace").decode().strip())

ssh.close()
