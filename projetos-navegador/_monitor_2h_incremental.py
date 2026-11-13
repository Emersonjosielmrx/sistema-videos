"""Monitor 2h com output incremental e auto-relaunch."""
import paramiko, time, re, os
from datetime import datetime
from scp import SCPClient

PC3_IP = "100.108.160.85"
PC3_USER = "Emerson-IA"
PC3_PASS = "Ssh@2026"
MONITOR_HOURS = 2
CHECK_INTERVAL = 300

def ssh_connect():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(PC3_IP, username=PC3_USER, password=PC3_PASS, timeout=30)
    t = ssh.get_transport()
    if t: t.set_keepalive(30)
    return ssh

def bot_alive(ssh):
    try:
        _, stdout, _ = ssh.exec_command(
            'powershell -c "Get-Process python* -EA SilentlyContinue | Select Id | Format-Table -A"',
            timeout=20)
        stdout.channel.settimeout(20)
        out = stdout.read().decode("utf-8", errors="replace").strip()
        return bool(out and "Id" in out)
    except:
        return None

def get_stats(ssh):
    try:
        _, stdout, _ = ssh.exec_command(
            r'powershell -c "Get-Content C:\projetos-navegador\bot_output.log -EA SilentlyContinue"',
            timeout=90)
        stdout.channel.settimeout(90)
        raw = stdout.read().decode("utf-8", errors="replace")
        lines = raw.splitlines()

        likes = sum(1 for l in lines if 'OK [L]' in l)
        lc = sum(1 for l in lines if 'OK [L+C]' in l)
        comments = sum(1 for l in lines if 'OK [C]' in l)
        chrome_d = sum(1 for l in lines if 'Chrome morreu' in l)

        return {
            "total": likes + lc + comments,
            "likes": likes,
            "comments": lc + comments,
            "chrome_d": chrome_d,
            "lines": lines
        }
    except:
        return {"total": 0, "likes": 0, "comments": 0, "chrome_d": 0, "lines": []}

def relaunch(ssh):
    try:
        ssh.exec_command('powershell -c "Stop-Process -Name python* -Force -EA SilentlyContinue"', timeout=15)
        time.sleep(3)
        ssh.exec_command(r'powershell -c "Remove-Item C:\projetos-navegador\bot_output.log -Force -EA SilentlyContinue"')
        time.sleep(1)

        launcher = r'''
$r = Invoke-WmiMethod -Class Win32_Process -Name Create -ArgumentList "C:\projetos-navegador\venv\Scripts\python.exe -u C:\projetos-navegador\_bot_wrapper.py"
if ($r.ReturnValue -eq 0) { Write-Output "PID=$($r.ProcessId)" }
else { Write-Output "FAIL=$($r.ReturnValue)" }
'''
        tmp = os.path.join(os.environ.get("TEMP", "/tmp"), f"_rl_{int(time.time())}.ps1")
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(launcher)

        scp = SCPClient(ssh.get_transport(), socket_timeout=60)
        scp.put(tmp, "C:/projetos-navegador/_rl_tmp.ps1")
        scp.close()
        os.unlink(tmp)

        _, stdout, _ = ssh.exec_command(
            r'powershell -ExecutionPolicy Bypass -File C:\projetos-navegador\_rl_tmp.ps1',
            timeout=30)
        result = stdout.read().decode("utf-8", errors="replace").strip()
        return result
    except Exception as e:
        return f"ERRO: {e}"

# ============================================================
print(f"[{datetime.now().strftime('%H:%M:%S')}] Monitor {MONITOR_HOURS}h iniciado")
print(f"Check a cada {CHECK_INTERVAL//60} min")
print()

start = time.time()
end = start + MONITOR_HOURS * 3600
relaunches = 0
checks = 0
max_uptime = 0
current_uptime = 0

# Checa se bot já está vivo
try:
    ssh = ssh_connect()
    alive = bot_alive(ssh)
    if not alive:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Bot morto, relancando...")
        r = relaunch(ssh)
        print(f"  {r}")
        relaunches += 1
        time.sleep(30)
    else:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Bot ja esta rodando")
    ssh.close()
except Exception as e:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Erro inicial: {e}")

while time.time() < end:
    time.sleep(CHECK_INTERVAL)
    checks += 1
    ts = datetime.now().strftime('%H:%M:%S')
    remaining_min = (end - time.time()) / 60

    try:
        ssh = ssh_connect()
        alive = bot_alive(ssh)
        stats = get_stats(ssh)

        if alive:
            current_uptime += 5
            if current_uptime > max_uptime:
                max_uptime = current_uptime

            print(f"[{ts}] Check {checks}: VIVO ({current_uptime}min) | OK={stats['total']} L={stats['likes']} C={stats['comments']} ChromeDead={stats['chrome_d']} | resta {remaining_min:.0f}min")
        else:
            current_uptime = 0
            print(f"[{ts}] Check {checks}: MORTO | OK={stats['total']} L={stats['likes']} C={stats['comments']} | RELANCANDO...")
            r = relaunch(ssh)
            print(f"  {r}")
            relaunches += 1
            time.sleep(30)

        ssh.close()
    except Exception as e:
        print(f"[{ts}] Check {checks}: ERRO ({str(e)[:60]}) | resta {remaining_min:.0f}min")
        current_uptime = 0

# RESULTADO FINAL
print(f"\n{'='*60}")
print(f"RESULTADO {MONITOR_HOURS}H")
print(f"{'='*60}")

try:
    ssh = ssh_connect()
    alive_final = bot_alive(ssh)
    stats_final = get_stats(ssh)
    ssh.close()

    print(f"Bot vivo no final: {'SIM' if alive_final else 'NAO'}")
    print(f"Relancamentos: {relaunches}")
    print(f"Max uptime continuo: {max_uptime} min")
    print()
    print(f"  OKs totais:    {stats_final['total']}")
    print(f"  Likes:         {stats_final['likes']}")
    print(f"  Comentarios:   {stats_final['comments']}")
    print(f"  Chrome morreu: {stats_final['chrome_d']}")
    print()

    if stats_final['comments'] > 0 and relaunches <= 3:
        print("[OK] FUNCIONANDO -- likes + comentarios + estavel")
    elif stats_final['comments'] > 0:
        print("[WARN] COMENTARIOS OK mas instavel")
    elif stats_final['total'] > 20 and stats_final['comments'] == 0:
        print("[WARN] LIKES OK mas 0 COMENTARIOS")
    else:
        print("[FAIL] PROBLEMAS")

    print("\nUltimas 10 linhas:")
    for l in stats_final['lines'][-10:]:
        print(f"  {l.strip()}")
except Exception as e:
    print(f"Erro lendo stats finais: {e}")
