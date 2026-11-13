"""Start mega_engage on PC3."""
import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("100.108.160.85", username="Emerson-IA", password="<SEGREDO_REMOVIDO>", timeout=15)

PYTHON = "C:\\Python314\\python.exe"

# Kill old
print("Matando processos antigos...")
for proc in ["python", "chrome"]:
    _, stdout, stderr = ssh.exec_command(
        f'powershell -c "Get-Process {proc}* -ErrorAction SilentlyContinue | Stop-Process -Force"',
        timeout=15
    )
    stdout.read(); stderr.read()

time.sleep(2)

# Check deps first
print("Verificando playwright...")
_, stdout, stderr = ssh.exec_command(
    f'cmd /c "{PYTHON} -c \\"import playwright; print(playwright.__version__)\\"" 2>&1',
    timeout=15
)
out = stdout.read().decode("utf-8", errors="replace").strip()
print(f"  playwright: {out}")

# Install playwright if missing
if "No module" in out or "Error" in out:
    print("  Instalando playwright...")
    _, stdout, _ = ssh.exec_command(
        f'cmd /c "{PYTHON} -m pip install playwright 2>&1"', timeout=120
    )
    print(f"  pip: {stdout.read().decode('utf-8', errors='replace')[-200:]}")
    _, stdout, _ = ssh.exec_command(
        f'cmd /c "{PYTHON} -m playwright install chromium 2>&1"', timeout=120
    )
    print(f"  chromium: {stdout.read().decode('utf-8', errors='replace')[-200:]}")

# Start bot
print("\nIniciando mega_engage.py em background...")
start_cmd = (
    f'powershell -c "Start-Process -FilePath '
    f"'{PYTHON}' "
    f"-ArgumentList 'C:\\projetos-navegador\\mega_engage.py' "
    f"-WorkingDirectory 'C:\\projetos-navegador' "
    f"-RedirectStandardOutput 'C:\\projetos-navegador\\bot_output.log' "
    f"-RedirectStandardError 'C:\\projetos-navegador\\bot_error.log' "
    f'-WindowStyle Hidden"'
)
_, stdout, stderr = ssh.exec_command(start_cmd, timeout=15)
stdout.read(); stderr.read()

time.sleep(8)

# Check if running
_, stdout, _ = ssh.exec_command(
    'powershell -c "(Get-Process python* -ErrorAction SilentlyContinue | Measure-Object).Count"',
    timeout=10
)
count = stdout.read().decode().strip()
print(f"Processos Python rodando: {count}")

# Check output log
_, stdout, _ = ssh.exec_command(
    'powershell -c "Get-Content C:\\projetos-navegador\\bot_output.log -Tail 30 -ErrorAction SilentlyContinue"',
    timeout=10
)
log = stdout.read().decode("utf-8", errors="replace").strip()
if log:
    print(f"\n=== bot_output.log ===\n{log}")

# Check error log
_, stdout, _ = ssh.exec_command(
    'powershell -c "Get-Content C:\\projetos-navegador\\bot_error.log -Tail 30 -ErrorAction SilentlyContinue"',
    timeout=10
)
errlog = stdout.read().decode("utf-8", errors="replace").strip()
if errlog:
    print(f"\n=== bot_error.log ===\n{errlog}")

ssh.close()
print("\nDone.")
