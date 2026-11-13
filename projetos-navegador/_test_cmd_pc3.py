"""Start bot on PC3 - cmd.exe approach."""
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
print("Kill old...")
run('powershell.exe -Command "Get-Process python*,chrome* -ErrorAction SilentlyContinue | Stop-Process -Force"')
time.sleep(2)

# Test: run Python directly via the SSH channel (not through powershell -c)
# The SSH shell is PowerShell, so we need to escape properly
# Use cmd.exe /c to bypass PowerShell parsing
print("=== Test import via cmd ===")
out, err = run('cmd.exe /c "C:\\Python314\\python.exe C:\\projetos-navegador\\_launcher.py" 2>&1', timeout=20)
# This will hang until the bot exits, so let's do it differently

# Actually, let's first just test if the import works
print("=== Test import only ===")
out, err = run(
    'cmd.exe /c "C:\\Python314\\python.exe -c "import sys; sys.path.insert(0, \'C:/projetos-navegador\'); sys.path.insert(0, \'C:/projetos-navegador/shared\'); from engage_modules.config import BASE_DIR; print(BASE_DIR)"" 2>&1',
    timeout=15
)
print(f"OUT: {out}")
if err:
    print(f"ERR: {err}")

ssh.close()
