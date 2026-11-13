import json, urllib.request, time

def exec(cmd, timeout=30):
    r = urllib.request.urlopen(
        urllib.request.Request("http://100.125.7.77:8771/exec",
            data=json.dumps({"cmd": cmd}).encode(),
            headers={"Content-Type": "application/json"}),
        timeout=timeout
    )
    return json.loads(r.read().decode())

# Check venv python
r = exec("C:/recapd-e-animes/venv/Scripts/python.exe --version")
print("Venv python:", r["stdout"].strip(), "rc:", r["returncode"])

# Kill existing workers
r = exec('taskkill /F /IM python.exe /FI "WINDOWTITLE eq *anime*"', timeout=5)
print("Kill workers:", r["returncode"], r["stderr"][:50] if r["stderr"] else "OK")

# Start worker in background
cmd = "start /B cmd /c C:\\recapd-e-animes\\venv\\Scripts\\python.exe C:\\recapd-e-animes\\bin\\anime_worker_loop.py"
r = exec(cmd, timeout=5)
print("Start worker:", r["returncode"])

# Wait and verify
time.sleep(5)
r = exec("tasklist | findstr python")
print("Python processes after start:")
print(r["stdout"])

# Check state
r = exec("python -c print(open('C:/recapd-e-animes/workspace/anime_worker_loop_state.json').read())")
print("State:", r["stdout"].strip()[:100])
