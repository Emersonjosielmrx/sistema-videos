"""Start bot on PC3 using a .bat wrapper."""
import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("100.108.160.85", username="Emerson-IA", password="<SEGREDO_REMOVIDO>", timeout=15)
sftp = ssh.open_sftp()

# Create a .bat file that runs the launcher
bat_content = b"""@echo off
cd /d C:\\projetos-navegador
C:\\Python314\\python.exe C:\\projetos-navegador\\_launcher.py > C:\\projetos-navegador\\bot_output.log 2> C:\\projetos-navegador\\bot_error.log
"""

with sftp.open("C:/projetos-navegador/_run_bot.bat", "wb") as f:
    f.write(bat_content)
print("_run_bot.bat uploaded")

# Also verify _launcher.py content
with sftp.open("C:/projetos-navegador/_launcher.py", "r") as f:
    content = f.read()
print(f"_launcher.py: {len(content)} bytes")
print(content.decode("utf-8", errors="replace"))

sftp.close()

# Kill old
_, stdout, _ = ssh.exec_command(
    "powershell -c \"Get-Process python*,chrome* -ErrorAction SilentlyContinue | Stop-Process -Force\"",
    timeout=10
)
stdout.read()
time.sleep(2)

# Run the bat via Start-Process (this actually works on Windows)
print("Starting via .bat...")
start_cmd = (
    "powershell -c \""
    "Start-Process -FilePath 'cmd.exe' "
    "-ArgumentList '/c','C:\\projetos-navegador\\_run_bot.bat' "
    "-WindowStyle Hidden"
    "\""
)
_, stdout, stderr = ssh.exec_command(start_cmd, timeout=15)
stdout.read(); stderr.read()

time.sleep(15)

# Check
_, stdout, _ = ssh.exec_command(
    "powershell -c \"(Get-Process python* -ErrorAction SilentlyContinue | Measure-Object).Count\"",
    timeout=10
)
count = stdout.read().decode().strip()
print(f"Processos Python: {count}")

_, stdout, _ = ssh.exec_command(
    "powershell -c \"(Get-Process chrome* -ErrorAction SilentlyContinue | Measure-Object).Count\"",
    timeout=10
)
chrome = stdout.read().decode().strip()
print(f"Processos Chrome: {chrome}")

# Logs
_, stdout, _ = ssh.exec_command(
    "powershell -c \"Get-Content C:/projetos-navegador/bot_output.log -Tail 30 -ErrorAction SilentlyContinue\"",
    timeout=10
)
log = stdout.read().decode("utf-8", errors="replace").strip()
print(f"\n=== bot_output.log ===\n{log}")

_, stdout, _ = ssh.exec_command(
    "powershell -c \"Get-Content C:/projetos-navegador/bot_error.log -Tail 30 -ErrorAction SilentlyContinue\"",
    timeout=10
)
errlog = stdout.read().decode("utf-8", errors="replace").strip()
if errlog:
    print(f"\n=== bot_error.log ===\n{errlog}")

# Also check file sizes of error/output logs
_, stdout, _ = ssh.exec_command(
    "powershell -c \"Get-ChildItem C:/projetos-navegador/bot_*.log | Select-Object Name,Length\"",
    timeout=10
)
print(f"\n=== Log sizes ===\n{stdout.read().decode().strip()}")

ssh.close()
print("\nDone.")
