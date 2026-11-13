import json, urllib.request

DAEMON = "http://100.125.7.77:8771"

def exec_cmd(cmd, timeout=30):
    payload = json.dumps({"cmd": cmd}).encode()
    req = urllib.request.Request(DAEMON + "/exec", data=payload, headers={"Content-Type": "application/json"})
    r = urllib.request.urlopen(req, timeout=timeout)
    return json.loads(r.read().decode())

# Kill workers
r = exec_cmd("tasklist | findstr python", timeout=10)
pids = [int(l.split()[1]) for l in r["stdout"].strip().splitlines() if l.split()[1].isdigit()]
for pid in pids:
    if pid != 10004:
        exec_cmd("taskkill /F /PID " + str(pid), timeout=5)

# Reset state
state_json = '{"runs": 0, "successes": 0, "failures": 0, "last_error": null}'
exec_cmd("python -c \"open('C:/recapd-e-animes/workspace/anime_worker_loop_state.json','w').write('" + state_json + "')\"", timeout=5)

# Start worker
exec_cmd("powershell -Command Start-Process -FilePath C:/recapd-e-animes/venv/Scripts/python.exe -ArgumentList C:/recapd-e-animes/bin/anime_worker_loop.py -WorkingDirectory C:/recapd-e-animes -WindowStyle Hidden", timeout=10)

import time; time.sleep(3)
r = exec_cmd("python -c print(open('C:/recapd-e-animes/workspace/anime_worker_loop_state.json').read())", timeout=10)
print(f"State: {r['stdout'].strip()}")
r = exec_cmd("python -c print(len(open('C:/recapd-e-animes/workspace/anime_worker_loop.log').readlines()))", timeout=10)
print(f"Log lines: {r['stdout'].strip()}")
