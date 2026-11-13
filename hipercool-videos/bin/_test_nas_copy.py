# -*- coding: utf-8 -*-
"""Test NAS->C: copy via daemon."""
import urllib.request, json

DAEMON = "http://100.125.7.77:8771"

def daemon_exec(cmd, cwd="C:/", timeout=30):
    p = json.dumps({"cmd": cmd, "cwd": cwd}).encode()
    req = urllib.request.Request(
        f"{DAEMON}/exec", data=p,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())

# Daemon: Copy-Item from NAS to C:/app
# Using PowerShell with escaped UNC path
src = r"\\100.118.234.102\d$\historias-em-frames\workspace\worker_jobs\_pc2_tests\test_copy_script.py"
dst = r"C:\app\test_from_nas.py"

# Test 1: Copy-Item via PowerShell
r = daemon_exec(
    f'powershell -Command "Copy-Item -Path \'{src}\' -Destination {dst} -Force; Write-Host COPY_OK"'
)
print("Copy-Item rc:", r.get("returncode"), "| stdout:", r.get("stdout", "").strip(), "| stderr:", (r.get("stderr") or "").strip()[:80])

# Test 2: Check if file exists
r2 = daemon_exec(r"powershell -Command \"Test-Path C:\app\test_from_nas.py\"")
print("File exists:", r2.get("returncode"), "|", r2.get("stdout", "").strip())
