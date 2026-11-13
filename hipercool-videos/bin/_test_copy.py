# -*- coding: utf-8 -*-
"""Test copy with verification."""
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

NAS_DIR = r"\\100.118.234.102\d$\historias-em-frames\workspace\worker_jobs\_pc2_tests"
SRC = r"C:\app\ssh_depth.png"

# Verify source
r = daemon_exec(
    r'powershell -Command "Get-Item C:\app\ssh_depth.png | Select-Object Length"'
)
print("Source:", r.get("stdout", "").strip())

# Copy
r = daemon_exec(
    r'powershell -Command "Copy-Item -Path C:\app\ssh_depth.png -Destination \\\\100.118.234.102\d$\historias-em-frames\workspace\worker_jobs\_pc2_tests -Force; Write-Host COPY_DONE"'
)
print("Copy rc:", r.get("returncode"), "| stdout:", r.get("stdout", "").strip())

# Verify dest
r = daemon_exec(
    r'powershell -Command "if (Test-Path \\100.118.234.102\d$\historias-em-frames\workspace\worker_jobs\_pc2_tests\ssh_depth.png) { Write-Host EXISTS } else { Write-Host MISSING }"'
)
print("Verify:", r.get("returncode"), "|", r.get("stdout", "").strip())

# Check on PC1 side
import pathlib
nas_path = pathlib.Path(r"//100.118.234.102/d$/historias-em-frames/workspace/worker_jobs/_pc2_tests/ssh_depth.png")
print("PC1 sees:", nas_path.exists(), "| size:", nas_path.stat().st_size if nas_path.exists() else 0)
