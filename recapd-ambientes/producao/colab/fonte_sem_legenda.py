r"""fonte_sem_legenda.py — nota de "legenda queimada" de um vídeo do YouTube SEM baixar o vídeo (dona 19/11: "tem que ter
uma seleção pra priorizar vídeos longos que não têm legenda, pois fica muito ruim a tarja branca na tela").

Usa as 3 miniaturas automáticas do YouTube (i.ytimg.com/vi/<id>/hq1..3.jpg = quadros do meio do vídeo, ~15 KB cada,
sem login, sem yt-dlp). Legenda queimada = linha de texto CLARO com contorno ESCURO, curta na vertical, na faixa de
baixo (70%-96% da altura), centrada. Nota = quantas das 3 miniaturas têm isso (0 = sem legenda, 3 = legenda o vídeo
todo). Cache em estado\legenda_fonte_cache.json (cada id é olhado 1 vez).

    python fonte_sem_legenda.py ID [ID ...]      # imprime a nota de cada um
"""
import json
import sys
import urllib.request
from pathlib import Path

import cv2
import numpy as np

CACHE = Path(__file__).resolve().parent.parent / "estado" / "legenda_fonte_cache.json"


def _baixar(vid, n):
    try:
        req = urllib.request.Request(f"https://i.ytimg.com/vi/{vid}/hq{n}.jpg", headers={"User-Agent": "Mozilla/5.0"})
        dados = urllib.request.urlopen(req, timeout=15).read()
        return cv2.imdecode(np.frombuffer(dados, np.uint8), cv2.IMREAD_COLOR)
    except Exception:  # noqa: BLE001
        return None


def _tem_texto(img):
    """True se a faixa de baixo tem uma linha de texto claro com contorno (legenda queimada)."""
    if img is None:
        return False
    # tira as tarjas pretas do 4:3 (hq*.jpg = 480x360 com o 16:9 no meio)
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    linhas_vivas = np.nonzero(g.mean(axis=1) > 12)[0]
    if len(linhas_vivas) < 40:
        return False
    g = g[linhas_vivas[0]:linhas_vivas[-1] + 1]
    h, w = g.shape
    img = img[linhas_vivas[0]:linhas_vivas[-1] + 1]
    y0, y1 = int(h * 0.66), int(h * 0.97)
    x0, x1 = int(w * 0.20), int(w * 0.80)  # legenda de recap = no centro
    faixa = img[y0:y1, x0:x1]
    fg = cv2.cvtColor(faixa, cv2.COLOR_BGR2GRAY)
    # letra = região CLARA ou de cor viva (amarelo/verde/branco) com contorno PRETO grosso em volta
    hsv = cv2.cvtColor(faixa, cv2.COLOR_BGR2HSV)
    viva = ((hsv[:, :, 2] > 170) & ((hsv[:, :, 1] > 120) | (fg > 200))).astype(np.uint8)
    preto = (fg < 45).astype(np.uint8)
    anel = cv2.dilate(preto, np.ones((3, 3), np.uint8))
    n, lab, st, _c = cv2.connectedComponentsWithStats(viva, 8)
    letras = []
    for k in range(1, n):
        x, y, ww, hh, area = st[k]
        if not (4 <= hh <= 0.22 * faixa.shape[0] and 1 <= ww <= 3 * hh and area >= 6):
            continue
        borda = cv2.dilate((lab[y:y + hh, x:x + ww] == k).astype(np.uint8), np.ones((3, 3), np.uint8))
        if (borda & anel[y:y + hh, x:x + ww]).sum() >= 0.35 * borda.sum() * 0.5:  # contorno escuro em volta
            letras.append((x, y, ww, hh))
    if len(letras) < 3:
        return False
    # >= 3 letras na MESMA linha (centros na vertical a menos de meia altura de letra)
    ys = np.array([y + hh / 2 for x, y, ww, hh in letras])
    hs = np.median([hh for *_r, hh in letras])
    for yc in ys:
        if (np.abs(ys - yc) < hs * 0.5).sum() >= 3:
            return True
    return False


def nota(vid):
    """0-3: em quantas das 3 miniaturas há legenda queimada. None = não deu pra olhar."""
    try:
        cache = json.loads(CACHE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        cache = {}
    if vid in cache:
        return cache[vid]
    imgs = [_baixar(vid, n) for n in (1, 2, 3)]
    if all(i is None for i in imgs):
        return None
    n = int(sum(bool(_tem_texto(i)) for i in imgs))
    cache[vid] = n
    try:
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        CACHE.write_text(json.dumps(cache, indent=0), encoding="utf-8")
    except OSError:
        pass
    return n


if __name__ == "__main__":
    for v in sys.argv[1:]:
        print(v, nota(v))
