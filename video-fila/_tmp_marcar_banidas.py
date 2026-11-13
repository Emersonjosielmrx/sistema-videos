import json, shutil
from datetime import datetime
from pathlib import Path
f = Path(r"D:\recapd-ambientes\producao\colab\kaggle_pool.json")
# 10/11: confirmadas na tela do Kaggle (messageId=bannedLogin), cada uma aberta pelo proxy dela
BANIDAS = {"inovaremanhwaverseit", "emersoncunhacunha", "emersonjosielcunha", "inovaremanhwaversein",
           "inovaremanhwaverseth", "emerson2033", "alucinaai", "inovarecap", "comoseriasecomia", "histriacomia", "inovaremanhwaver2010"}
shutil.copy2(f, f.with_name(f"kaggle_pool.json.bkp_{datetime.now():%Y%m%d_%H%M}_banidas10nov"))
p = json.loads(f.read_text(encoding="utf-8"))
n = 0
for c in p["contas"]:
    if c["username"] in BANIDAS and not c.get("banida"):
        c["banida"] = "10/11 confirmada na tela (bannedLogin) â€” caÃ­ram juntas 09/11 ~14:44"
        n += 1
f.write_text(json.dumps(p, ensure_ascii=False, indent=1), encoding="utf-8")
ativas = [c["username"] for c in p["contas"] if c.get("verificada") and not c.get("banida")]
print("marcadas", n, "| verificadas ativas:", len(ativas), ativas)

