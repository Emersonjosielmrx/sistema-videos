"""Monitor 2h leve - roda local, checa PC3 a cada 10 min.
Output ASCII only (sem emoji pra nao crashar charmap Windows)."""
import paramiko, time, os
from datetime import datetime

PC3_IP = "100.108.160.85"
PC3_USER = "Emerson-IA"
PC3_PASS = "Ssh@2026"
MONITOR_HOURS = 2
CHECK_INTERVAL = 600  # 10 min

REPORT = os.path.join(os.path.dirname(__file__), "_monitor_report.txt")


def log(msg):
    ts = datetime.now().strftime('%H:%M:%S')
    line = f"[{ts}] {msg}"
    # ASCII safe
    line = line.encode('ascii', errors='replace').decode('ascii')
    print(line, flush=True)
    with open(REPORT, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def ssh_connect():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(PC3_IP, username=PC3_USER, password=PC3_PASS, timeout=30)
    t = ssh.get_transport()
    if t:
        t.set_keepalive(30)
    return ssh


def run_cmd(ssh, cmd, timeout=30):
    _, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    stdout.channel.settimeout(timeout)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    return out + err


def bot_alive(ssh):
    try:
        out = run_cmd(ssh, 'powershell -c "(Get-Process python* -EA SilentlyContinue).Count"', 15)
        n = out.strip()
        return int(n) > 0 if n.isdigit() else False
    except Exception:
        return None


def get_stats(ssh):
    try:
        out = run_cmd(ssh,
            r'powershell -ExecutionPolicy Bypass -File C:\projetos-navegador\_check_logs.ps1',
            60)
        safe = out.encode('ascii', errors='replace').decode('ascii')

        # Parse stats from output
        lines = safe.split('\n')
        size = 0
        log_lines = []
        for line in lines:
            if 'Size:' in line and 'bytes' in line:
                try:
                    size = int(line.split('Size:')[1].split('bytes')[0].strip())
                except Exception:
                    pass
            log_lines.append(line.rstrip())

        # Count from bot_output.log directly
        out2 = run_cmd(ssh,
            r'powershell -c "Get-Content C:\projetos-navegador\bot_output.log -EA SilentlyContinue"',
            60)
        bot_lines = out2.split('\n')
        likes = sum(1 for l in bot_lines if 'OK [L]' in l)
        lc = sum(1 for l in bot_lines if 'OK [L+C]' in l)
        comments = sum(1 for l in bot_lines if 'OK [C]' in l)
        chrome_dead = sum(1 for l in bot_lines if 'Chrome morreu' in l)
        comment_debug = sum(1 for l in bot_lines if 'COMMENT-DEBUG' in l)
        errors = sum(1 for l in bot_lines if 'ERRO ' in l)
        bans = sum(1 for l in bot_lines if 'COMMENT-BAN' in l)

        # Last 5 meaningful lines
        meaningful = [l.strip() for l in bot_lines if l.strip() and '[2026-' in l]
        last5 = meaningful[-5:] if len(meaningful) >= 5 else meaningful

        return {
            "size": size,
            "likes": likes + lc,
            "comments": lc + comments,
            "chrome_dead": chrome_dead,
            "errors": errors,
            "comment_debug": comment_debug,
            "bans": bans,
            "total_lines": len([l for l in bot_lines if l.strip()]),
            "last5": last5,
        }
    except Exception as e:
        return {"error": str(e)}


def relaunch(ssh):
    try:
        run_cmd(ssh, 'powershell -c "Stop-Process -Name python* -Force -EA SilentlyContinue; Stop-Process -Name chrome* -Force -EA SilentlyContinue"', 20)
        time.sleep(5)
        run_cmd(ssh, r'powershell -c "Remove-Item C:\projetos-navegador\bot_output.log -Force -EA SilentlyContinue"', 10)
        time.sleep(1)
        out = run_cmd(ssh, r'powershell -ExecutionPolicy Bypass -File C:\projetos-navegador\_launch_bot.ps1', 30)
        return out.strip()
    except Exception as e:
        return f"ERRO: {e}"


# ============================================================
# MAIN
# ============================================================
with open(REPORT, "w", encoding="utf-8") as f:
    f.write("")

log(f"Monitor {MONITOR_HOURS}h iniciado (check cada {CHECK_INTERVAL//60} min)")

start = time.time()
end = start + MONITOR_HOURS * 3600
relaunches = 0
checks = 0
max_likes = 0
max_comments = 0

while time.time() < end:
    time.sleep(CHECK_INTERVAL)
    checks += 1
    remaining = (end - time.time()) / 60

    try:
        ssh = ssh_connect()
        alive = bot_alive(ssh)
        stats = get_stats(ssh)

        if "error" in stats:
            log(f"Check {checks}: ERRO stats ({stats['error']}) | resta {remaining:.0f}min")
            ssh.close()
            continue

        likes = stats["likes"]
        comments = stats["comments"]
        if likes > max_likes:
            max_likes = likes
        if comments > max_comments:
            max_comments = comments

        status = "VIVO" if alive else "MORTO"
        log(f"Check {checks}: {status} | L={likes} C={comments} Err={stats['errors']} ChromeDead={stats['chrome_dead']} ComDebug={stats['comment_debug']} Bans={stats['bans']} Lines={stats['total_lines']} | {remaining:.0f}min")

        if not alive:
            log(f"  Relancando bot...")
            r = relaunch(ssh)
            log(f"  {r.encode('ascii', errors='replace').decode('ascii')}")
            relaunches += 1
            time.sleep(30)

        # Print last line
        if stats.get("last5"):
            last = stats["last5"][-1].encode('ascii', errors='replace').decode('ascii')
            log(f"  Ultimo: {last[:120]}")

        ssh.close()
    except Exception as e:
        safe = str(e).encode('ascii', errors='replace').decode('ascii')
        log(f"Check {checks}: CONEXAO FALHOU ({safe[:60]}) | {remaining:.0f}min")

# RESULTADO FINAL
log("")
log("=" * 60)
log(f"RESULTADO {MONITOR_HOURS}H")
log("=" * 60)

try:
    ssh = ssh_connect()
    alive = bot_alive(ssh)
    stats = get_stats(ssh)
    ssh.close()

    if "error" not in stats:
        log(f"Bot vivo: {'SIM' if alive else 'NAO'}")
        log(f"Relancamentos: {relaunches}")
        log(f"Likes: {stats['likes']}")
        log(f"Comentarios: {stats['comments']}")
        log(f"Chrome morreu: {stats['chrome_dead']}")
        log(f"Erros: {stats['errors']}")
        log(f"Comment-ban: {stats['bans']}")
        log("")

        if stats["likes"] > 20 and stats["comments"] > 0 and relaunches <= 2:
            log("[OK] FUNCIONANDO PERFEITO -- likes + comentarios + estavel")
        elif stats["likes"] > 20 and relaunches <= 2:
            log("[OK] LIKES ESTAVEIS -- bot robusto, comentarios shadowban YouTube")
        elif stats["likes"] > 0 and stats["comments"] == 0:
            log("[WARN] LIKES OK mas 0 COMENTARIOS (shadowban)")
        else:
            log("[FAIL] PROBLEMAS")

        if stats.get("last5"):
            log("")
            log("Ultimas linhas:")
            for l in stats["last5"]:
                log(f"  {l.encode('ascii', errors='replace').decode('ascii')[:120]}")
    else:
        log(f"Erro stats finais: {stats['error']}")
except Exception as e:
    log(f"Erro final: {e}")

log("Monitor finalizado.")
