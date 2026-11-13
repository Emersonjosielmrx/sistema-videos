import json, shutil
from datetime import datetime
from pathlib import Path
f = Path(r"D:\recapd-ambientes\producao\config\parceiro.json")
shutil.copy2(f, f.with_name(f"parceiro.json.bkp_{datetime.now():%Y%m%d_%H%M}_3novos"))
j = json.loads(f.read_text(encoding="utf-8"))
novos = [("neithkpop", "dorama"), ("exploramundofc", "fatos"), ("segurancaexplicada", "fatos")]
tem = {x.get("nome") for x in j["fontes"]}
for nome, tipo in novos:
    if nome in tem:
        print("já tem", nome); continue
    j["fontes"].append({"url": f"https://www.youtube.com/@{nome}/shorts", "tipo": tipo, "nome": nome,
                        "cobertura": "auto", "_obs": "08/11 dona: parceiro autorizado novo"})
    print("add", nome, tipo)
f.write_text(json.dumps(j, ensure_ascii=False, indent=1), encoding="utf-8")
json.loads(f.read_text(encoding="utf-8")); print("json ok", len(j["fontes"]))
