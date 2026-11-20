"""Vocabulário EXCLUSIVO de cada narrador (dona 20/11: "o Virjão fala 'guria', 'trancada no boga', os outros não
falam isso; e tem coisa que os outros falam que ele não fala — não é só a voz, é absorver o jeito de falar").

Compara as falas reais de TODOS os narradores parceiros (dataset_narradores/<voz>/metadata.csv + segs.json dos jobs
de sub-vozes quando houver). Para cada narrador:
  so_dele  = palavras/expressões que ELE usa bem mais que os outros (taxa dele >= 4x a dos outros e >= 3 vezes)
  nao_fala = palavras/expressões comuns nos OUTROS que ele quase nunca usa (vai pro "evitar" do roteiro)
Grava em linguagem_v2.json["so_dele"] / ["nao_fala"] (local + Drive com --sobe). O anime_script já usa "evitar";
"so_dele" entra como vocabulário próprio.
    python vocabulario_exclusivo.py [--sobe]
"""
import csv, json, math, re, subprocess, sys
from collections import Counter
from pathlib import Path

DS = Path(r"D:\hipercool-materiais\amostras_voz\dataset_narradores")
SV = Path(r"D:\tmp\estudo_voz\sv")
VOZES = Path(r"D:\hipercool-materiais\models\rvc\vozes")
R = r"D:\tools\rclone.exe"
# palavras de enredo/gramática que todo mundo usa (não dizem nada do jeito)
COMUNS = set("""a o e é de do da que um uma pra para com não se ele ela eles elas no na nos nas em por mais mas
como já tá ta foi vai ser ter tem isso esse essa aqui ali lá ai aí então ou só me te lhe meu minha seu sua dele dela
eu tu nós vocês você cara ele ela pro pra um uns umas quando onde porque pois também bem muito ainda depois antes
""".split())


def tokens(t):
    t = t.lower()
    ws = re.findall(r"[a-záéíóúâêôãõç]+", t)
    return [w for w in ws if len(w) > 2 and w not in COMUNS] + \
           [f"{a} {b}" for a, b in zip(ws, ws[1:]) if a not in COMUNS or b not in COMUNS]


def falas(voz):
    out = []
    meta = DS / voz / "metadata.csv"
    if meta.exists():
        out += [r[1] for r in csv.reader(open(meta, encoding="utf-8"), delimiter="|") if len(r) > 1]
    for sj in list(SV.rglob(f"{voz}*/segs.json")) + [p for p in SV.rglob("segs.json") if f"/{voz}/" in p.as_posix()]:
        out += [s["texto"] for s in json.loads(sj.read_text(encoding="utf-8")) if s.get("sim", 0) >= 0.5]
    return out


# 20/11: palavra de ENREDO (nome de personagem, termo da obra) não é jeito de falar. Com vários vídeos do narrador,
# só vale palavra que aparece em >= 2 vídeos dele; com 1 vídeo só, só vale se for marcador de FALA conhecido
# (gíria, interjeição, conector, apelido, palavrão, regionalismo) — o resto é história.
_MARCADOR = re.compile(r"(?i)^(.* )?(pi[aá]\w*|guri\w*|compadre|mano|véi|rapai?z?|molecad\w*|brab\w*|caba|bicho|"
                       r"tipo|né|bah|tchê|uai|oxe|eita|vixe|caraca|cacete|porra|caralho|merda|foda\w*|puta|"
                       r"porém|nisso|daí|então|tipo assim|olha só|imagina|simplesmente|praticamente|"
                       r"prot[ai]\w*|nosso (herói|cara|brabo)|maluco|moleque|piazinho|quatoz\w*|popóis|"
                       r"brutamontes|galera|meu povo|pessoal|rapaziada|boga|trancad\w*|pra completar|"
                       r"do nada|sem mais|bora|vamo\w*)$")


def _videos_por_palavra(voz):
    """{palavra: nº de vídeos diferentes em que o narrador usou} (só existe pra quem tem segs.json com 'video')."""
    vids = {}
    for sj in SV.rglob("segs.json"):
        if f"/{voz}/" not in sj.as_posix():
            continue
        for s in json.loads(sj.read_text(encoding="utf-8")):
            if s.get("sim", 0) < 0.5:
                continue
            for w in set(tokens(s["texto"])):
                vids.setdefault(w, set()).add(s.get("video") or sj.parent.name)
    return vids


def main(sobe=False):
    vozes = sorted(p.name for p in DS.iterdir() if p.is_dir())
    cont, tot = {}, {}
    for v in vozes:
        c = Counter(w for t in falas(v) for w in tokens(t))
        if sum(c.values()) >= 300:
            cont[v], tot[v] = c, sum(c.values())
    print("narradores com material:", {v: tot[v] for v in cont})
    for v in cont:
        outros = Counter()
        for o in cont:
            if o != v:
                outros.update(cont[o])
        tot_o = sum(outros.values()) or 1
        so, nao = [], []
        for w, n in cont[v].items():
            tx, to = n / tot[v], (outros[w] + 1) / tot_o
            if n >= 3 and tx / to >= 4:
                so.append((round(math.log2(tx / to) * n, 1), w))
        for w, n in outros.items():
            to, tx = n / tot_o, (cont[v][w] + 0.5) / tot[v]
            nos_outros = sum(1 for o in cont if o != v and cont[o][w] >= 2)
            if n >= 12 and nos_outros >= 3 and to / tx >= 6 and " " not in w:
                nao.append((round(to / tx, 1), w))
        vpp = _videos_por_palavra(v)
        if vpp and max((len(x) for x in vpp.values()), default=0) >= 2:
            so = [(n_, w) for n_, w in so if len(vpp.get(w, ())) >= 2]
        else:
            so = [(n_, w) for n_, w in so if _MARCADOR.match(w)]
        nao = [(n_, w) for n_, w in nao if _MARCADOR.match(w)]
        so = [w for _, w in sorted(so, reverse=True)[:25]]
        nao = [w for _, w in sorted(nao, reverse=True)[:15]]
        arq = VOZES / v / "linguagem_v2.json"
        try:
            g = json.loads(arq.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            g = {}
        g["so_dele"], g["nao_fala"] = so, nao
        g["_vocabulario_fonte"] = "vocabulario_exclusivo.py 20/11 (comparando com " + ", ".join(o for o in cont if o != v) + ")"
        arq.parent.mkdir(parents=True, exist_ok=True)
        arq.write_text(json.dumps(g, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\n== {v}\n  SÓ DELE: {', '.join(so)}\n  NÃO FALA: {', '.join(nao)}")
        if sobe:
            subprocess.run([R, "copyto", str(arq), f"manhwa-drive:colab_recap/vozes/{v}/linguagem_v2.json"],
                           capture_output=True)


if __name__ == "__main__":
    main("--sobe" in sys.argv)
