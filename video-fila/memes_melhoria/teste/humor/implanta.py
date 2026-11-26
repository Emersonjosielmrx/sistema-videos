# -*- coding: utf-8 -*-
import shutil, subprocess, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
T = Path(r"D:\video-fila\memes_melhoria\teste\humor")
B = Path(r"D:\recapd-ambientes\producao\bin")
# 1) módulo (novo arquivo: backup só se já existir)
dst = B / "humor_narrador.py"
if dst.exists():
    shutil.copy2(dst, dst.with_name(dst.name + ".antes_26nov"))
shutil.copy2(T / "humor_narrador.py", dst)
compile(dst.read_text(encoding="utf-8"), dst.name, "exec")
print("modulo copiado:", dst)
# 2) patch no anime_script.py
r = subprocess.run([sys.executable, str(T / "patch_humor.py"), str(B / "anime_script.py")], capture_output=True, text=True)
print(r.stdout.strip(), r.stderr.strip()[-300:])
if r.returncode:
    sys.exit(1)
# 3) importa de verdade (pega erro de nome/indentação)
r = subprocess.run([sys.executable, "-c", "import sys;sys.dont_write_bytecode=True;sys.path.insert(0,r'%s');"
                    "import anime_script, humor_narrador;print('import ok')" % B], capture_output=True, text=True)
print(r.stdout.strip(), r.stderr.strip()[-400:])
if r.returncode:
    sys.exit(1)
# 4) sobe ao Drive do Kaggle e confere
R = r"D:\tools\rclone.exe"; D = "manhwa-drive:colab_recap/raiz/D/recapd-ambientes/producao/bin"
inc = ["--include", "anime_script.py", "--include", "humor_narrador.py", "--include", "humor_narradores.json"]
r = subprocess.run([R, "copy", str(B), D, *inc], capture_output=True, text=True)
print("copy rc", r.returncode, r.stderr[-200:])
r = subprocess.run([R, "check", str(B), D, "--one-way", *inc], capture_output=True, text=True)
print([l for l in r.stderr.splitlines() if "differences" in l or "matching" in l or "ERROR" in l])
