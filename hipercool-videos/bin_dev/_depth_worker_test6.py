# -*- coding: utf-8 -*-
"""Test depth model with snapshot path instead of model ID."""
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

NAS_DIR = "D:/historias-em-frames/workspace/worker_jobs/_depth_test6"
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
MODEL_PATH = "\\\\100.118.234.102\\d$\\historias-em-frames\\workspace\\hf_cache\\hub\\models--depth-anything--Depth-Anything-V2-Small-hf\\snapshots\\5426e4f0f36572d16453bbda7a8389317b1bef99"

py_script = rf'''
import os, sys, pathlib
HF_HOME = r"{HF_HOME}"
MODEL_PATH = r"{MODEL_PATH}"
os.environ["HF_HOME"] = HF_HOME
os.environ["HF_HUB_OFFLINE_MODE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
print("HF_HOME:", HF_HOME, flush=True)
print("MODEL_PATH:", MODEL_PATH, flush=True)
print("MODEL_PATH exists:", pathlib.Path(MODEL_PATH).exists(), flush=True)

# List what's in the model path
model_path = pathlib.Path(MODEL_PATH)
if model_path.exists():
    for f in sorted(model_path.iterdir()):
        print(f"  {f.name}: {f.stat().st_size if f.is_file() else 'dir'}", flush=True)

try:
    from transformers import pipeline, AutoModelForDepthEstimation, AutoImageProcessor
    print("Trying with local_files_only=True...", flush=True)

    # Try loading via pipeline with local files
    depth = pipeline(
        "depth-estimation",
        model=MODEL_PATH,
        local_files_only=True
    )
    print("Model loaded via pipeline!", flush=True)

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
    print("ERROR:", type(e).__name__, str(e)[:400], flush=True)
    import traceback
    traceback.print_exc()
'''

nas_script = os.path.join(NAS_DIR, "depth_test6.py")
with open(nas_script, "w", encoding="utf-8") as f:
    f.write(py_script)
nas_script_unc = to_unc(nas_script)

cmd = f'powershell -Command "Copy-Item -Path \'{nas_script_unc}\' -Destination C:\\app\\depth_test6.py -Force; Write-Host COPY_OK"'
r = _exec(cmd)
print(f"Copy script: rc={r.get('returncode')} stdout={r.get('stdout','').strip()}")

print("\nRunning depth-anything on PC2 (snapshot path)...")
t0 = time.time()
r = _exec("python C:\\app\\depth_test6.py", timeout=300)
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
