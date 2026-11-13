# -*- coding: utf-8 -*-
"""Full depth test: HF_HOME pointing to PC1's local HF cache via SMB D$ share."""
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

NAS_DIR = "D:/historias-em-frames/workspace/worker_jobs/_depth_final"
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

# HF_HOME points to PC1's local HF cache via SMB D$ share
HF_HOME = "\\\\100.118.234.102\\d$\\modelos_cache\\huggingface"

py_script = (
    "import os, sys, pathlib\n"
    "HF_HOME = r'" + HF_HOME + "'\n"
    "NAS_INPUT = r'" + nas_input_unc + "'\n"
    "NAS_OUTPUT = r'" + nas_output_unc + "'\n"
    "os.environ['HF_HOME'] = HF_HOME\n"
    "os.environ['HF_HUB_OFFLINE_MODE'] = '1'\n"
    "os.environ['TRANSFORMERS_OFFLINE'] = '1'\n"
    "print('HF_HOME:', HF_HOME, flush=True)\n"
    "print('Loading depth-anything...', flush=True)\n"
    "from transformers import pipeline\n"
    "depth = pipeline('depth-estimation', model='depth-anything/Depth-Anything-V2-Small-hf')\n"
    "print('Model loaded!', flush=True)\n"
    "print('Running inference...', flush=True)\n"
    "result = depth(NAS_INPUT)\n"
    "print('Inference done!', flush=True)\n"
    "out_path = pathlib.Path(NAS_OUTPUT)\n"
    "out_path.parent.mkdir(parents=True, exist_ok=True)\n"
    "result['depth'].save(out_path)\n"
    "print('Saved:', out_path.exists(), out_path.stat().st_size // 1024, 'KB', flush=True)\n"
)

nas_script = os.path.join(NAS_DIR, "depth_final.py")
with open(nas_script, "w", encoding="utf-8") as f:
    f.write(py_script)
nas_script_unc = to_unc(nas_script)

cmd = "powershell -Command \"Copy-Item -Path '" + nas_script_unc + "' -Destination C:\\app\\depth_final.py -Force; Write-Host COPY_OK\""
r = _exec(cmd)
print(f"Copy script: rc={r.get('returncode')} stdout={r.get('stdout','').strip()}")

print("\nRunning depth-anything on PC2 (HF_HOME=D$ share)...")
t0 = time.time()
r = _exec("python C:\\app\\depth_final.py", timeout=300)
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
