"""Deep check PC3 bot — look for engage logs, stats, and activity."""
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

# Process details
print("=== Python processes ===")
out = run('powershell.exe -Command "Get-Process python* -ErrorAction SilentlyContinue | Select-Object Id,CPU,WorkingSet,StartTime | Format-Table -AutoSize"')
print(out if out else "none")

print("\n=== Browser count ===")
out = run('powershell.exe -Command "(Get-Process chrome*,chromium*,msedge* -ErrorAction SilentlyContinue | Measure-Object).Count"')
print(f"  {out} browser processes")

# Check ALL files in C:/projetos-navegador that were modified in last 30 min
print("\n=== Recently modified files (last 30 min) ===")
out = run('powershell.exe -Command "Get-ChildItem C:/projetos-navegador -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -gt (Get-Date).AddMinutes(-30) } | Select-Object FullName,Length,LastWriteTime | Format-Table -AutoSize"')
print(out if out else "none")

# Check engage_stats.json
print("\n=== engage_stats.json ===")
out = run('powershell.exe -Command "if (Test-Path C:/projetos-navegador/engage_stats.json) { Get-Content C:/projetos-navegador/engage_stats.json -Tail 5 } else { \'not found\' }"')
print(out)

# Check any .log files
print("\n=== All .log files in projetos-navegador ===")
out = run('powershell.exe -Command "Get-ChildItem C:/projetos-navegador -Filter *.log -Recurse -ErrorAction SilentlyContinue | Select-Object FullName,Length,LastWriteTime | Format-Table -AutoSize"')
print(out if out else "none")

# Check any .json files modified recently
print("\n=== JSON files modified recently ===")
out = run('powershell.exe -Command "Get-ChildItem C:/projetos-navegador -Filter *.json -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -gt (Get-Date).AddMinutes(-30) } | Select-Object FullName,Length,LastWriteTime | Format-Table -AutoSize"')
print(out if out else "none")

# Check console output directly — maybe the bat redirect isn't working
# Try reading the Windows Task Scheduler log
print("\n=== Task Scheduler history ===")
out = run('powershell.exe -Command "Get-WinEvent -LogName \"Microsoft-Windows-TaskScheduler/Operational\" -MaxEvents 10 -ErrorAction SilentlyContinue | Select-Object TimeCreated,Id,Message | Format-Table -AutoSize"', timeout=15)
print(out if out else "not available")

# Check logins-google directory
print("\n=== C:/logins-google ===")
out = run('powershell.exe -Command "if (Test-Path C:/logins-google) { (Get-ChildItem C:/logins-google -ErrorAction SilentlyContinue | Measure-Object).Count } else { \'dir not found\' }"')
print(f"  entries: {out}")

ssh.close()
print("\nDone.")
