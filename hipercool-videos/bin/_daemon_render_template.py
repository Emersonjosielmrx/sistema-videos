# -*- coding: utf-8 -*-
"""Daemon render script - written to NAS, executed by PC2 daemon."""
import shutil, pathlib, subprocess, sys

NAS_INPUT = pathlib.Path(r"D:\historias-em-frames\workspace\worker_jobs\_py_script_test\input.png")
NAS_OUTPUT = pathlib.Path(r"D:\historias-em-frames\workspace\worker_jobs\_py_script_test\output.mp4")
TMP_IMG = pathlib.Path(r"C:\app\_r_img.png")
TMP_OUT = pathlib.Path(r"C:\app\_r_out.mp4")

print("Copying from NAS:", NAS_INPUT, flush=True)
shutil.copy2(NAS_INPUT, TMP_IMG)
if not TMP_IMG.exists() or TMP_IMG.stat().st_size < 1000:
    print("FALHA:copy", flush=True)
    sys.exit(1)
print("IMG OK:", TMP_IMG.stat().st_size // 1024, "KB", flush=True)

print("ffmpeg...", flush=True)
zoom_filter = "zoompan=z='if(lte(i,1),1.03,1)':d=1:s=720x1280,fps=25"
vf = f"scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2:color=black,{zoom_filter}"
ff = subprocess.run(
    ["ffmpeg", "-y", "-loop", "1", "-i", str(TMP_IMG),
     "-vf", vf,
     "-pix_fmt", "yuv420p", "-r", "25", "-t", "3",
     "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23", "-threads", "2",
     str(TMP_OUT)],
    capture_output=True, text=True, timeout=120
)
print("ff rc:", ff.returncode, flush=True)
if ff.returncode != 0:
    print("ERR:", ff.stderr[-300:], flush=True)
    sys.exit(1)
if not TMP_OUT.exists() or TMP_OUT.stat().st_size < 5000:
    print("ERR:no_output", flush=True)
    sys.exit(1)
print("ff output:", TMP_OUT.stat().st_size // 1024, "KB", flush=True)

print("Writing to NAS...", flush=True)
NAS_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(TMP_OUT, NAS_OUTPUT)
for f in [TMP_IMG, TMP_OUT]:
    f.unlink(missing_ok=True)
if NAS_OUTPUT.exists() and NAS_OUTPUT.stat().st_size > 5000:
    print("OK:", NAS_OUTPUT.stat().st_size // 1024, "KB", flush=True)
    sys.exit(0)
else:
    print("FALHA:output", flush=True)
    sys.exit(1)
