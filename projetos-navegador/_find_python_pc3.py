"""Find Python on PC3 and start the bot."""
import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("100.108.160.85", username="Emerson-IA", password="<SEGREDO_REMOVIDO>", timeout=15)

# Find Python (multiple places)
search_cmds = [
    r'powershell -c "Get-ChildItem C:\Python* -Filter python.exe -Recurse -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName"',
    r'powershell -c "Get-ChildItem C:\Users\*\AppData\Local\Programs\Python -Filter python.exe -Recurse -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName"',
    r'powershell -c "Get-ChildItem C:\Program*\Python* -Filter python.exe -Recurse -Depth 2 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName"',
    r'powershell -c "where.exe python 2>$null"',
    r'powershell -c "[Environment]::GetEnvironmentVariable(''Path'',''Machine'') -split '';'' | Where-Object {$_ -match ''[Pp]ython''}"',
    r'powershell -c "[Environment]::GetEnvironmentVariable(''Path'',''User'') -split '';'' | Where-Object {$_ -match ''[Pp]ython''}"',
    r'cmd /c "where python"',
]

py_path = None
for cmd in search_cmds:
    _, stdout, _ = ssh.exec_command(cmd, timeout=15)
    out = stdout.read().decode("utf-8", errors="replace").strip()
    if out:
        print(f"Found: {out}")
        for line in out.splitlines():
            if "python.exe" in line.lower() or "python" in line.lower():
                py_path = line.strip()
                break
        if py_path and py_path.endswith(".exe"):
            break

# Also check if there's a venv on PC3
_, stdout, _ = ssh.exec_command(
    r'powershell -c "Test-Path C:\projetos-navegador\venv\Scripts\python.exe"', timeout=10
)
has_venv = stdout.read().decode().strip()
print(f"\nVenv exists: {has_venv}")

# Check py launcher
_, stdout, _ = ssh.exec_command(r'cmd /c "py --version 2>&1"', timeout=10)
py_ver = stdout.read().decode().strip()
print(f"py launcher: {py_ver}")

if not py_path:
    # Try py launcher path
    _, stdout, _ = ssh.exec_command(r'cmd /c "where py 2>&1"', timeout=10)
    py_loc = stdout.read().decode().strip()
    print(f"py location: {py_loc}")

print(f"\nBest python found: {py_path}")
ssh.close()
