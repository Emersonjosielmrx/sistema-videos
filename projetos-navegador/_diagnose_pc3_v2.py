"""Deep check — find where bot actually logs, check logins, see browser activity."""
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
    return out

# Python process details
print("=== Python processes ===")
out = run('powershell.exe -Command "Get-Process python* | Format-List Id,StartTime,Path,CommandLine"')
print(out if out else "none")

# Browser process details (count)
out = run('powershell.exe -Command "(Get-Process chrome*,chromium* -ErrorAction SilentlyContinue | Measure-Object).Count"')
print(f"\nBrowsers: {out}")

# Check what's inside C:/logins-google
print("\n=== C:/logins-google contents ===")
out = run('powershell.exe -Command "Get-ChildItem C:/logins-google -ErrorAction SilentlyContinue | Select-Object Name,PSIsContainer | Format-Table -AutoSize"')
print(out if out else "(empty dir)")

# Check all recently written files on the machine
print("\n=== Files modified in last 10 min (projetos-navegador, recursive) ===")
out = run('powershell.exe -Command "Get-ChildItem C:/projetos-navegador -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -gt (Get-Date).AddMinutes(-10) } | Select-Object FullName,Length,LastWriteTime | Format-Table -AutoSize"')
print(out if out else "none")

# The logger in engage_modules/logger.py usually writes to a specific file
# Check what file it logs to
print("\n=== logger.py content ===")
out = run('powershell.exe -Command "Get-Content C:/projetos-navegador/engage_modules/logger.py -ErrorAction SilentlyContinue"')
print(out if out else "not found")

# Check engage_config.json
print("\n=== engage_config.json ===")
out = run('powershell.exe -Command "Get-Content C:/projetos-navegador/engage_config.json -ErrorAction SilentlyContinue"')
print(out if out else "not found")

# Maybe the bat redirect doesn't work because schtask used redirects already
# Let's look at what the bat ACTUALLY does — maybe the > redirect gets eaten
# Check: is there a C:/projetos-navegador/bot_output.log with content?
print("\n=== bot log files with actual sizes ===")
out = run('powershell.exe -Command "Get-ChildItem C:/projetos-navegador/bot_* -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName + \' = \' + $_.Length }"')
print(out if out else "none")

# Check if there's engage*.log pattern
out = run('powershell.exe -Command "Get-ChildItem C:/projetos-navegador -Filter engage*.log -Recurse -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName + \' = \' + $_.Length }"')
print(f"\nengage*.log: {out}")

ssh.close()
print("\nDone.")
