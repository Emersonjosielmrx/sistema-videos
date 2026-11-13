"""Start bot on PC3 using scheduled task (most reliable on Windows)."""
import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("100.108.160.85", username="Emerson-IA", password="<SEGREDO_REMOVIDO>", timeout=15)

def run(cmd, timeout=30):
    _, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="replace").strip()
    err = stderr.read().decode("utf-8", errors="replace").strip()
    return out, err

# Kill old
run("powershell -c \"Get-Process python*,chrome* -ErrorAction SilentlyContinue | Stop-Process -Force\"")
time.sleep(2)

# First test: can Python even import our modules?
print("=== Quick test ===")
out, err = run(
    "powershell -c \"& 'C:/Python314/python.exe' 'C:/projetos-navegador/_launcher.py' 2>&1 | Select-Object -First 5\"",
    timeout=20
)
print(f"OUT: {out}")
if err:
    print(f"ERR: {err}")

# Check if Python process appeared and died
out2, _ = run("powershell -c \"(Get-Process python* -ErrorAction SilentlyContinue).Count\"")
print(f"Python processes after test: {out2}")

# If the quick test shows nothing, let python run inline for a bit
print("\n=== Inline run (10s window) ===")
_, stdout, stderr = ssh.exec_command(
    "powershell -c \"& 'C:/Python314/python.exe' 'C:/projetos-navegador/_launcher.py' 2>&1\"",
    timeout=20
)
time.sleep(10)
stdout.channel.settimeout(3)
stderr.channel.settimeout(3)
try:
    partial_out = stdout.read(8192).decode("utf-8", errors="replace")
    print(f"STDOUT:\n{partial_out[:2000]}")
except:
    print("STDOUT: (timeout)")
try:
    partial_err = stderr.read(8192).decode("utf-8", errors="replace")
    if partial_err:
        print(f"STDERR:\n{partial_err[:2000]}")
except:
    pass

ssh.close()
print("\nDone.")
