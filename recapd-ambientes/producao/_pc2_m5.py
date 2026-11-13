import json, urllib.request

DAEMON = "http://100.125.7.77:8771"

def exec_cmd(cmd, timeout=30):
    payload = json.dumps({"cmd": cmd}).encode()
    req = urllib.request.Request(DAEMON + "/exec", data=payload, headers={"Content-Type": "application/json"})
    r = urllib.request.urlopen(req, timeout=timeout)
    return json.loads(r.read().decode())

# Get last 5 pipeline metrics
r = exec_cmd("python -c f=open('C:/recapd-e-animes/workspace/pipeline_metrics.jsonl','rb');d=f.read();f.close();print(d.decode('utf-8','replace'))", timeout=15)
lines = r["stdout"].strip().splitlines()
print(f"Total: {len(lines)} entries")
for line in lines[-5:]:
    try:
        m = json.loads(line)
        print(f"  {m['video_id']} dur={m['orig_dur_s']:.0f}s status={m['status']} reason={m.get('reason_fail','ok')[:60]}")
    except:
        print(f"  {line[:100]}")
