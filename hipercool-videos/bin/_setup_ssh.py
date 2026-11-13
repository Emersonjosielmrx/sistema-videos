# -*- coding: utf-8 -*-
"""Add SSH public key to PC2 authorized_keys via daemon."""
import pathlib, urllib.request, json, os

ssh_dir = pathlib.Path(os.environ.get("USERPROFILE", "C:/Users/Haylla")) / ".ssh"
pub_key = (ssh_dir / "id_rsa_pc2.pub").read_text().strip()
print("Key:", pub_key[:60], "...")

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

# Step 1: Create .ssh dir
r = _exec(r"mkdir C:\Users\Emerson-IA\.ssh", cwd="C:/Users/Emerson-IA")
print("1. mkdir .ssh:", r.get("returncode"))

# Step 2: Write authorized_keys with our public key
auth_keys = r"C:\Users\Emerson-IA\.ssh\authorized_keys"
# Use PowerShell to write the file
write_cmd = (
    r"powershell -Command \""
    r"Set-Content -Path '" + auth_keys + "' -Value '" + pub_key + r"' -NoNewline -Encoding utf8; "
    r"Write-Host OK\""
)
r = _exec(write_cmd, cwd="C:/Users/Emerson-IA")
print("2. Write authorized_keys:", r.get("returncode"), r.get("stdout", "").strip())

# Step 3: Verify
verify_cmd = r"powershell -Command \"Get-Content " + auth_keys + r"\""
r = _exec(verify_cmd, cwd="C:/Users/Emerson-IA")
print("3. Verify rc:", r.get("returncode"))
if r.get("returncode") == 0:
    content = r.get("stdout", "")
    print("   Contains our key:", pub_key[:40] in content)
    print("   Lines:", len(content.strip().splitlines()))

# Step 4: Set proper permissions
r = _exec(
    r"icacls " + auth_keys + r" /inheritance:r /grant:r 'Emerson-IA:R'",
    cwd="C:/Users/Emerson-IA"
)
print("4. Set permissions:", r.get("returncode"), r.get("stdout", "").strip()[:50])
