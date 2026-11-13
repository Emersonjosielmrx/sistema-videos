# 01/11 dona: "agrupa os A B C D E F G dentro de uma subpasta daquela obra, e faça isso também com as que já estão lá,
# e põe de nome apenas A ou B ou C". Uma vez só: parceiro_<id>_<L>.png -> <obra>\<L>.png; reprovadas -> <obra>\reprovadas\
import re
import shutil
from pathlib import Path

from gerar_todos import NOMES, pasta

AQUI = Path(__file__).parent
RE = re.compile(r"parceiro_(.+)_([A-G])\.png$")


def destino_livre(p):
    if not p.exists():
        return p
    n = 2
    while (q := p.with_name(f"{p.stem}_{n}{p.suffix}")).exists():
        n += 1
    return q


for raiz in (AQUI / "brutas", AQUI / "brutas_google"):
    logs = raiz / "_logs"
    for f in list(raiz.glob("*.log")):
        if f.name == "gerador.log":
            continue
        logs.mkdir(exist_ok=True)
        shutil.move(str(f), str(logs / f.name))
    origens = [(raiz, False)] + [(raiz / d, True) for d in ("reprovadas", "_reprovadas") if (raiz / d).is_dir()]
    for dirp, reprovada in origens:
        for f in list(dirp.glob("parceiro_*_*.png")):
            m = RE.match(f.name)
            if not m or m.group(1) not in NOMES:
                print("ficou:", f)
                continue
            alvo = pasta(raiz, m.group(1))
            if reprovada:
                alvo = alvo / "reprovadas"
                alvo.mkdir(exist_ok=True)
            d = destino_livre(alvo / f"{m.group(2)}.png")
            shutil.move(str(f), str(d))
            print(f"{f.relative_to(AQUI)} -> {d.relative_to(AQUI)}")
    for vid in NOMES:  # a capa original do parceiro junto, pra comparar
        shutil.copy2(AQUI / f"parceiro_{vid}.jpg", pasta(raiz, vid) / "original.jpg")
    for d in ("reprovadas", "_reprovadas"):
        p = raiz / d
        if p.is_dir() and not any(p.iterdir()):
            p.rmdir()
