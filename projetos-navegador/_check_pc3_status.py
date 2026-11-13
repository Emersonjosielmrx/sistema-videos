"""Check PC3 bot status after it's been running."""
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

# Processes
out, _ = run('powershell.exe -Command "(Get-Process python* -ErrorAction SilentlyContinue | Measure-Object).Count"')
print(f"Python processes: {out}")

out, _ = run('powershell.exe -Command "(Get-Process chrome*,chromium*,msedge* -ErrorAction SilentlyContinue | Measure-Object).Count"')
print(f"Browser processes: {out}")

# Task status
out, _ = run('schtasks /Query /TN MegaEngageBot /FO LIST', timeout=10)
print(f"\nTask Status:\n{out}")

# Output log
print("\n=== bot_output.log (last 50 lines) ===")
out, _ = run('powershell.exe -Command "Get-Content C:/projetos-navegador/bot_output.log -Tail 50 -ErrorAction SilentlyContinue"')
print(out if out else "(vazio)")

# Error log
print("\n=== bot_error.log (last 50 lines) ===")
out, _ = run('powershell.exe -Command "Get-Content C:/projetos-navegador/bot_error.log -Tail 50 -ErrorAction SilentlyContinue"')
print(out if out else "(sem erros)")

# File sizes of logs
out, _ = run('powershell.exe -Command "Get-ChildItem C:/projetos-navegador/bot_*.log -ErrorAction SilentlyContinue | Select-Object Name,Length | Format-Table -AutoSize"')
print(f"\nLog sizes:\n{out}")

# Check if there's an engage log
out, _ = run('powershell.exe -Command "Get-ChildItem C:/projetos-navegador/logs/ -ErrorAction SilentlyContinue | Select-Object Name,Length,LastWriteTime | Format-Table -AutoSize"')
print(f"\nlogs/ dir:\n{out}")

# Check if stats.json exists
out, _ = run('powershell.exe -Command "Test-Path C:/projetos-navegador/engage_stats.json"')
print(f"\nengage_stats.json exists: {out}")

ssh.close()
print("\nDone.")
