#!/usr/bin/env python3
"""dedupe_video.py - o Veo nao posta quase o mesmo clipe duas vezes (item AB-08 de D:\\veo\\docs\\PLANO_MELHORIAS_VEO.md).

O dedupe de FALA (conferir_fala/AT-04) nao pega o mesmo clipe com outra fala nem o clipe re-limpo com outro nome.
Copiado de D:\\manhwa-react\\mr\\memoria.py (hashes_quadros, _parecido, limiar 0,35): dHash de 1 quadro a cada 0,5 s
do QUADRADO CENTRAL (80% da largura: fica fora da legenda queimada a 78% da altura e do @ do canal no topo), e o
"parecido" e a fracao dos quadros do video novo que tem um quadro quase igual (<= 10 bits) num indexado.

Indice: logs\\hashes_videos.json {stem: [hashes]} - os limpos (D:\\hipercool-materiais\\veo\\limpos). Os 730 finais
antigos dos canais encerrados nao estao no disco (so no backup do Drive): ficam de fora.
    python dedupe_video.py --indexar          # indexa o que falta (uma vez; depois o limpar_veo indexa cada novo)
    python dedupe_video.py --duplicados       # pares de limpos repetidos entre si
    python dedupe_video.py video.mp4          # repetido de quem?
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

FFMPEG = r"D:\hipercool-materiais\bin\ffmpeg.exe"
LIMPOS = Path(r"D:\hipercool-materiais\veo\limpos")
INDICE = Path(__file__).resolve().parent / "logs" / "hashes_videos.json"
# 0,35 e o do react (mesma gravacao do dono). No Veo, com 243 limpos (16/10): os 5 pares de 1,00 sao o MESMO clipe
# salvo com 2 nomes (so a legenda muda); 0,75 / 0,62 / 0,44 / 0,38 eram clipes diferentes no mesmo estudio/cenario
# (pessoa, alien x robo) - conferidos nos quadros. Por isso 0,9.
LIMIAR = 0.9


def hashes(video, passo=0.5):
    vf = (f"fps=1/{passo},crop='trunc(min(iw,ih)*0.8/2)*2':'trunc(min(iw,ih)*0.8/2)*2',"
          "scale=9:8:flags=area,format=gray")
    r = subprocess.run([FFMPEG, "-hide_banner", "-loglevel", "error", "-threads", "2", "-i", str(video), "-an",
                        "-vf", vf, "-f", "rawvideo", "-"], capture_output=True, timeout=300)
    dados = np.frombuffer(r.stdout, np.uint8)
    out = []
    for i in range(len(dados) // 72):
        q = dados[i * 72:(i + 1) * 72].reshape(8, 9).astype(np.int16)
        if q.std() > 6:  # tela preta/lisa nao identifica nada
            out.append(int("".join("1" if v else "0" for v in (q[:, 1:] > q[:, :-1]).flatten()), 2))
    return out


def parecido(a, b, dist=10):
    """Fracao dos quadros de `a` que tem um quadro quase igual em `b`."""
    if not a or not b:
        return 0.0
    B = np.array(b, dtype=np.uint64)
    hit = 0
    for x in a:
        bits = np.unpackbits(np.bitwise_xor(B, np.uint64(x)).view(np.uint8)).reshape(len(B), 64).sum(axis=1)
        if bits.min() <= dist:
            hit += 1
    return hit / len(a)


def carregar():
    return json.loads(INDICE.read_text("utf-8")) if INDICE.exists() else {}


def guardar(ind):
    INDICE.parent.mkdir(parents=True, exist_ok=True)
    tmp = INDICE.with_suffix(".tmp")
    tmp.write_text(json.dumps(ind), "utf-8")
    tmp.replace(INDICE)


def repetido(video, ignorar=None, ind=None, hs=None):
    """(stem, fracao) do indexado mais parecido se >= LIMIAR, senao None. `ignorar`: o proprio stem."""
    ind = ind if ind is not None else carregar()
    hs = hs if hs is not None else hashes(video)
    melhor = max(((parecido(hs, h), s) for s, h in ind.items() if s != ignorar), default=(0.0, None))
    return (melhor[1], round(melhor[0], 2)) if melhor[0] >= LIMIAR else None


def indexar(video, ind=None):
    """Calcula e grava os hashes de um video (o limpar_veo chama para cada limpo novo). Devolve os hashes."""
    ind = ind if ind is not None else carregar()
    ind[Path(video).stem] = hs = hashes(video)
    guardar(ind)
    return hs


def main():
    a = sys.argv[1:]
    if a == ["--indexar"]:
        ind = carregar()
        falta = [p for p in sorted(LIMPOS.glob("*.mp4")) if p.stem not in ind]
        for i, p in enumerate(falta, 1):
            ind[p.stem] = hashes(p)
            if i % 20 == 0 or i == len(falta):
                guardar(ind)
                print(f"[{i}/{len(falta)}] indexados", flush=True)
        print(f"indice: {len(ind)} videos")
    elif a == ["--duplicados"]:
        ind = carregar()
        stems = sorted(ind)
        for i, s in enumerate(stems):
            for t in stems[i + 1:]:
                f = max(parecido(ind[s], ind[t]), parecido(ind[t], ind[s]))
                if f >= LIMIAR:
                    print(f"{f:.2f}  {s}  {t}")
    elif len(a) == 1:
        print(repetido(a[0], ignorar=Path(a[0]).stem))
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
