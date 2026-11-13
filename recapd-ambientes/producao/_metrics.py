import json, urllib.request
from pathlib import Path

DAEMON = "http://100.125.7.77:8771"

def exec_cmd(cmd, timeout=30):
    payload = json.dumps({"cmd": cmd}).encode()
    req = urllib.request.Request(DAEMON + "/exec", data=payload, headers={"Content-Type": "application/json"})
    r = urllib.request.urlopen(req, timeout=timeout)
    return json.loads(r.read().decode())

# Check pipeline metrics
r = exec_cmd("python -c f=open('C:/recapd-e-animes/workspace/pipeline_metrics.jsonl','rb');d=f.read();f.close();print(d.decode('utf-8','replace'))", timeout=15)
lines = r["stdout"].strip().splitlines()
print(f"Pipeline metrics: {len(lines)} entries")
for line in lines[-3:]:
    try:
        m = json.loads(line)
        print(f"  {m.get('id','?')} orig={m.get('orig_dur_s',0):.0f}s error={m.get('error','ok')[:50]}")
    except:
        print(f"  {line[:100]}")
