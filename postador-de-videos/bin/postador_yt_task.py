#!/usr/bin/env python3
import json
import os
import subprocess
import time
from pathlib import Path

ROOT = Path("D:/hipercool-producao")
SHORTS_DIR = ROOT / "workspace" / "shorts"
YT_POSTED = ROOT / "logs" / "youtube_posted.json"
YT_CHANNELS = ["inovare recap manga", "nova conta de manga br"]
CUR_CHAN_FILE = ROOT / "logs" / "current_yt_chan.txt"

def get_posted():
    if os.path.exists(YT_POSTED):
        try:
            with open(YT_POSTED, "r") as f:
                return json.load(f)
        except: pass
    return []

def save_posted(p):
    with open(YT_POSTED, "w") as f:
        json.dump(p, f)

def get_next_channel():
    idx = 0
    if CUR_CHAN_FILE.exists():
        try:
            with open(CUR_CHAN_FILE, "r") as f:
                idx = int(f.read().strip())
        except: pass
    c = YT_CHANNELS[idx % len(YT_CHANNELS)]
    with open(CUR_CHAN_FILE, "w") as f:
        f.write(str(idx + 1))
    return c

def process():
    if not SHORTS_DIR.exists(): return
    posted = get_posted()
    
    for obra_dir in SHORTS_DIR.iterdir():
        if not obra_dir.is_dir(): continue
        
        dir_name = obra_dir.name
        
        # Ignorar oq ja foi postado no youtube (procura nome do dir)
        if any(dir_name in p for p in posted):
            continue
            
        obra_nome = "Recap Manga"
        capitulo = 1
        
        if "-cap" in dir_name:
            try:
                obra_nome = dir_name.split("-cap")[0].replace("-", " ").title()
                capitulo = int(dir_name.split("-cap")[1])
            except: pass

        # O batch-post-shorts EXIGE o parametro --video, mesmo quando reusa a pasta já cortada
        # Vamos passar um dummy video path porque ele precisa do argumento (ou verificar se tem arg melhor no original)
        dummy_video = str(ROOT / "dummy.mp4")
        if not os.path.exists(dummy_video):
            with open(dummy_video, "w") as f: f.write("dummy")

        canal = get_next_channel()
        now_h = time.localtime().tm_hour
        next_h = now_h + 1 if now_h < 22 else 8
        
        print(f"Postando YT: {dir_name} no canal '{canal}' as {next_h}:00")
        
        cmd = [
            "D:/hipercool-videos/venv/Scripts/python.exe",
            str(ROOT / "bin" / "batch-post-shorts.py"),
            "--video", dummy_video,
            "--shorts-dir", str(obra_dir),
            "--obra", obra_nome,
            "--capitulo", str(capitulo),
            "--canal", canal,
            "--hora-inicio", f"{next_h}:00",
            "--intervalo", "60"
        ]
        
        env = os.environ.copy()
        env['PYTHONUTF8'] = '1'
        res = subprocess.run(cmd, env=env, text=True, capture_output=True)
        print(res.stdout)
        if res.stderr: print("ERRO:", res.stderr)
        
        if res.returncode == 0:
            posted.append(dir_name)
            save_posted(posted)
            return  # Processa apenas 1 diretório (um bundle de shorts) por execução do cron
            
if __name__ == "__main__":
    try:
        process()
    except Exception as e:
        print("Err:", e)
