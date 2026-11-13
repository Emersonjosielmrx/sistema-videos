"""Deploy v3: pre-patch locally, upload clean files, start bot."""
import paramiko
import os
import tempfile
import shutil

PC3 = "100.108.160.85"
USER = "Emerson-IA"
PASSW = "Ssh@2026"
LOCAL_BASE = r"D:\projetos-navegador"
REMOTE_BASE = "C:/projetos-navegador"

REPLACEMENTS = [
    ("D:/projetos-navegador", "C:/projetos-navegador"),
    ("D:\\projetos-navegador", "C:\\projetos-navegador"),
    ("D:/logins-google", "C:/logins-google"),
    ("D:\\logins-google", "C:\\logins-google"),
    ("D:/hipercool-videos/venv/Scripts/python.exe", "python"),
    ("D:\\hipercool-videos\\venv\\Scripts\\python.exe", "python"),
    ("D:/hipercool-videos/secrets", "C:/projetos-navegador/secrets"),
    ("D:\\hipercool-videos\\secrets", "C:\\projetos-navegador\\secrets"),
]

PATCH_FILES = {
    "mega_engage.py", "engage_server.py", "engage_config.json",
    "engage_modules/config.py", "engage_modules/main.py",
    "engage_modules/browser.py", "engage_modules/worker.py",
    "shared/google_session.py", "shared/chrome_profile.py",
    "RODAR_ENGAGE.bat",
}

# Collect all files to upload
files_to_upload = []

# Root files
root_files = [
    "mega_engage.py", "engage_config.json", "all_channel_videos_full.json",
    "engage_server.py", "local_proxy.py", "RODAR_ENGAGE.bat",
]
for f in root_files:
    local = os.path.join(LOCAL_BASE, f)
    if os.path.exists(local):
        files_to_upload.append((f, local))

# engage_modules/*.py
mod_dir = os.path.join(LOCAL_BASE, "engage_modules")
for f in os.listdir(mod_dir):
    if f.endswith(".py"):
        files_to_upload.append((f"engage_modules/{f}", os.path.join(mod_dir, f)))

# shared/*.py
shared_dir = os.path.join(LOCAL_BASE, "shared")
for f in os.listdir(shared_dir):
    if f.endswith(".py"):
        files_to_upload.append((f"shared/{f}", os.path.join(shared_dir, f)))

# Pre-patch locally into temp dir
tmpdir = tempfile.mkdtemp(prefix="engage_deploy_")
print(f"Temp dir: {tmpdir}")

for rel, local_path in files_to_upload:
    content = open(local_path, "rb").read()

    if rel in PATCH_FILES:
        text = content.decode("utf-8", errors="replace")
        for old, new in REPLACEMENTS:
            text = text.replace(old, new)
        content = text.encode("utf-8")

    # Write to temp
    dest = os.path.join(tmpdir, rel.replace("/", os.sep))
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "wb") as f:
        f.write(content)

print(f"Pre-patched {len(files_to_upload)} files")

# Connect and upload
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(PC3, username=USER, password=PASSW, timeout=15)
sftp = ssh.open_sftp()

# Ensure dirs
for d in ["", "engage_modules", "shared", "proxy_ext"]:
    rdir = REMOTE_BASE + "/" + d if d else REMOTE_BASE
    try:
        sftp.stat(rdir)
    except:
        try:
            sftp.mkdir(rdir)
        except:
            pass

# Upload
total_ok = 0
for rel, _ in files_to_upload:
    local = os.path.join(tmpdir, rel.replace("/", os.sep))
    remote = REMOTE_BASE + "/" + rel
    local_size = os.path.getsize(local)
    sftp.put(local, remote)

    # Verify size
    remote_stat = sftp.stat(remote)
    remote_size = remote_stat.st_size
    status = "OK" if remote_size == local_size else f"MISMATCH ({remote_size} vs {local_size})"
    print(f"  {status} {rel} ({local_size}b)")
    if remote_size == local_size:
        total_ok += 1

sftp.close()

# Cleanup temp
shutil.rmtree(tmpdir, ignore_errors=True)

print(f"\nUpload: {total_ok}/{len(files_to_upload)} OK")

# Now start the bot
print("\n=== Iniciando bot ===")
import time

# Kill old processes
ssh.exec_command("powershell -c \"Get-Process python*,chrome* -ErrorAction SilentlyContinue | Stop-Process -Force\"", timeout=10)
time.sleep(2)

# Create a launcher script on PC3
launcher = (
    "import os, sys\n"
    "os.chdir('C:/projetos-navegador')\n"
    "sys.path.insert(0, 'C:/projetos-navegador')\n"
    "sys.path.insert(0, 'C:/projetos-navegador/shared')\n"
    "exec(open('C:/projetos-navegador/mega_engage.py').read())\n"
)
# Write launcher via SSH
ssh.exec_command(
    f"powershell -c \"Set-Content -Path 'C:/projetos-navegador/_launcher.py' -Value @'\n{launcher}\n'@\"",
    timeout=10
)
time.sleep(1)

# Start with Start-Process
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

time.sleep(10)

# Check
_, stdout, _ = ssh.exec_command(
    "powershell -c \"(Get-Process python* -ErrorAction SilentlyContinue | Measure-Object).Count\"",
    timeout=10
)
count = stdout.read().decode().strip()
print(f"Processos Python: {count}")

_, stdout, _ = ssh.exec_command(
    "powershell -c \"Get-Content C:/projetos-navegador/bot_output.log -Tail 20 -ErrorAction SilentlyContinue\"",
    timeout=10
)
print(f"\n=== Output ===\n{stdout.read().decode('utf-8', errors='replace').strip()}")

_, stdout, _ = ssh.exec_command(
    "powershell -c \"Get-Content C:/projetos-navegador/bot_error.log -Tail 20 -ErrorAction SilentlyContinue\"",
    timeout=10
)
errlog = stdout.read().decode('utf-8', errors='replace').strip()
if errlog:
    print(f"\n=== Errors ===\n{errlog}")

ssh.close()
print("\nDone.")
