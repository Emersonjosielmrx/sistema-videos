# -*- coding: utf-8 -*-
"""Teste completo: Python script no NAS executado pelo daemon."""
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

# 1. Garante C:/app no daemon
r = _exec('powershell -Command "New-Item -ItemType Directory -Force -Path C:\\app | Out-Null; Write-Host MKDIR_OK"')
print(f"1. MKDIR C:/app: rc={r.get('returncode')} stdout={r.get('stdout','').strip()}")

# 2. PC1: prepara dir no NAS
NAS_DIR = r"D:\historias-em-frames\workspace\worker_jobs\_py_script_test"
os.makedirs(NAS_DIR, exist_ok=True)
img_src = r"D:\historias-em-frames\workspace\images\comedia_d39446a4ff\scene_00_final.png"
nas_input = os.path.join(NAS_DIR, "input.png")
nas_output = os.path.join(NAS_DIR, "output.mp4")
shutil.copy2(img_src, nas_input)
print(f"2. PC1: wrote {os.path.getsize(nas_input)//1024}KB image to NAS")

# 3. PC1: escreve script para NAS (substitui paths no template)
template = open(r"D:\hipercool-videos\bin\_daemon_render_template.py", encoding="utf-8").read()
script = template.replace(
    r"D:\historias-em-frames\workspace\worker_jobs\_py_script_test\input.png",
    nas_input.replace("/", "\\")
).replace(
    r"D:\historias-em-frames\workspace\worker_jobs\_py_script_test\output.mp4",
    nas_output.replace("/", "\\")
)
nas_script = os.path.join(NAS_DIR, "render.py")
with open(nas_script, "w", encoding="utf-8") as f:
    f.write(script)
print(f"3. PC1: wrote script to NAS ({len(script)} chars)")

# 4. Daemon: copia script NAS -> C:/app
nas_script_unc = nas_script.replace("/", "\\")
r = _exec(
    f'powershell -Command "Copy-Item -Path \'{nas_script_unc}\' -Destination C:\\app\\_render.py -Force; Write-Host COPY_OK"'
)
print(f"4. Daemon copy NAS->C:/app: rc={r.get('returncode')} stdout={r.get('stdout','').strip()}")

# 5. Daemon: verifica script em C:/app
r = _exec('python -c "import pathlib; print(pathlib.Path(r\'C:\\app\\_render.py\').stat().st_size)"')
print(f"5. Script size in C:/app: rc={r.get('returncode')} stdout={r.get('stdout','').strip()}")

# 6. Daemon: executa render
print("6. Executing render script...")
t0 = time.time()
r = _exec("python C:\\app\\_render.py", timeout=180)
elapsed = time.time() - t0
print(f"   rc={r.get('returncode')} em {elapsed:.0f}s")
for line in r.get("stdout", "").split("\n"):
    if line.strip():
        print(f"   {line.strip()}")
if r.get("stderr"):
    print(f"   stderr: {r.get('stderr','').strip()[:200]}")

# 7. PC1: verifica output
if os.path.exists(nas_output):
    size = os.path.getsize(nas_output)
    print(f"\n=== SUCCESS! Output: {size//1024} KB em {elapsed:.0f}s ===")
else:
    print("\n=== FALHA: output nao encontrado no NAS ===")
    if os.path.exists(NAS_DIR):
        for f in os.listdir(NAS_DIR):
            fp = os.path.join(NAS_DIR, f)
            print(f"  NAS/{f}: {os.path.getsize(fp)//1024} KB")

# 8. Cleanup
shutil.rmtree(NAS_DIR, ignore_errors=True)
print("Done.")
