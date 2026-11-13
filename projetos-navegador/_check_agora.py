"""Check rapido: bot vivo? quantos OKs? que tipo de acoes?"""
import paramiko, re
from datetime import datetime

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("100.108.160.85", username="Emerson-IA", password="<SEGREDO_REMOVIDO>", timeout=30)

# Processo vivo?
_, stdout, _ = ssh.exec_command(
    'powershell -c "Get-Process python* -ErrorAction SilentlyContinue | Select-Object Id,CPU,WorkingSet64 | Format-Table -AutoSize"',
    timeout=20
)
procs = stdout.read().decode("utf-8", errors="replace").strip()
print("=== PROCESSOS ===")
print(procs if procs else "(nenhum — bot MORTO)")

# Log completo
_, stdout, _ = ssh.exec_command(
    r'powershell -c "Get-Content C:\projetos-navegador\bot_output.log -ErrorAction SilentlyContinue"',
    timeout=60
)
raw = stdout.read().decode("utf-8", errors="replace")
lines = raw.splitlines()

# Timestamps
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

# Contar tipos de acao
likes = sum(1 for l in lines if "OK [L]" in l)
comments = sum(1 for l in lines if "OK [C]" in l)
subscribes = sum(1 for l in lines if "OK [S]" in l)
watches = sum(1 for l in lines if "OK [W]" in l)
ok_other = sum(1 for l in lines if "OK [" in l) - likes - comments - subscribes - watches

health_cd = sum(1 for l in lines if "[HEALTH]" in l and "cooldown" in l)
chrome_morreu = sum(1 for l in lines if "Chrome morreu" in l)
proxy_falhou = sum(1 for l in lines if "Proxy falhou" in l)

total_ok = likes + comments + subscribes + watches + ok_other

print(f"\n{'='*50}")
print(f"  ESTADO ATUAL DO BOT")
print(f"{'='*50}")
print(f"Tempo de log: {mins:.1f} min")
print(f"")
print(f"  ACOES BEM-SUCEDIDAS:")
print(f"    Likes [L]:        {likes}")
print(f"    Comentarios [C]:  {comments}")
print(f"    Subscribes [S]:   {subscribes}")
print(f"    Watch time [W]:   {watches}")
if ok_other > 0:
    print(f"    Outros:           {ok_other}")
print(f"    TOTAL:            {total_ok}")
if mins > 0:
    print(f"    Taxa:             {total_ok/mins:.2f}/min ({total_ok/mins*60:.0f}/hora)")
print(f"")
print(f"  ERROS:")
print(f"    Chrome morreu:    {chrome_morreu}")
print(f"    Proxy falhou:     {proxy_falhou}")
print(f"    Health cooldowns: {health_cd}")

# Ultimas 25 linhas
print(f"\n{'='*50}")
print(f"ULTIMAS 25 LINHAS:")
for l in lines[-25:]:
    try:
        print(l.strip())
    except UnicodeEncodeError:
        print(l.encode("ascii", errors="replace").decode().strip())

ssh.close()
