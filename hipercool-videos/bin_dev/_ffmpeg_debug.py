# -*- coding: utf-8 -*-
"""Debug ffmpeg zoompan filter syntax via daemon."""
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

NAS_DIR = "D:/historias-em-frames/workspace/worker_jobs/_ffmpeg_debug"
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

# Daemon: verify image in C:/app
r = _exec("powershell -Command \"Get-ChildItem C:\\app | Select-Object Name,Length\"")
print(f"C:/app: rc={r.get('returncode')}")
for line in r.get("stdout", "").split("\n"):
    if line.strip():
        print(f"  {line.strip()}")

# Test different zoompan syntaxes
tests = [
    # Test 1: simple zoompan with single quotes
    ("zoompan simple", (
        "ffmpeg -y -loop 1 -i C:\\app\\input.png "
        "-vf \"zoompan=z='1.03':d=1:s=720x1280,fps=25\" "
        "-pix_fmt yuv420p -r 25 -t 1 "
        "-c:v libx264 -preset ultrafast -crf 23 C:\\app\\test1.mp4"
    )),
    # Test 2: zoompan without quotes in z expr
    ("zoompan no quotes", (
        "ffmpeg -y -loop 1 -i C:\\app\\input.png "
        "-vf zoompan=z=1.03:d=1:s=720x1280,fps=25 "
        "-pix_fmt yuv420p -r 25 -t 1 "
        "-c:v libx264 -preset ultrafast -crf 23 C:\\app\\test2.mp4"
    )),
    # Test 3: just scale+pad (no zoompan)
    ("scale+pad only", (
        "ffmpeg -y -loop 1 -i C:\\app\\input.png "
        "-vf \"scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2:color=black\" "
        "-pix_fmt yuv420p -r 25 -t 1 "
        "-c:v libx264 -preset ultrafast -crf 23 C:\\app\\test3.mp4"
    )),
    # Test 4: scale+pad via daemon with working syntax (test3's filter string in double quotes)
    ("full filter with escaped quotes", (
        "ffmpeg -y -loop 1 -i C:\\app\\input.png "
        "-vf \"scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2:color=black,zoompan=z='1.03':d=1:s=720x1280,fps=25\" "
        "-pix_fmt yuv420p -r 25 -t 1 "
        "-c:v libx264 -preset ultrafast -crf 23 C:\\app\\test4.mp4"
    )),
]

for name, ff_cmd in tests:
    print(f"\n--- Test: {name} ---")
    r = _exec(ff_cmd, timeout=60)
    rc = r.get("returncode")
    stderr = r.get("stderr", "")
    if rc == 0:
        # Check file size
        r2 = _exec("powershell -Command \"Get-ChildItem C:\\app\\test*.mp4 | Select-Object Name,Length\"")
        print(f"  rc={rc} OK")
        for line in r2.get("stdout", "").split("\n"):
            if line.strip(): print(f"  {line.strip()}")
    else:
        # Show first 3 lines of stderr
        err_lines = [l for l in stderr.split("\n") if l.strip()][:3]
        print(f"  rc={rc}")
        for l in err_lines:
            print(f"  stderr: {l.strip()[:100]}")

shutil.rmtree(NAS_DIR, ignore_errors=True)
print("\nDone.")
