# 02/11 22h dona: BANCO DE FOTOS DAS MULHERES de cada obra (manhwa e anime), tiradas do próprio vídeo, pra usar de
# referência de rosto/cabelo/cor nas capas A/B/C dos longos. Roda no venv_imgutils (Python 3.11: o imgutils pede
# numpy<2, que não tem roda pro 3.13 do D:\veo\venv).
#   venv_imgutils\Scripts\python.exe banco_mulheres.py <video.mp4> <obra> [passo_s]
#   -> capas_referencias\<obra>\mulheres\pNN\rosto_*.jpg corpo_*.jpg + indice.json
# Depois: nomear.py <obra> (no D:\veo\venv) dá nome/idade cruzando com o roteiro. Menor de idade nunca vai pra capa.
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("HF_HOME", r"D:\caches\huggingface")  # nada no C
# 03/11: em prioridade normal este lote comia ~6 núcleos do PC1 (03h e 11h17) e travava controlador, Veo e postagens.
# Lote de fundo = prioridade abaixo do normal sempre (BELOW_NORMAL_PRIORITY_CLASS), venha de onde vier o disparo.
if os.name == "nt":
    import ctypes
    # 04/11: a versão de 03/11 não funcionava — GetCurrentProcess() volta como int de 32 bits no ctypes e o handle chegava
    # errado (o processo seguia "Normal" com ~6 núcleos e o ffmpeg das solares estourava o tempo). Handle como ponteiro,
    # prioridade OCIOSA (só usa CPU que ninguém quer) e só os 2 últimos núcleos.
    _k = ctypes.windll.kernel32
    _k.GetCurrentProcess.restype = ctypes.c_void_p
    _eu = ctypes.c_void_p(_k.GetCurrentProcess())
    _k.SetPriorityClass(_eu, 0x00000040)  # IDLE_PRIORITY_CLASS
    _n = os.cpu_count() or 2
    _k.SetProcessAffinityMask(_eu, ctypes.c_size_t(3 << max(0, _n - 2)))
for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ.setdefault(_v, "2")
import cv2  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402
from imgutils.detect import detect_faces, detect_person  # noqa: E402
from imgutils.metrics import (ccip_batch_differences, ccip_clustering, ccip_default_threshold,  # noqa: E402
                              ccip_extract_feature)
from imgutils.tagging import get_wd14_tags  # noqa: E402

AQUI = Path(__file__).parent
MENOR = {"child", "loli", "shota", "kindergarten", "toddler", "baby", "aged_down", "elementary_school"}
SEM_JANELA = 0x08000000


def quadros(video, passo, tmp):
    subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-vf", f"fps=1/{passo},scale=1280:-2", "-q:v", "3",
                    str(Path(tmp) / "q_%05d.jpg")], check=True, creationflags=SEM_JANELA)
    return sorted(Path(tmp).glob("q_*.jpg"))


def nitidez(img):
    return float(cv2.Laplacian(cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2GRAY), cv2.CV_64F).var())


def colorido(img):
    hsv = cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2HSV)
    return float(hsv[..., 1].mean()) > 35


def recorte(img, box, margem):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    return img.crop((max(0, int(x0 - w * margem)), max(0, int(y0 - h * margem)),
                     min(img.width, int(x1 + w * margem)), min(img.height, int(y1 + h * margem))))


def _homens(rostos, base, maximo=3):
    """03/11: protagonista / personagens principais homens -> <obra>\\homens\\hNN\\rosto_*.jpg + homens.json
    (os que mais aparecem primeiro). Mesmo agrupamento CCIP das mulheres, sem nome (o nomear.py dá)."""
    destino = base / "homens"
    if len(rostos) < 3:
        return
    feats = [ccip_extract_feature(r["cara"]) for r in rostos]
    rot = ccip_clustering(feats, method="optics", min_samples=3)
    grupos = {}
    for i, g in enumerate(rot):
        if g >= 0:
            grupos.setdefault(int(g), []).append(i)
    dif = ccip_batch_differences(feats)
    lim = ccip_default_threshold()
    junto = True
    while junto:
        junto = False
        ids = list(grupos)
        for a in ids:
            for b in ids:
                if a < b and a in grupos and b in grupos and \
                        float(np.mean(dif[np.ix_(grupos[a], grupos[b])])) < lim:
                    grupos[a] += grupos.pop(b)
                    junto = True
    ordem = sorted(grupos.values(), key=len, reverse=True)[:maximo]
    if destino.exists():
        shutil.rmtree(destino)
    indice = []
    for n, idx in enumerate(ordem, 1):
        pasta = destino / f"h{n:02d}"
        pasta.mkdir(parents=True)
        arqs, vistos = [], set()
        for r in sorted((rostos[i] for i in idx), key=lambda r: -r["nitidez"]):
            if round(r["seg"] / 10) in vistos:
                continue
            vistos.add(round(r["seg"] / 10))
            f = pasta / f"rosto_{len(arqs) + 1}.jpg"
            r["cara"].save(f, quality=92)
            arqs.append({"arquivo": f.name, "seg": r["seg"]})
            if len(arqs) == 6:
                break
        indice.append({"personagem": pasta.name, "nome": "", "principal": n == 1, "aparicoes": len(idx),
                       "arquivos": arqs})
    (base / "homens.json").write_text(json.dumps({"homens": indice}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(indice)} homens -> {destino}")


def main(video, obra, passo=2.5):
    destino = AQUI / obra / "mulheres"
    tmp = tempfile.mkdtemp(prefix="banco_", dir=r"D:\hipercool-materiais\tmp")
    try:
        fotos = quadros(video, passo, tmp)
        rostos, homens = [], []
        for i, q in enumerate(fotos):
            img = Image.open(q).convert("RGB")
            for box, _lbl, score in detect_faces(img):
                x0, y0, x1, y1 = box
                if score < 0.6 or min(x1 - x0, y1 - y0) < 70:
                    continue
                if y1 > img.height * 0.82:  # faixa da legenda/tarja embaixo
                    continue
                cara = recorte(img, box, 0.35)
                if not colorido(cara):
                    continue
                _rating, tags, _chars = get_wd14_tags(cara, general_threshold=0.35)
                girl, boy = tags.get("1girl", 0), tags.get("1boy", 0)
                item = {"quadro": str(q), "seg": round(i * passo, 1), "box": box, "cara": cara,
                        "nitidez": nitidez(cara) * (x1 - x0), "menor": sorted(MENOR & set(tags))}
                # 03/11 dona: "precisa de mulheres diferentes e do protagonista claro ou personagens principais" ->
                # rosto de homem vai pro banco dos homens (protagonista), não some
                if boy >= 0.6 and girl < 0.3:
                    homens.append(item)
                    continue
                # 03/11 teste 6g2b: o herói (menino de cabelo preto) entrou junto com a mulher no p01
                if girl < 0.6 or boy > 0.3:
                    continue
                rostos.append(item)
        # 04/11: KJ5F (76 min, muita luta) ficou 8 h preso no agrupamento CCIP, que compara todos x todos (N²).
        # Fica só com os 400 rostos mais nítidos de cada lado antes de agrupar.
        rostos = sorted(rostos, key=lambda r: -r["nitidez"])[:400]
        homens = sorted(homens, key=lambda r: -r["nitidez"])[:400]
        print(f"rostos: {len(rostos)} mulheres, {len(homens)} homens", flush=True)
        if homens:
            _homens(homens, AQUI / obra)
        if not rostos:
            print("nenhum rosto de mulher")
            return
        feats = [ccip_extract_feature(r["cara"]) for r in rostos]
        rotulos = ccip_clustering(feats, method="optics", min_samples=3)
        grupos = {}
        for i, g in enumerate(rotulos):
            if g >= 0:
                grupos.setdefault(int(g), []).append(i)
        # 03/11 teste 6g2b: a mesma menina saiu em 5 grupos (caras diferentes: chorando, rindo, de lado) -> junta os
        # grupos cuja diferença média CCIP fica abaixo do limiar padrão
        dif = ccip_batch_differences(feats)
        lim = ccip_default_threshold()
        ids = list(grupos)
        junto = True
        while junto:
            junto = False
            for a in ids:
                for b in ids:
                    if a < b and a in grupos and b in grupos and \
                            float(np.mean(dif[np.ix_(grupos[a], grupos[b])])) < lim:
                        grupos[a] += grupos.pop(b)
                        junto = True
            ids = list(grupos)
        grupos = {g: [rostos[i] for i in idx] for g, idx in grupos.items()}
        # 03/11 dona ("estão coletando fotos das mesmas mulheres, preciso de mulheres diferentes"): 6 grupos saíam
        # todos da mesma (Mia x5, Selena x6). Guarda até 10 grupos; o nomear.py junta os de mesmo nome depois.
        ordem = sorted(grupos.values(), key=len, reverse=True)[:10]
        if destino.exists():
            shutil.rmtree(destino)
        indice = []
        for n, grupo in enumerate(ordem, 1):
            pasta = destino / f"p{n:02d}"
            pasta.mkdir(parents=True)
            melhores, vistos = [], set()
            for r in sorted(grupo, key=lambda r: -r["nitidez"]):
                if round(r["seg"] / 10) in vistos:  # fotos de cenas diferentes, não 6 do mesmo plano
                    continue
                vistos.add(round(r["seg"] / 10))
                melhores.append(r)
                if len(melhores) == 6:
                    break
            arqs = []
            for k, r in enumerate(melhores, 1):
                f = pasta / f"rosto_{k}.jpg"
                r["cara"].save(f, quality=92)
                arqs.append({"arquivo": f.name, "seg": r["seg"]})
            corpos = 0
            for r in melhores:
                if corpos == 3:
                    break
                img = Image.open(r["quadro"]).convert("RGB")
                fx = (r["box"][0] + r["box"][2]) / 2
                for box, _l, s in detect_person(img):
                    if s > 0.5 and box[0] <= fx <= box[2] and box[1] <= r["box"][1] + 5 \
                            and box[3] - box[1] > (r["box"][3] - r["box"][1]) * 2.2:
                        corpos += 1
                        f = pasta / f"corpo_{corpos}.jpg"
                        img.crop(tuple(int(v) for v in box)).save(f, quality=92)
                        arqs.append({"arquivo": f.name, "seg": r["seg"]})
                        break
            indice.append({"personagem": pasta.name, "nome": "", "principal": n == 1, "aparicoes": len(grupo),
                           "possivel_menor": sorted({t for r in grupo for t in r["menor"]}), "arquivos": arqs})
        (AQUI / obra / "indice.json").write_text(json.dumps({"video": str(video), "passo_s": passo,
                                                             "mulheres": indice}, ensure_ascii=False, indent=1),
                                                 encoding="utf-8")
        print(f"{len(indice)} mulheres -> {destino}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main(Path(sys.argv[1]), sys.argv[2], float(sys.argv[3]) if len(sys.argv) > 3 else 2.5)
