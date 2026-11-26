import subprocess, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
R = r"D:\tools\rclone.exe"; B = r"D:\recapd-ambientes\producao\bin"
D = "manhwa-drive:colab_recap/raiz/D/recapd-ambientes/producao/bin"
inc = ["--include", "anime_script.py", "--include", "humor_narrador.py", "--include", "humor_narradores.json"]
r = subprocess.run([R, "copy", B, D, *inc], capture_output=True, text=True)
print("copy rc", r.returncode, r.stderr[-200:])
r = subprocess.run([R, "check", B, D, "--one-way", *inc], capture_output=True, text=True)
print([l for l in r.stderr.splitlines() if "differences" in l or "matching" in l or "ERROR" in l])
