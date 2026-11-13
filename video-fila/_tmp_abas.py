import json, sys, urllib.request
sys.path.insert(0, r"D:\logins-google")
import cofre
em, e = cofre.conta(sys.argv[1])
for a in json.loads(urllib.request.urlopen(f"http://127.0.0.1:{e['porta']}/json/list", timeout=10).read()):
    if a.get("type") == "page":
        print(a["url"][:130], "|", a.get("title", "")[:80])
