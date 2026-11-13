"""Mostra os parâmetros de nós do fluxo. Uso: python no.py arquivo.json "parte do nome" [...]"""
import json, sys
w = json.load(open(sys.argv[1], encoding="utf-8"))
w = w[0] if isinstance(w, list) else w
for alvo in sys.argv[2:]:
    for n in w["nodes"]:
        if alvo in n["name"]:
            print("=" * 20, n["name"], n["type"], n.get("typeVersion"))
            p = n["parameters"]
            for k, v in p.items():
                if isinstance(v, str) and len(v) > 200:
                    print(f"--- {k}:\n{v}")
                else:
                    print(f"--- {k}: {json.dumps(v, ensure_ascii=False)}")
            print("--> sai para:", json.dumps(w["connections"].get(n["name"], {}), ensure_ascii=False))
