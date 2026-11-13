# -*- coding: utf-8 -*-
"""Verify robocopy output visibility on PC1."""
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

NAS_DIR = "D:/historias-em-frames/workspace/worker_jobs/_robocopy_verify"
os.makedirs(NAS_DIR, exist_ok=True)
img_src = "D:/historias-em-frames/workspace/images/comedia_d39446a4ff/scene_00_final.png"
nas_input = os.path.join(NAS_DIR, "input.png")
nas_output_dir = os.path.join(NAS_DIR, "out")
os.makedirs(nas_output_dir, exist_ok=True)
nas_output = os.path.join(nas_output_dir, "test.mp4")
shutil.copy2(img_src, nas_input)
print(f"PC1: wrote image to NAS")

# Daemon: Copy NAS -> C:/app
nas_unc = nas_input.replace("/", "\\")
cmd = f'powershell -Command "Copy-Item -Path \'{nas_unc}\' -Destination C:\\app -Force; Write-Host COPY_OK"'
r = _exec(cmd)
print(f"Copy NAS->C:/app: rc={r.get('returncode')} stdout={r.get('stdout','').strip()}")

# Daemon: ffmpeg
ff_cmd = (
    "ffmpeg -y -loop 1 -i C:\\app\\input.png "
    '-vf "scale=720:1280:force_original_aspect_ratio=decrease,'
    'pad=720:1280:(ow-iw)/2:(oh-ih)/2:color=black,'
    "zoompan=z='1.03':d=1:s=720x1280,fps=25\" "
    "-pix_fmt yuv420p -r 25 -t 3 "
    "-c:v libx264 -preset ultrafast -crf 23 -threads 2 C:\\app\\test.mp4"
)
r = _exec(ff_cmd, timeout=120)
print(f"ffmpeg: rc={r.get('returncode')}")
if r.get("returncode") != 0:
    print(f"  stderr: {r.get('stderr','').strip()[:300]}")
else:
    r = _exec('powershell -Command "Get-ChildItem C:\\app | Select-Object Name,Length"')
    print(f"C:/app contents: rc={r.get('returncode')}")
    for line in r.get("stdout", "").split("\n"):
        if line.strip():
            print(f"  {line.strip()}")

    # Daemon: mkdir on NAS
    nas_out_dir_unc = nas_output_dir.replace("/", "\\")
    cmd = f'powershell -Command "New-Item -ItemType Directory -Force -Path \'{nas_out_dir_unc}\' | Out-Null; Write-Host MKDIR_OK"'
    r = _exec(cmd)
    print(f"mkdir NAS dir: rc={r.get('returncode')} stdout={r.get('stdout','').strip()}")

    # Daemon: robocopy
    rob_cmd = f'robocopy C:\\app "{nas_out_dir_unc}" test.mp4 /R:2 /W:5 /NP /NFL /NDL /NJH /NJS'
    r = _exec(rob_cmd)
    print(f"robocopy: rc={r.get('returncode')}")

# PC1: check via D: drive
time.sleep(0.5)
print(f"\nPC1 via D: output dir exists: {os.path.exists(nas_output_dir)}")
print(f"PC1 via D: output exists: {os.path.exists(nas_output)}")
if os.path.exists(nas_output):
    print(f"PC1 D: Output size: {os.path.getsize(nas_output)//1024} KB")

# PC1: also check via UNC
unc_output = r"\\100.118.234.102\d$\historias-em-frames\workspace\worker_jobs\_robocopy_verify\out\test.mp4"
print(f"\nPC1 via UNC output exists: {os.path.exists(unc_output)}")
if os.path.exists(unc_output):
    print(f"PC1 UNC Output size: {os.path.getsize(unc_output)//1024} KB")

shutil.rmtree(NAS_DIR, ignore_errors=True)
print("\nDone.")
