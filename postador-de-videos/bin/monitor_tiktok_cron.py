#!/usr/bin/env python3
import json
import os
import subprocess
import time
from pathlib import Path

ROOT = Path("D:/hipercool-producao")
POSTED_LOG = ROOT / "logs" / "tiktok_posted.json"
SHORTS_DIR = ROOT / "workspace" / "shorts"
CURRENT_PORT_FILE = ROOT / "logs" / "current_port.txt"
LAST_COUNT_FILE = ROOT / "logs" / "last_posted_count.txt"

def get_posted_count():
    if os.path.exists(POSTED_LOG):
        try:
            with open(POSTED_LOG, "r", encoding="utf-8") as f:
                return len(json.load(f))
        except:
            pass
    return 0

def check_status():
    print(f"[{time.strftime('%H:%M:%S')}] Monitor TikTok CDP rodando...")
    
    # 1. Checa contagem pra ver se avançou
    current_count = get_posted_count()
    last_count = 0
    if LAST_COUNT_FILE.exists():
        try:
            with open(LAST_COUNT_FILE, "r") as f:
                last_count = int(f.read().strip())
        except: pass
        
    print(f"Total postado Tiktok: {current_count} (Anterior: {last_count})")
    
    if current_count > last_count:
        print("-> SUCESSO: Novos vídeos foram postados!")
        with open(LAST_COUNT_FILE, "w") as f:
            f.write(str(current_count))
            
    # 2. Testa as portas
    print("Testando estabilidade dos Chromes...")
    ativo = 0
    import urllib.request
    for p in [9222, 9271]:
        try:
            req = urllib.request.Request(f"http://127.0.0.1:{p}/json")
            urllib.request.urlopen(req, timeout=3)
            print(f" - Porta {p}: Online")
            ativo += 1
        except Exception as e:
            print(f" - Porta {p}: Offline ({e})")

    if ativo == 0:
        print("! ALERTA ! NENHUM CHROME ONLINE. Relancando via schtasks...")
        subprocess.run(["cmd.exe", "/c", "schtasks /run /tn TikTokCDP"],
                      env={**os.environ, 'MSYS_NO_PATHCONV': '1'})
        
if __name__ == "__main__":
    check_status()
