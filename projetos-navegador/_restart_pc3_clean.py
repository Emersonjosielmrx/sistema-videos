"""Kill everything, clean lock, restart bot on PC3."""
import paramiko
import time
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("100.108.160.85", username="Emerson-IA", password="<SEGREDO_REMOVIDO>", timeout=15)

def run(cmd, timeout=30):
    _, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="replace").strip()
    err = stderr.read().decode("utf-8", errors="replace").strip()
    return out, err

# 1) Kill ALL python and chrome
print("1) Kill all processes...")
run('powershell.exe -Command "Get-Process python*,chrome*,chromium* -ErrorAction SilentlyContinue | Stop-Process -Force"')
time.sleep(3)

# Verify
out, _ = run('powershell.exe -Command "(Get-Process python* -ErrorAction SilentlyContinue | Measure-Object).Count"')
print(f"   Python after kill: {out}")
out, _ = run('powershell.exe -Command "(Get-Process chrome*,chromium* -ErrorAction SilentlyContinue | Measure-Object).Count"')
print(f"   Chrome after kill: {out}")

# 2) Remove lock file
print("2) Remove lock file...")
run('powershell.exe -Command "Remove-Item C:/projetos-navegador/engage_bot.lock -Force -ErrorAction SilentlyContinue"')
run('powershell.exe -Command "Remove-Item C:/projetos-navegador/engage_bot.pid -Force -ErrorAction SilentlyContinue"')

# 3) Clean old logs
print("3) Clean old logs...")
run('powershell.exe -Command "Remove-Item C:/projetos-navegador/bot_output.log,C:/projetos-navegador/bot_error.log,C:/projetos-navegador/mega_engage_log.txt -Force -ErrorAction SilentlyContinue"')

# 4) Delete old schtask
print("4) Delete old schtask...")
run('schtasks /Delete /TN MegaEngageBot /F')
time.sleep(1)

# 5) Update the bat to NOT redirect (let schtask + Start-Process handle it)
# Actually, let's use a DIFFERENT approach: write a _start.py that logs to file directly
print("5) Upload improved _launcher.py...")
sftp = ssh.open_sftp()

launcher = b"""import os, sys, traceback

# Setup paths
os.chdir('C:/projetos-navegador')
sys.path.insert(0, 'C:/projetos-navegador')
sys.path.insert(0, 'C:/projetos-navegador/shared')

# Redirect stdout/stderr to file immediately
log_file = open('C:/projetos-navegador/bot_output.log', 'w', encoding='utf-8', buffering=1)
err_file = open('C:/projetos-navegador/bot_error.log', 'w', encoding='utf-8', buffering=1)
sys.stdout = log_file
sys.stderr = err_file

try:
    print("=== Launcher starting ===", flush=True)
    print(f"Python: {sys.version}", flush=True)
    print(f"CWD: {os.getcwd()}", flush=True)
    print(f"Path: {sys.path}", flush=True)

    from engage_modules.main import main
    print("=== Import OK, calling main() ===", flush=True)
    main()
except Exception as e:
    traceback.print_exc(file=err_file)
    err_file.flush()
finally:
    log_file.close()
    err_file.close()
"""

with sftp.open("C:/projetos-navegador/_launcher.py", "wb") as f:
    f.write(launcher)
stat = sftp.stat("C:/projetos-navegador/_launcher.py")
print(f"   _launcher.py: {stat.st_size} bytes")

# 6) Write bat without redirect (launcher handles it)
bat = b"""@echo off
cd /d C:\\projetos-navegador
C:\\Python314\\python.exe C:\\projetos-navegador\\_launcher.py
"""
with sftp.open("C:/projetos-navegador/_run_bot.bat", "wb") as f:
    f.write(bat)
stat = sftp.stat("C:/projetos-navegador/_run_bot.bat")
print(f"   _run_bot.bat: {stat.st_size} bytes")

sftp.close()

# 7) Create and run schtask
print("6) Create schtask...")
out, err = run('schtasks /Create /TN MegaEngageBot /TR "C:\\projetos-navegador\\_run_bot.bat" /SC ONCE /ST 00:00 /F /RU Emerson-IA /RP Ssh@2026')
print(f"   {out}")

print("7) Run schtask...")
out, err = run('schtasks /Run /TN MegaEngageBot')
print(f"   {out}")

# 8) Wait and check
print("8) Waiting 20s...")
time.sleep(20)

out, _ = run('powershell.exe -Command "(Get-Process python* -ErrorAction SilentlyContinue | Measure-Object).Count"')
print(f"   Python: {out}")
out, _ = run('powershell.exe -Command "(Get-Process chrome*,chromium* -ErrorAction SilentlyContinue | Measure-Object).Count"')
print(f"   Chrome: {out}")

# 9) Check logs
print("\n=== bot_output.log ===")
out, _ = run('powershell.exe -Command "Get-Content C:/projetos-navegador/bot_output.log -ErrorAction SilentlyContinue"')
print(out if out else "(vazio)")

print("\n=== bot_error.log ===")
out, _ = run('powershell.exe -Command "Get-Content C:/projetos-navegador/bot_error.log -ErrorAction SilentlyContinue"')
print(out if out else "(sem erros)")

print("\n=== mega_engage_log.txt (tail 20) ===")
out, _ = run('powershell.exe -Command "Get-Content C:/projetos-navegador/mega_engage_log.txt -Tail 20 -ErrorAction SilentlyContinue"')
print(out if out else "(vazio)")

# 10) Task status
print("\n=== Task Status ===")
out, _ = run('schtasks /Query /TN MegaEngageBot /FO LIST')
print(out)

ssh.close()
print("\nDone.")
