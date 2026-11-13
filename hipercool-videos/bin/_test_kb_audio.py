# -*- coding: utf-8 -*-
"""Diagnostic: zoompan with scale+pad+pan."""
import urllib.request, json, time

DAEMON = 'http://100.125.7.77:8771'

def _run(script, timeout=300):
    payload = json.dumps({'script': script}).encode()
    req = urllib.request.Request(f'{DAEMON}/run', data=payload,
        headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())

def _exec(cmd, cwd='C:/', timeout=60):
    payload = json.dumps({'cmd': cmd, 'cwd': cwd}).encode()
    req = urllib.request.Request(f'{DAEMON}/exec', data=payload,
        headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())

UNC_IMG = r'\\100.118.234.102\d$\historias-em-frames\workspace\images\superacao_f25044c4a3\scene_29_final.png'
UNC_AUDIO = r'\\100.118.234.102\d$\historias-em-frames\workspace\narration_cache\a16bde31e52d9af1a0e1e17a46b055c8.wav'
UNC_OUT = r'\\100.118.234.102\d$\historias-em-frames\workspace\worker_jobs\_final_test3\scene_29_kb_v5.mp4'

for src, fname in [(UNC_IMG, '_kb_img.png'), (UNC_AUDIO, '_kb_audio.wav')]:
    _exec("powershell -Command \"Copy-Item -Path '" + src + "' -Destination C:\\app\\" + fname + " -Force; Write-Host OK\"",
          cwd='C:/', timeout=60)

dur = 5.0
zoom_dur = int(dur * 25)
NAS_OUT_ESC = UNC_OUT.replace("/", "//")

script = (
    "import subprocess, pathlib, shutil, sys, time\n"
    "tmp_img = pathlib.Path(r'C:\\app\\_kb_img.png')\n"
    "tmp_audio = pathlib.Path(r'C:\\app\\_kb_audio.wav')\n"
    "tmp_out = pathlib.Path(r'C:\\app\\_kb_out.mp4')\n"
    "nas_out = pathlib.Path(r'" + NAS_OUT_ESC + "')\n"
    "dur = float(" + str(dur) + ")\n"
    "zoom_dur = int(dur * 25)\n"
    "vf = (\n"
    "    'scale=720:720:force_original_aspect_ratio=decrease,'\n"
    "    'pad=720:1280:(ow-iw)/2:(oh-ih)/2:color=black,'\n"
    "    'zoompan=z=\\'min(zoom+0.0005,1.1)\\'\\:d=' + str(zoom_dur) + '\\:s=720x1280'\n"
    "    ':x=\\'iw/2-(iw/zoom/2)\\'\\:y=\\'ih/2-(ih/zoom/2)\\'\n"
    ")\n"
    "print('vf:', repr(vf), flush=True)\n"
    "args = ['ffmpeg', '-y', '-loop', '1', '-i', str(tmp_img),\n"
    "    '-i', str(tmp_audio),\n"
    "    '-vf', vf,\n"
    "    '-pix_fmt', 'yuv420p', '-r', '25',\n"
    "    '-t', str(dur),\n"
    "    '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '23',\n"
    "    '-threads', '2', '-shortest', str(tmp_out)]\n"
    "result = subprocess.run(args, capture_output=True, text=True, timeout=180)\n"
    "print('rc:', result.returncode, flush=True)\n"
    "if result.returncode != 0:\n"
    "    print('STDERR:', result.stderr[-2000:], flush=True)\n"
    "    sys.exit(1)\n"
    "nas_out.parent.mkdir(parents=True, exist_ok=True)\n"
    "shutil.copy2(tmp_out, nas_out)\n"
    "print('NAS OK:', nas_out.stat().st_size // 1024, 'KB', flush=True)\n"
    "for f in [tmp_img, tmp_audio, tmp_out]: f.unlink(missing_ok=True)\n"
    "sys.exit(0)\n"
)

print("vf lines:")
lines = [
    "import subprocess, pathlib, shutil, sys, time",
    "tmp_img = pathlib.Path(r'C:\\app\\_kb_img.png')",
    "tmp_audio = pathlib.Path(r'C:\\app\\_kb_audio.wav')",
    "tmp_out = pathlib.Path(r'C:\\app\\_kb_out.mp4')",
    "nas_out = pathlib.Path(r'" + NAS_OUT_ESC + "')",
    "dur = float(" + str(dur) + ")",
    "zoom_dur = int(dur * 25)",
    "vf = (",
    "    'scale=720:720:force_original_aspect_ratio=decrease,'",
    "    'pad=720:1280:(ow-iw)/2:(oh-ih)/2:color=black,'",
    "    'zoompan=z=\\'min(zoom+0.0005,1.1)\\'\\:d=' + str(zoom_dur) + '\\:s=720x1280'",
    "    ':x=\\'iw/2-(iw/zoom/2)\\'\\:y=\\'ih/2-(ih/zoom/2)\\'",
    ")",
]
for l in lines:
    print(" ", repr(l))

r = _run(script, timeout=200)
print(f'rc={r["returncode"]}')
print('STDOUT:', r.get('stdout', ''))
if r.get('stderr'):
    print('STDERR:', r.get('stderr', '')[:500])
