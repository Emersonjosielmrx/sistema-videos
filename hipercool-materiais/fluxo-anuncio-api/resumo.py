import json, re, sys
w = json.load(open(sys.argv[1], encoding="utf-8"))
w = w[0] if isinstance(w, list) else w
for n in w["nodes"]:
    p = json.dumps(n["parameters"], ensure_ascii=False)
    urls = sorted(set(re.findall(r"(?:https?://|video-oficina)[^\"\s\\]+", p)))
    print(n["type"].split(".")[-1], "|", n["name"], "|", len(p), "|", urls[:4])
print("conexoes:", len(w["connections"]))
