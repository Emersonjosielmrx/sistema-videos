"""canais_parceiros.py — levanta os canais de parceiro (dono 17-18/10/2026) e baixa 1 Short de amostra de cada, para medir
onde ficam a legenda e a marca deles (cobertura com a tarja branca). Resultado em estado/canais_parceiros.json e
amostras em estado/amostras/<nome>.mp4 + <nome>_tile.png (quadros aos 3, 10 e 20 s lado a lado).

    python canais_parceiros.py listar     # lista Shorts de cada canal (id, views, título) — rápido
    python canais_parceiros.py amostras   # baixa 1 Short por canal e monta a tira de quadros
"""
import sys as _sys
_sys.path.insert(0, r"D:\hipercool-materiais\comum")
import sem_janela  # noqa: E402,F401 — 29/10 (dona): nenhum processo filho (yt-dlp, ssh, ffmpeg) abre janela
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.append(r"D:\hipercool-materiais\comum")
from ytdlp_vez import vez as _vez  # noqa: E402  (1 yt-dlp por vez no PC: as 6 threads abaixo eram rajada)

BASE = Path(__file__).resolve().parent
EST = BASE / "estado"
AMO = EST / "amostras"
SAIDA = EST / "canais_parceiros.json"

CANAIS = [
    # (nome curto, url, tipo) — lista do dono, 17/10
    ("kaijinre", "https://www.youtube.com/@kaijinre/shorts", "manhwa"),
    ("king_chan01", "https://www.youtube.com/@king_chan01/shorts", "manhwa"),
    ("richan", "https://www.youtube.com/@richan-anime/shorts", "anime"),
    ("ansaketv", "https://www.youtube.com/@ansaketv/shorts", "anime"),
    ("nerdcf", "https://www.youtube.com/@nerdcf.animes/shorts", "anime"),
    ("100animee", "https://www.youtube.com/@100ANIMEE/shorts", "anime"),
    ("a_UCQ1X71", "https://www.youtube.com/channel/UCQ1X71snvUD7OKA3B8S3n6Q/shorts", "anime"),
    ("a_UCHCxgk", "https://www.youtube.com/channel/UCHCxgkOUs9jw0ngpEtNb3xg/shorts", "anime"),
    ("a_UCbYDJC", "https://www.youtube.com/channel/UCbYDJCicgdEOFPtgJLppCfw/shorts", "anime"),
    ("a_UCoj3c_", "https://www.youtube.com/channel/UCoj3c_Mw_zTLCZt9bshd__w/shorts", "anime"),
    ("a_UCK9vMO", "https://www.youtube.com/channel/UCK9vMOZaWjfSwQFiBPQt6iA/shorts", "anime"),
    ("drameela", "https://www.youtube.com/@drameela/shorts", "dorama"),
    ("d_UCDP44A", "https://www.youtube.com/channel/UCDP44AK1qd0xpAuArni_nbQ/shorts", "dorama"),
    ("d_UCSJ6_g", "https://www.youtube.com/channel/UCSJ6_grRhGTfH8FZWy9ofew/shorts", "dorama"),
    ("d_UC8SqOf", "https://www.youtube.com/channel/UC8SqOfxuoCHNn2V2irOXFsQ/shorts", "dorama"),
    ("d_UCrQEaK", "https://www.youtube.com/channel/UCrQEaKmguE65TOO4EedWHzA/shorts", "dorama"),
    ("d_UCJ4ZMy", "https://www.youtube.com/channel/UCJ4ZMyMwgcHYgpJogOJrYiQ/shorts", "dorama"),
    ("d_UCGk8PI", "https://www.youtube.com/channel/UCGk8PIaZgPZPOgDkbRzeFbQ/shorts", "dorama"),
    ("d_UCOHGNd", "https://www.youtube.com/channel/UCOHGNd14T45bHhvFfTI-B1Q/shorts", "dorama"),
    ("f_UCRKSO0", "https://www.youtube.com/channel/UCRKSO0AInMtfM7rDgurjyyw/shorts", "filme"),
    ("olaranjo1", "https://www.youtube.com/@olaranjo1/shorts", "anime"),
    ("animax_97", "https://www.youtube.com/@animax_97/shorts", "anime"),
    ("jresumos", "https://www.youtube.com/@jresumos/shorts", "dorama"),
    ("andreu_edit1", "https://www.youtube.com/@andreu.edit1/shorts", "filme_sem_voz"),
    ("inusifatos", "https://www.youtube.com/@inusifatos/shorts", "fatos"),
    ("xiuliamelo", "https://www.youtube.com/@xiuliamelo/shorts", "fatos"),
    ("carlosmerchanat", "https://www.youtube.com/@carlosmerchanat/shorts", "fatos"),
    ("canalutopia", "https://www.youtube.com/@canalutopia/shorts", "fatos"),
    ("thalisshortsbr", "https://www.youtube.com/@thalisshortsbr/shorts", "fatos"),
    ("futtres", "https://www.youtube.com/@futtres/shorts", "esportes"),
    ("fabioindaia2006", "https://www.youtube.com/@fabioindaia2006/shorts", "esportes"),
]


def _listar(c):
    nome, url, tipo = c
    with _vez(f"parceiros: lista {nome}"):
        r = subprocess.run(["yt-dlp", "--flat-playlist", "--encoding", "utf-8", "--playlist-end", "300", "--print",
                            "%(id)s\t%(view_count)s\t%(channel)s\t%(title)s", url],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
    itens = []
    for l in (r.stdout or "").splitlines():
        p = l.split("\t", 3)
        if len(p) == 4 and p[0]:
            itens.append({"id": p[0], "views": int(p[1]) if p[1].isdigit() else 0, "canal": p[2], "titulo": p[3]})
    itens.sort(key=lambda x: -x["views"])
    return {"nome": nome, "url": url, "tipo": tipo, "n": len(itens),
            "canal": next((x["canal"] for x in itens if x["canal"] not in ("NA", "")), ""), "top": itens[:5],
            "erro": (r.stderr or "").strip().splitlines()[-1][:200] if not itens else ""}


def listar():
    with ThreadPoolExecutor(6) as ex:
        res = list(ex.map(_listar, CANAIS))
    EST.mkdir(exist_ok=True)
    SAIDA.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    for c in res:
        top = c["top"][0] if c["top"] else {}
        print(f"{c['nome']:12} {c['tipo']:7} {c['n']:4} Shorts | {c['canal'][:28]:28} | top {top.get('views', 0):>9} "
              f"{top.get('titulo', c['erro'])[:60]}")


def _amostra(c):
    if not c["top"]:
        return c["nome"], "sem Shorts"
    AMO.mkdir(parents=True, exist_ok=True)
    mp4 = AMO / f"{c['nome']}.mp4"
    if not mp4.exists():
        with _vez(f"parceiros: amostra {c['nome']}"):
            subprocess.run(["yt-dlp", "-q", "-S", "res:1280", "--merge-output-format", "mp4", "-o", str(mp4),
                            f"https://www.youtube.com/shorts/{c['top'][0]['id']}"], capture_output=True, timeout=600)
    if not mp4.exists():
        return c["nome"], "download falhou"
    pngs = []
    for t in (3, 10, 20):
        png = AMO / f"{c['nome']}_{t}.png"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", str(mp4), "-frames:v", "1", "-vf",
                        "scale=270:480:force_original_aspect_ratio=decrease,pad=270:480:(ow-iw)/2:(oh-ih)/2", str(png)],
                       capture_output=True)
        if png.exists():
            pngs.append(png)
    if len(pngs) >= 2:
        tile = AMO / f"{c['nome']}_tile.png"
        args = sum((["-i", str(p)] for p in pngs), [])
        subprocess.run(["ffmpeg", "-v", "error", "-y", *args, "-filter_complex", f"hstack={len(pngs)}", str(tile)],
                       capture_output=True)
    return c["nome"], "ok"


def amostras():
    res = json.loads(SAIDA.read_text(encoding="utf-8"))
    with ThreadPoolExecutor(4) as ex:
        for nome, st in ex.map(_amostra, res):
            print(nome, st)


if __name__ == "__main__":
    {"listar": listar, "amostras": amostras}[sys.argv[1] if len(sys.argv) > 1 else "listar"]()
