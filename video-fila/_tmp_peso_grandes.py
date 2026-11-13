import json, shutil
from datetime import datetime
from pathlib import Path
f = Path(r"D:\recapd-ambientes\producao\config\parceiro.json")
# 09/11 dona: "dar prioridade aos novos parceiros maiores" — canais com 1 mi+ inscritos (CANAIS_DARK_PARA_CONTATO.md)
GRANDES = {"fatosdesconhecidos": 3, "zackdfilms": 3, "dailydoseofinternet": 3, "chills": 2.5, "tinocandotv": 2.5,
           "kpophmkshorts": 2.5, "slappedham": 2, "top5s": 2, "spotniks": 2, "score90": 2, "Batimaanimes": 2,
           "OssosPerdidos": 2, "FocanaHistória": 2, "Clark69": 2, "GuilhermeAnalisa": 2, "UniversoNarrado": 2,
           "SOLUCIONANDOFILMES": 2, "coldfusion": 2, "magnatesmedia": 2, "howmoneyworks": 2, "storyrecapped": 2}
shutil.copy2(f, f.with_name(f"parceiro.json.bkp_{datetime.now():%Y%m%d_%H%M}_grandes"))
j = json.loads(f.read_text(encoding="utf-8"))
n = 0
for x in j["fontes"]:
    if x["nome"] in GRANDES and x.get("peso", 1) != 0:
        x["peso"] = GRANDES[x["nome"]]
        x["_peso_obs"] = "09/11 dona: prioridade aos parceiros novos maiores (1 mi+ inscritos). Desfazer: apagar peso"
        n += 1
f.write_text(json.dumps(j, ensure_ascii=False, indent=1), encoding="utf-8")
print("pesos aplicados:", n)
