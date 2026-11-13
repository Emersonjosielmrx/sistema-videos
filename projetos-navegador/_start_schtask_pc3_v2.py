"""Start bot on PC3 using schtasks — v2 with encoding fix."""
import paramiko
import time
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

PC3 = "100.108.160.85"
USER = "Emerson-IA"
PASSW = "Ssh@2026"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(PC3, username=USER, password=PASSW, timeout=15)

def run(cmd, timeout=30):
    _, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="replace").strip()
    err = stderr.read().decode("utf-8", errors="replace").strip()
    return out, err

# Task was already created. Run it now.
print("1) Running schtask...")
out, err = run('schtasks /Run /TN MegaEngageBot', timeout=15)
print(f"   {out}")
if err:
    print(f"   err: {err}")

print("2) Waiting 20s...")
time.sleep(20)

# Check processes
out, _ = run('powershell.exe -Command "(Get-Process python* -ErrorAction SilentlyContinue | Measure-Object).Count"')
print(f"3) Python processes: {out}")

out, _ = run('powershell.exe -Command "(Get-Process chrome*,chromium* -ErrorAction SilentlyContinue | Measure-Object).Count"')
print(f"   Chrome processes: {out}")

# Check logs
print("\n=== bot_output.log (last 40 lines) ===")
out, _ = run('powershell.exe -Command "Get-Content C:/projetos-navegador/bot_output.log -Tail 40 -ErrorAction SilentlyContinue"')
print(out if out else "(vazio)")

print("\n=== bot_error.log (last 40 lines) ===")
out, _ = run('powershell.exe -Command "Get-Content C:/projetos-navegador/bot_error.log -Tail 40 -ErrorAction SilentlyContinue"')
print(out if out else "(sem erros)")

# Task status
print("\n=== Task Status ===")
out, _ = run('schtasks /Query /TN MegaEngageBot /FO LIST', timeout=10)
print(out)

# Also check if _launcher.py exists and has content
print("\n=== _launcher.py ===")
out, _ = run('powershell.exe -Command "Get-Content C:/projetos-navegador/_launcher.py"')
print(out)

ssh.close()
print("\nDone.")
