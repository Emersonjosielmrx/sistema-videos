"""Check config paths and LOG_FILE on PC3, then see what we need to copy."""
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

# 1) Read config.py to see paths
print("=== config.py ===")
out = run('powershell.exe -Command "Get-Content C:/projetos-navegador/engage_modules/config.py"')
print(out)

# 2) Check mega_engage_log.txt
print("\n=== mega_engage_log.txt ===")
out = run('powershell.exe -Command "if (Test-Path C:/projetos-navegador/mega_engage_log.txt) { Get-Content C:/projetos-navegador/mega_engage_log.txt -Tail 30 } else { \'not found\' }"')
print(out)

# 3) What's in C:/logins-google?
print("\n=== C:/logins-google (detailed) ===")
out = run('powershell.exe -Command "Get-ChildItem C:/logins-google -Recurse -ErrorAction SilentlyContinue | Select-Object FullName,Length | Format-Table -AutoSize"')
print(out if out else "(completely empty)")

# 4) Check secrets dir
print("\n=== C:/projetos-navegador/secrets ===")
out = run('powershell.exe -Command "if (Test-Path C:/projetos-navegador/secrets) { Get-ChildItem C:/projetos-navegador/secrets | Select-Object Name,Length } else { \'not found\' }"')
print(out)

ssh.close()
print("\nDone.")
