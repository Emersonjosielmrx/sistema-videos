import json, shutil
from datetime import datetime
from pathlib import Path
f = Path(r"D:\recapd-ambientes\producao\colab\kaggle_pool.json")
shutil.copy2(f, f.with_name(f"kaggle_pool.json.bkp_{datetime.now():%Y%m%d_%H%M}_usernames"))
j = json.loads(f.read_text(encoding="utf-8"))
# username real da tela Settings (print _kaggle/token_*/settings.png), telefone "Verified" no print
certo = {
 "inovaremanhwaversefrench@gmail.com": ("emersoncunhacunha", True),
 "inovaremanhwaverseita@gmail.com": ("inovaremanhwaverseit", True),
 "inovaremanhwaverserussian@gmail.com": ("emersonjosielcunha", True),
 "inovaremanhwaverseind@gmail.com": ("inovaremanhwaversein", True),
 "inovaremanhwaversethai@gmail.com": ("inovaremanhwaverseth", True),
 "mundosolar1995@gmail.com": ("mundosolar1995", True),
 "inovaremanhwaverse5@gmail.com": ("inovare", True),
 "inovaremanhwaverse6@gmail.com": ("inovareee", True),
 "inovaremanhwaverse2@gmail.com": (None, False),  # sem print da Settings: confirmar
}
for c in j["contas"]:
    if c.get("cofre") in certo:
        u, v = certo[c["cofre"]]
        if u:
            c["username"] = u
        c["verificada"] = v
        c["papel"] = "curto"
        c["nota"] = ("08/11 dona: 10 contas novas, IP rnprmtfo exclusivo; telefone Verified no print" if v else
                     "08/11: token ok, mas sem print da Settings — username/telefone a conferir antes de liberar")
        print(c["cofre"], c["username"], c["verificada"])
f.write_text(json.dumps(j, ensure_ascii=False, indent=1), encoding="utf-8")
json.loads(f.read_text(encoding="utf-8"))
print("ok")
