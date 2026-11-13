# -*- coding: utf-8 -*-
"""Debug robocopy - check from daemon's perspective after."""
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

NAS_DIR = "D:/historias-em-frames/workspace/worker_jobs/_robocopy_debug2"
os.makedirs(NAS_DIR, exist_ok=True)
img_src = "D:/historias-em-frames/workspace/images/comedia_d39446a4ff/scene_00_final.png"
nas_input = os.path.join(NAS_DIR, "input.png")
nas_output = os.path.join(NAS_DIR, "output.mp4")
nas_output_dir = os.path.dirname(nas_output).replace("/", "\\")
shutil.copy2(img_src, nas_input)
print(f"PC1: wrote image to NAS")

def to_unc(path):
    p = path.replace("/", "\\")
    if p.startswith("D:") or p.startswith("D\\"):
        return "\\\\100.118.234.102\\d$" + p[2:]
    return p

nas_input_unc = to_unc(nas_input)

# Daemon: Copy NAS -> C:/app
cmd = f'powershell -Command "Copy-Item -Path \'{nas_input_unc}\' -Destination C:\\app\\input.png -Force; Write-Host COPY_OK"'
r = _exec(cmd)
print(f"Copy: rc={r.get('returncode')} stdout={r.get('stdout','').strip()}")

# Daemon: create output dir on NAS
nas_out_dir_unc = to_unc(os.path.dirname(nas_output))
cmd = f'powershell -Command "New-Item -ItemType Directory -Force -Path \'{nas_out_dir_unc}\' | Out-Null; Write-Host MKDIR_OK"'
r = _exec(cmd)
print(f"mkdir: rc={r.get('returncode')} stdout={r.get('stdout','').strip()}")

# Daemon: run ffmpeg
py_wrapper = r'''
import subprocess, sys, pathlib
img = pathlib.Path(r"C:\app\input.png")
out = pathlib.Path(r"C:\app\output.mp4")
print("IMG:", img.exists(), img.stat().st_size if img.exists() else 0, flush=True)
vf = "scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2:color=black,zoompan=z='1.03':d=1:fps=25:s=720x1280"
args = [
    "ffmpeg", "-y", "-loop", "1", "-i", str(img),
    "-vf", vf, "-pix_fmt", "yuv420p", "-t", "3",
    "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23", "-threads", "2", str(out)
]
print("ffmpeg...", flush=True)
result = subprocess.run(args, capture_output=True, text=True, timeout=120)
print("rc:", result.returncode, flush=True)
if result.returncode != 0:
    print("ERR:", result.stderr[-200:], flush=True)
    sys.exit(1)
print("OUT:", out.stat().st_size, flush=True)
sys.exit(0)
'''
nas_wrapper = os.path.join(NAS_DIR, "render.py")
with open(nas_wrapper, "w", encoding="utf-8") as f:
    f.write(py_wrapper)
nas_wrapper_unc = to_unc(nas_wrapper)
cmd = f'powershell -Command "Copy-Item -Path \'{nas_wrapper_unc}\' -Destination C:\\app\\render.py -Force; Write-Host COPY_OK"'
r = _exec(cmd)

print("Running ffmpeg...")
r = _exec("python C:\\app\\render.py", timeout=180)
for line in r.get("stdout", "").split("\n"):
    if line.strip():
        print(f"  {line.strip()}")
if r.get("stderr"):
    print(f"  stderr: {r.get('stderr','').strip()[:200]}")

# Daemon: check C:/app before robocopy
r = _exec('powershell -Command "Get-ChildItem C:\\app\\*.mp4 | Select-Object Name,Length"')
print(f"\nDaemon sees in C:/app:")
for line in r.get("stdout", "").split("\n"):
    if line.strip():
        print(f"  {line.strip()}")

# Daemon: robocopy C:/app -> NAS
print(f"\nRobocopy source: C:\\app\\output.mp4")
print(f"Robocopy dest: {nas_out_dir_unc}")
rob_cmd = f'robocopy C:\\app "{nas_out_dir_unc}" output.mp4 /R:2 /W:5 /NP /NFL /NDL /NJH /NJS'
r = _exec(rob_cmd)
print(f"robocopy rc={r.get('returncode')} stdout={r.get('stdout','').strip()[:80]}")

# Daemon: verify NAS output immediately after robocopy
nas_out_unc = to_unc(nas_output)
r = _exec(f'powershell -Command "if (Test-Path \'{nas_out_unc}\') {{ Get-Item \'{nas_out_unc}\' | Select-Object Name,Length }} else {{ Write-Host NOT_FOUND }}"')
print(f"\nDaemon sees NAS output: rc={r.get('returncode')} stdout={r.get('stdout','').strip()}")
if r.get('stderr'):
    print(f"  stderr: {r.get('stderr','').strip()[:200]}")

# PC1: check via D:
time.sleep(1)
print(f"\nPC1 via D: exists={os.path.exists(nas_output)}")
if os.path.exists(nas_output):
    print(f"PC1 D: size={os.path.getsize(nas_output)//1024} KB")

# PC1: check via UNC directly
print(f"PC1 via UNC exists={os.path.exists(to_unc(nas_output))}")

# Daemon: also check if robocopy itself is finding the file
rob_verbose = f'robocopy C:\\app "{nas_out_dir_unc}" output.mp4 /R:2 /W:5 /V'
r = _exec(rob_verbose)
print(f"\nRobocopy verbose rc={r.get('returncode')}")
for line in r.get("stdout", "").split("\n"):
    if line.strip():
        print(f"  {line.strip()[:120]}")

shutil.rmtree(NAS_DIR, ignore_errors=True)
print("\nDone.")
