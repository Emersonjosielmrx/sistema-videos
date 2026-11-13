"""Diagnose PC3 — check logins, error logs, re-read output."""
import paramiko
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

# Check if Python is running
out, _ = run('powershell.exe -Command "(Get-Process python* -ErrorAction SilentlyContinue | Measure-Object).Count"')
print(f"Python: {out}")

# Read ALL of bot_error.log (it has 119-ish bytes from the .bat wrapper)
print("\n=== bot_error.log (FULL) ===")
out, _ = run('powershell.exe -Command "Get-Content C:/projetos-navegador/bot_error.log -ErrorAction SilentlyContinue"')
print(out if out else "(vazio)")

# Read ALL of bot_output.log
print("\n=== bot_output.log (FULL) ===")
out, _ = run('powershell.exe -Command "Get-Content C:/projetos-navegador/bot_output.log -ErrorAction SilentlyContinue"')
print(out if out else "(vazio)")

# Check C:/logins-google
print("\n=== C:/logins-google ===")
out, _ = run('powershell.exe -Command "Test-Path C:/logins-google"')
print(f"  exists: {out}")

out, _ = run('powershell.exe -Command "if (Test-Path C:/logins-google) { Get-ChildItem C:/logins-google | Select-Object Name | Format-Table -AutoSize } else { \'DIR NOT FOUND\' }"')
print(f"  content: {out}")

# Check where the bot expects profiles — read config.py
print("\n=== config.py LOGINS_DIR ===")
out, _ = run('powershell.exe -Command "Select-String -Path C:/projetos-navegador/engage_modules/config.py -Pattern \'login|LOGINS|profiles|chrome_profile\' -ErrorAction SilentlyContinue"')
print(out if out else "not found")

# Check _run_bot.bat content
print("\n=== _run_bot.bat (content) ===")
out, _ = run('powershell.exe -Command "Get-Content C:/projetos-navegador/_run_bot.bat"')
print(out)

# List all .log files with names this time
print("\n=== .log files with NAMES ===")
out, _ = run('powershell.exe -Command "Get-ChildItem C:/projetos-navegador/*.log -ErrorAction SilentlyContinue | Select-Object Name,Length,LastWriteTime | Format-Table -AutoSize"')
print(out if out else "none")

# Are there browser profiles elsewhere?
print("\n=== C:/Users/Emerson-IA directories ===")
out, _ = run('powershell.exe -Command "Get-ChildItem C:/Users/Emerson-IA -Directory | Select-Object Name"')
print(out)

ssh.close()
print("\nDone.")
