# D:\hipercool-materiais\fluxos-n8n\novos\insta_integra\baixa.py
# Baixa os 2 fluxos (diagnóstico e 30 dias) e mostra nós, tipos e ligações.
import sys, json, os
sys.path.insert(0, r"D:\hipercool-materiais\fluxos-n8n\ferramentas")
from n8n_servidor import api
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = os.path.dirname(os.path.abspath(__file__))
for wid in ("Zj1EwQeAGBTwpShB", "Cy1QZOsj5WimgWnC"):
    st, w = api("GET", f"/workflows/{wid}")
    json.dump(w, open(os.path.join(AQUI, f"original_{wid}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("=" * 100); print(wid, w["name"], "ativo=", w.get("active"), "nós=", len(w["nodes"]))
    for n in w["nodes"]:
        p = n["parameters"]
        extra = ""
        if n["type"].endswith(".webhook"): extra = "path=" + str(p.get("path")) + " " + str(p.get("httpMethod", "GET"))
        if n["type"].endswith(".code"): extra = f"js={len(p.get('jsCode',''))}"
        if n["type"].endswith("httpRequest"): extra = str(p.get("url"))[:90]
        if "agent" in n["type"] or "lmChat" in n["type"]: extra = str(p.get("model", ""))[:60]
        print(f"  {n['name'][:55]:55} {n['type'].split('.')[-1][:28]:28} {extra}")
    print("-- ligações")
    for a, c in w["connections"].items():
        for i, saida in enumerate(c.get("main", [])):
            for d in saida or []:
                print(f"  {a[:45]} [{i}] -> {d['node'][:45]}")
