"""Find Python on PC3 - simple checks."""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("100.108.160.85", username="Emerson-IA", password="<SEGREDO_REMOVIDO>", timeout=15)

checks = [
    'cmd /c "python --version 2>&1"',
    'cmd /c "py --version 2>&1"',
    'cmd /c "py -0p 2>&1"',
    'cmd /c "where py 2>&1"',
    'powershell -c "Test-Path C:\\Python314\\python.exe"',
    'powershell -c "Test-Path C:\\Python313\\python.exe"',
    'powershell -c "Test-Path C:\\Python312\\python.exe"',
    'powershell -c "Test-Path C:\\Python311\\python.exe"',
    "powershell -c \"Test-Path 'C:\\Users\\Emerson-IA\\AppData\\Local\\Programs\\Python\\Python314\\python.exe'\"",
    "powershell -c \"Test-Path 'C:\\Users\\Emerson-IA\\AppData\\Local\\Programs\\Python\\Python313\\python.exe'\"",
    "powershell -c \"Test-Path 'C:\\Users\\Emerson-IA\\AppData\\Local\\Programs\\Python\\Python312\\python.exe'\"",
    "powershell -c \"$env:PATH -split ';' | Select-String -Pattern 'ython'\"",
]

for c in checks:
    _, stdout, stderr = ssh.exec_command(c, timeout=10)
    out = stdout.read().decode("utf-8", errors="replace").strip()
    err = stderr.read().decode("utf-8", errors="replace").strip()
    result = out or err or "(empty)"
    print(f"$ {c[:70]}")
    print(f"  -> {result}\n")

ssh.close()
