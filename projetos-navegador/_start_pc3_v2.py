"""Start bot on PC3 - PowerShell native."""
import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("100.108.160.85", username="Emerson-IA", password="<SEGREDO_REMOVIDO>", timeout=15)

PYTHON = "C:/Python314/python.exe"

def run(cmd, timeout=120):
    print(f"$ {cmd[:110]}")
    _, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="replace").strip()
    err = stderr.read().decode("utf-8", errors="replace").strip()
    if out:
        tail = out[-600:] if len(out) > 600 else out
        print(tail)
    if err:
        tail = err[-400:] if len(err) > 400 else err
        print(f"ERR: {tail}")
    return out, err

# Test import (PowerShell syntax, no &&)
print("=== Teste de import ===")
run(f"powershell -c \"Set-Location C:/projetos-navegador; & '{PYTHON}' -c 'from engage_modules.main import main; print(chr(73)+chr(77)+chr(80)+chr(79)+chr(82)+chr(84)+chr(32)+chr(79)+chr(75))'\"")

# Check what error log says
print("\n=== bot_error.log ===")
run("powershell -c \"Get-Content C:/projetos-navegador/bot_error.log -ErrorAction SilentlyContinue\"")

# Start with Start-Process using full path
print("\n=== Iniciando bot ===")
start_cmd = (
    "powershell -c \""
    "Start-Process "
    f"-FilePath '{PYTHON}' "
    "-ArgumentList 'C:/projetos-navegador/mega_engage.py' "
    "-WorkingDirectory 'C:/projetos-navegador' "
    "-RedirectStandardOutput 'C:/projetos-navegador/bot_output.log' "
    "-RedirectStandardError 'C:/projetos-navegador/bot_error.log' "
    "-WindowStyle Hidden"
    "\""
)
run(start_cmd, timeout=15)

time.sleep(10)

# Check process
run("powershell -c \"(Get-Process python* -ErrorAction SilentlyContinue | Measure-Object).Count\"")

# Check logs
print("\n=== bot_output.log ===")
run("powershell -c \"Get-Content C:/projetos-navegador/bot_output.log -Tail 30 -ErrorAction SilentlyContinue\"")
print("\n=== bot_error.log ===")
run("powershell -c \"Get-Content C:/projetos-navegador/bot_error.log -Tail 30 -ErrorAction SilentlyContinue\"")

ssh.close()
print("\nDone.")
