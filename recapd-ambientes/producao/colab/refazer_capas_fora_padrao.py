r"""refazer_capas_fora_padrao.py — 11/11 dona (prints do canal): "esses da imagem as capas estão fora do padrão, assim
ninguém vê, troque elas". Longos de 03-07/11 saíram com a 'pose do catálogo' (capa de SHORT: herói sozinho, sem
mulheres) porque capa_melhorada devolvia None (corrigido 11/11 06:30: CAPA_LONGO_SEM_CATALOGO). Recoloca cada um no
capas_depois.json como PENDENTE no topo da fila, guardando a capa velha (.antiga_catalogo) e tirando o .capa.json
(senão o capas_depois reaproveita). Os canais sem A/B fazem só a capa A (CAPAS_DEPOIS_SO_A_SEM_AB).

Fora de propósito: obras com elenco MENOR de idade (asv0 Chivalry, q5Sv Tenpuru) — regra 02/11 22h35: sem capa sensual.

    python refazer_capas_fora_padrao.py          # mostra o que faria
    python refazer_capas_fora_padrao.py --fazer
"""
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
FILA = AQUI / "capas_depois.json"
LAT = Path(r"D:\hipercool-materiais\animes recap\videos laterais")
MENORES = {"asv0DQxVhVw", "q5Sv63C0THA"}  # fonte com elenco menor de idade
# nd67 = Medieval parte 3: A com 'BEFORE / AFTER' escrito em inglês (dona 11/11)
EXTRA = {"nd67FAr0h14"}
# longos antigos (antes do capas_depois) que a dona mostrou nas prints: vid do YouTube -> pasta
ANTIGOS = {"RpgQqQ5lRsA": ("hNQrW5ouNe0Ni5Me", "when-a-genius-blacksmith-humiliates-everyone-at-the-academy_cap1_20261104"),
           "1grmgiKjpoc": ("novo_inovaremanhwaverse", "sem-obra-c7b992_cap1_20261104")}


def _params_de_postar(pasta):
    x = json.loads((pasta / "postar.json").read_text(encoding="utf-8"))
    cc = json.loads((pasta / "capa.capa.json").read_text(encoding="utf-8")) if (pasta / "capa.capa.json").exists() else {}
    return {"anime": x.get("obra") or pasta.name.split("_cap")[0], "cap": int(x.get("cap") or 1),
            "texto": cc.get("texto", ""), "cena": x.get("titulo", ""), "protagonista": "", "generos": None,
            "formato": "16:9", "source_url": x.get("fonte", "")}


def main(fazer):
    fila = json.loads(FILA.read_text(encoding="utf-8"))
    alvo = []
    for it in fila:
        p = Path(it["pasta"])
        j = p / "capa.capa.json"
        pose = json.loads(j.read_text(encoding="utf-8")).get("pose", "") if j.exists() else ""
        src = it["params"].get("source_url", "")
        if any(m in src for m in MENORES):
            continue
        if (pose and not pose.startswith(("v2_", "tolerada_"))) or it["vid"] in EXTRA:
            alvo.append(it)
    novos = []
    for vid, (cred, nome) in ANTIGOS.items():
        if any(x["vid"] == vid for x in fila):
            continue
        pasta = LAT / nome
        novos.append({"canal": cred, "vid": vid, "pasta": str(pasta), "params": _params_de_postar(pasta),
                      "publicar": False, "estado": "pendente", "tentativas": 0,
                      "em": datetime.now().isoformat("T", "minutes"), "refazer": "fora_padrao_1111"})
    print(f"{len(alvo)} da fila + {len(novos)} antigos:")
    for it in alvo + novos:
        print(" ", it["vid"], it["canal"][:24], Path(it["pasta"]).name[:50])
    if not fazer:
        return
    for it in alvo + novos:
        p = Path(it["pasta"])
        for f in list(p.glob("capa*.jpg")) + list(p.glob("capa*.capa.json")):
            if ".antiga" in f.name:
                continue
            dest = f.with_name(f.name + ".antiga_catalogo")
            if not dest.exists():
                shutil.copy2(f, dest)
            f.unlink()
        it["estado"], it["tentativas"], it["refazer"] = "pendente", 0, "fora_padrao_1111"
    ids = {x["vid"] for x in alvo}
    resto = [x for x in fila if x["vid"] not in ids]
    pend_novos = [x for x in resto if x["estado"] == "pendente"]  # longos recém-postados continuam na frente
    outros = [x for x in resto if x["estado"] != "pendente"]
    FILA.write_text(json.dumps(outros + pend_novos + alvo + novos, ensure_ascii=False, indent=1), encoding="utf-8")
    print("gravado")


if __name__ == "__main__":
    main("--fazer" in sys.argv)
