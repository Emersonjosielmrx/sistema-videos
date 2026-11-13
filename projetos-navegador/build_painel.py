import json, os, datetime, re, subprocess
from collections import defaultdict

DIR = "D:/projetos-navegador"
LOG_FILE = os.path.join(DIR, "mega_engage_log.txt")
PROGRESS_FILE = os.path.join(DIR, "mega_engage_progress.json")
TEMPLATE_FILE = os.path.join(DIR, "painel_template.html")
OUTPUT_FILE = os.path.join(DIR, "painel_engage.html")
CONFIG_FILE = os.path.join(DIR, "engage_config.json")

def is_bot_running():
    try:
        out = subprocess.check_output('wmic process where "name=\'python.exe\'" get commandline,processid', shell=True).decode('utf-8', errors='ignore')
        for line in out.splitlines():
            if 'mega_engage.py' in line:
                parts = line.strip().rsplit(' ', 1)
                pid = parts[-1]
                return pid
    except:
        pass
    return None

def build_data():
    accounts_done = 0
    accounts_total = 0
    accounts_list = []
    
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                prog = json.load(f)
                accounts_total = len(prog)
                for email, info in prog.items():
                    if info.get("status") == "success":
                        accounts_done += 1
                        info['email'] = email
                        accounts_list.append(info)
        except:
            pass

    log_entries = []
    errors = []
    video_stats = defaultdict(lambda: {"likes": 0, "comments": 0})
    
    total_actions = 0
    hourly_counts = [0] * 24
    now = datetime.datetime.now()
    
    last_engagement_ts = None
    first_log_ts = None
    
    errors_3h = 0
    actions_3h = 0

    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines:
                    stamp = ""
                    m = re.match(r'^\[(.*?)\]', line)
                    if m:
                        stamp = m.group(1)
                        try:
                            # 2026-07-06 14:15:30
                            ts = datetime.datetime.strptime(stamp, "%Y-%m-%d %H:%M:%S")
                            if first_log_ts is None:
                                first_log_ts = ts
                            
                            delta_hours = (now - ts).total_seconds() / 3600
                            if delta_hours < 24:
                                hr_idx = int(delta_hours)
                                hourly_counts[hr_idx] += 1
                                
                            if delta_hours <= 3:
                                actions_3h += 1
                                if "ERRO" in line or "FALHA" in line:
                                    errors_3h += 1
                        except:
                            pass

                    entry = {"time": stamp, "msg": line.strip(), "ts_raw": stamp}
                    log_entries.append(entry)
                    
                    if "ERRO" in line or "FALHA" in line or "Error" in line:
                        errors.append(entry)
                        
                    if "✅ Liked" in line or "✅ Comment" in line:
                        last_engagement_ts = stamp
                        total_actions += 1
                        
                        vurl = ""
                        vm = re.search(r'(https://www\.youtube\.com/watch\?v=[\w-]+)', line)
                        if vm: vurl = vm.group(1)
                        
                        if vurl:
                            if "Liked" in line: video_stats[vurl]["likes"] += 1
                            if "Comment" in line: video_stats[vurl]["comments"] += 1
                            video_stats[vurl]["url"] = vurl
        except Exception as e:
            print("Erro log:", e)
            
    vlist = list(video_stats.values())
    vlist.sort(key=lambda x: x["likes"] + x["comments"], reverse=True)
    
    log_entries.reverse()
    errors.reverse()
    
    config = {}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)

    bot_pid = is_bot_running()
    
    uptime = ""
    if hasattr(first_log_ts, 'timestamp') and bot_pid:
        delta = now - first_log_ts
        hours, rem = divmod(delta.seconds, 3600)
        mins, _ = divmod(rem, 60)
        uptime = f"{hours}h {mins}m"
    else:
        uptime = "N/A"

    error_rate_3h = round((errors_3h / max(1, actions_3h)) * 100, 1)

    return {
        "accounts_done": accounts_done,
        "accounts_total": accounts_total,
        "accounts_list": accounts_list,
        "total_actions": total_actions,
        "log_entries": log_entries,
        "errors": errors,
        "videos": vlist,
        "config": config,
        "bot_pid": bot_pid,
        "last_engagement": last_engagement_ts or "Nunca",
        "uptime": uptime,
        "error_rate_3h": error_rate_3h,
        "hourly_chart": list(reversed(hourly_counts)),
        "gen_time": now.strftime("%Y-%m-%d %H:%M:%S")
    }

import sys
def main():
    if '--json' in sys.argv:
        print(json.dumps(build_data(), ensure_ascii=False))
        return

    data = build_data()
    if os.path.exists(TEMPLATE_FILE):
        with open(TEMPLATE_FILE, 'r', encoding='utf-8') as f:
            html = f.read()
            html = html.replace('const initData = {};', f'const initData = {json.dumps(data)};')
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(html)
        print("Painel HTML regerado.")

if __name__ == "__main__":
    main()
