import os
import re
import sys
import time
import subprocess
import json
import logging
from datetime import datetime

# Config
BASE_DIR = "D:\\hipercool-inferior-fix"
LOG_FILE = os.path.join(BASE_DIR, "logs", "rotina_rw_51_88.log")
NIGHT_SHIFT_FILE = os.path.join(BASE_DIR, "logs", "night-shift.md")
VIDEOS_DIR = os.path.join(BASE_DIR, "workspace", "videos", "regressed-warriors")
STATE_FILE = os.path.join(BASE_DIR, "workspace", "cron_state.json")

# Configuração de logger temporario p/ stdout (caso a cron rode com log)
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(message)s", datefmt="%H:%M:%S")

def format_dur(secs):
    return f"{float(secs):.1f}s" if secs else "N/A"

def append_to_night_shift(text):
    print(f"Escrevendo n night-shift.md:\n{text}")
    with open(NIGHT_SHIFT_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n{text}\n")

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"last_completed_cap": 0, "stuck_checks": {}}

def save_state(s):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(s, f)

def get_ffmpeg_processes():
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        out = subprocess.check_output(
            ["tasklist", "/FI", "IMAGENAME eq ffmpeg.exe", "/FO", "CSV"],
            text=True,
            startupinfo=startupinfo
        )
        # Parse CSV
        processes = []
        for line in out.strip().split("\n")[1:]:  # skip header
            if not line: continue
            parts = [p.strip('"') for p in line.split('","')]
            if len(parts) >= 5:
                pid = parts[1]
                mem = parts[4].replace(" K", "").replace(".", "")
                processes.append({"pid": pid, "mem": int(mem)})
        return processes
    except Exception as e:
        print(f"Erro tasklist ffmpeg: {e}")
        return []

def kill_process(pid):
    try:
        subprocess.check_output(["taskkill", "/PID", str(pid), "/F"])
        print(f"Forced Kill PID {pid}")
    except Exception as e:
        print(f"Erro kill {pid}: {e}")

def check_stuck_ffmpeg(state):
    procs = get_ffmpeg_processes()
    current_pids = [p["pid"] for p in procs]

    # Limpa pids velhos no estado
    state["stuck_checks"] = {k: v for k, v in state["stuck_checks"].items() if k in current_pids}

    for p in procs:
        pid = p["pid"]
        mem = p["mem"]
        if pid in state["stuck_checks"]:
            prev_mem = state["stuck_checks"][pid]["mem"]
            count = state["stuck_checks"][pid]["count"]
            if abs(mem - prev_mem) < 10:  # Memória estabilizou muito (zumbi)
                count += 1
                state["stuck_checks"][pid]["count"] = count
                print(f"ffmpeg {pid} memoery flat at {mem}k por {count} checks")

                if count >= 3:
                     append_to_night_shift(f"⚠️ **Intervenção Autônoma:** ffmpeg PID {pid} zumbi detectado (memória congelada em {mem}K). Processo morto pelo agente.")
                     kill_process(pid)
                     del state["stuck_checks"][pid]
            else:
                state["stuck_checks"][pid] = {"mem": mem, "count": 0}
        else:
            state["stuck_checks"][pid] = {"mem": mem, "count": 0}

def validate_video(path):
    if not os.path.exists(path):
        return None
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        cmd = [
            "ffprobe", "-v", "quiet",
            "-show_entries", "format=duration,size",
            "-show_entries", "stream=width,height,codec_name",
            "-of", "json", path
        ]
        out = subprocess.check_output(cmd, text=True, startupinfo=startupinfo)
        data = json.loads(out)

        w=0; h=0
        for s in data.get("streams", []):
            if "width" in s:
                w = s["width"]
                h = s["height"]
        dur = data.get("format", {}).get("duration", "0")
        sz = data.get("format", {}).get("size", "0")

        return {"w":w, "h":h, "dur":dur, "mb": round(int(sz)/(1024*1024), 1)}
    except Exception as e:
        return None

def check_completed_caps(state):
    # Procura caps baseados no que tá escrito no log mas que ainda não documentamos
    last_cap = state["last_completed_cap"]

    # 1. Obter pasta e numeracao, o hipercool output são v1.mp4
    highest_cap_found = 0

    if os.path.exists(VIDEOS_DIR):
        for cap_dir in os.listdir(VIDEOS_DIR):
            m = re.match(r'cap(\d+)', cap_dir)
            if not m: continue
            cap_num = int(m.group(1))

            if cap_num <= last_cap:
                continue

            # Verifica se os dois arquivos existem
            norm_path = os.path.join(VIDEOS_DIR, cap_dir, "edge", "normal", "v1.mp4")
            cens_path = os.path.join(VIDEOS_DIR, cap_dir, "censored", "v1.mp4")

            if os.path.exists(norm_path) and os.path.exists(cens_path):
                # Validar e registrar se não estao sendo escritos mais (checar tempo variação de tscap ou tentar travar se ffmpeg escrevendo)
                norm_mtime = os.path.getmtime(norm_path)
                cens_mtime = os.path.getmtime(cens_path)
                if (time.time() - cens_mtime) > 60: # 1 min desde ultimo db (seguro)
                    norm_data = validate_video(norm_path)
                    cens_data = validate_video(cens_path)

                    if norm_data and cens_data:
                        now = datetime.now().strftime("%Y-%m-%d %H:%M")
                        text = f"## Cap {cap_num} — O Guerreiro Regressou ✅\n"
                        text += f"- **Concluído:** {now} (Monitor Cron)\n"
                        text += f"- **Normal:** {format_dur(norm_data['dur'])}, {norm_data['w']}x{norm_data['h']}, {norm_data['mb']}MB\n"
                        text += f"- **Censurada:** {format_dur(cens_data['dur'])}, {cens_data['w']}x{cens_data['h']}, {cens_data['mb']}MB\n"
                        text += "- ✅ Validado automaticamente pass\n"

                        append_to_night_shift(text)

                        if cap_num > highest_cap_found:
                            highest_cap_found = cap_num

    if highest_cap_found > last_cap:
        state["last_completed_cap"] = highest_cap_found

def main():
    state = load_state()
    # Se last_cap é zero, puxa manual de 54 q foi o meu último pra não duplicar logs
    if state["last_completed_cap"] == 0:
        state["last_completed_cap"] = 54

    check_stuck_ffmpeg(state)
    check_completed_caps(state)

    save_state(state)
    print("Health check completed.")

if __name__ == "__main__":
    main()
