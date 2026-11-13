# -*- coding: utf-8 -*-
"""FFmpeg test via daemon Python subprocess (avoids shell escaping)."""
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

NAS_DIR = "D:/historias-em-frames/workspace/worker_jobs/_ffmpeg_py_test"
os.makedirs(NAS_DIR, exist_ok=True)
img_src = "D:/historias-em-frames/workspace/images/comedia_d39446a4ff/scene_00_final.png"
nas_input = os.path.join(NAS_DIR, "input.png")
shutil.copy2(img_src, nas_input)
print(f"PC1: wrote image to NAS")

# Daemon: Copy NAS -> C:/app
nas_unc = nas_input.replace("/", "\\")
cmd = f'powershell -Command "Copy-Item -Path \'{nas_unc}\' -Destination C:\\app -Force; Write-Host COPY_OK"'
r = _exec(cmd)
print(f"Copy: rc={r.get('returncode')} stdout={r.get('stdout','').strip()}")

# Daemon: write Python wrapper to C:/app that calls ffmpeg directly
py_wrapper = r'''
import subprocess, sys, pathlib
img = pathlib.Path(r"C:\app\input.png")
out = pathlib.Path(r"C:\app\py_test.mp4")
print("IMG exists:", img.exists(), "size:", img.stat().st_size if img.exists() else 0)
vf = "scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2:color=black,zoompan=z='if(lte(i,1),1.03,1)':d=1:s=720x1280,fps=25"
args = [
    "ffmpeg", "-y",
    "-loop", "1", "-i", str(img),
    "-vf", vf,
    "-pix_fmt", "yuv420p", "-r", "25", "-t", "3",
    "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23", "-threads", "2",
    str(out)
]
print("Running:", " ".join(args[:5]) + " ...")
result = subprocess.run(args, capture_output=True, text=True, timeout=120)
print("rc:", result.returncode)
if result.returncode != 0:
    print("stderr:", result.stderr[-300:])
sys.exit(result.returncode)
'''
nas_wrapper = os.path.join(NAS_DIR, "fftest.py")
with open(nas_wrapper, "w", encoding="utf-8") as f:
    f.write(py_wrapper)
nas_wrapper_unc = nas_wrapper.replace("/", "\\")
cmd = f'powershell -Command "Copy-Item -Path \'{nas_wrapper_unc}\' -Destination C:\\app\\fftest.py -Force; Write-Host COPY_OK"'
r = _exec(cmd)
print(f"Copy wrapper: rc={r.get('returncode')} stdout={r.get('stdout','').strip()}")

# Execute via daemon Python (no shell escaping!)
r = _exec("python C:\\app\\fftest.py", timeout=180)
print(f"Python ffmpeg: rc={r.get('returncode')} em {r.get('stdout','').strip()}")
for line in r.get("stdout", "").split("\n"):
    if line.strip():
        print(f"  {line.strip()}")
if r.get("stderr"):
    print(f"  stderr: {r.get('stderr','').strip()[:200]}")

# Check C:/app
r = _exec("powershell -Command \"Get-ChildItem C:\\app\\*.mp4 | Select-Object Name,Length\"")
print(f"C:/app mp4s: rc={r.get('returncode')}")
for line in r.get("stdout", "").split("\n"):
    if line.strip():
        print(f"  {line.strip()}")

shutil.rmtree(NAS_DIR, ignore_errors=True)
print("Done.")
