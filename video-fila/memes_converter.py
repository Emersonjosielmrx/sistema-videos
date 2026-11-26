# -*- coding: utf-8 -*-
"""Converte todos os .mp4 da pasta de memes (exceto 9_NAO) para H264/AAC, que o player do Windows abre.
Os que já são H264/AAC ficam como estão. Guarda o original em _antes_conversao somente se mudar."""
import json, os, subprocess, sys
from pathlib import Path

FF = r"D:\hipercool-materiais\bin\ffmpeg.exe"
FP = r"D:\hipercool-materiais\bin\ffprobe.exe"
M = Path(r"C:\Users\Haylla\Desktop\memes_pt")
BAK = M / "9_NAO USAR (ingles, duplicados, backups)" / "antes_conversao"

def codecs(f):
    r = subprocess.run([FP, "-v", "error", "-show_entries", "stream=codec_type,codec_name", "-of", "json", str(f)],
                       capture_output=True, text=True, timeout=30)
    j = json.loads(r.stdout or "{}")
    v = [s["codec_name"] for s in j.get("streams", []) if s.get("codec_type") == "video"]
    a = [s["codec_name"] for s in j.get("streams", []) if s.get("codec_type") == "audio"]
    return (v[0] if v else ""), (a[0] if a else "")

convertidos = 0
for f in sorted(M.rglob("*.mp4")):
    if "9_NAO" in str(f):
        continue
    vc, ac = codecs(f)
    if vc == "h264" and ac == "aac":
        continue
    BAK.mkdir(parents=True, exist_ok=True)
    bk = BAK / f.name
    if not bk.exists():
        import shutil; shutil.copy2(f, bk)
    tmp = f.with_suffix(".conv.mp4")
    cmd = [FF, "-nostdin", "-loglevel", "error", "-y", "-i", str(f),
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-ac", "2",
           "-movflags", "+faststart", str(tmp)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300, stdin=subprocess.DEVNULL)
    if r.returncode == 0 and tmp.exists() and tmp.stat().st_size > 500:
        tmp.replace(f)
        convertidos += 1
        print(f"OK {vc}/{ac} -> h264/aac  {f.name[:60]}", flush=True)
    else:
        tmp.unlink(missing_ok=True)
        print(f"FALHA {f.name[:60]}: {(r.stderr or '')[:120]}", flush=True)

print(f"\n{convertidos} convertidos", flush=True)
