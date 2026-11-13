"""Debug PC3 bot startup."""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("100.108.160.85", username="Emerson-IA", password="<SEGREDO_REMOVIDO>", timeout=15)

def run(cmd, timeout=30):
    _, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="replace").strip()
    err = stderr.read().decode("utf-8", errors="replace").strip()
    return out, err

# Check mega_engage.py content on PC3
print("=== mega_engage.py no PC3 ===")
out, _ = run("powershell -c \"Get-Content C:/projetos-navegador/mega_engage.py\"")
print(out)

# Check that engage_modules exists
print("\n=== engage_modules/ no PC3 ===")
out, _ = run("powershell -c \"Get-ChildItem C:/projetos-navegador/engage_modules/*.py | Select-Object Name,Length\"")
print(out)

# Try running python directly in the right dir
print("\n=== Teste direto ===")
# Use powershell to set location and run
test_cmd = (
    "powershell -c \""
    "Set-Location 'C:/projetos-navegador'; "
    "& 'C:/Python314/python.exe' '-c' "
    "'import os; os.chdir(os.path.dirname(os.path.abspath(chr(67)+chr(58)+chr(47)+chr(112)+chr(114)+chr(111)+chr(106)+chr(101)+chr(116)+chr(111)+chr(115)+chr(45)+chr(110)+chr(97)+chr(118)+chr(101)+chr(103)+chr(97)+chr(100)+chr(111)+chr(114)+chr(47)+chr(109)+chr(101)+chr(103)+chr(97)+chr(95)+chr(101)+chr(110)+chr(103)+chr(97)+chr(103)+chr(101)+chr(46)+chr(112)+chr(121)))); import sys; sys.path.insert(0, os.getcwd()); print(os.getcwd()); from engage_modules.config import BASE_DIR; print(BASE_DIR)'"
    "\""
)
out, err = run(test_cmd)
print(f"OUT: {out}")
if err:
    print(f"ERR: {err}")

# Simpler test - just run mega_engage.py properly
print("\n=== Teste com python mega_engage.py ===")
out, err = run(
    "powershell -c \""
    "Set-Location 'C:/projetos-navegador'; "
    "& 'C:/Python314/python.exe' 'mega_engage.py' 2>&1 | Select-Object -First 10"
    "\"",
    timeout=20
)
print(f"OUT: {out}")
if err:
    print(f"ERR: {err}")

ssh.close()
