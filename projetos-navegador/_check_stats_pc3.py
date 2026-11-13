import paramiko, re

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
proxy_blacklists = [l for l in lines if "PROXY BLACKLIST" in l]
infra = [l for l in lines if "Chrome morreu" in l]
report_failures = [l for l in lines if "report_failure" in l.lower() or ("[HEALTH]" in l and "falhas seguidas" in l)]
ban_signals = [l for l in lines if "BAN SIGNAL" in l or "BAN DETECTADO" in l]

print(f"Total linhas: {len(lines)}")
print(f"OKs (acoes): {len(oks)}")
print(f"Proxy errors (NAO penaliza conta): {len(proxy_errs)}")
print(f"Proxy blacklists: {len(proxy_blacklists)}")
print(f"Chrome morreu (infra): {len(infra)}")
print(f"Health cooldowns (CONTA penalizada): {len(health_cds)}")
print(f"Ban signals: {len(ban_signals)}")
print()

if oks:
    print("=== ULTIMOS 10 OKs ===")
    for l in oks[-10:]:
        try:
            print(l.strip())
        except UnicodeEncodeError:
            print(l.encode("ascii", errors="replace").decode().strip())

if health_cds:
    print(f"\n=== HEALTH COOLDOWNS ({len(health_cds)}) ===")
    for l in health_cds[-5:]:
        try:
            print(l.strip())
        except UnicodeEncodeError:
            print(l.encode("ascii", errors="replace").decode().strip())

# Contas unicas com OK
accounts_ok = set()
for l in oks:
    m = re.search(r'<- (\S+)', l)
    if m:
        accounts_ok.add(m.group(1))
print(f"\nContas ativas com OKs: {len(accounts_ok)}")
if accounts_ok:
    for a in sorted(accounts_ok):
        cnt = sum(1 for l in oks if a in l)
        try:
            print(f"  {a}: {cnt} OKs")
        except UnicodeEncodeError:
            print(f"  {a.encode('ascii', errors='replace').decode()}: {cnt} OKs")

ssh.close()
