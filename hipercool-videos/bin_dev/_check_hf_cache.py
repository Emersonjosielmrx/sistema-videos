# -*- coding: utf-8 -*-
"""Test if daemon can read PC1's local HF cache via SMB."""
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

test_unc = r"\\100.118.234.102\d$\modelos_cache\huggingface\hub\models--depth-anything--Depth-Anything-V2-Small-hf\snapshots"

# Part 1: check filesystem structure
script1 = (
    "import pathlib, os\n"
    "p = pathlib.Path(r'" + test_unc + "')\n"
    "print('UNC exists:', p.exists())\n"
    "if p.exists():\n"
    "    for f in sorted(p.iterdir()):\n"
    "        print(f.name, 'DIR' if f.is_dir() else f.stat().st_size)\n"
    "    config = p / 'config.json'\n"
    "    print('config exists:', config.exists(), 'islink:', os.path.islink(str(config)))\n"
    "    blobs = (p.parent.parent / 'blobs')\n"
    "    if blobs.exists():\n"
    "        for f in sorted(blobs.iterdir())[:5]:\n"
    "            is_link = os.path.islink(str(f))\n"
    "            print('blob:', f.name, f.stat().st_size if not is_link else 'LINK')\n"
)

# Part 2: try loading config
HF_NAS = r"\\100.118.234.102\d$\modelos_cache\huggingface"
script2 = (
    "import os\n"
    "os.environ['HF_HOME'] = r'" + HF_NAS + "'\n"
    "os.environ['HF_HUB_OFFLINE_MODE'] = '1'\n"
    "os.environ['TRANSFORMERS_OFFLINE'] = '1'\n"
    "from transformers import AutoConfig\n"
    "try:\n"
    "    cfg = AutoConfig.from_pretrained('depth-anything/Depth-Anything-V2-Small-hf', local_files_only=True)\n"
    "    print('Config OK:', cfg.architectures)\n"
    "except Exception as e:\n"
    "    print('ERROR:', type(e).__name__, str(e)[:200])\n"
)

nas_dir = "D:/historias-em-frames/workspace/worker_jobs/_daemon_read_test"
os.makedirs(nas_dir, exist_ok=True)

results = []
for i, script in enumerate([script1, script2]):
    nas_script = os.path.join(nas_dir, f"check_{i}.py")
    with open(nas_script, "w", encoding="utf-8") as f:
        f.write(script)

    script_unc = nas_script.replace("/", "\\")
    if script_unc.startswith("D:") or script_unc.startswith("D\\"):
        script_unc = "\\\\100.118.234.102\\d$" + script_unc[2:]

    cmd = "powershell -Command \"Copy-Item -Path '" + script_unc + "' -Destination C:\\app\\check_" + str(i) + ".py -Force; Write-Host COPY_OK\""
    r = _exec(cmd)
    r = _exec("python C:\\app\\check_" + str(i) + ".py", timeout=60)
    results.append(r)
    print(f"\n=== Script {i} ===")
    print(f"rc={r.get('returncode')}")
    for line in r.get("stdout", "").split("\n"):
        if line.strip():
            print(f"  {line.strip()}")
    if r.get("stderr") and r.get("stderr").strip():
        print(f"  stderr: {r.get('stderr','').strip()[:200]}")

shutil.rmtree(nas_dir, ignore_errors=True)
