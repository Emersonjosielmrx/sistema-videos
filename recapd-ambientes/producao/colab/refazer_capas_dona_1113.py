r"""refazer_capas_dona_1113.py — 13/11 dona (prints dos canais): capas fora do critério — sem mulher, sem protagonista
parecido com a história, só o herói sozinho, quadro do vídeo, nomes sobrepostos. Ela autorizou trocar. Põe cada uma
na fila do capas_depois como PENDENTE, guarda a capa velha (.dona_1113) e tira o .capa.json pra forçar gerar de novo.
Item que não estava na fila é montado pela pasta do vídeo (postar.json da pasta lateral, mesmo formato do
refazer_capas_fora_padrao.py)."""
import json
import shutil
from pathlib import Path

AQUI = Path(__file__).resolve().parent
FILA = AQUI / "capas_depois.json"
LAT = Path(r"D:\hipercool-materiais\animes recap\videos laterais")
MENORES = {"asv0DQxVhVw", "q5Sv63C0THA"}
# vid do YouTube -> motivo (o que a dona apontou)
ALVOS = {  # 13/11 16h — auditoria (auditar_capas_longos.py) conferida por mim olhando a imagem
    "COp7UBa6CPo": "só o herói assustado, mulher minúscula no canto",
}
# 2ª leva (15h45, já na fila): opyASXVvTc4, 3KvZHmc_PTo, 8fsdSEFZtMw, JA1JeAzMI7M, pXI9Nuf5EZw
# cIB4X-Q9MIk (parte 9): a dona disse que é a ÚNICA em que o protagonista parece — fica


def _params(pasta, titulo):
    x = json.loads((pasta / "postar.json").read_text(encoding="utf-8"))
    return {"anime": x.get("obra") or pasta.name.split("_cap")[0], "cap": int(x.get("cap") or 1), "texto": "",
            "cena": x.get("titulo") or titulo, "protagonista": "", "generos": None, "formato": "16:9",
            "source_url": x.get("fonte", "")}


def main():
    fila = json.loads(FILA.read_text(encoding="utf-8"))
    por_vid = {x["vid"]: x for x in fila}
    post = json.loads((AQUI / "longos_postados.json").read_text(encoding="utf-8"))["postados"]
    feito = []
    for vid, motivo in ALVOS.items():
        if vid in MENORES:
            continue
        it = por_vid.get(vid)
        if it is None:
            p = next((x for x in post if (x.get("url") or "").endswith(vid)), None)
            if not p:
                print(f"{vid}: não achei o post — pulado")
                continue
            pastas = sorted(LAT.glob(f"*/postar.json"), key=lambda f: f.stat().st_mtime, reverse=True)
            pasta = next((f.parent for f in pastas
                          if json.loads(f.read_text(encoding="utf-8")).get("posted_url", "").endswith(vid)
                          or vid in f.read_text(encoding="utf-8")), None)
            if not pasta:
                print(f"{vid}: sem pasta do vídeo — pulado")
                continue
            it = {"canal": p["canal"], "vid": vid, "pasta": str(pasta), "params": _params(pasta, p.get("titulo", "")),
                  "publicar": False, "estado": "feito", "tentativas": 0, "em": p.get("em", "")}
            fila.append(it)
        pasta = Path(it["pasta"])
        for f in ("capa.jpg", "capa.capa.json"):
            if (pasta / f).exists():
                shutil.move(str(pasta / f), str(pasta / f"{f}.dona_1113"))
        it.update(estado="pendente", tentativas=0, refazer=f"dona_1113: {motivo}")
        feito.append(vid)
        print(f"{vid}: na fila — {motivo}")
    FILA.write_text(json.dumps(fila, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(feito)} capas na fila pra refazer")


if __name__ == "__main__":
    main()
