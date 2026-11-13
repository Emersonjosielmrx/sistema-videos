# -*- coding: utf-8 -*-
"""Test: daemon runs depth-anything model with HF_HOME on NAS UNC."""
import urllib.request, json, shutil, os

DAEMON = "http://100.125.7.77:8771"

def _exec(cmd, cwd="C:/", timeout=30):
    p = json.dumps({"cmd": cmd, "cwd": cwd}).encode()
    req = urllib.request.Request(
        f"{DAEMON}/exec", data=p,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())

NAS_DIR = "D:/historias-em-frames/workspace/worker_jobs/_depth_test"
os.makedirs(NAS_DIR, exist_ok=True)
img_src = "D:/historias-em-frames/workspace/images/comedia_d39446a4ff/scene_00_final.png"
nas_input = os.path.join(NAS_DIR, "input.png")
nas_output = os.path.join(NAS_DIR, "depth.png")
shutil.copy2(img_src, nas_input)
print(f"PC1: wrote {os.path.getsize(nas_input)//1024}KB image to NAS")

def to_unc(path):
    p = path.replace("/", "\\")
    if p.startswith("D:") or p.startswith("D\\"):
        return "\\\\100.118.234.102\\d$" + p[2:]
    return p

nas_input_unc = to_unc(nas_input)
nas_output_unc = to_unc(nas_output)
HF_HOME = "\\\\100.118.234.102\\d$\\historias-em-frames\\workspace\\hf_cache"

# Python script that runs depth-anything on daemon
py_script = (
    "import os, sys, pathlib\n"
    "os.environ['HF_HOME'] = r'" + HF_HOME + "'\n"
    "os.environ['TRANSFORMERS_OFFLINE'] = '0'\n"
    "print('HF_HOME:', os.environ.get('HF_HOME'), flush=True)\n"
    "\n"
    "from transformers import pipeline\n"
    "print('Loading depth-anything-v2...', flush=True)\n"
    "depth = pipeline('depth-estimation', model='depth-anything/Depth-Anything-V2-base-hf')\n"
    "print('Model loaded!', flush=True)\n"
    "\n"
    "NAS_INPUT = pathlib.Path(r'" + nas_input_unc + "')\n"
    "NAS_OUTPUT = pathlib.Path(r'" + nas_output_unc + "')\n"
    "print('Input exists:', NAS_INPUT.exists(), flush=True)\n"
    "\n"
    "result = depth(str(NAS_INPUT))\n"
    "print('Depth inference done!', flush=True)\n"
    "\n"
    "depth_img = result['depth']\n"
    "NAS_OUTPUT.parent.mkdir(parents=True, exist_ok=True)\n"
    "depth_img.save(NAS_OUTPUT)\n"
    "print('Saved:', NAS_OUTPUT.exists(), NAS_OUTPUT.stat().st_size // 1024, 'KB', flush=True)\n"
)

nas_script = os.path.join(NAS_DIR, "depth_test.py")
with open(nas_script, "w", encoding="utf-8") as f:
    f.write(py_script)
nas_script_unc = to_unc(nas_script)
print(f"PC1: wrote script to NAS")

# Daemon: Copy script NAS -> C:/app
cmd = f'powershell -Command "Copy-Item -Path \'{nas_script_unc}\' -Destination C:\\app\\depth_test.py -Force; Write-Host COPY_OK"'
r = _exec(cmd)
print(f"Copy script: rc={r.get('returncode')} stdout={r.get('stdout','').strip()}")

# Daemon: run depth test
print("\nExecuting depth-anything on PC2 (first run downloads model to NAS cache)...")
import time; t0 = time.time()
r = _exec("python C:\\app\\depth_test.py", timeout=600)
elapsed = time.time() - t0
print(f"\nrc={r.get('returncode')} em {elapsed:.0f}s")
for line in r.get("stdout", "").split("\n"):
    if line.strip():
        print(f"  {line.strip()}")
if r.get("stderr"):
    err = r.get("stderr", "")
    if err.strip():
        print(f"  stderr: {err.strip()[:300]}")

# PC1: verify output
print(f"\nPC1: depth output exists: {os.path.exists(nas_output)}")
if os.path.exists(nas_output):
    print(f"SUCCESS: depth map {os.path.getsize(nas_output)//1024} KB")

shutil.rmtree(NAS_DIR, ignore_errors=True)
print("\nDone.")
