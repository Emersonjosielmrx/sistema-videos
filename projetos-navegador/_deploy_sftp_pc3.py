"""Deploy engage project to PC3 via SFTP (paramiko)."""
import paramiko
import os

PC3 = "100.108.160.85"
USER = "Emerson-IA"
PASSW = "Ssh@2026"

LOCAL_BASE = r"D:\projetos-navegador"
REMOTE_BASE = "C:/projetos-navegador"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(PC3, username=USER, password=PASSW, timeout=15)
sftp = ssh.open_sftp()

# Ensure remote dirs
for d in ["", "engage_modules", "shared", "proxy_ext"]:
    rdir = REMOTE_BASE + "/" + d if d else REMOTE_BASE
    try:
        sftp.stat(rdir)
    except:
        try:
            sftp.mkdir(rdir)
            print(f"  MKDIR {rdir}")
        except:
            pass

# Root files
root_files = [
    "mega_engage.py", "engage_config.json", "all_channel_videos_full.json",
    "engage_server.py", "local_proxy.py", "RODAR_ENGAGE.bat",
]

total = 0
for f in root_files:
    local = os.path.join(LOCAL_BASE, f)
    remote = REMOTE_BASE + "/" + f
    if os.path.exists(local):
        sftp.put(local, remote)
        sz = os.path.getsize(local)
        print(f"  OK {f} ({sz}b)")
        total += 1

# engage_modules/*.py
mod_dir = os.path.join(LOCAL_BASE, "engage_modules")
for f in os.listdir(mod_dir):
    if f.endswith(".py"):
        local = os.path.join(mod_dir, f)
        remote = REMOTE_BASE + "/engage_modules/" + f
        sftp.put(local, remote)
        sz = os.path.getsize(local)
        print(f"  OK engage_modules/{f} ({sz}b)")
        total += 1

# shared/*.py
shared_dir = os.path.join(LOCAL_BASE, "shared")
for f in os.listdir(shared_dir):
    if f.endswith(".py"):
        local = os.path.join(shared_dir, f)
        remote = REMOTE_BASE + "/shared/" + f
        sftp.put(local, remote)
        sz = os.path.getsize(local)
        print(f"  OK shared/{f} ({sz}b)")
        total += 1

print(f"\nTotal: {total} arquivos enviados")

# Patch D: -> C:
print("\n[PATCH] Corrigindo caminhos D: -> C:...")
patch_targets = [
    "mega_engage.py", "engage_server.py",
    "engage_modules/config.py", "engage_modules/main.py",
    "shared/google_session.py", "shared/chrome_profile.py",
]
replacements = [
    ("D:/projetos-navegador", "C:/projetos-navegador"),
    ("D:\\projetos-navegador", "C:\\projetos-navegador"),
    ("D:/logins-google", "C:/logins-google"),
    ("D:\\logins-google", "C:\\logins-google"),
    ("D:/hipercool-videos/venv/Scripts/python.exe", "python"),
    ("D:\\hipercool-videos\\venv\\Scripts\\python.exe", "python"),
]

patched = 0
for rel in patch_targets:
    remote = REMOTE_BASE + "/" + rel
    try:
        with sftp.open(remote, "r") as rf:
            content = rf.read().decode("utf-8", errors="replace")
        original = content
        for old, new in replacements:
            content = content.replace(old, new)
        if content != original:
            with sftp.open(remote, "w") as wf:
                wf.write(content.encode("utf-8"))
            print(f"  PATCHED {rel}")
            patched += 1
        else:
            print(f"  OK {rel} (sem mudanca)")
    except Exception as e:
        print(f"  SKIP {rel}: {e}")

print(f"\nPatch: {patched} arquivos corrigidos")
sftp.close()

# Verify
_, stdout, _ = ssh.exec_command(
    r'powershell -c "(Get-Item C:\projetos-navegador\mega_engage.py).Length"', timeout=10
)
print(f"\nmega_engage.py no PC3: {stdout.read().decode().strip()} bytes")

_, stdout, _ = ssh.exec_command(
    r'powershell -c "(Get-ChildItem C:\projetos-navegador\engage_modules\*.py).Count"', timeout=10
)
print(f"engage_modules/*.py: {stdout.read().decode().strip()} arquivos")

ssh.close()
print("\nDeploy SFTP concluido!")
