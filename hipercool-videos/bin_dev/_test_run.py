# -*- coding: utf-8 -*-
"""Test /run endpoint."""
import urllib.request, json

DAEMON = "http://100.125.7.77:8771"

def daemon_run(script, timeout=30):
    p = json.dumps({"script": script}).encode()
    req = urllib.request.Request(
        f"{DAEMON}/run", data=p,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())

# Test 1: simple print
r = daemon_run('print("Hello from daemon Python!")')
print("1. Simple:", r.get("returncode"), "|", r.get("stdout", "").strip())

# Test 2: UNC path exists
NAS_DIR = r"\\100.118.234.102\d$\historias-em-frames\workspace\worker_jobs\_pc2_tests"
script2 = (
    "import pathlib\n"
    f"NAS_DIR = r'{NAS_DIR}'\n"
    "print('NAS_DIR:', NAS_DIR)\n"
    "p = pathlib.Path(NAS_DIR)\n"
    "print('exists:', p.exists())\n"
    "src = pathlib.Path(r'C:\\app\\ssh_depth.png')\n"
    "print('src exists:', src.exists(), 'size:', src.stat().st_size)\n"
    "dst = p / 'ssh_depth.png'\n"
    "import shutil\n"
    "shutil.copy2(src, dst)\n"
    "print('Copied! size:', dst.stat().st_size)\n"
)
r = daemon_run(script2)
print("2. Copy rc:", r.get("returncode"))
print("   stdout:", r.get("stdout", "").strip())
print("   stderr:", (r.get("stderr") or "").strip()[:80])

# Test 3: verify on PC1
import pathlib
nas_path = pathlib.Path(r"//100.118.234.102/d$/historias-em-frames/workspace/worker_jobs/_pc2_tests/ssh_depth.png")
print("3. PC1 sees:", nas_path.exists(), "| size:", nas_path.stat().st_size if nas_path.exists() else 0)
