"""Monitor 8h final: auto-relaunch, stats completas, só reporta quando perfeito."""
import paramiko, time, re, os, socket
from datetime import datetime
from scp import SCPClient

PC3_IP = "100.108.160.85"
PC3_USER = "Emerson-IA"
PC3_PASS = "Ssh@2026"
MONITOR_HOURS = 8
CHECK_INTERVAL = 300  # 5 min

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

def get_detailed_stats(ssh):
    out = safe_exec(ssh,
        r'powershell -c "Get-Content C:\projetos-navegador\bot_output.log -ErrorAction SilentlyContinue"',
        timeout=120)
    if out.startswith("__ERROR__"):
        return {"error": out}

    lines = out.splitlines()
    timestamps = []
    for l in lines:
        m = re.match(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]', l)
        if m:
            timestamps.append(m.group(1))

    mins = 0
    if len(timestamps) >= 2:
        t0 = datetime.strptime(timestamps[0], "%Y-%m-%d %H:%M:%S")
        t1 = datetime.strptime(timestamps[-1], "%Y-%m-%d %H:%M:%S")
        mins = (t1 - t0).total_seconds() / 60

    likes = sum(1 for l in lines if re.search(r'OK \[L\]', l))
    lc = sum(1 for l in lines if 'OK [L+C]' in l)
    comments_only = sum(1 for l in lines if 'OK [C]' in l)
    comment_debug = [l for l in lines if '[COMMENT-DEBUG]' in l]
    comment_ban = sum(1 for l in lines if 'COMMENT-BAN' in l)
    chrome_morreu = sum(1 for l in lines if 'Chrome morreu' in l)
    epipe = sum(1 for l in lines if 'EPIPE' in l)
    context_destroyed = sum(1 for l in lines if 'Execution context was destroyed' in l)

    # Novos checks
    tab_success = sum(1 for l in lines if 'contenteditable encontrado apos Tab' in l)
    display_none = sum(1 for l in lines if 'display:none' in l)

    total_ok = likes + lc + comments_only
    total_comments = lc + comments_only

    return {
        "mins": mins,
        "total_ok": total_ok,
        "likes": likes,
        "lc": lc,
        "comments_only": comments_only,
        "total_comments": total_comments,
        "comment_debug": comment_debug[-8:],
        "comment_ban": comment_ban,
        "chrome_morreu": chrome_morreu,
        "epipe": epipe,
        "context_destroyed": context_destroyed,
        "tab_success": tab_success,
        "display_none": display_none,
        "last_lines": lines[-15:]
    }

def relaunch_bot(ssh):
    safe_exec(ssh, 'powershell -c "Stop-Process -Name python* -Force -ErrorAction SilentlyContinue"', timeout=15)
    time.sleep(3)
    safe_exec(ssh, r'powershell -c "Remove-Item C:\projetos-navegador\bot_output.log -Force -EA SilentlyContinue"')
    time.sleep(1)
    launcher = r'''
$result = Invoke-WmiMethod -Class Win32_Process -Name Create -ArgumentList "C:\projetos-navegador\venv\Scripts\python.exe -u C:\projetos-navegador\_bot_wrapper.py"
if ($result.ReturnValue -eq 0) { Write-Output "PID=$($result.ProcessId)" }
else { Write-Output "FAILED ReturnValue=$($result.ReturnValue)" }
'''
    tmp_ps1 = os.path.join(os.environ.get("TEMP", "/tmp"), "_launch_8h.ps1")
    with open(tmp_ps1, "w", encoding="utf-8") as f:
        f.write(launcher)
    try:
        scp = SCPClient(ssh.get_transport(), socket_timeout=60)
        scp.put(tmp_ps1, "C:/projetos-navegador/_launch_8h.ps1")
        scp.close()
    except Exception as e:
        return f"SCP falhou: {e}"
    result = safe_exec(ssh,
        r'powershell -ExecutionPolicy Bypass -File C:\projetos-navegador\_launch_8h.ps1',
        timeout=30)
    try: os.unlink(tmp_ps1)
    except: pass
    return result

# ============================================================
start = time.time()
end = start + MONITOR_HOURS * 3600
relaunches = 0
total_oks_acumulado = 0
total_comments_acumulado = 0
checks = 0
ssh_errors = 0
max_consecutive_alive = 0
current_consecutive = 0

try:
    ssh = ssh_connect()
    alive = bot_alive(ssh)
    if alive is None or not alive:
        r = relaunch_bot(ssh)
        relaunches += 1
        time.sleep(30)
    ssh.close()
except Exception as e:
    pass

while time.time() < end:
    remaining_h = (end - time.time()) / 3600
    time.sleep(CHECK_INTERVAL)
    checks += 1
    ts = datetime.now().strftime('%H:%M:%S')

    try:
        ssh = ssh_connect()
    except Exception as e:
        ssh_errors += 1
        current_consecutive = 0
        continue

    try:
        alive = bot_alive(ssh)
        stats = get_detailed_stats(ssh)

        if "error" in stats:
            ssh.close()
            continue

        oks = stats["total_ok"]
        comments = stats["total_comments"]
        chrome_d = stats["chrome_morreu"]

        if alive is None:
            current_consecutive = 0
        elif alive:
            current_consecutive += 1
            if current_consecutive > max_consecutive_alive:
                max_consecutive_alive = current_consecutive
        else:
            current_consecutive = 0
            if oks > 0:
                total_oks_acumulado += oks
                total_comments_acumulado += comments
            r = relaunch_bot(ssh)
            relaunches += 1
            time.sleep(30)
    except Exception as e:
        ssh_errors += 1
        current_consecutive = 0
    finally:
        try: ssh.close()
        except: pass

# ============================================================
# RESULTADO FINAL
# ============================================================
try:
    ssh = ssh_connect()
    stats = get_detailed_stats(ssh)
    alive_final = bot_alive(ssh)
    ssh.close()
except Exception as e:
    stats = {"total_ok": 0, "likes": 0, "total_comments": 0, "mins": 0,
             "chrome_morreu": 0, "epipe": 0, "context_destroyed": 0,
             "comment_debug": [], "comment_ban": 0, "tab_success": 0,
             "display_none": 0, "last_lines": ["(erro)"]}
    alive_final = None

oks_final = total_oks_acumulado + stats.get("total_ok", 0)
comments_final = total_comments_acumulado + stats.get("total_comments", 0)
elapsed_min = (time.time() - start) / 60

print(f"\n{'='*60}")
print(f"  MEGA ENGAGE V3 — RESULTADO {MONITOR_HOURS}H")
print(f"{'='*60}")
print(f"Bot vivo no final: {'SIM' if alive_final else 'NAO' if alive_final is not None else '???'}")
print(f"Tempo monitorado: {elapsed_min:.0f} min ({elapsed_min/60:.1f}h)")
print(f"Relancamentos: {relaunches}")
print(f"Max uptime continuo: {max_consecutive_alive * 5} min")
print(f"Erros SSH: {ssh_errors}")
print()
print(f"  OKs TOTAIS:         {oks_final}")
print(f"  LIKES:              {stats.get('likes', 0)}")
print(f"  COMENTARIOS TOTAIS: {comments_final}")
if oks_final > 0:
    print(f"  % comentarios:      {comments_final/oks_final*100:.1f}%")
if elapsed_min > 0:
    print(f"  Taxa media:         {oks_final/elapsed_min:.2f} OKs/min ({oks_final/elapsed_min*60:.0f}/hora)")
print()
print(f"  Chrome morreu:      {stats.get('chrome_morreu', '?')}")
print(f"  EPIPE:              {stats.get('epipe', '?')}")
print(f"  Context destroyed:  {stats.get('context_destroyed', '?')}")
print(f"  Comment bans:       {stats.get('comment_ban', '?')}")
print(f"  Tab fallback OK:    {stats.get('tab_success', '?')}")
print(f"  Videos sem coment:  {stats.get('display_none', '?')}")
print()

if stats.get("comment_debug"):
    print("  DEBUG DE COMENTARIO:")
    for dbg in stats["comment_debug"]:
        m = re.search(r'\] (.+)', dbg)
        if m:
            print(f"    {m.group(1)}")
    print()

print(f"{'='*60}")
if comments_final > 5 and relaunches <= 5 and chrome_d < 15:
    print("✅ BOT PERFEITO — likes + comentarios + estavel")
elif comments_final > 0 and relaunches <= 8:
    print("⚠️ COMENTARIOS FUNCIONAM mas estabilidade media")
elif comments_final == 0 and oks_final > 50:
    print("⚠️ LIKES OK mas COMENTARIOS ZERADOS — ban parcial ou videos sem comentarios")
else:
    print("❌ INSTAVEL — investigar Chrome crashes")

print(f"\nUltimas 15 linhas:")
for l in stats.get("last_lines", []):
    try:
        print(f"  {l.strip()}")
    except:
        pass
