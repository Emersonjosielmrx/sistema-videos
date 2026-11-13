"""Quick check — PC3 bot activity + PC1 bot status."""
import paramiko
import sys
import io
import subprocess

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ========== PC3 ==========
print("========== PC3 (100.108.160.85) ==========")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("100.108.160.85", username="Emerson-IA", password="<SEGREDO_REMOVIDO>", timeout=15)

def run(cmd, timeout=30):
    _, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    return stdout.read().decode("utf-8", errors="replace").strip()

out = run('powershell.exe -Command "(Get-Process python* -ErrorAction SilentlyContinue | Measure-Object).Count"')
print(f"Python: {out}")
out = run('powershell.exe -Command "(Get-Process chrome*,chromium* -ErrorAction SilentlyContinue | Measure-Object).Count"')
print(f"Chrome: {out}")

# Last 5 log lines
print("\nUltimas 5 linhas do log:")
out = run('powershell.exe -Command "Get-Content C:/projetos-navegador/mega_engage_log.txt -Tail 5 -ErrorAction SilentlyContinue"')
print(out if out else "(vazio)")

# Count total OK lines
out = run('powershell.exe -Command "(Select-String -Path C:/projetos-navegador/mega_engage_log.txt -Pattern \'OK \\[L\\]\' -ErrorAction SilentlyContinue | Measure-Object).Count"')
print(f"\nLikes totais (OK [L]): {out}")

out = run('powershell.exe -Command "(Select-String -Path C:/projetos-navegador/mega_engage_log.txt -Pattern \'OK \\[C\\]\' -ErrorAction SilentlyContinue | Measure-Object).Count"')
print(f"Comments totais (OK [C]): {out}")

ssh.close()

# ========== PC1 (local) ==========
print("\n========== PC1 (local) ==========")
try:
    r = subprocess.run(
        ["tasklist", "/FI", "IMAGENAME eq python.exe"],
        capture_output=True, text=True, timeout=10
    )
    lines = [l for l in r.stdout.split("\n") if "python" in l.lower()]
    print(f"Python processes: {len(lines)}")
    for l in lines[:5]:
        print(f"  {l.strip()}")
except Exception as e:
    print(f"Error: {e}")

# Check local log
import os
log_path = r"D:\projetos-navegador\mega_engage_log.txt"
if os.path.exists(log_path):
    with open(log_path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    print(f"\nLocal log: {len(lines)} lines")
    if lines:
        print("Ultimas 5:")
        for l in lines[-5:]:
            print(f"  {l.rstrip()}")
else:
    print(f"\nLocal log not found at {log_path}")

print("\nDone.")
