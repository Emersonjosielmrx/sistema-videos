import os
import glob
import subprocess
from datetime import datetime

base_dir = "D:/hipercool-inferior-fix"
videos_dir = f"{base_dir}/workspace/videos/regressed-warriors"
night_shift_log = f"{base_dir}/logs/night-shift.md"

def log_learning(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(night_shift_log, "a", encoding="utf-8") as f:
        f.write(f"\n- **{ts}**: {msg}")

def testar_video(cap, tag, video_path):
    if not os.path.exists(video_path): return
    try:
        dur_raw = subprocess.check_output(f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{video_path}"', shell=True).decode().strip()
        dur_v = float(dur_raw)
        dur_a_raw = subprocess.check_output(f'ffprobe -v error -select_streams a:0 -show_entries stream=duration -of default=noprint_wrappers=1:nokey=1 "{video_path}"', shell=True).decode().strip()
        dur_a = float(dur_a_raw) if dur_a_raw and dur_a_raw.lower() != 'n/a' else 0.0
        
        diff = abs(dur_v - dur_a)
        if diff > 5.0 and dur_v > 60:
            log_learning(f"Problema no cap {cap} [{tag}]: diferença áudio/vídeo alta ({dur_v:.1f}x{dur_a:.1f})")
    except Exception as e:
        log_learning(f"Falha ao validar cap {cap} [{tag}]: {str(e)}")

def checar_andamento():
    os.makedirs(f"{base_dir}/logs", exist_ok=True)
    if not os.path.exists(night_shift_log):
        with open(night_shift_log, "w", encoding="utf-8") as f:
            f.write("# Night Shift Log\n")
    
    # Caps atuais sendo processados (v1.mp4 gerados)
    for cap_idx in range(26, 89):
        cap_str = f"cap{cap_idx:02d}"
        cap_dir = f"{videos_dir}/{cap_str}"
        if not os.path.isdir(cap_dir): continue
        
        norm = f"{cap_dir}/edge/normal/v1.mp4"
        cens = f"{cap_dir}/censored/v1.mp4"
        testar_video(cap_str, "NORMAL", norm)
        testar_video(cap_str, "CENSURADO", cens)

if __name__ == "__main__":
    try:
        checar_andamento()
    except Exception as e:
        import traceback
        log_learning(f"CRASH no script de check: {traceback.format_exc()}")
