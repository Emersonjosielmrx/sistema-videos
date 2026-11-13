"""Monitor 6h resiliente: auto-relaunch, stats detalhadas, diagnóstico de comentários."""
import paramiko, time, re, os, socket
from datetime import datetime
from scp import SCPClient

PC3_IP = "100.108.160.85"
PC3_USER = "Emerson-IA"
PC3_PASS = "Ssh@2026"
MONITOR_HOURS = 6
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
    replies = sum(1 for l in lines if 'REPLY' in l)
    comment_debug = [l for l in lines if '[COMMENT-DEBUG]' in l]
    comment_ban = sum(1 for l in lines if 'COMMENT-BAN' in l)
    chrome_morreu = sum(1 for l in lines if 'Chrome morreu' in l)
    epipe = sum(1 for l in lines if 'EPIPE' in l)
    context_destroyed = sum(1 for l in lines if 'Execution context was destroyed' in l)

    total_ok = likes + lc + comments_only
    total_comments = lc + comments_only

    return {
        "mins": mins,
        "total_ok": total_ok,
        "likes": likes,
        "lc": lc,
        "comments_only": comments_only,
        "total_comments": total_comments,
        "replies": replies,
        "comment_debug": comment_debug[-5:],
        "comment_ban": comment_ban,
        "chrome_morreu": chrome_morreu,
        "epipe": epipe,
        "context_destroyed": context_destroyed,
        "last_lines": lines[-10:]
    }

def relaunch_bot(ssh):
    safe_exec(ssh, 'powershell -c "Stop-Process -Name python* -Force -ErrorAction SilentlyContinue"', timeout=15)
    time.sleep(3)
    # Limpa log pra novo run
    safe_exec(ssh, r'powershell -c "Remove-Item C:\projetos-navegador\bot_output.log -Force -EA SilentlyContinue"')
    time.sleep(1)
    launcher = r'''
$result = Invoke-WmiMethod -Class Win32_Process -Name Create -ArgumentList "C:\projetos-navegador\venv\Scripts\python.exe -u C:\projetos-navegador\_bot_wrapper.py"
if ($result.ReturnValue -eq 0) { Write-Output "PID=$($result.ProcessId)" }
else { Write-Output "FAILED ReturnValue=$($result.ReturnValue)" }
'''
    tmp_ps1 = os.path.join(os.environ.get("TEMP", "/tmp"), "_launch_mon6h.ps1")
    with open(tmp_ps1, "w", encoding="utf-8") as f:
        f.write(launcher)
    try:
        scp = SCPClient(ssh.get_transport(), socket_timeout=60)
        scp.put(tmp_ps1, "C:/projetos-navegador/_launch_mon6h.ps1")
        scp.close()
    except Exception as e:
        return f"SCP falhou: {e}"
    result = safe_exec(ssh,
        r'powershell -ExecutionPolicy Bypass -File C:\projetos-navegador\_launch_mon6h.ps1',
        timeout=30)
    try: os.unlink(tmp_ps1)
    except: pass
    return result

# ============================================================
print(f"MONITOR {MONITOR_HOURS}H — Inicio: {datetime.now().strftime('%H:%M:%S')}")
print(f"Check a cada {CHECK_INTERVAL//60} min, auto-relaunch se crashar\n")

start = time.time()
end = start + MONITOR_HOURS * 3600
relaunches = 0
total_oks_acumulado = 0
total_comments_acumulado = 0
checks = 0
ssh_errors = 0
max_consecutive_alive = 0
current_consecutive = 0

# Verifica se bot já está vivo (hotfix 5 acabou de lançar)
try:
    ssh = ssh_connect()
    alive = bot_alive(ssh)
    if alive is None or not alive:
        print("Bot não está rodando, lançando...")
        r = relaunch_bot(ssh)
        print(f"  {r}")
        relaunches += 1
        time.sleep(30)
    else:
        print("Bot já está rodando (do hotfix 5)")
    ssh.close()
except Exception as e:
    print(f"Erro inicial: {e}")

while time.time() < end:
    remaining_h = (end - time.time()) / 3600
    time.sleep(CHECK_INTERVAL)
    checks += 1
    ts = datetime.now().strftime('%H:%M:%S')
    elapsed_total_min = (time.time() - start) / 60

    try:
        ssh = ssh_connect()
    except Exception as e:
        ssh_errors += 1
        print(f"[{ts}] Check {checks}: SSH FALHOU ({e}) | resta {remaining_h:.1f}h")
        current_consecutive = 0
        continue

    try:
        alive = bot_alive(ssh)
        stats = get_detailed_stats(ssh)

        if "error" in stats:
            print(f"[{ts}] Check {checks}: ERRO lendo stats ({stats['error'][:50]}) | resta {remaining_h:.1f}h")
            ssh.close()
            continue

        oks = stats["total_ok"]
        comments = stats["total_comments"]
        chrome_d = stats["chrome_morreu"]

        if alive is None:
            print(f"[{ts}] Check {checks}: INCONCLUSIVO (timeout) | resta {remaining_h:.1f}h")
            current_consecutive = 0
        elif alive:
            current_consecutive += 1
            if current_consecutive > max_consecutive_alive:
                max_consecutive_alive = current_consecutive

            rate = oks / stats["mins"] if stats["mins"] > 0 else 0
            cmt_pct = (comments / oks * 100) if oks > 0 else 0

            line = (f"[{ts}] Check {checks}: VIVO ({current_consecutive*5}min) "
                    f"| OK={oks} ({rate:.1f}/min) "
                    f"| L={stats['likes']} C={comments} "
                    f"| Chrome☠={chrome_d} "
                    f"| resta {remaining_h:.1f}h")
            print(line)

            # Mostra debug de comentários se houve
            if stats["comment_debug"]:
                for dbg in stats["comment_debug"]:
                    m = re.search(r'\] (.+)', dbg)
                    if m:
                        print(f"  💬 {m.group(1)}")
        else:
            current_consecutive = 0
            print(f"[{ts}] Check {checks}: MORTO | OK={oks} L={stats['likes']} C={comments} | RELANÇANDO...")
            if oks > 0:
                total_oks_acumulado += oks
                total_comments_acumulado += comments
            r = relaunch_bot(ssh)
            print(f"  {r}")
            relaunches += 1
            time.sleep(30)
    except Exception as e:
        ssh_errors += 1
        print(f"[{ts}] Check {checks}: EXCEPTION ({e}) | resta {remaining_h:.1f}h")
        current_consecutive = 0
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
    stats = get_detailed_stats(ssh)
    alive_final = bot_alive(ssh)
    ssh.close()
except Exception as e:
    print(f"Erro lendo stats finais: {e}")
    stats = {"total_ok": 0, "likes": 0, "total_comments": 0, "mins": 0,
             "chrome_morreu": 0, "epipe": 0, "context_destroyed": 0,
             "comment_debug": [], "comment_ban": 0, "last_lines": ["(erro)"]}
    alive_final = None

oks_final = total_oks_acumulado + stats.get("total_ok", 0)
comments_final = total_comments_acumulado + stats.get("total_comments", 0)
elapsed_min = (time.time() - start) / 60

print(f"Bot vivo no final: {'SIM' if alive_final else 'NAO' if alive_final is not None else '???'}")
print(f"Tempo monitorado: {elapsed_min:.0f} min ({elapsed_min/60:.1f}h)")
print(f"Relançamentos: {relaunches}")
print(f"Max uptime contínuo: {max_consecutive_alive * 5} min")
print(f"Erros SSH: {ssh_errors}")
print()
print(f"  OKs TOTAIS:         {oks_final}")
print(f"  COMENTÁRIOS TOTAIS: {comments_final}")
if oks_final > 0:
    print(f"  % comentários:      {comments_final/oks_final*100:.1f}%")
if elapsed_min > 0:
    print(f"  Taxa média:         {oks_final/elapsed_min:.2f} OKs/min ({oks_final/elapsed_min*60:.0f}/hora)")
print()
print(f"  Chrome morreu:      {stats.get('chrome_morreu', '?')}")
print(f"  EPIPE:              {stats.get('epipe', '?')}")
print(f"  Context destroyed:  {stats.get('context_destroyed', '?')}")
print(f"  Comment bans:       {stats.get('comment_ban', '?')}")
print()

if stats.get("comment_debug"):
    print("  ÚLTIMOS DEBUG DE COMENTÁRIO:")
    for dbg in stats["comment_debug"]:
        m = re.search(r'\] (.+)', dbg)
        if m:
            print(f"    {m.group(1)}")
    print()

print(f"{'='*60}")
if comments_final > 0 and relaunches <= 3:
    print("✅ BOT FUNCIONANDO — likes + comentários + estável")
elif comments_final > 0 and relaunches > 3:
    print("⚠️ COMENTÁRIOS OK, mas instável (muitos relançamentos)")
elif comments_final == 0 and oks_final > 0:
    print("❌ LIKES OK mas COMENTÁRIOS ZERADOS — investigar seletores/comment_banned")
else:
    print("❌ BOT COM PROBLEMAS — investigar logs")

print(f"\nÚltimas 10 linhas:")
for l in stats.get("last_lines", []):
    try:
        print(f"  {l.strip()}")
    except:
        pass
