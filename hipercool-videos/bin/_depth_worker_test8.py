# -*- coding: utf-8 -*-
"""Test: daemon downloads depth model directly to C: (no NAS intermediary)."""
import urllib.request, json, shutil, os, time

DAEMON = "http://100.125.7.77:8771"

def _exec(cmd, cwd="C:/", timeout=30):
    p = json.dumps({"cmd": cmd, "cwd": cwd}).encode()
    req = urllib.request.Request(
        f"{DAEMON}/exec", data=p,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())

NAS_DIR = "D:/historias-em-frames/workspace/worker_jobs/_depth_test8"
os.makedirs(NAS_DIR, exist_ok=True)
img_src = "D:/historias-em-frames/workspace/images/comedia_d39446a4ff/scene_00_final.png"
nas_input = os.path.join(NAS_DIR, "input.png")
nas_output = os.path.join(NAS_DIR, "depth.png")
shutil.copy2(img_src, nas_input)
print(f"PC1: wrote image to NAS")

def to_unc(path):
    p = path.replace("/", "\\")
    if p.startswith("D:") or p.startswith("D\\"):
        return "\\\\100.118.234.102\\d$" + p[2:]
    return p

nas_input_unc = to_unc(nas_input)
nas_output_unc = to_unc(nas_output)
HF_LOCAL = "C:\\hf_cache"

py_script = rf'''
import os, sys, pathlib, shutil

HF_LOCAL = r"{HF_LOCAL}"
NAS_INPUT = r"{nas_input_unc}"
NAS_OUTPUT = r"{nas_output_unc}"

os.environ["HF_HOME"] = HF_LOCAL
os.environ["HF_HUB_OFFLINE_MODE"] = "0"
os.environ["TRANSFORMERS_OFFLINE"] = "0"
os.environ["HF_TOKEN"] = ""

print("HF_HOME:", HF_LOCAL, flush=True)
print("Disk space:", flush=True)
for part in ["C:\\", "D:\\"]:
    try:
        import shutil as sh
        total, used, free = sh.disk_usage(part)
        print("  " + part + " free=" + str(free // 1024 // 1024) + " MB", flush=True)
    except:
        pass

from transformers import pipeline
print("Downloading depth-anything Small...", flush=True)
depth = pipeline("depth-estimation", model="depth-anything/Depth-Anything-V2-Small-hf")
print("Model loaded!", flush=True)

result = depth(NAS_INPUT)
print("Inference done!", flush=True)
depth_img = result["depth"]
NAS_OUTPUT_PATH = pathlib.Path(NAS_OUTPUT)
NAS_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
depth_img.save(NAS_OUTPUT_PATH)
print("Saved:", NAS_OUTPUT_PATH.exists(), NAS_OUTPUT_PATH.stat().st_size // 1024, "KB", flush=True)
'''

nas_script = os.path.join(NAS_DIR, "depth_test8.py")
with open(nas_script, "w", encoding="utf-8") as f:
    f.write(py_script)
nas_script_unc = to_unc(nas_script)

cmd = f'powershell -Command "Copy-Item -Path \'{nas_script_unc}\' -Destination C:\\app\\depth_test8.py -Force; Write-Host COPY_OK"'
r = _exec(cmd)
print(f"Copy script: rc={r.get('returncode')} stdout={r.get('stdout','').strip()}")

print("\nRunning depth-anything on PC2 (direct download to C:)...")
t0 = time.time()
r = _exec("python C:\\app\\depth_test8.py", timeout=600)
elapsed = time.time() - t0
print(f"\nrc={r.get('returncode')} em {elapsed:.0f}s")
for line in r.get("stdout", "").split("\n"):
    if line.strip():
        print(f"  {line.strip()}")
if r.get("stderr"):
    err = r.get("stderr", "")
    if err.strip():
        print(f"  stderr: {err.strip()[:500]}")

print(f"\nPC1: depth output exists: {os.path.exists(nas_output)}")
if os.path.exists(nas_output):
    print(f"SUCCESS: depth map {os.path.getsize(nas_output)//1024} KB")

shutil.rmtree(NAS_DIR, ignore_errors=True)
