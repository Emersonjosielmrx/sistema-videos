# -*- coding: utf-8 -*-
"""marca_scan.py — tira a marca do scan dos painéis de um capítulo ANTES do render.

Hoje: Blackout ("BLACKOUTCOMICS.COM / Aqui, você lê com a melhor qualidade." carimbado em ~1 de cada 7 painéis,
mais as duas faixas verticais "BLACKOUTCOMICS.COM" nas laterais). Acha cada marca pelo CONTORNO das letras
(config/marca_scan/<marca>_contorno.png — funciona com o carimbo mais apagado dos capítulos novos, onde a cor azul
falha) só na coluna onde ela fica, e apaga com a máscara exata do carimbo (<marca>_mascara.png: empilhando 44-54
recortes, o que não muda entre painéis é o carimbo), preenchendo pelo entorno (inpaint). Originais ficam em
<pasta>/_originais/ (o render ignora pastas e arquivos que começam com _).

  python bin/marca_scan.py <pasta de painéis> [--ensaio]
"""
import json
import shutil
import sys
from pathlib import Path

import cv2
import numpy as np

CFG = Path(__file__).resolve().parent.parent / "config" / "marca_scan"
LIMIAR = 0.70   # nota do contorno: carimbo 0,85-0,95 (inclusive apagado); fundo azul/arte 0,0-0,50
FOLGA_X = 30    # px de tolerância na coluna esperada da marca
EXTS = (".jpg", ".jpeg", ".png", ".webp")
_marcas = None


def _carregar():
    global _marcas
    if _marcas is None:
        meta = json.loads((CFG / "marcas.json").read_text(encoding="utf-8"))
        _marcas = {k: (cv2.imread(str(CFG / f"{k}_contorno.png"), 0).astype(np.float32) / 255,
                       cv2.imread(str(CFG / f"{k}_mascara.png"), 0), v["x"])
                   for k, v in meta.items() if not k.startswith("_")}
    return _marcas


def limpar(im):
    """(imagem sem a marca, [(marca, nota, x, y)]). Sem marca: a própria imagem e []."""
    E = cv2.dilate(cv2.Canny(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY), 60, 160), np.ones((3, 3), np.uint8))
    E = E.astype(np.float32) / 255
    mask, achou = np.zeros(im.shape[:2], np.uint8), []
    for nome, (t, m, x_esp) in _carregar().items():
        h, w = t.shape
        xa, xb = max(0, x_esp - FOLGA_X), min(E.shape[1], x_esp + FOLGA_X + w)  # só a coluna da marca
        if h > E.shape[0] or xb - xa < w:
            continue
        r = cv2.matchTemplate(E[:, xa:xb], t, cv2.TM_CCORR_NORMED)
        while True:
            _, nota, _, (dx, y) = cv2.minMaxLoc(r)
            if nota < LIMIAR:
                break
            r[max(0, y - h):y + h, :] = 0
            x = xa + dx
            mask[y:y + h, x:x + w] |= m
            achou.append((nome, round(float(nota), 2), int(x), int(y)))
    if not achou:
        return im, []
    # 9 px: engole o contorno/sombra do carimbo — com menos, o preenchimento puxa o azul da borda (fantasma)
    mask = cv2.dilate(mask, np.ones((9, 9), np.uint8))
    return cv2.inpaint(im, mask, 7, cv2.INPAINT_TELEA), achou


def _herdar_cache_censura(novo, antigo):
    """O cache da censura (Sightengine e regiões do Gemini) é chaveado pelo md5 do arquivo: ao
    reescrever o painel sem a marca, o md5 muda e tudo seria pago de novo — com 4 chaves Sightengine
    (1 já esgotada) e o Gemini em 429, isso derruba a detecção pro NudeNet, que é fraco em manhwa.
    Copia as entradas do md5 antigo pro novo. Só cache: se não existir, não faz nada."""
    import hashlib
    cache = Path(__file__).resolve().parent.parent / "workspace" / "censura_cache"
    if not cache.is_dir():
        return
    try:
        h_velho = hashlib.md5(Path(antigo).read_bytes()).hexdigest()
        h_novo = hashlib.md5(Path(novo).read_bytes()).hexdigest()
    except OSError:
        return
    if h_velho == h_novo:
        return
    for sufixo in (".json", ".regioes2.json"):
        de, para = cache / f"{h_velho}{sufixo}", cache / f"{h_novo}{sufixo}"
        if de.exists() and not para.exists():
            try:
                shutil.copy2(de, para)
            except OSError:
                pass


def limpar_pasta(pasta, ensaio=False):
    """Limpa os painéis da pasta (uma vez: marca em _marca_limpa.json). {arquivo: [(marca, nota, x, y)]}."""
    pasta = Path(pasta)
    feito = pasta / "_marca_limpa.json"
    if feito.exists() and not ensaio:
        return json.loads(feito.read_text(encoding="utf-8"))
    orig, res = pasta / "_originais", {}
    for f in sorted(pasta.iterdir()):
        if not f.is_file() or f.suffix.lower() not in EXTS or f.name.startswith("_"):
            continue
        im = cv2.imread(str(f))
        if im is None:
            continue
        out, achou = limpar(im)
        if not achou:
            continue
        res[f.name] = achou
        if not ensaio:
            orig.mkdir(exist_ok=True)
            if not (orig / f.name).exists():
                shutil.copy2(f, orig / f.name)
            cv2.imwrite(str(f), out, [cv2.IMWRITE_JPEG_QUALITY, 95] if f.suffix.lower() in (".jpg", ".jpeg") else [])
            _herdar_cache_censura(f, orig / f.name)
    if not ensaio:
        feito.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    return res


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    r = limpar_pasta(sys.argv[1], ensaio="--ensaio" in sys.argv)
    print(f"{len(r)} painéis com marca{' (ensaio: nada gravado)' if '--ensaio' in sys.argv else ''}")
    for k, v in r.items():
        print(f"  {k}: {', '.join(f'{n} {s}' for n, s, _x, _y in v)}")
