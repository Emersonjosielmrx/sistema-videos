#!/usr/bin/env python3
import json
import os
import time
import subprocess
from pathlib import Path

# Paths e dirs
ROOT = Path("D:/hipercool-producao")
POSTED_LOG = ROOT / "logs" / "tiktok_posted.json"
SHORTS_DIR = ROOT / "workspace" / "shorts"

PORTS = [9222, 9271]
CURRENT_PORT_FILE = ROOT / "logs" / "current_port.txt"

def get_next_port():
    idx = 0
    if CURRENT_PORT_FILE.exists():
        try:
            with open(CURRENT_PORT_FILE, "r") as f:
                idx = int(f.read().strip())
        except:
            pass
    port = PORTS[idx % len(PORTS)]
    idx += 1
    with open(CURRENT_PORT_FILE, "w") as f:
        f.write(str(idx))
    return port

def load_posted():
    if os.path.exists(POSTED_LOG):
        try:
            with open(POSTED_LOG, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return []

def run_once():
    print("Iniciando postador TikTok autônomo...")
    
    # 0. Acha diretórios de shorts
    if not SHORTS_DIR.exists():
        print(f"Diretório de shorts vazio: {SHORTS_DIR}")
        return
        
    posted = load_posted()
    posted_files = [p.get("file") for p in posted if "file" in p]
    
    for p_dir in SHORTS_DIR.iterdir():
        if not p_dir.is_dir(): continue
        
        # Verifica se já mandou todos desse diretório
        files_in_dir = [f.name for f in p_dir.iterdir() if f.name.endswith(".mp4")]
        if all(f in posted_files for f in files_in_dir):
            continue
            
        print(f"Rodando CDP POSTER para: {p_dir.name}")
        port = get_next_port()
        
        cmd = [
            "D:/hipercool-videos/venv/Scripts/python.exe",
            str(ROOT / "bin" / "tiktok_cdp_poster.py"),
            "--videos-dir", str(p_dir),
            "--max", "1", 
            "--ports", str(port),
            "--delay", "120"
        ]
        
        env = os.environ.copy()
        env['PYTHONUTF8'] = '1'
        
        # Como o playwright pode dar erro de Timeout na injeção, repetimos se falhar
        for attempt in range(2):
            proc = subprocess.run(cmd, env=env, capture_output=True, text=True)
            if "Timeout" not in proc.stdout and "Timeout" not in proc.stderr:
                print(proc.stdout)
                if proc.stderr: print("ERRO:", proc.stderr)
                break
            else:
                print("Falhou com timeout."); print("Stderr:", proc.stderr); print("Stdout:", proc.stdout)
                time.sleep(10)
                
        # Só tenta subir de UM diretório por vez.
        return

if __name__ == "__main__":
    try:
        run_once()
    except Exception as e:
        print(f"Erro global: {e}")
