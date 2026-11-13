"""Start bot on PC3 using schtasks (Windows Task Scheduler) — most reliable for SSH."""
import paramiko
import time

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

# 1) Kill old
print("1) Kill old processes...")
run('powershell.exe -Command "Get-Process python*,chrome* -ErrorAction SilentlyContinue | Stop-Process -Force"')
time.sleep(2)

# 2) Test Python can import our modules — via cmd.exe to bypass PowerShell
print("2) Test Python import via cmd.exe...")
out, err = run(
    'cmd.exe /c "C:\\Python314\\python.exe -c "import sys; print(sys.version)""',
    timeout=15
)
print(f"   Python version: {out}")
if err:
    print(f"   ERR: {err}")

# 3) Create a wrapper .bat that schtasks will run
print("3) Creating wrapper .bat...")
# Use powershell Set-Content to write the file (avoids quoting issues)
bat_lines = [
    "@echo off",
    "cd /d C:\\projetos-navegador",
    "C:\\Python314\\python.exe C:\\projetos-navegador\\_launcher.py >> C:\\projetos-navegador\\bot_output.log 2>> C:\\projetos-navegador\\bot_error.log",
]
# Write each line via PowerShell (most reliable on this machine)
bat_content = "\\r\\n".join(bat_lines)
run(
    f'powershell.exe -Command "Set-Content -Path \'C:/projetos-navegador/_run_bot.bat\' -Value (\'{bat_content}\')"',
    timeout=10
)
# Verify
out, _ = run('powershell.exe -Command "(Get-Item C:/projetos-navegador/_run_bot.bat).Length"')
print(f"   _run_bot.bat: {out} bytes")

# 4) Clear old logs
print("4) Clear old logs...")
run('powershell.exe -Command "Remove-Item C:/projetos-navegador/bot_output.log,C:/projetos-navegador/bot_error.log -Force -ErrorAction SilentlyContinue"')

# 5) Delete old scheduled task if exists
print("5) Remove old schtask...")
run('schtasks /Delete /TN MegaEngageBot /F', timeout=10)
time.sleep(1)

# 6) Create scheduled task to run NOW
print("6) Creating schtask...")
# schtasks via cmd.exe — no PowerShell quoting issues
out, err = run(
    'schtasks /Create /TN MegaEngageBot /TR "C:\\projetos-navegador\\_run_bot.bat" /SC ONCE /ST 00:00 /F /RU Emerson-IA /RP Ssh@2026',
    timeout=15
)
print(f"   Create: {out}")
if err:
    print(f"   ERR: {err}")

# 7) Run the task immediately
print("7) Running schtask NOW...")
out, err = run('schtasks /Run /TN MegaEngageBot', timeout=15)
print(f"   Run: {out}")
if err:
    print(f"   ERR: {err}")

# 8) Wait and check
print("8) Waiting 15s for bot to start...")
time.sleep(15)

out, _ = run('powershell.exe -Command "(Get-Process python* -ErrorAction SilentlyContinue | Measure-Object).Count"')
print(f"   Python processes: {out}")

out, _ = run('powershell.exe -Command "(Get-Process chrome*,chromium* -ErrorAction SilentlyContinue | Measure-Object).Count"')
print(f"   Chrome processes: {out}")

# 9) Check logs
print("\n=== bot_output.log (last 30 lines) ===")
out, _ = run('powershell.exe -Command "Get-Content C:/projetos-navegador/bot_output.log -Tail 30 -ErrorAction SilentlyContinue"')
print(out if out else "(empty)")

print("\n=== bot_error.log (last 30 lines) ===")
out, _ = run('powershell.exe -Command "Get-Content C:/projetos-navegador/bot_error.log -Tail 30 -ErrorAction SilentlyContinue"')
print(out if out else "(no errors)")

# 10) Check task status
print("\n=== Task Status ===")
out, _ = run('schtasks /Query /TN MegaEngageBot /FO LIST', timeout=10)
print(out)

ssh.close()
print("\nDone.")
