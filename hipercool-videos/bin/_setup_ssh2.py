# -*- coding: utf-8 -*-
"""Setup SSH access: write pub key to NAS, daemon copies to PC2."""
import pathlib, urllib.request, json, os, shutil

DAEMON = "http://100.125.7.77:8771"

def _exec(cmd, cwd="C:/", timeout=30):
    p = json.dumps({"cmd": cmd, "cwd": cwd}).encode()
    req = urllib.request.Request(
        f"{DAEMON}/exec", data=p,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"returncode": -1, "stdout": "", "stderr": str(e)}

# 1. PC1: write public key to NAS
ssh_dir = pathlib.Path(os.environ.get("USERPROFILE", "C:/Users/Haylla")) / ".ssh"
pub_key = (ssh_dir / "id_rsa_pc2.pub").read_text().strip()
print("PC1: pub key length:", len(pub_key))

nas_pubkey = "D:/historias-em-frames/workspace/worker_jobs/_ssh_pubkey.txt"
pathlib.Path(nas_pubkey).parent.mkdir(parents=True, exist_ok=True)
pathlib.Path(nas_pubkey).write_text(pub_key + "\n", encoding="utf-8")
print("PC1: wrote pub key to NAS:", nas_pubkey)

# Convert to UNC for daemon
nas_pubkey_unc = "\\\\100.118.234.102\\d$\\historias-em-frames\\workspace\\worker_jobs\\_ssh_pubkey.txt"
auth_keys = "C:\\Users\\Emerson-IA\\.ssh\\authorized_keys"

# 2. Daemon: create .ssh dir
r = _exec(r"mkdir C:\Users\Emerson-IA\.ssh", cwd="C:/Users/Emerson-IA")
print("Daemon: mkdir .ssh rc:", r.get("returncode"))

# 3. Daemon: copy pubkey from NAS to authorized_keys
# Use PowerShell Copy-Item then append
copy_cmd = (
    "powershell -Command \""
    "Copy-Item -Path '" + nas_pubkey_unc + "' -Destination " + auth_keys + " -Force; "
    "Write-Host COPY_OK\""
)
r = _exec(copy_cmd, cwd="C:/Users/Emerson-IA")
print("Daemon: copy NAS->authorized_keys rc:", r.get("returncode"), r.get("stdout", "").strip())

# 4. Daemon: verify
verify = r"powershell -Command \"Get-Content " + auth_keys + r" | Measure-Object -Line\""
r = _exec(verify, cwd="C:/Users/Emerson-IA")
print("Daemon: lines in authorized_keys:", r.get("stdout", "").strip())

# Check content
check = r"powershell -Command \"Get-Content " + auth_keys + r"\""
r = _exec(check, cwd="C:/Users/Emerson-IA")
if r.get("returncode") == 0:
    content = r.get("stdout", "").strip()
    print("    First 80 chars:", content[:80])
    print("    Contains our key:", pub_key[:40] in content)

# 5. Set permissions
r = _exec(
    r"icacls " + auth_keys + r" /grant:r 'Emerson-IA:(R,W)'",
    cwd="C:/Users/Emerson-IA"
)
print("Daemon: set permissions rc:", r.get("returncode"))

# 6. Test SSH connection
print("\nPC1: Testing SSH connection...")
import subprocess
key_path = str(ssh_dir / "id_rsa_pc2")
result = subprocess.run(
    ["ssh", "-i", key_path,
     "-o", "StrictHostKeyChecking=no",
     "-o", "ConnectTimeout=10",
     "-o", "BatchMode=yes",
     "Emerson-IA@100.125.7.77",
     "echo SSH_OK && python --version"],
    capture_output=True, text=True, timeout=15
)
print("SSH rc:", result.returncode)
print("SSH stdout:", result.stdout.strip()[:100])
if result.returncode != 0:
    print("SSH stderr:", result.stderr.strip()[:200])
