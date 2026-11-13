"""Diagnóstico completo: o que pode ser corrigido."""
import paramiko, re, json
from collections import Counter

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("100.108.160.85", username="Emerson-IA", password="<SEGREDO_REMOVIDO>", timeout=15)

# 1. LOG COMPLETO
cmd = r'powershell -c "Get-Content C:\projetos-navegador\bot_output.log -ErrorAction SilentlyContinue"'
_, stdout, _ = ssh.exec_command(cmd, timeout=30)
raw = stdout.read().decode("utf-8", errors="replace")
lines = raw.splitlines()

# 2. ACCOUNT HEALTH
cmd2 = r'powershell -c "Get-Content C:\projetos-navegador\data\account_health.json -ErrorAction SilentlyContinue"'
_, stdout2, _ = ssh.exec_command(cmd2, timeout=10)
health_raw = stdout2.read().decode("utf-8", errors="replace")
try:
    health = json.loads(health_raw)
except:
    health = {}

# 3. DEAD ACCOUNTS
cmd3 = r'powershell -c "Get-Content C:\projetos-navegador\dead_accounts.txt -ErrorAction SilentlyContinue"'
_, stdout3, _ = ssh.exec_command(cmd3, timeout=10)
dead_raw = stdout3.read().decode("utf-8", errors="replace").strip()
dead_accounts = [l.strip() for l in dead_raw.splitlines() if l.strip()] if dead_raw else []

print("=" * 60)
print("DIAGNOSTICO COMPLETO PC3")
print("=" * 60)

# ERROS POR TIPO
erros = [l for l in lines if "ERRO " in l]
erros_tipo = Counter()
for e in erros:
    if "Navigation to" in e:
        erros_tipo["Navigation timeout (proxy)"] += 1
    elif "Target page" in e or "browser has been closed" in e:
        erros_tipo["Chrome morreu (infra)"] += 1
    elif "Execution context was destroyed" in e:
        erros_tipo["Context destroyed (race)"] += 1
    elif "Timeout" in e or "TUNNEL" in e or "ERR_CONNECTION" in e:
        erros_tipo["Proxy connection"] += 1
    elif "Page.evaluate" in e:
        erros_tipo["Evaluate failed"] += 1
    else:
        erros_tipo["Outro"] += 1

print(f"\n1. TIPOS DE ERRO ({len(erros)} total):")
for tipo, cnt in erros_tipo.most_common():
    print(f"   {tipo}: {cnt}")

# CONTAS COM PROBLEMAS
print(f"\n2. CONTAS ({len(health)} registradas):")
cooldown_contas = []
fail_contas = []
for acc, data in health.items():
    cd = data.get("cooldown_until")
    fails = data.get("consecutive_fails", 0)
    if cd:
        cooldown_contas.append((acc, cd, fails))
    elif fails >= 3:
        fail_contas.append((acc, fails))

if cooldown_contas:
    print(f"   EM COOLDOWN: {len(cooldown_contas)}")
    for acc, cd, fails in cooldown_contas[:5]:
        print(f"      {acc}: cooldown ate {cd[:16]}, {fails} fails")
else:
    print("   EM COOLDOWN: 0 ✅")

if fail_contas:
    print(f"   FALHAS CONSECUTIVAS (>=3): {len(fail_contas)}")
    for acc, fails in fail_contas[:5]:
        print(f"      {acc}: {fails} falhas")

if dead_accounts:
    print(f"   MORTAS (dead_accounts.txt): {len(dead_accounts)}")
    for d in dead_accounts[:5]:
        print(f"      {d}")
else:
    print("   MORTAS: 0 ✅")

# CONTAS QUE NUNCA ENGAJARAM
oks = [l for l in lines if "OK [" in l]
contas_ativas = set()
for l in oks:
    m = re.search(r'<- (\S+)', l)
    if m:
        contas_ativas.add(m.group(1))

todas_contas = set(health.keys())
inativas = todas_contas - contas_ativas
if inativas:
    print(f"   NUNCA ENGAJARAM: {len(inativas)}")
    for i in sorted(inativas)[:10]:
        try:
            print(f"      {i}")
        except:
            pass

# TAXA ATUAL
timestamps = []
for l in lines:
    m = re.match(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]', l)
    if m:
        timestamps.append(m.group(1))

if len(timestamps) >= 2:
    from datetime import datetime
    t0 = datetime.strptime(timestamps[0], "%Y-%m-%d %H:%M:%S")
    t1 = datetime.strptime(timestamps[-1], "%Y-%m-%d %H:%M:%S")
    mins = (t1 - t0).total_seconds() / 60
    print(f"\n3. PERFORMANCE:")
    print(f"   Rodando ha: {mins:.1f} min")
    print(f"   OKs: {len(oks)}")
    print(f"   Taxa: {len(oks)/mins:.1f} OKs/min")
    print(f"   Contas ativas: {len(contas_ativas)}/{len(todas_contas)}")

# SUGESTOES
print(f"\n4. O QUE PODE MELHORAR:")
sugestoes = []

if len(erros_tipo.get("Navigation timeout (proxy)", 0)) > 30:
    sugestoes.append("- Proxies ruins: health check mais agressivo ou trocar pool")

if len(erros_tipo.get("Chrome morreu (infra)", 0)) > 10:
    sugestoes.append("- Chrome instavel: adicionar retry automatico ao relancar")

if len(contas_ativas) < len(todas_contas) * 0.5:
    sugestoes.append(f"- Apenas {len(contas_ativas)}/{len(todas_contas)} contas ativas: verificar scheduler")

if dead_accounts:
    sugestoes.append(f"- {len(dead_accounts)} contas em dead_accounts.txt: limpar se foram erro de proxy")

if len(oks) / mins < 1.5 if mins > 0 else False:
    sugestoes.append("- Taxa baixa (<1.5 OKs/min): aumentar concorrencia ou reduzir delays")

if not sugestoes:
    sugestoes.append("✅ Sistema rodando bem, apenas gargalo de proxies ruins")

for s in sugestoes:
    print(s)

ssh.close()
