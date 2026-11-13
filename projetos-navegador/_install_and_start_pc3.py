"""Install playwright + deps on PC3 then start bot."""
import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("100.108.160.85", username="Emerson-IA", password="<SEGREDO_REMOVIDO>", timeout=15)

PYTHON = "C:\\Python314\\python.exe"

def run(cmd, timeout=120):
    print(f"$ {cmd[:90]}")
    _, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="replace").strip()
    err = stderr.read().decode("utf-8", errors="replace").strip()
    if out:
        # Print last 500 chars to avoid flooding
        tail = out[-500:] if len(out) > 500 else out
        print(f"  {tail}")
    if err:
        tail = err[-300:] if len(err) > 300 else err
        print(f"  ERR: {tail}")
    return out, err

# Step 1: Install playwright + other deps
print("=== Instalando dependencias ===")
run(f'cmd /c "{PYTHON} -m pip install playwright 2>&1"', timeout=120)

print("\n=== Instalando Chromium (playwright) ===")
run(f'cmd /c "{PYTHON} -m playwright install chromium 2>&1"', timeout=180)

# Also install any other deps the project needs
print("\n=== Outros pacotes ===")
run(f'cmd /c "{PYTHON} -m pip install httpx aiofiles 2>&1"', timeout=60)

# Verify
print("\n=== Verificando ===")
run(f'cmd /c "{PYTHON} -c \\"import playwright; print(\'playwright OK\')\\"" 2>&1')

# Step 2: Start bot
print("\n=== Iniciando bot ===")
start_cmd = (
    f'powershell -c "Start-Process -FilePath '
    f"'{PYTHON}' "
    f"-ArgumentList 'C:\\projetos-navegador\\mega_engage.py' "
    f"-WorkingDirectory 'C:\\projetos-navegador' "
    f"-RedirectStandardOutput 'C:\\projetos-navegador\\bot_output.log' "
    f"-RedirectStandardError 'C:\\projetos-navegador\\bot_error.log' "
    f'-WindowStyle Hidden"'
)
run(start_cmd, timeout=15)

time.sleep(10)

# Check
run('powershell -c "(Get-Process python* -ErrorAction SilentlyContinue | Measure-Object).Count"')
run('powershell -c "Get-Content C:\\projetos-navegador\\bot_output.log -Tail 20 -ErrorAction SilentlyContinue"')
run('powershell -c "Get-Content C:\\projetos-navegador\\bot_error.log -Tail 20 -ErrorAction SilentlyContinue"')

ssh.close()
print("\nDone.")
