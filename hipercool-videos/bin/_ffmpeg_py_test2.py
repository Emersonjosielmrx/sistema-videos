# -*- coding: utf-8 -*-
"""FFmpeg test via daemon Python subprocess - with proper UNC paths."""
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

NAS_DIR = "D:/historias-em-frames/workspace/worker_jobs/_ffmpeg_py_test2"
os.makedirs(NAS_DIR, exist_ok=True)
img_src = "D:/historias-em-frames/workspace/images/comedia_d39446a4ff/scene_00_final.png"
nas_input = os.path.join(NAS_DIR, "input.png")
shutil.copy2(img_src, nas_input)
print(f"PC1: wrote image to NAS ({os.path.getsize(nas_input)//1024}KB)")

# PC1 local D:\ -> PC2 daemon UNC
def to_unc(path):
    p = path.replace("/", "\\")
    if p.startswith("D:") or p.startswith("D\\"):
        return "\\\\100.118.234.102\\d$" + p[2:]
    return p

nas_input_unc = to_unc(nas_input)
print(f"NAS input UNC: {nas_input_unc}")

# Daemon: Copy NAS -> C:/app
cmd = f'powershell -Command "Copy-Item -Path \'{nas_input_unc}\' -Destination C:\\app\\input.png -Force; Write-Host COPY_OK"'
r = _exec(cmd)
print(f"Copy: rc={r.get('returncode')} stdout={r.get('stdout','').strip()}")

# Daemon: verify image in C:/app
r = _exec("powershell -Command \"Get-ChildItem C:\\app\\input.png | Select-Object Name,Length\"")
print(f"Image in C:/app: rc={r.get('returncode')}")
for line in r.get("stdout", "").split("\n"):
    if line.strip():
        print(f"  {line.strip()}")

# Daemon: write Python wrapper to C:/app (daemon itself writes the file)
py_wrapper = r'''
import subprocess, sys, pathlib
img = pathlib.Path(r"C:\app\input.png")
out = pathlib.Path(r"C:\app\py_test.mp4")
print("IMG exists:", img.exists(), flush=True)
if not img.exists():
    print("FALHA: input not found", flush=True)
    sys.exit(1)
print("IMG size:", img.stat().st_size, flush=True)

vf = "scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2:color=black,zoompan=z=if(lte(i,1),1.03,1):d=1:s=720x1280,fps=25"
args = [
    "ffmpeg", "-y",
    "-loop", "1", "-i", str(img),
    "-vf", vf,
    "-pix_fmt", "yuv420p", "-r", "25", "-t", "3",
    "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23", "-threads", "2",
    str(out)
]
print("Running ffmpeg...", flush=True)
result = subprocess.run(args, capture_output=True, text=True, timeout=120)
print("rc:", result.returncode, flush=True)
if result.returncode != 0:
    print("stderr:", result.stderr[-400:], flush=True)
    sys.exit(1)
print("OUT size:", out.stat().st_size, flush=True)
sys.exit(0)
'''

# Daemon writes the wrapper directly to C:/app (no NAS intermediary)
wrapped = json.dumps({"cmd": "python -c \"open(r'C:\\app\\fftest.py','w',encoding='utf-8').write(" + json.dumps(py_wrapper) + "); print('wrote') + str(open(r'C:\\app\\fftest.py').read().__len__())\"", "cwd": "C:/"})
# Simpler: daemon writes using echo redirect
# Actually let's just use the NAS approach but with UNC
nas_wrapper = os.path.join(NAS_DIR, "fftest.py")
with open(nas_wrapper, "w", encoding="utf-8") as f:
    f.write(py_wrapper)
nas_wrapper_unc = to_unc(nas_wrapper)
print(f"Script UNC: {nas_wrapper_unc}")

# Daemon: Copy script from NAS (UNC) -> C:/app
cmd = f'powershell -Command "Copy-Item -Path \'{nas_wrapper_unc}\' -Destination C:\\app\\fftest.py -Force; Write-Host COPY_OK"'
r = _exec(cmd)
print(f"Copy script: rc={r.get('returncode')} stdout={r.get('stdout','').strip()}")

# Daemon: verify script in C:/app
r = _exec("powershell -Command \"Get-ChildItem C:\\app\\fftest.py | Select-Object Name,Length\"")
print(f"Script in C:/app: rc={r.get('returncode')}")
for line in r.get("stdout", "").split("\n"):
    if line.strip():
        print(f"  {line.strip()}")

# Daemon: execute via Python (no shell escaping)
print("Executing Python ffmpeg wrapper...")
r = _exec("python C:\\app\\fftest.py", timeout=180)
print(f"rc={r.get('returncode')}")
for line in r.get("stdout", "").split("\n"):
    if line.strip():
        print(f"  {line.strip()}")
if r.get("stderr"):
    print(f"  stderr: {r.get('stderr','').strip()[:200]}")

# Check C:/app for mp4
r = _exec("powershell -Command \"Get-ChildItem C:\\app\\*.mp4 | Select-Object Name,Length\"")
print(f"C:/app mp4s: rc={r.get('returncode')}")
for line in r.get("stdout", "").split("\n"):
    if line.strip():
        print(f"  {line.strip()}")

# Daemon: robocopy output to NAS
nas_output = os.path.join(NAS_DIR, "output.mp4")
nas_output_dir_unc = to_unc(os.path.dirname(nas_output))
nas_output_unc = to_unc(nas_output)
cmd = f'powershell -Command "New-Item -ItemType Directory -Force -Path \'{nas_output_dir_unc}\' | Out-Null; Write-Host MKDIR_OK"'
r = _exec(cmd)
print(f"mkdir NAS dir: rc={r.get('returncode')} stdout={r.get('stdout','').strip()}")

rob_cmd = f'robocopy C:\\app "{nas_output_dir_unc}" py_test.mp4 /R:2 /W:5 /NP /NFL /NDL /NJH /NJS'
r = _exec(rob_cmd)
print(f"robocopy: rc={r.get('returncode')}")

# PC1: verify
print(f"\nPC1: output exists: {os.path.exists(nas_output)}")
if os.path.exists(nas_output):
    print(f"PC1: output size: {os.path.getsize(nas_output)//1024} KB")

shutil.rmtree(NAS_DIR, ignore_errors=True)
print("Done.")
