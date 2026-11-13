# -*- coding: utf-8 -*-
"""Full round-trip test: SSH depth inference -> daemon /run copy to NAS."""
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

NAS_DIR = r"\\100.118.234.102\d$\historias-em-frames\workspace\worker_jobs\_pc2_tests"
script = (
    "import shutil, pathlib, sys\n"
    f"NAS_DIR = r'{NAS_DIR}'\n"
    "src = pathlib.Path(r'C:\\app\\final_depth.png')\n"
    "dst = pathlib.Path(NAS_DIR) / 'final_depth.png'\n"
    "dst.parent.mkdir(parents=True, exist_ok=True)\n"
    "shutil.copy2(src, dst)\n"
    "print('Copied:', dst.stat().st_size, 'bytes')\n"
    "sys.exit(0)\n"
)

r = daemon_run(script)
print("rc:", r.get("returncode"))
print("stdout:", r.get("stdout", "").strip())
print("stderr:", (r.get("stderr") or "").strip()[:80])

# Verify on PC1
import pathlib
nas_path = pathlib.Path(r"//100.118.234.102/d$/historias-em-frames/workspace/worker_jobs/_pc2_tests/final_depth.png")
print("PC1 sees:", nas_path.exists(), "| size:", nas_path.stat().st_size if nas_path.exists() else 0)
