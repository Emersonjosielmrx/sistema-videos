"""Install Chromium on PC3, check errors, start bot."""
import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("100.108.160.85", username="Emerson-IA", password="<SEGREDO_REMOVIDO>", timeout=15)

PYTHON = "C:\\Python314\\python.exe"

def run(cmd, timeout=120):
    print(f"$ {cmd[:100]}")
    _, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="replace").strip()
    err = stderr.read().decode("utf-8", errors="replace").strip()
    combined = out
    if err:
        combined += "\n" + err
    tail = combined[-800:] if len(combined) > 800 else combined
    if tail:
        print(tail)
    return out, err

# Check chromium
print("=== Verificando Chromium ===")
run(f'cmd /c "{PYTHON} -m playwright install chromium 2>&1"', timeout=300)

# Check what error the bot gives now
print("\n=== Teste de import completo ===")
run(f'cmd /c "cd /d C:\\projetos-navegador && {PYTHON} -c \\"from engage_modules.main import main; print(\'IMPORT OK\')\\" 2>&1"')

# Check last error log
print("\n=== Ultimo bot_error.log ===")
run('powershell -c "Get-Content C:\\projetos-navegador\\bot_error.log -ErrorAction SilentlyContinue"')

# Try starting directly (not Start-Process) to see immediate output
print("\n=== Tentando rodar direto (5s timeout pra ver output) ===")
try:
    _, stdout, stderr = ssh.exec_command(
        f'cmd /c "cd /d C:\\projetos-navegador && {PYTHON} mega_engage.py 2>&1"',
        timeout=15
    )
    time.sleep(12)
    # Force read with small timeout
    stdout.channel.settimeout(2)
    try:
        partial = stdout.read(4096).decode("utf-8", errors="replace")
        print(f"OUTPUT: {partial[:1000]}")
    except:
        pass
    stderr.channel.settimeout(2)
    try:
        partial_err = stderr.read(4096).decode("utf-8", errors="replace")
        print(f"STDERR: {partial_err[:1000]}")
    except:
        pass
except Exception as e:
    print(f"Timeout/erro: {e}")

# Now check processes
run('powershell -c "(Get-Process python* -ErrorAction SilentlyContinue).Count"')

ssh.close()
print("\nDone.")
