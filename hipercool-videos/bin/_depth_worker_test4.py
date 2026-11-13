# -*- coding: utf-8 -*-
"""Test depth-anything on PC2 daemon with HF_HOME on NAS UNC."""
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

NAS_DIR = "D:/historias-em-frames/workspace/worker_jobs/_depth_test4"
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
HF_HOME = "\\\\100.118.234.102\\d$\\historias-em-frames\\workspace\\hf_cache"

py_script = rf'''
import os, sys, pathlib
HF_HOME = r"{HF_HOME}"
os.environ["HF_HOME"] = HF_HOME
os.environ["TRANSFORMERS_OFFLINE"] = "1"
print("HF_HOME:", HF_HOME, flush=True)

hub = pathlib.Path(HF_HOME) / "hub"
print("Hub exists:", hub.exists(), flush=True)
if hub.exists():
    for d in sorted(hub.iterdir())[:5]:
        if not d.name.startswith("."):
            print("  model:", d.name, flush=True)

try:
    from transformers import pipeline
    print("Loading depth-anything Small...", flush=True)
    depth = pipeline("depth-estimation", model="depth-anything/Depth-Anything-V2-Small-hf")
    print("Model loaded!", flush=True)

    NAS_INPUT = pathlib.Path(r"{nas_input_unc}")
    NAS_OUTPUT = pathlib.Path(r"{nas_output_unc}")
    print("Input:", NAS_INPUT.exists(), flush=True)

    result = depth(str(NAS_INPUT))
    print("Inference done!", flush=True)

    depth_img = result["depth"]
    NAS_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    depth_img.save(NAS_OUTPUT)
    print("Saved:", NAS_OUTPUT.exists(), NAS_OUTPUT.stat().st_size // 1024, "KB", flush=True)
except Exception as e:
    print("ERROR:", type(e).__name__, str(e)[:200], flush=True)
    import traceback
    traceback.print_exc()
'''

nas_script = os.path.join(NAS_DIR, "depth_test4.py")
with open(nas_script, "w", encoding="utf-8") as f:
    f.write(py_script)
nas_script_unc = to_unc(nas_script)

cmd = f'powershell -Command "Copy-Item -Path \'{nas_script_unc}\' -Destination C:\\app\\depth_test4.py -Force; Write-Host COPY_OK"'
r = _exec(cmd)
print(f"Copy script: rc={r.get('returncode')} stdout={r.get('stdout','').strip()}")

print("\nRunning depth-anything on PC2 (HF_HOME=NAS)...")
t0 = time.time()
r = _exec("python C:\\app\\depth_test4.py", timeout=300)
elapsed = time.time() - t0
print(f"\nrc={r.get('returncode')} em {elapsed:.0f}s")
for line in r.get("stdout", "").split("\n"):
    if line.strip():
        print(f"  {line.strip()}")
if r.get("stderr"):
    err = r.get("stderr", "")
    if err.strip():
        print(f"  stderr: {err.strip()[:400]}")

print(f"\nPC1: depth output exists: {os.path.exists(nas_output)}")
if os.path.exists(nas_output):
    print(f"SUCCESS: depth map {os.path.getsize(nas_output)//1024} KB")

shutil.rmtree(NAS_DIR, ignore_errors=True)
