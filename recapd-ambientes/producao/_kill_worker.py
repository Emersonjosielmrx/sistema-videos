import json, urllib.request

DAEMON = "http://100.125.7.77:8771"

def exec_cmd(cmd, timeout=30):
    payload = json.dumps({"cmd": cmd}).encode()
    req = urllib.request.Request(DAEMON + "/exec", data=payload, headers={"Content-Type": "application/json"})
    r = urllib.request.urlopen(req, timeout=timeout)
    return json.loads(r.read().decode())

# Get all python processes with command line
r = exec_cmd("wmic process where \"name='python.exe'\" get processid,commandline", timeout=15)
with open("D:/recapd-e-animes/_py_procs.txt", "wb") as f:
    f.write(r["stdout"].encode("utf-8", errors="replace"))
print(r["stdout"][:2000])
