"""Watchdog que roda NO PC3: auto-relaunch do bot + stats a cada 5 min.
Output vai pra C:\projetos-navegador\_watchdog_output.txt
Roda por MONITOR_HOURS e depois para."""
import subprocess, time, os, sys, re
from datetime import datetime

BOT_CMD = r"C:\projetos-navegador\venv\Scripts\python.exe"
BOT_SCRIPT = r"C:\projetos-navegador\_bot_wrapper.py"
BOT_LOG = r"C:\projetos-navegador\bot_output.log"
WATCHDOG_LOG = r"C:\projetos-navegador\_watchdog_output.txt"
MONITOR_HOURS = 2
CHECK_INTERVAL = 300  # 5 min

def log(msg):
    ts = datetime.now().strftime('%H:%M:%S')
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(WATCHDOG_LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def bot_alive():
    try:
        r = subprocess.run(
            ["powershell", "-c",
             "Get-Process python* -EA SilentlyContinue | Where-Object {$_.Id -ne " + str(os.getpid()) + "} | Select Id | Format-Table -A"],
            capture_output=True, text=True, timeout=15)
        out = r.stdout.strip()
        return bool(out and "Id" in out)
    except:
        return False

def kill_bot():
    try:
        subprocess.run(
            ["powershell", "-c",
             "Get-Process python* -EA SilentlyContinue | Where-Object {$_.Id -ne " + str(os.getpid()) + "} | Stop-Process -Force"],
            capture_output=True, timeout=15)
    except:
        pass

def launch_bot():
    try:
        if os.path.exists(BOT_LOG):
            os.remove(BOT_LOG)
    except:
        pass
    subprocess.Popen(
        [BOT_CMD, "-u", BOT_SCRIPT],
        cwd=r"C:\projetos-navegador",
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW
    )

def get_stats():
    try:
        with open(BOT_LOG, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        likes = sum(1 for l in lines if "OK [L]" in l)
        lc = sum(1 for l in lines if "OK [L+C]" in l)
        comments = sum(1 for l in lines if "OK [C]" in l)
        chrome_d = sum(1 for l in lines if "Chrome morreu" in l)
        return {"total": likes + lc + comments, "likes": likes,
                "comments": lc + comments, "chrome_d": chrome_d, "log_lines": len(lines)}
    except:
        return {"total": 0, "likes": 0, "comments": 0, "chrome_d": 0, "log_lines": 0}

# ============================================================
with open(WATCHDOG_LOG, "w", encoding="utf-8") as f:
    f.write("")

log(f"Watchdog {MONITOR_HOURS}h iniciado (PID={os.getpid()})")
log(f"Check a cada {CHECK_INTERVAL//60} min")

start = time.time()
end = start + MONITOR_HOURS * 3600
relaunches = 0
max_uptime = 0
current_uptime = 0
checks = 0

if not bot_alive():
    log("Bot morto, lancando...")
    kill_bot()
    time.sleep(2)
    launch_bot()
    relaunches += 1
    time.sleep(30)
else:
    log("Bot ja rodando")

while time.time() < end:
    time.sleep(CHECK_INTERVAL)
    checks += 1
    remaining_min = (end - time.time()) / 60

    alive = bot_alive()
    stats = get_stats()

    if alive:
        current_uptime += 5
        if current_uptime > max_uptime:
            max_uptime = current_uptime
        log(f"Check {checks}: VIVO ({current_uptime}min) | OK={stats['total']} L={stats['likes']} C={stats['comments']} ChromeDead={stats['chrome_d']} loglines={stats['log_lines']} | resta {remaining_min:.0f}min")
    else:
        current_uptime = 0
        log(f"Check {checks}: MORTO | OK={stats['total']} L={stats['likes']} C={stats['comments']} | RELANCANDO...")
        kill_bot()
        time.sleep(2)
        launch_bot()
        relaunches += 1
        time.sleep(30)

# RESULTADO FINAL
log("")
log("=" * 60)
log(f"RESULTADO {MONITOR_HOURS}H")
log("=" * 60)

alive_final = bot_alive()
stats_final = get_stats()

log(f"Bot vivo no final: {'SIM' if alive_final else 'NAO'}")
log(f"Relancamentos: {relaunches}")
log(f"Max uptime continuo: {max_uptime} min")
log(f"  OKs totais:    {stats_final['total']}")
log(f"  Likes:         {stats_final['likes']}")
log(f"  Comentarios:   {stats_final['comments']}")
log(f"  Chrome morreu: {stats_final['chrome_d']}")

if stats_final['comments'] > 0 and relaunches <= 3:
    log("[OK] FUNCIONANDO -- likes + comentarios + estavel")
elif stats_final['comments'] > 0:
    log("[WARN] COMENTARIOS OK mas instavel")
elif stats_final['total'] > 20 and stats_final['comments'] == 0:
    log("[WARN] LIKES OK mas 0 COMENTARIOS (provavel shadowban)")
else:
    log("[FAIL] PROBLEMAS")

log("Watchdog finalizado.")
