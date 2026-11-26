import subprocess, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
R = r"D:\tools\rclone.exe"
D = "manhwa-drive:colab_recap/raiz/D"
jobs = [
    (r"D:\recapd-ambientes\producao\bin", D + "/recapd-ambientes/producao/bin", ["memes_visuais.py", "anime-pipeline.py"]),
    (r"D:\hipercool-materiais\assets\memes_img\memes_novos", D + "/hipercool-materiais/assets/memes_img/memes_novos", ["*.mp4", "memes.json", "fichas.json"]),
]
for src, dst, inc in jobs:
    flt = sum((["--include", i] for i in inc), [])
    r = subprocess.run([R, "copy", src, dst, *flt], capture_output=True, text=True)
    print("copy rc", r.returncode, r.stderr[-300:])
    r = subprocess.run([R, "check", src, dst, "--one-way", *flt], capture_output=True, text=True)
    print("check:", [l for l in r.stderr.splitlines() if "differences" in l or "matching" in l or "ERROR" in l])
