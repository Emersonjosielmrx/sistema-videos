"""Upload launcher and start bot on PC3."""
import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("100.108.160.85", username="Emerson-IA", password="<SEGREDO_REMOVIDO>", timeout=15)
sftp = ssh.open_sftp()

# Write _launcher.py via SFTP
launcher_content = b"""import os, sys
os.chdir('C:/projetos-navegador')
sys.path.insert(0, 'C:/projetos-navegador')
sys.path.insert(0, 'C:/projetos-navegador/shared')
from engage_modules.main import main
main()
"""

with sftp.open("C:/projetos-navegador/_launcher.py", "wb") as f:
    f.write(launcher_content)
print("_launcher.py uploaded")

# Verify
stat = sftp.stat("C:/projetos-navegador/_launcher.py")
print(f"  Size: {stat.st_size} bytes")
sftp.close()

# Kill old
ssh.exec_command("powershell -c \"Get-Process python*,chrome* -ErrorAction SilentlyContinue | Stop-Process -Force\"", timeout=10)
time.sleep(2)

# Start bot
start_cmd = (
    "powershell -c \""
    "Start-Process "
    "-FilePath 'C:/Python314/python.exe' "
    "-ArgumentList 'C:/projetos-navegador/_launcher.py' "
    "-WorkingDirectory 'C:/projetos-navegador' "
    "-RedirectStandardOutput 'C:/projetos-navegador/bot_output.log' "
    "-RedirectStandardError 'C:/projetos-navegador/bot_error.log' "
    "-WindowStyle Hidden"
    "\""
)
_, stdout, stderr = ssh.exec_command(start_cmd, timeout=15)
stdout.read(); stderr.read()

time.sleep(12)

# Check process count
_, stdout, _ = ssh.exec_command(
    "powershell -c \"(Get-Process python* -ErrorAction SilentlyContinue | Measure-Object).Count\"",
    timeout=10
)
count = stdout.read().decode().strip()
print(f"\nProcessos Python: {count}")

# Check chrome too
_, stdout, _ = ssh.exec_command(
    "powershell -c \"(Get-Process chrome* -ErrorAction SilentlyContinue | Measure-Object).Count\"",
    timeout=10
)
chrome = stdout.read().decode().strip()
print(f"Processos Chrome: {chrome}")

# Output log
_, stdout, _ = ssh.exec_command(
    "powershell -c \"Get-Content C:/projetos-navegador/bot_output.log -Tail 30 -ErrorAction SilentlyContinue\"",
    timeout=10
)
log = stdout.read().decode("utf-8", errors="replace").strip()
print(f"\n=== bot_output.log ===\n{log}")

# Error log
_, stdout, _ = ssh.exec_command(
    "powershell -c \"Get-Content C:/projetos-navegador/bot_error.log -Tail 30 -ErrorAction SilentlyContinue\"",
    timeout=10
)
errlog = stdout.read().decode("utf-8", errors="replace").strip()
if errlog:
    print(f"\n=== bot_error.log ===\n{errlog}")

ssh.close()
print("\nDone.")
