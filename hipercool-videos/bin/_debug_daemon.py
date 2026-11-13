# -*- coding: utf-8 -*-
"""Debug daemon SMB access."""
import urllib.request, json

DAEMON = "http://100.125.7.77:8771"

def daemon_exec(cmd, cwd="C:/"):
    p = json.dumps({"cmd": cmd, "cwd": cwd}).encode()
    req = urllib.request.Request(
        f"{DAEMON}/exec", data=p,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())

tests = [
    ("1. Local write", "powershell -Command \"Set-Content -Path C:\\app\\_debug.txt -Value debug_test; Write-Host OK\""),
    ("2. whoami", "whoami"),
    ("3. NAS base", "powershell -Command \"Test-Path '\\\\100.118.234.102\\d$'\""),
    ("4. ssh_depth.png", "powershell -Command \"Get-Item C:\\app\\ssh_depth.png | Select-Object Length\""),
    ("5. NAS worker_jobs", "powershell -Command \"Get-ChildItem '\\\\100.118.234.102\\d$\\historias-em-frames\\workspace\\worker_jobs' | Select-Object Name\""),
]

for label, cmd in tests:
    r = daemon_exec(cmd)
    stdout = r.get("stdout", "").strip()
    stderr = r.get("stderr", "").strip()
    print(f"{label}: rc={r.get('returncode')} stdout={stdout[:80]} stderr={stderr[:40]}")

# Copy-Item test
cmd6 = "powershell -Command \"Copy-Item -Path C:\\app\\ssh_depth.png -Destination '\\\\\\\\100.118.234.102\\\\d$\\\\historias-em-frames\\\\workspace\\\\worker_jobs\\\\_pc2_tests' -Force; Write-Host OK\""
r = daemon_exec(cmd6)
print(f"6. Copy-Item to NAS: rc={r.get('returncode')} stdout={r.get('stdout','').strip()}")
