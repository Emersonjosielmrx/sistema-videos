"""Monitor 4 horas com auto-relaunch se bot crashar. v2 — robusto a timeouts SSH."""
import paramiko, time, re, os, socket
from datetime import datetime
from scp import SCPClient

PC3_IP = "100.108.160.85"
PC3_USER = "Emerson-IA"
PC3_PASS = "Ssh@2026"
MONITOR_HOURS = 4
CHECK_INTERVAL = 300

def ssh_connect():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(PC3_IP, username=PC3_USER, password=PC3_PASS, timeout=30)
    transport = ssh.get_transport()
    if transport:
        transport.set_keepalive(30)
    return ssh

def safe_exec(ssh, cmd, timeout=30):
    try:
        _, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
        stdout.channel.settimeout(timeout)
        return stdout.read().decode("utf-8", errors="replace").strip()
    except Exception as e:
        return f"__ERROR__:{e}"

def bot_alive(ssh):
    out = safe_exec(ssh,
        'powershell -c "Get-Process python* -ErrorAction SilentlyContinue | Select-Object Id | Format-Table -AutoSize"',
        timeout=20)
    if out.startswith("__ERROR__"):
        return None
    return bool(out and "Id" in out)

def get_ok_count(ssh):
    out = safe_exec(ssh,
        r'powershell -c "(Select-String -Path C:\projetos-navegador\bot_output.log -Pattern \"OK \[\" -EA SilentlyContinue).Count"',
        timeout=30)
    if out.startswith("__ERROR__"):
        return -1
    try:
        return int(out)
    except:
        return 0

def relaunch_bot(ssh):
    safe_exec(ssh, 'powershell -c "Stop-Process -Name python* -Force -ErrorAction SilentlyContinue"', timeout=15)
    time.sleep(3)
    launcher = r'''
$result = Invoke-WmiMethod -Class Win32_Process -Name Create -ArgumentList "C:\projetos-navegador\venv\Scripts\python.exe -u C:\projetos-navegador\_bot_wrapper.py"
if ($result.ReturnValue -eq 0) { Write-Output "PID=$($result.ProcessId)" }
else { Write-Output "FAILED ReturnValue=$($result.ReturnValue)" }
'''
    tmp_ps1 = os.path.join(os.environ.get("TEMP", "/tmp"), "_launch_mon.ps1")
    with open(tmp_ps1, "w", encoding="utf-8") as f:
        f.write(launcher)
    try:
        scp = SCPClient(ssh.get_transport(), socket_timeout=60)
        scp.put(tmp_ps1, "C:/projetos-navegador/_launch_mon.ps1")
        scp.close()
    except Exception as e:
        return f"SCP falhou: {e}"
    result = safe_exec(ssh,
        r'powershell -ExecutionPolicy Bypass -File C:\projetos-navegador\_launch_mon.ps1',
        timeout=30)
    try: os.unlink(tmp_ps1)
    except: pass
    return result

def get_full_stats(ssh):
    out = safe_exec(ssh,
        r'powershell -c "Get-Content C:\projetos-navegador\bot_output.log -ErrorAction SilentlyContinue"',
        timeout=90)
    if out.startswith("__ERROR__"):
        return {"mins": 0, "oks": 0, "health_cd": 0, "proxy_bl": 0,
                "chrome_morreu": 0, "context_destroyed": 0, "epipe": 0,
                "last_lines": [f"(erro lendo log: {out})"]}

    lines = out.splitlines()
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

    return {
        "mins": mins,
        "oks": sum(1 for l in lines if "OK [" in l),
        "health_cd": sum(1 for l in lines if "[HEALTH]" in l and "cooldown" in l),
        "proxy_bl": sum(1 for l in lines if "PROXY BLACKLIST" in l),
        "chrome_morreu": sum(1 for l in lines if "Chrome morreu" in l),
        "context_destroyed": sum(1 for l in lines if "Execution context was destroyed" in l),
        "epipe": sum(1 for l in lines if "EPIPE" in l),
        "last_lines": lines[-10:]
    }

# ============================================================
print(f"MONITOR {MONITOR_HOURS}H v2 — Inicio: {datetime.now().strftime('%H:%M:%S')}")
print(f"Check a cada {CHECK_INTERVAL//60} min, auto-relaunch se crashar\n")

start = time.time()
end = start + MONITOR_HOURS * 3600
relaunches = 0
total_oks_acumulado = 0
checks = 0
ssh_errors = 0

# Primeiro launch
try:
    ssh = ssh_connect()
    alive = bot_alive(ssh)
    if alive is None or not alive:
        print("Bot nao esta rodando, lancando...")
        r = relaunch_bot(ssh)
        print(f"  {r}")
        relaunches += 1
        time.sleep(30)
    else:
        print("Bot ja esta rodando")
    ssh.close()
except Exception as e:
    print(f"Erro inicial: {e} — tentando de novo em 60s")
    time.sleep(60)
    try:
        ssh = ssh_connect()
        r = relaunch_bot(ssh)
        print(f"  Relancado: {r}")
        relaunches += 1
        ssh.close()
    except Exception as e2:
        print(f"FALHA CRITICA: {e2}")

while time.time() < end:
    remaining_h = (end - time.time()) / 3600
    time.sleep(CHECK_INTERVAL)
    checks += 1
    ts = datetime.now().strftime('%H:%M:%S')

    try:
        ssh = ssh_connect()
    except Exception as e:
        ssh_errors += 1
        print(f"[{ts}] Check {checks}: SSH FALHOU ({e}) — retry proximo ciclo | resta {remaining_h:.1f}h")
        continue

    try:
        alive = bot_alive(ssh)
        oks_now = get_ok_count(ssh)

        if alive is None:
            print(f"[{ts}] Check {checks}: INCONCLUSIVO (timeout) | resta {remaining_h:.1f}h")
        elif alive:
            print(f"[{ts}] Check {checks}: VIVO | OKs={oks_now} | resta {remaining_h:.1f}h")
        else:
            print(f"[{ts}] Check {checks}: MORTO | OKs={oks_now} | RELANCANDO...")
            if oks_now > 0:
                total_oks_acumulado += oks_now
            safe_exec(ssh, r'powershell -c "Remove-Item C:\projetos-navegador\bot_output.log -Force -EA SilentlyContinue"')
            time.sleep(1)
            r = relaunch_bot(ssh)
            print(f"  {r}")
            relaunches += 1
            time.sleep(30)
    except Exception as e:
        ssh_errors += 1
        print(f"[{ts}] Check {checks}: EXCEPTION ({e}) | resta {remaining_h:.1f}h")
    finally:
        try: ssh.close()
        except: pass

# ============================================================
# RESULTADO FINAL
# ============================================================
print(f"\n{'='*60}")
print(f"  RESULTADO FINAL — {MONITOR_HOURS} HORAS")
print(f"{'='*60}")

try:
    ssh = ssh_connect()
    stats = get_full_stats(ssh)
    alive_final = bot_alive(ssh)
    ssh.close()
except Exception as e:
    print(f"Erro lendo stats finais: {e}")
    stats = {"mins": 0, "oks": 0, "health_cd": 0, "proxy_bl": 0,
             "chrome_morreu": 0, "context_destroyed": 0, "epipe": 0,
             "last_lines": ["(erro)"]}
    alive_final = None

oks_final = total_oks_acumulado + stats["oks"]
elapsed_min = (time.time() - start) / 60

print(f"Bot vivo no final: {'SIM' if alive_final else 'NAO' if alive_final is not None else '???'}")
print(f"Tempo real monitorado: {elapsed_min:.0f} min ({elapsed_min/60:.1f}h)")
print(f"Relancamentos: {relaunches}")
print(f"Erros SSH: {ssh_errors}")
print(f"")
print(f"  OKs TOTAIS:          {oks_final}")
if elapsed_min > 0:
    print(f"  Taxa media:          {oks_final/elapsed_min:.2f} OKs/min")
    print(f"  Por hora:            {oks_final/elapsed_min * 60:.0f} OKs/hora")
print(f"")
print(f"  Stats do ultimo run:")
print(f"    Tempo log:           {stats['mins']:.1f} min")
print(f"    OKs neste run:       {stats['oks']}")
print(f"    Proxy blacklists:    {stats['proxy_bl']}")
print(f"    Chrome morreu:       {stats['chrome_morreu']}")
print(f"    Context destroyed:   {stats['context_destroyed']}")
print(f"    EPIPE crashes:       {stats['epipe']}")
print(f"    Health cooldowns:    {stats['health_cd']}")
print(f"")
print(f"{'='*60}")
if stats['health_cd'] == 0:
    print("0 health cooldowns injustos em todo o periodo")
else:
    print(f"ALERTA: {stats['health_cd']} health cooldowns")

print(f"\nUltimas 10 linhas do log:")
for l in stats['last_lines']:
    try:
        print(l.strip())
    except UnicodeEncodeError:
        print(l.encode("ascii", errors="replace").decode().strip())
