"""parceiro_marca.py — tira a legenda e a marca do canal PARCEIRO do vídeo-fonte SÓ onde elas estão e escreve a NOSSA
marca no lugar (dono, 16/10: "está muito borrado no meio do vídeo, tem que ser só em cima da marca e colocar a nossa").

@kaijinre (conferido 16/10 no resumo de 2,6 mi):
  - legenda amarela com contorno preto, sempre na mesma linha (~73-75% da altura; medida por vídeo);
  - marca "@kaijinre" branca semitransparente, centralizada na horizontal, tamanho fixo, que DESCE e SOBE devagar o
    vídeo inteiro (84% -> 11% -> 84% da altura em 70 s) — marca d'água animada.

Achar a marca: "quanto o pixel clareou em relação ao que faltava pro branco" ((I - fundo) / (255 - fundo), fundo =
mediana 9x9) — overlay branco com transparência dá o mesmo valor sobre fundo claro ou escuro e a linha preta do
desenho fica de fora. Molde nesse espaço, só na faixa central, 4 quadros/s; a trilha da altura é suavizada (mediana
móvel) e o que foge dela é descartado (erro da busca); entre as amostras, interpolação.

  detectar(video)                    -> dict (cache <video>.parceiro.json)
  cobrir(video, saida, handle, det)  -> Path   (1 passada: lê, cobre, grava; áudio copiado)
"""
import json
import os
import logging
import subprocess
from pathlib import Path

import cv2
import numpy as np

CONFIG = Path(__file__).resolve().parent.parent / "config" / "parceiro_marcas"
FONTE_MARCA = r"C:\Windows\Fonts\timesbd.ttf"   # serifada em negrito, como a marca deles
ANALISE_S = 0.5      # a busca roda em meia resolução (360x640)
AMOSTRA_FPS = 4
MOLDE = {"kaijinre": {"arquivo": "kaijinre_alfa.png", "x": 0.36, "w": 0.30, "h": 0.043}}
DELOGO_MAX_H = 0.12  # 30/10: delogo maior que isso (fração da altura) borra a tela em listras — não aplica


def _alfa(g):
    g = g.astype(np.float32)
    bg = cv2.medianBlur(g.astype(np.uint8), 9).astype(np.float32)
    return np.clip((g - bg) / np.maximum(255.0 - bg, 25.0), 0, 1)


def _dims(video):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=width,height,r_frame_rate:format=duration", "-of", "json", str(video)],
                       capture_output=True, text=True, timeout=60)
    d = json.loads(r.stdout)
    s = d["streams"][0]
    num, den = (s.get("r_frame_rate") or "30/1").split("/")
    return int(s["width"]), int(s["height"]), float(num) / float(den or 1), float(d["format"]["duration"])


def _faixa_legenda(video, W, H):
    """[y0, y1] da linha da legenda amarela deles (histograma de 'letra amarela com contorno preto' por linha), ou None."""
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(video), "-vf", "fps=1", "-f", "rawvideo",
                          "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
    linhas, n = np.zeros(H), 0
    while True:
        buf = p.stdout.read(W * H * 3)
        if len(buf) < W * H * 3:
            break
        f = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
        linhas += _letra_amarela(f).sum(axis=1)
        n += 1
    p.wait()
    if not n or linhas.max() < 50 * n:
        return None
    on = np.where(linhas > linhas.max() * 0.15)[0]
    on = on[on > H * 0.4]  # a legenda deles fica na metade de baixo
    return [int(on.min()) - 8, int(on.max()) + 8] if len(on) else None


def _letra_amarela(f):
    hsv = cv2.cvtColor(f, cv2.COLOR_BGR2HSV)
    amarelo = ((hsv[..., 0] >= 16) & (hsv[..., 0] <= 38) & (hsv[..., 1] > 110) & (hsv[..., 2] > 150)).astype(np.uint8)
    escuro = (f.max(axis=2) < 70).astype(np.uint8)
    return amarelo & cv2.dilate(escuro, np.ones((5, 5), np.uint8))


def _extensoes_legenda(video, W, faixa, fps_saida):
    """[x0, x1] das palavras deles em CADA quadro de saída (ou None). Lê só a faixa da legenda (rápido). As letras
    entram animadas: num quadro isolado a palavra aparece pela metade (16/10: sobrou "O DELE" descoberto) — por isso
    vale a união numa janela de ±7 quadros (~0,23 s)."""
    # altura e topo PARES + exact=1: com 49 linhas o crop do ffmpeg entregava 48 sem avisar, cada leitura comia uma
    # linha do quadro seguinte e aos 41 s a janela estava ~26 quadros atrasada (16/10)
    y0 = faixa[0] - faixa[0] % 2
    hb = faixa[1] - y0
    hb += hb % 2
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(video), "-vf",
                          f"fps={fps_saida},crop={W}:{hb}:0:{y0}:exact=1",
                          "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
    ext = []
    while True:
        buf = p.stdout.read(W * hb * 3)
        if len(buf) < W * hb * 3:
            break
        cols = np.where(_letra_amarela(np.frombuffer(buf, np.uint8).reshape(hb, W, 3)).sum(axis=0) > 0)[0]
        ext.append([int(cols.min()), int(cols.max())] if len(cols) > 6 else None)
    p.wait()
    out = []
    for i in range(len(ext)):
        jan = [e for e in ext[max(0, i - 7):i + 8] if e]
        out.append([min(a for a, _ in jan), max(b for _, b in jan)] if jan else None)
    return out


VERSAO = 3


def detectar(video, parceiro="kaijinre", fps_saida=30):
    """{"W","H","fps","dur","faixa":[y0,y1]|None, "legenda_x":[[x0,x1]|None por quadro de saída],
        "marca": {"x","w","h","trilha":[[t,y],...]}|None}."""
    video = Path(video)
    cache = video.with_suffix(".parceiro.json")
    try:
        d = json.loads(cache.read_text(encoding="utf-8"))
        if d.get("tamanho") == video.stat().st_size and d.get("versao") == VERSAO and d.get("fps_saida") == fps_saida:
            return d
    except (OSError, ValueError):
        pass
    W, H, fps, dur = _dims(video)
    det = {"versao": VERSAO, "tamanho": video.stat().st_size, "W": W, "H": H, "fps": fps, "dur": dur,
           "fps_saida": fps_saida, "faixa": _faixa_legenda(video, W, H), "legenda_x": None, "marca": None}
    if det["faixa"]:
        det["legenda_x"] = _extensoes_legenda(video, W, det["faixa"], fps_saida)
    cfg = MOLDE.get(parceiro)
    molde = cv2.imread(str(CONFIG / cfg["arquivo"]), cv2.IMREAD_GRAYSCALE) if cfg else None
    if molde is not None:
        w, h = int(W * ANALISE_S), int(H * ANALISE_S)
        tpl = molde.astype(np.float32) / 255.0   # molde feito com o vídeo em 360 px de largura
        if w != 360:
            tpl = cv2.resize(tpl, None, fx=w / 360.0, fy=w / 360.0, interpolation=cv2.INTER_AREA)
        x0s, x1s = int(w * 0.22), int(w * 0.78)
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(video), "-vf",
                              f"fps={AMOSTRA_FPS},scale={w}:{h},format=gray", "-f", "rawvideo", "-"],
                             stdout=subprocess.PIPE)
        pts, k = [], 0
        while True:
            buf = p.stdout.read(w * h)
            if len(buf) < w * h:
                break
            A = _alfa(np.frombuffer(buf, np.uint8).reshape(h, w))[:, x0s:x1s]
            r = cv2.matchTemplate(A, tpl, cv2.TM_CCOEFF_NORMED)
            cx = (np.arange(r.shape[1]) + x0s + tpl.shape[1] / 2) / w
            r[:, np.abs(cx - 0.5) > 0.06] = -1   # a marca deles é centralizada
            _, v, _, loc = cv2.minMaxLoc(r)
            pts.append((k / AMOSTRA_FPS, loc[1] / h, v))
            k += 1
        p.wait()
        if len(pts) >= 8:
            t = np.array([q[0] for q in pts])
            y = np.array([q[1] for q in pts])
            med = np.array([np.median(y[max(0, i - 4):i + 5]) for i in range(len(y))])
            ok = np.abs(y - med) < 0.025      # trilha suave: o que foge dela é erro da busca
            if ok.sum() >= len(y) * 0.5:
                det["marca"] = {"x": cfg["x"], "w": cfg["w"], "h": cfg["h"],
                                "trilha": [[round(float(a), 2), round(float(b), 4)] for a, b in zip(t[ok], y[ok])],
                                "descartados": int((~ok).sum())}
    try:
        cache.write_text(json.dumps(det, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass
    logging.info(f"[parceiro] legenda deles: {det['faixa']} | marca: "
                 f"{'%d pontos' % len(det['marca']['trilha']) if det['marca'] else 'não achada'}")
    return det


def _nossa_marca(handle, altura_px):
    """RGBA da nossa marca no estilo da deles: serifada em negrito, branca semitransparente, sombra leve."""
    from PIL import Image, ImageDraw, ImageFont
    fonte = ImageFont.truetype(FONTE_MARCA, max(12, int(altura_px * 0.8)))
    l, t, r, b = ImageDraw.Draw(Image.new("RGBA", (4, 4))).textbbox((0, 0), handle, font=fonte, stroke_width=2)
    img = Image.new("RGBA", (r - l + 8, b - t + 8), (0, 0, 0, 0))
    ImageDraw.Draw(img).text((4 - l, 4 - t), handle, font=fonte, fill=(255, 255, 255, 150),
                             stroke_width=2, stroke_fill=(0, 0, 0, 70))
    a = np.array(img)
    return cv2.cvtColor(a, cv2.COLOR_RGBA2BGRA)


def _colar(frame, rgba, cx, cy):
    h, w = rgba.shape[:2]
    x0, y0 = int(cx - w / 2), int(cy - h / 2)
    fx0, fy0, fx1, fy1 = max(0, x0), max(0, y0), min(frame.shape[1], x0 + w), min(frame.shape[0], y0 + h)
    if fx1 <= fx0 or fy1 <= fy0:
        return
    sub = rgba[fy0 - y0:fy1 - y0, fx0 - x0:fx1 - x0]
    a = sub[..., 3:4].astype(np.float32) / 255.0
    roi = frame[fy0:fy1, fx0:fx1].astype(np.float32)
    frame[fy0:fy1, fx0:fx1] = (roi * (1 - a) + sub[..., :3].astype(np.float32) * a).astype(np.uint8)


def _borrar(frame, x0, y0, x1, y1, escurecer=0.0, sigma=8):
    x0, y0, x1, y1 = max(0, x0), max(0, y0), min(frame.shape[1], x1), min(frame.shape[0], y1)
    if x1 - x0 < 4 or y1 - y0 < 4:
        return
    roi = frame[y0:y1, x0:x1]
    bl = cv2.GaussianBlur(roi, (0, 0), sigma)
    if escurecer:
        bl = (bl.astype(np.float32) * (1 - escurecer)).astype(np.uint8)
    # borda suave: o retângulo não fica "recortado"
    m = np.zeros(roi.shape[:2], np.float32)
    m[3:-3, 3:-3] = 1
    m = cv2.GaussianBlur(m, (0, 0), 2.5)[..., None]
    frame[y0:y1, x0:x1] = (roi * (1 - m) + bl * m).astype(np.uint8)


FONTE_TARJA = r"C:\Windows\Fonts\impact.ttf"
TARJA_Y = (0.04, 0.04)  # folga em cima/embaixo da faixa da legenda deles (fração da altura)


def _tarja(W, H, faixa, titulo, folga=TARJA_Y, leg_x=None):
    """(BGRA, y0) da TARJA BRANCA com o título chamativo em preto (dono 17/10: "um desses canais coloca uma tarja
    branca em cima da legenda e um título extremamente chamativo, tipo 'essa garota fez isso'"). Cobre a faixa da
    legenda deles com folga; título em até 2 linhas, o maior que couber. leg_x = [x0, x1] da legenda deles: a tarja
    fica só um pouco mais larga que ela."""
    from PIL import Image, ImageDraw, ImageFont
    y0 = max(0, int(faixa[0] - folga[0] * H))
    y1 = min(H, int(faixa[1] + folga[1] * H))
    # teto de 72% (dono 26/10: "muito grande, deixar menos larga"; era 80%) — o fx_clips corta 5% de cada lado e o
    # movimento de câmera dá zoom de até 12%: mais que isso o título saía cortado nas pontas (17/10, "...ARCISISTA").
    # Com a largura da legenda deles medida: ela + 3% de cada lado (mín. 45% pro título caber)
    try:  # 27/10: limites que o MELHORADOR dos Cortes pode ajustar (bin\cortes_ajustes.json), dentro de faixas fixas
        aj = json.loads((Path(__file__).resolve().parent / "cortes_ajustes.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        aj = {}
    teto = min(0.80, max(0.50, float(aj.get("tarja_largura_max", 0.72))))
    letra = min(0.62, max(0.38, float(aj.get("tarja_letra", 0.50))))
    # 27/10 (dono: "a tarja tem que cobrir EXATAMENTE a área da legenda"): largura medida + 2% de cada lado
    frac = teto if not leg_x else max(0.30, min(teto, (leg_x[1] - leg_x[0]) + 0.04))
    larg, alt = int(W * frac), y1 - y0
    img = Image.new("RGBA", (larg, alt), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, larg - 1, alt - 1], radius=int(alt * 0.18), fill=(255, 255, 255, 255))
    palavras = titulo.upper().split()
    melhor = None
    for tam in range(int(alt * letra), 10, -2):  # 26/10: letra menor (era 62% da altura da tarja)
        f = ImageFont.truetype(FONTE_TARJA, tam)
        for corte in ([len(palavras)] + list(range(1, len(palavras)))):
            linhas = [" ".join(palavras[:corte]), " ".join(palavras[corte:])]
            linhas = [l for l in linhas if l]
            bbs = [d.textbbox((0, 0), l, font=f) for l in linhas]
            lw = max(b[2] - b[0] for b in bbs)
            lh = sum(b[3] - b[1] for b in bbs) + int(tam * 0.15) * (len(linhas) - 1)
            if lw <= larg * 0.86 and lh <= alt * 0.84:
                melhor = (f, linhas, bbs, lh, tam)
                break
        if melhor:
            break
    if melhor:
        f, linhas, bbs, lh, tam = melhor
        y = (alt - lh) / 2
        for l, b in zip(linhas, bbs):
            d.text(((larg - (b[2] - b[0])) / 2 - b[0], y - b[1]), l, font=f, fill=(10, 10, 10, 255))
            y += (b[3] - b[1]) + int(tam * 0.15)
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGBA2BGRA), y0


def modo_cobertura(video):
    """"delogo" ou "tarja" (cortes_ajustes cobertura_legenda; "ab" = sorteio fixo por vídeo, teste T2)."""
    try:
        _aj = json.loads((Path(__file__).resolve().parent / "cortes_ajustes.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        _aj = {}
    cobertura = os.environ.get("CORTES_COBERTURA") or _aj.get("cobertura_legenda") or "tarja"
    if cobertura == "ab":
        import hashlib
        cobertura = "delogo" if int(hashlib.md5(str(video).encode()).hexdigest(), 16) % 2 else "tarja"
    return cobertura


def cobrir(video, saida, handle, det=None, fps_saida=30, titulo=None):
    """Cobre a legenda deles (só a largura das palavras de cada quadro) e a marca (só o retângulo dela, com a nossa
    marca escrita por cima). Com `titulo`: em vez do borrão, TARJA BRANCA fixa com o título sobre a faixa da legenda
    (a nossa legenda vai pra outro lugar). Devolve Path(saida) ou None."""
    det = det or detectar(video, fps_saida=fps_saida)
    W, H = det["W"], det["H"]
    # 27/10 (dono: "a tarja ainda está grande" no Short do @kaijinre): o caminho antigo também do TAMANHO EXATO — largura
    # = palavras deles medidas quadro a quadro (90% dos quadros cabem), folga mínima (era 4% em cima e embaixo)
    xs = [x for x in (det.get("legenda_x") or []) if x]
    lx = None
    if xs:
        lx = [float(np.percentile([x[0] for x in xs], 5)) / W, float(np.percentile([x[1] for x in xs], 95)) / W]
    # 28/10 (dona: tarja branca "ainda aparecendo"): este caminho antigo também segue cobertura_legenda="delogo"
    delogo = None
    if det.get("faixa") and modo_cobertura(video) == "delogo":
        titulo = None
        x0 = max(2, int((lx[0] if lx else 0.05) * W) - 6)
        x1 = min(W - 3, int((lx[1] if lx else 0.95) * W) + 6)
        y0, y1 = max(2, int(det["faixa"][0]) - 4), min(H - 3, int(det["faixa"][1]) + 4)
        if (y1 - y0) <= DELOGO_MAX_H * H:
            delogo = f"delogo=x={x0}:y={y0}:w={x1 - x0}:h={y1 - y0}"
            logging.info(f"[parceiro] cobertura DELOGO (caminho antigo): {delogo}")
        else:  # 30/10: faixa alta demais = "vidro derretido" na tela toda; a nossa legenda entra em cima da deles
            logging.warning(f"[parceiro] faixa deles alta demais ({(y1 - y0) / H:.0%} da tela) — sem delogo")
    tarja = _tarja(W, H, det["faixa"], titulo, (0.008, 0.008), leg_x=lx) if titulo and det.get("faixa") else None
    leg_x = [] if delogo else (det.get("legenda_x") or [])
    marca = det.get("marca")
    if marca:
        tt = np.array([p[0] for p in marca["trilha"]])
        yy = np.array([p[1] for p in marca["trilha"]])
        mw, mh, mx = int(marca["w"] * W), int(marca["h"] * H), int(marca["x"] * W)
        nossa = _nossa_marca(handle, mh) if handle else None
    faixa = det.get("faixa")
    leitor = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(video), "-vf",
                               f"fps={fps_saida}" + (f",{delogo}" if delogo else ""), "-f", "rawvideo",
                               "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
    escritor = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                                 "-r", str(fps_saida), "-i", "-", "-i", str(video), "-map", "0:v", "-map", "1:a?",
                                 "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
                                 "-c:a", "copy", "-shortest", str(saida)], stdin=subprocess.PIPE)
    n = 0
    try:
        while True:
            buf = leitor.stdout.read(W * H * 3)
            if len(buf) < W * H * 3:
                break
            f = np.frombuffer(buf, np.uint8).reshape(H, W, 3).copy()
            t = n / fps_saida
            if tarja is None and faixa and n < len(leg_x) and leg_x[n]:  # legenda deles: só onde tem palavra (±0,23 s)
                y0, y1 = faixa
                x0, x1 = leg_x[n]
                _borrar(f, x0 - 20, y0 - 4, x1 + 20, y1 + 4, escurecer=0.35, sigma=10)
            if marca:
                my = int(float(np.interp(t, tt, yy)) * H)
                _borrar(f, mx - 8, my - 6, mx + mw + 8, my + mh + 6, sigma=7)
                if nossa is not None:
                    _colar(f, nossa, mx + mw / 2, my + mh / 2)
            # tarja por ÚLTIMO (dono 22/10: a nossa @, que anda junto com a marca deles, parava NA FRENTE da tarja e o
            # borrão embaçava o título): ao cruzar a faixa a marca passa POR TRÁS da tarja, que já esconde a deles
            if tarja is not None:
                _colar(f, tarja[0], W / 2, tarja[1] + tarja[0].shape[0] / 2)
            escritor.stdin.write(f.tobytes())
            n += 1
    finally:
        leitor.stdout.close()
        leitor.wait()
        escritor.stdin.close()
        escritor.wait()
    ok = escritor.returncode == 0 and Path(saida).exists() and Path(saida).stat().st_size > 10000
    logging.info(f"[parceiro] coberto: {n} quadros -> {Path(saida).name} ({'ok' if ok else 'FALHOU'})")
    return Path(saida) if ok else None


def centro_legenda_saida(det, crop=0.90):
    """Fração da altura, NO VÍDEO FINAL, do centro da linha da legenda deles (o fx_clips corta 10% e reescala) —
    vai no SUB_Y_CENTER pra nossa legenda cair em cima da placa que cobriu a deles."""
    if not det.get("faixa"):
        return None
    c = (det["faixa"][0] + det["faixa"][1]) / 2 / det["H"]
    return round((c - (1 - crop) / 2) / crop, 4)


# ─── canais NOVOS de parceiro (17/10): cobertura pela configuração do canal ──────────────────────────────────────
# config/parceiro.json "fontes"[i]["cobertura"] (frações da ALTURA do vídeo-fonte, medidas nas amostras):
#   "legenda": [y0, y1] da legenda palavra-a-palavra deles, ou "auto" (visão: anime_hardsub_detect)
#   "titulo_topo": [y0, y1] do título/cabeçalho que eles põem no topo (muitos canais de dorama) — a NOSSA tarja vai
#                  em cima dele; aí a legenda deles vira placa borrada e a NOSSA legenda entra em cima dela
#   "apagar": [[x0, y0, x1, y1], ...] marcas d'água, logos, avisos ("No were harmed...") — borrados o vídeo inteiro;
#             ou "auto" (_marcas_fixas)
#   "marca_y": altura da NOSSA @ (padrão 0.30)
def _faixa_px(fr, H):
    return [max(0, int(fr[0] * H)), min(H, int(fr[1] * H))]


def _marcas_fixas(video, W, H, dur, n=16):
    """(marcas, candidatas): retângulos [x0,y0,x1,y1] px de bordas que ficam no MESMO lugar nos quadros (o conteúdo
    mexe, a marca não). Linhas compridas (borda do 16:9 no meio da tela) ficam de fora. Candidata = borda em ≥70% dos
    quadros (serve pra achar a linha da legenda deles); marca = candidata com ≥10% dos pixels em ≥90% dos quadros —
    o traço denso de anime passa dos 70% por acaso no meio da tela e virava borrão (18/10: logo real 28%, acaso 0%)."""
    w, h = W // 2, H // 2
    cont, k = np.zeros((h, w), np.int32), 0
    for i in range(n):
        t = dur * (0.05 + 0.9 * i / (n - 1))
        r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", str(video), "-frames:v", "1",
                            "-vf", f"scale={w}:{h},format=gray", "-f", "rawvideo", "-"], capture_output=True, timeout=60)
        if len(r.stdout) < w * h:
            continue
        cont += cv2.dilate(cv2.Canny(np.frombuffer(r.stdout[:w * h], np.uint8).reshape(h, w), 50, 130),
                           np.ones((3, 3), np.uint8)) > 0
        k += 1
    if k < 4:
        return [], []
    # 70% e não 100%: num quadro de fundo claro ou de transição a marca some e o AND zerava tudo (OpusClip, 18/10)
    fixo = cont >= 0.7 * k
    forte = cont >= 0.9 * k
    m = cv2.morphologyEx(fixo.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((9, 15), np.uint8))
    _, lab, st, _ = cv2.connectedComponentsWithStats(m)
    p = int(0.012 * w)
    marcas, cands = [], []
    for i, (x, y, bw, bh, area) in enumerate(st[1:], 1):
        if area < w * h * 0.0004 or bw > w * 0.6 or bh > h * 0.25 or bh < h * 0.012 or bw / bh > 25:
            continue
        caixa = [int(max(0, (x - p) * 2)), int(max(0, (y - p) * 2)),
                 int(min(W, (x + bw + p) * 2)), int(min(H, (y + bh + p) * 2))]
        cands.append(caixa)
        if forte[lab == i].mean() >= 0.1:
            marcas.append(caixa)
    return marcas, cands


# ─── texto sobreposto: legenda deles x título/marca FIXOS (25/10) ─────────────────────────────────────────────────
# Dono 25/10 (Filme Noturno, fonte do cineverso): a visão chamou de "legenda" o TÍTULO amarelo fixo do topo — a tarja
# foi pra lá e a legenda deles ficou à mostra embaixo (23 de 300 detecções de 18-24/10 caíram no topo). Legenda é a
# linha que fica na MESMA altura e MUDA de um quadro pro outro; título/marca é o mesmo desenho em todos os quadros.
TXT_AMOSTRAS = 48
TXT_LARG = 360


def _quadros_texto(video, W, H, dur, n=TXT_AMOSTRAS, w=TXT_LARG):
    """n quadros espalhados pelo vídeo, em BGR com w de largura."""
    h = int(round(H * w / W / 2) * 2)
    out = []
    if dur <= 240:  # Short: 1 passada só (o fps escolhe os quadros) sai mais rápido que n buscas
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(video), "-vf",
                              f"fps={n / max(dur, 1.0):.5f},scale={w}:{h}", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                             stdout=subprocess.PIPE)
        try:
            while len(out) < n + 2:
                buf = p.stdout.read(w * h * 3)
                if len(buf) < w * h * 3:
                    break
                out.append(np.frombuffer(buf, np.uint8).reshape(h, w, 3))
        finally:
            p.stdout.close()
            p.wait()
    else:
        for i in range(n):
            t = dur * (0.03 + 0.94 * i / (n - 1))
            r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", str(video), "-frames:v", "1",
                                "-vf", f"scale={w}:{h}", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                               capture_output=True, timeout=60)
            if len(r.stdout) >= w * h * 3:
                out.append(np.frombuffer(r.stdout[:w * h * 3], np.uint8).reshape(h, w, 3))
    return out, w, h


def _letras(f):
    """Letra de legenda/título: pixel bem claro (branco ou cor forte) colado num contorno preto."""
    mx = f.max(axis=2)
    mn = f.min(axis=2)
    claro = (mx >= 200) & ((mn >= 170) | (mx.astype(np.int16) - mn >= 110))
    perto = cv2.dilate((mx <= 60).astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    return (claro & perto).astype(np.uint8)


def _caixa_justa(video, W, H, dur, faixa):
    """27/10 (dono: "a tarja/o apagado tem que cobrir EXATAMENTE a área da legenda; o dos longos é tão sutil que quase
    não dá pra perceber"): caixa [y0, y1] e [x0, x1] (frações) das palavras da legenda deles DENTRO da faixa da visão,
    juntando vários quadros (a legenda muda de largura). None se não achar palavra em >= 3 quadros (aí vale a faixa)."""
    # resolução maior que a da análise (360 px): legenda pequena de vídeo deitado virava ruído
    fr, w, h = _quadros_texto(video, W, H, dur, n=24, w=min(W, 960))
    if not fr:
        return None
    a, b = max(0, int(faixa[0] * h)), min(h, int(faixa[1] * h))
    caixas, n = [], 0
    for f in fr:
        m = _letras(f)
        m[:a], m[b:] = 0, 0
        cs = [c for c in _palavras(m) if a <= (c[1] + c[3]) / 2 <= b]
        if cs:
            # só a LINHA principal (mais largura de palavras): texto do desenho na mesma faixa não entra
            alt = float(np.median([c[3] - c[1] for c in cs]))
            grupos = []
            for c in sorted(cs, key=lambda c: (c[1] + c[3]) / 2):
                meio = (c[1] + c[3]) / 2
                if grupos and abs(meio - grupos[-1][0]) <= 0.6 * alt:
                    grupos[-1][1].append(c)
                else:
                    grupos.append([meio, [c]])
            princ = max(grupos, key=lambda x: sum(c[2] - c[0] for c in x[1]))
            # 27/10 (de73a8): legenda que quebra em 2 linhas ("diretamente no cé / rebro") — a linha colada acima/abaixo
            # da principal é a mesma legenda; só ela ficava fora do apagado
            g = [c for meio, cs_ in grupos if abs(meio - princ[0]) <= 1.8 * alt for c in cs_]
            n += 1
            caixas.append([min(c[0] for c in g), min(c[1] for c in g), max(c[2] for c in g), max(c[3] for c in g)])
    if n < 3:
        return None
    x0 = float(np.percentile([c[0] for c in caixas], 3)) / w
    x1 = float(np.percentile([c[2] for c in caixas], 97)) / w
    y0 = float(np.percentile([c[1] for c in caixas], 3)) / h  # 27/10: a 2ª linha aparece em poucos quadros (era 10/90)
    y1 = float(np.percentile([c[3] for c in caixas], 97)) / h
    return [round(y0, 3), round(y1, 3)], [round(x0, 3), round(x1, 3)]


# ───────── delogo que ACOMPANHA a legenda no tempo (13/11, pedido do chat do D:) ─────────
# A cobertura "delogo" era UMA caixa para o vídeo inteiro: a largura vinha da legenda MAIS LARGA (percentil 97 de todos
# os quadros, _caixa_justa) ou, sem medida (leg_x None), de 5% a 95% da tela — e a altura, da união das 2 linhas. Em 18
# de 86 Shorts a faixa pegava a largura toda; em fundo com textura vira listras ("vidro derretido") o tempo inteiro,
# mesmo quando a legenda deles é uma palavra curta ou nem está na tela.
# Agora mede as palavras dentro da faixa várias vezes por segundo e monta um delogo por TRECHO (enable='between(t,…)'),
# com a largura e a altura daquele trecho; sem legenda na tela = sem delogo naquele instante.
# PARCEIRO_DELOGO_TEMPO=0 volta à caixa única.
DELOGO_FPS = 5            # amostras por segundo
DELOGO_MAX_TRECHOS = 80   # teto de filtros delogo encadeados (acima disso junta os vizinhos)


def _extensoes_no_tempo(video, W, H, faixa, fps=DELOGO_FPS, larg=720):
    """Caixa das palavras da legenda deles em cada amostra do vídeo: lista de None | (x0, x1, y0, y1) em FRAÇÃO do
    quadro, uma a cada 1/fps s. faixa = [y0, y1] em fração (onde procurar). Lê só o recorte da faixa (rápido)."""
    w = int(min(W, larg) // 2 * 2)
    esc = w / W
    h_ref = H * esc
    ya = max(0, int(faixa[0] * H) - int(faixa[0] * H) % 2)
    hb = min(H, int(round(faixa[1] * H))) - ya
    hb += hb % 2
    hb = min(hb, H - ya - (H - ya) % 2)
    if hb < 8:
        return []
    hs = int(round(hb * esc / 2) * 2) or 2
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(video), "-vf",
                          f"fps={fps},crop={W}:{hb}:0:{ya}:exact=1,scale={w}:{hs}",
                          "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
    out = []
    try:
        while True:
            buf = p.stdout.read(w * hs * 3)
            if len(buf) < w * hs * 3:
                break
            cs = _palavras(_letras(np.frombuffer(buf, np.uint8).reshape(hs, w, 3)), h_ref=h_ref)
            if not cs:
                out.append(None)
                continue
            out.append((min(c[0] for c in cs) / w, max(c[2] for c in cs) / w,
                        (ya + min(c[1] for c in cs) / esc) / H, (ya + max(c[3] for c in cs) / esc) / H))
    finally:
        p.stdout.close()
        p.wait()
    return out


def _trechos_delogo(amostras, W, H, fps=DELOGO_FPS, margem_x=6, margem_y=4, max_h=DELOGO_MAX_H,
                    max_trechos=DELOGO_MAX_TRECHOS, salto=0.06):
    """amostras (de _extensoes_no_tempo) -> [{"t0","t1","x","y","w","h"}] em segundos e pixels: um delogo por trecho
    em que a legenda deles está na tela, do tamanho dela NAQUELE trecho. Função pura (sem vídeo).
    - a letra entra animada (num quadro isolado a palavra aparece pela metade): cada amostra vale a união com as
      vizinhas (±1 amostra), e o trecho começa/termina 1 amostra antes/depois;
    - buraco de 1 amostra não quebra o trecho; mudança de largura maior que `salto` (fração da tela) abre outro;
    - trecho mais alto que max_h da tela fica SEM delogo (viraria listras), como já era a regra da caixa única."""
    n = len(amostras)
    passo = 1.0 / fps
    suave = []
    for i in range(n):
        jan = [a for a in amostras[max(0, i - 1):i + 2] if a]
        suave.append((min(a[0] for a in jan), max(a[1] for a in jan), min(a[2] for a in jan), max(a[3] for a in jan))
                     if amostras[i] or len(jan) == 2 else None)
    trechos, atual = [], None
    for i, a in enumerate(suave):
        if a is None:
            atual = None
            continue
        if atual and (abs(a[0] - atual["cx"][0]) > salto or abs(a[1] - atual["cx"][1]) > salto):
            atual = None  # outra legenda (bem mais larga ou mais curta): caixa própria
        if atual is None:
            atual = {"i0": i, "i1": i, "cx": [a[0], a[1]], "cy": [a[2], a[3]]}
            trechos.append(atual)
        else:
            atual["i1"] = i
            atual["cx"] = [min(atual["cx"][0], a[0]), max(atual["cx"][1], a[1])]
            atual["cy"] = [min(atual["cy"][0], a[2]), max(atual["cy"][1], a[3])]
    while len(trechos) > max_trechos:  # filtro demais: junta os dois vizinhos mais próximos no tempo
        k = min(range(len(trechos) - 1), key=lambda j: trechos[j + 1]["i0"] - trechos[j]["i1"])
        a, b = trechos[k], trechos.pop(k + 1)
        a["i1"] = b["i1"]
        a["cx"] = [min(a["cx"][0], b["cx"][0]), max(a["cx"][1], b["cx"][1])]
        a["cy"] = [min(a["cy"][0], b["cy"][0]), max(a["cy"][1], b["cy"][1])]
    out = []
    for t in trechos:
        x0, x1 = max(2, int(t["cx"][0] * W) - margem_x), min(W - 3, int(t["cx"][1] * W) + margem_x)
        y0, y1 = max(2, int(t["cy"][0] * H) - margem_y), min(H - 3, int(t["cy"][1] * H) + margem_y)
        if x1 - x0 < 8 or y1 - y0 < 4 or (y1 - y0) > max_h * H:
            continue
        out.append({"t0": round(max(0.0, (t["i0"] - 1) * passo), 2), "t1": round((t["i1"] + 2) * passo, 2),
                    "x": x0, "y": y0, "w": x1 - x0, "h": y1 - y0})
    for a, b in zip(out, out[1:]):  # vizinhos não se sobrepõem no tempo (2 delogos no mesmo quadro = borrão dobrado)
        if b["t0"] < a["t1"]:
            meio = round((a["t1"] + b["t0"]) / 2, 2)
            a["t1"], b["t0"] = meio, meio
    return out


def _filtro_delogo(trechos):
    """Cadeia de filtros do ffmpeg: um delogo por trecho, ligado só no intervalo dele."""
    return ",".join(f"delogo=x={t['x']}:y={t['y']}:w={t['w']}:h={t['h']}:enable='between(t,{t['t0']},{t['t1']})'"
                    for t in trechos)


def delogo_no_tempo(video, W, H, faixa_px, leg_x=None):
    """Filtro delogo acompanhando a legenda deles, ou None (não mediu palavra nenhuma / desligado: vale a caixa única).
    faixa_px = [y0, y1] da faixa da legenda (pixels); procura numa folga de meia faixa pra cima e pra baixo, e, se
    leg_x veio medido, só dentro dele (texto do desenho ao lado não entra)."""
    if os.environ.get("PARCEIRO_DELOGO_TEMPO", "1") == "0":
        return None
    alt = faixa_px[1] - faixa_px[0]
    faixa = [max(0.0, (faixa_px[0] - 0.5 * alt) / H), min(1.0, (faixa_px[1] + 0.5 * alt) / H)]
    am = _extensoes_no_tempo(video, W, H, faixa)
    if leg_x:
        am = [None if a is None or a[1] < leg_x[0] - 0.03 or a[0] > leg_x[1] + 0.03 else a for a in am]
    com = sum(1 for a in am if a)
    if com < 3:
        return None
    tr = _trechos_delogo(am, W, H)
    if not tr:
        return None
    larg = sorted(t["w"] / W for t in tr)
    logging.info(f"[parceiro] delogo no tempo: {len(tr)} trecho(s), legenda na tela em {com}/{len(am)} amostras, "
                 f"largura mediana {larg[len(larg) // 2]:.0%} (máx. {larg[-1]:.0%})")
    return _filtro_delogo(tr)


MARCA_YS = (0.30, 0.24, 0.36, 0.18, 0.64)  # alturas possíveis da nossa @ (a 1ª é a de sempre)


def _y_marca(video, W, H, dur, evitar, alt):
    """27/10 (júri + melhorador: "@ do canal em cima do rosto/olhos"): altura da @ com MENOS detalhe (bordas) na faixa
    dela ao longo do vídeo — rosto, olho e ação têm muita borda; céu/fundo, pouca. `evitar` = [(y0, y1)] px (tarja,
    legenda). Empate (diferença < 15%) fica a mais perto de 30%. Devolve y (px) do centro."""
    fr, w, h = _quadros_texto(video, W, H, dur, n=16)
    if not fr:
        return int(MARCA_YS[0] * H)
    meia = max(2, int(alt / 2 * h / H)) + 2
    notas = []
    for f in MARCA_YS:
        yc = int(f * H)
        if any(yc + alt > a and yc - alt < b for a, b in evitar):
            continue
        c = int(f * h)
        x0, x1 = int(w * 0.25), int(w * 0.75)
        bordas = [cv2.Canny(cv2.cvtColor(q[max(0, c - meia):c + meia, x0:x1], cv2.COLOR_BGR2GRAY), 80, 160).mean()
                  for q in fr]
        notas.append((float(np.mean(bordas)), f))
    if not notas:
        return int(MARCA_YS[0] * H)
    menor = min(n for n, _f in notas)
    f = next(f for n, f in notas if n <= menor * 1.15)  # na ordem de MARCA_YS: a de sempre ganha o empate
    logging.info(f"[parceiro] @ do canal em {f:.2f} da altura (bordas por altura: "
                 f"{', '.join(f'{ff:.2f}={n:.1f}' for n, ff in notas)})")
    return int(f * H)


def _palavras(m, h_ref=None):
    """Caixas [x0,y0,x1,y1] com forma de palavra (altura de letra, mais larga que alta) na máscara de letras.
    h_ref: altura do quadro INTEIRO quando m é só um recorte (a régua de "altura de letra" é do quadro, não do recorte)."""
    h, w = m.shape
    h = h_ref or h
    j = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (7, 3)))
    _n, _lab, st, _c = cv2.connectedComponentsWithStats(j)
    out = []
    for x, y, bw, bh, _a in st[1:]:
        if not (0.010 * h <= bh <= 0.07 * h) or bw < 0.9 * bh or bw < 0.025 * w:
            continue
        if 0.08 <= m[y:y + bh, x:x + bw].mean() <= 0.85:
            out.append((int(x), int(y), int(x + bw), int(y + bh)))
    return out


def _cruza(a, b):
    return max(0.0, min(a[1], b[1]) - max(a[0], b[0]))


def _texto_sobreposto(video, W, H, dur):
    """Faixas de texto sobreposto do vídeo-fonte (frações da altura). Devolve None (não leu quadros) ou
    {"legenda": [y0,y1] | None — a linha que MUDA (só quando a leitura é segura: fina, centralizada, presente),
     "fixos": [{"y","x","fundo"}] — título/marca iguais em todos os quadros; fundo = cor do letterbox em volta (BGR)
              ou None (texto em cima da imagem: aí não se mexe),
     "recusar": f([y0,y1]) -> True se essa faixa é texto FIXO e não legenda (pra conferir a resposta da visão),
     "resumo": texto pro log}."""
    fr, w, h = _quadros_texto(video, W, H, dur)
    N = len(fr)
    if N < 8:
        return None
    L = [_letras(f) for f in fr]
    P = [_palavras(m) for m in L]
    linhas = np.zeros((N, h), bool)
    for i, cs in enumerate(P):
        for _x0, y0, _x1, y1 in cs:
            linhas[i, y0:y1] = True
    sm = np.convolve(linhas.mean(axis=0), np.ones(3) / 3, mode="same")
    on = sm >= max(0.15, 0.35 * float(sm.max()))
    blocos, y = [], 0
    while y < h:
        if on[y]:
            s = y
            while y < h and on[y]:
                y += 1
            if blocos and s - blocos[-1][1] <= int(0.012 * h):
                blocos[-1][1] = y
            else:
                blocos.append([s, y])
        y += 1
    faixas = []
    for a, b in blocos:
        if b - a < 0.008 * h:
            continue
        cs = [[c for c in P[i] if a <= (c[1] + c[3]) / 2 <= b] for i in range(N)]
        com = [i for i in range(N) if cs[i]]
        ious = []
        for i, k in zip(com, com[1:]):
            A, B = L[i][a:b] > 0, L[k][a:b] > 0
            u = (A | B).sum()
            if u:
                ious.append((A & B).sum() / u)
        todos = [c for lst in cs for c in lst]
        lin = [abs((min(c[0] for c in cs[i]) + max(c[2] for c in cs[i])) / 2 / w - 0.5) for i in com]
        fx = {"px": [a, b], "y": [round(float(np.percentile([c[1] for c in todos], 5)) / h, 3),
                                 round(float(np.percentile([c[3] for c in todos], 95)) / h, 3)],
              "x": [round(min(c[0] for c in todos) / w, 3), round(max(c[2] for c in todos) / w, 3)],
              "pres": round(len(com) / N, 2), "pico": round(float(sm[a:b].max()), 2),
              "iou": round(float(np.median(ious)) if ious else 0.0, 2),
              "dx": round(float(np.median(lin)), 3) if lin else 1.0}
        fx["tipo"] = "fixo" if fx["iou"] >= 0.55 and fx["pres"] >= 0.5 else "muda"
        faixas.append(fx)

    # legenda segura: linha que muda, presente, fina (até 2 linhas) e centralizada — senão quem decide é a visão
    boas = [f for f in faixas if f["tipo"] == "muda" and f["iou"] < 0.45 and f["pres"] >= 0.35 and f["pico"] >= 0.5
            and f["dx"] <= 0.08 and f["y"][1] - f["y"][0] <= 0.12]
    legenda = legenda_x = None
    # 26/10 (dono: tarja no lugar errado): legenda fica embaixo — faixa no topo (centro < 30%) só se não houver outra
    baixo = [f for f in boas if (f["y"][0] + f["y"][1]) / 2 >= 0.30]
    boas = baixo or boas
    if boas:
        best = max(boas, key=lambda f: f["pres"] * f["pico"] * (1 - f["iou"]))
        legenda_x = list(best["x"])
        a, b = best["px"]
        tops, bots = [], []
        for cs in P:  # legenda em 2 linhas: junta as palavras coladas em cima/embaixo da linha principal
            g = [c for c in cs if a <= (c[1] + c[3]) / 2 <= b]
            if not g:
                continue
            alt = float(np.median([c[3] - c[1] for c in g]))
            for _ in range(3):
                t, u = min(c[1] for c in g), max(c[3] for c in g)
                x0, x1 = min(c[0] for c in g), max(c[2] for c in g)
                mais = [c for c in cs if c not in g and 0.6 * alt <= c[3] - c[1] <= 1.6 * alt
                        and x0 - 0.15 * w <= (c[0] + c[2]) / 2 <= x1 + 0.15 * w
                        and (t - 0.8 * alt <= c[3] <= t + 2 or u - 2 <= c[1] <= u + 0.8 * alt)]
                if not mais:
                    break
                g += mais
            tops.append(min(c[1] for c in g))
            bots.append(max(c[3] for c in g))
        # a tarja tem de cobrir TODO quadro (a 2ª linha aparece em ~20% deles): 2º menor topo / 2º maior base
        tops, bots = sorted(tops), sorted(bots)
        k = 1 if len(tops) >= 6 else 0
        legenda = [round(tops[k] / h, 3), round(bots[-1 - k] / h, 3)]
        if legenda[1] - legenda[0] > 0.16:  # juntou coisa da cena
            legenda = [round(float(np.percentile(tops, 10)) / h, 3), round(float(np.percentile(bots, 90)) / h, 3)]
            if legenda[1] - legenda[0] > 0.16:
                legenda = list(best["y"])

    # texto FIXO: as linhas de um mesmo título (até ~3% de vão) viram um bloco só
    blocos_fixos = []
    for f in faixas:
        if f["tipo"] != "fixo":
            continue
        a, b = f["px"]
        cs = [c for lst in P for c in lst if a <= (c[1] + c[3]) / 2 <= b]
        caixa = [min(c[0] for c in cs), min(c[1] for c in cs), max(c[2] for c in cs), max(c[3] for c in cs)]
        if blocos_fixos and caixa[1] - blocos_fixos[-1][3] <= 0.03 * h:
            u = blocos_fixos[-1]
            blocos_fixos[-1] = [min(u[0], caixa[0]), min(u[1], caixa[1]), max(u[2], caixa[2]), max(u[3], caixa[3])]
        else:
            blocos_fixos.append(caixa)
    Ld = None

    def letterbox(x0, y0, x1, y1):
        """(retângulo a pintar, cor) se o texto está em fundo quase preto em TODOS os quadros (letterbox) — o
        retângulo cresce só por linhas escuras, nunca entra na imagem do filme; senão None."""
        nonlocal Ld
        if Ld is None:
            Ld = [cv2.dilate(m, np.ones((7, 7), np.uint8)) > 0 for m in L]
        xa, xb = max(0, x0 - int(0.02 * w)), min(w, x1 + int(0.02 * w))

        def escura(yy):
            if yy < 0 or yy >= h:
                return False
            for q, ld in zip(fr, Ld):
                seg = q[yy, xa:xb].max(axis=1)[~ld[yy, xa:xb]]
                if len(seg) and (seg <= 45).mean() < 0.95:
                    return False
            return True

        if not all(escura(yy) for yy in range(y0, y1)):
            return None
        a, b = y0, y1
        while a > 0 and y0 - a < 3 and escura(a - 1):
            a -= 1
        while b < h and b - y1 < 3 and escura(b):
            b += 1
        px = np.concatenate([q[a:b, xa:xb][~ld[a:b, xa:xb]] for q, ld in zip(fr, Ld)])
        return [xa, a, xb, b], tuple(int(v) for v in np.median(px, axis=0))

    fixos = []
    for x0, y0, x1, y1 in blocos_fixos:
        lb = letterbox(x0, y0, x1, y1)
        fixos.append({"y": [round(y0 / h, 3), round(y1 / h, 3)], "x": [round(x0 / w, 3), round(x1 / w, 3)],
                      "fundo": lb[1] if lb else None,
                      "pintar": [round(lb[0][0] / w, 4), round(lb[0][1] / h, 4), round(lb[0][2] / w, 4),
                                 round(lb[0][3] / h, 4)] if lb else None})

    G = None

    def recusar(fx):
        """True = a faixa [y0,y1] é texto FIXO (título/marca/@), não a legenda deles."""
        nonlocal G
        fixas = [f for f in faixas if f["tipo"] == "fixo"]
        ov_fixo = sum(_cruza(fx, f["y"]) for f in fixas)
        ov_muda = sum(_cruza(fx, f["y"]) for f in faixas if f["tipo"] == "muda" and f["pres"] >= 0.3)
        if ov_fixo >= ov_muda and any(_cruza(fx, f["y"]) >= min(0.4 * (fx[1] - fx[0]), 0.6 * (f["y"][1] - f["y"][0]))
                                      for f in fixas):
            return True
        if ov_muda > 0:
            return False
        # nada achado ali: confere se as linhas da faixa ficam paradas (diferença média entre quadros <= 3 de 255)
        if G is None:
            G = [cv2.cvtColor(q, cv2.COLOR_BGR2GRAY).astype(np.int16) for q in fr]
        a, b = max(0, int(fx[0] * h)), min(h, int(fx[1] * h))
        if b - a < 2:
            return False
        d = np.median(np.array([np.abs(G[i][a:b] - G[i + 1][a:b]).mean(axis=1) for i in range(N - 1)]), axis=0)
        return float((d <= 3.0).mean()) >= 0.6

    def confirma(fx):
        """26/10: a visão diz [y0,y1]; vale só se os pixels acham ali uma linha de texto que MUDA e é centralizada
        (legenda). Devolve ([y0,y1] justo dos pixels, [x0,x1]) ou None (sem legenda = sem tarja)."""
        ok = [f for f in faixas if f["tipo"] == "muda" and f["iou"] < 0.45 and f["pres"] >= 0.3
              and f["dx"] <= 0.1 and f["y"][1] - f["y"][0] <= 0.12 and _cruza(fx, f["y"]) > 0]
        if not ok:
            return None
        return ([min(f["y"][0] for f in ok), max(f["y"][1] for f in ok)],
                [min(f["x"][0] for f in ok), max(f["x"][1] for f in ok)])

    resumo = " ".join(f"{f['tipo']}{f['y']}(pres {f['pres']}, iou {f['iou']}, dx {f['dx']})" for f in faixas) or "nada"
    return {"legenda": legenda, "legenda_x": legenda_x, "fixos": fixos, "recusar": recusar, "confirma": confirma,
            "resumo": f"{resumo} -> legenda {legenda}"}


def cobrir_canal(video, saida, handle, cob, titulo=None, fps_saida=30):
    """Cobre um vídeo de canal parceiro NOVO pela configuração do canal. Devolve {"tarja": [y0,y1] px | None,
    "placa": [y0,y1] px | None, "H": H} (pro anime_auto saber onde pôr a nossa legenda) ou None se falhou."""
    W, H, _fps, _dur = _dims(video)
    cands = []
    if cob.get("apagar") == "auto":
        apagar, cands = _marcas_fixas(video, W, H, _dur)
        logging.info(f"[parceiro] marcas fixas achadas: {apagar} (candidatas: {cands})")
    else:
        apagar = [[int(r[0] * W), int(r[1] * H), int(r[2] * W), int(r[3] * H)] for r in cob.get("apagar") or []]
    leg = cob.get("legenda")
    visao = pixels = False
    leg_x = None  # [x0, x1] da legenda deles (pixels): a tarja só precisa dessa largura
    titulo_auto = None
    topo_fixo = None  # [y0, y1] fração: texto fixo deles no alto que NÃO foi apagado (fica na tela)
    limpar = []  # título fixo deles no letterbox: pintado da cor do fundo (some, e o nosso gancho entra limpo)
    rodape_delogo = []  # 04/11: texto FIXO deles no rodapé por cima da imagem (CTA "se inscreve") — delogo sutil
    if leg == "auto":
        leg = None
        txt = None
        try:
            txt = _texto_sobreposto(video, W, H, _dur)
            if txt:
                logging.info(f"[parceiro] texto sobreposto: {txt['resumo']}")
        except Exception as e:  # noqa: BLE001
            logging.warning(f"[parceiro] leitura do texto sobreposto falhou ({type(e).__name__}: {e})")
        vb = None
        veredito = "falhou"
        try:
            import anime_hardsub_detect as ahd
            for _ in range(2):  # o gateway às vezes volta vazio (18/10)
                b = ahd.detect_hardsub_band(str(video))
                veredito = getattr(ahd, "VEREDITO", "falhou")
                if b:
                    vb = [b[0] - 0.01, b[0] + b[1] + 0.01]
                    break
                if veredito != "falhou":
                    break
        except Exception as e:  # noqa: BLE001
            logging.warning(f"[parceiro] visão da legenda falhou ({type(e).__name__})")
        if veredito != "com":
            # 27/10: a visão OLHOU os 6 quadros e não leu legenda — o detector de pixels não pode criar tarja por cima
            # (falso positivo no Short dos ovos, 26/10 19:00: visão "sem", pixels [0,59, 0,68] -> tarja à toa)
            # 31/10 dona (Short gKErqZ0iuBI, 28/10 21:12: visão "recusou/vazio" 2x, pixels acharam [0.606, 0.675] e o
            # delogo borrou uma faixa sem legenda nenhuma): "só deve ter quando houver uma legenda embaixo" — sem a
            # visão CONFIRMAR que leu legenda, nada é coberto (nem pelos pixels, nem pelas marcas fixas).
            logging.info(f"[parceiro] visão: {'SEM legenda legível' if veredito == 'sem' else 'não respondeu'} -> "
                         "sem cobertura da legenda (pixels e marcas fixas ignorados)")
            txt = dict(txt, legenda=None) if txt else txt
            vb = None
        # 25/10: a visão apontava o título fixo do topo -> recusar(). 27/10: a visão agora só responde com textos LIDOS e
        # DIFERENTES entre quadros (título fixo já sai lá), e o recusar() derrubava legenda real que fica 3-4 s parada
        # em cima de painel parado (pixels viam "linha parada") — só vale quando a visão não leu nada diferente
        if False and vb and txt and txt["recusar"](vb):
            logging.warning(f"[parceiro] visão apontou texto FIXO (título/marca) em {[round(v, 3) for v in vb]} — "
                            "descartada")
            vb = None
        if txt and txt["legenda"]:  # linha que muda, achada com segurança nos pixels: é ela que a tarja cobre
            # (só ela: a faixa da visão vem folgada e, somada, a tarja passava de 17% da tela)
            leg, pixels = list(txt["legenda"]), True
            leg_x = txt.get("legenda_x")
            try:  # 27/10 (de73a8): os pixels medem 1 linha só; legenda que quebra em 2 linhas/mais larga ficava de fora
                _alt = leg[1] - leg[0]
                # para cima NÃO: acima da linha costuma ser a imagem (delogo nela = listras); a 2ª linha cai embaixo
                cj = _caixa_justa(video, W, H, _dur, [leg[0], leg[1] + 1.3 * _alt])
                if cj and _cruza(cj[0], leg) > 0:
                    leg = [leg[0], max(leg[1], cj[0][1])]
                    leg_x = [min(leg_x[0], cj[1][0]), max(leg_x[1], cj[1][1])] if leg_x else cj[1]
                    logging.info(f"[parceiro] caixa justa em volta da linha dos pixels: y {leg} x {leg_x}")
            except Exception as e:  # noqa: BLE001
                logging.warning(f"[parceiro] caixa justa (pixels) falhou ({type(e).__name__}: {e})")
            if vb and not _cruza(vb, leg):
                logging.info(f"[parceiro] visão {[round(v, 3) for v in vb]} discorda dos pixels {leg} — "
                             "vale a linha que muda")
        elif vb:
            # 26/10: a visão só responde legenda que ela LEU e que muda (anime_hardsub_detect); se os pixels acham a
            # mesma linha, vale a medida deles (justa) — a da visão vem folgada (legenda com brilho/chinês os pixels
            # não acham: aí fica a da visão)
            conf = txt["confirma"](vb) if txt else None
            leg, visao = vb, True
            if conf:
                leg, leg_x = conf
            try:  # 27/10: caixa JUSTA das palavras dentro da faixa (a da visão vem folgada: 15% da altura)
                # 29/10: + 1,3 linha para BAIXO (igual ao ramo dos pixels): bleach_cap1_20261029 (animax_97) a visão leu
                # [0.432, 0.495], a 2ª linha deles ("ME DEIXE / AGRADECER") em [0.493, 0.542] ficou à mostra sob a nossa
                cj = _caixa_justa(video, W, H, _dur, [leg[0], leg[1] + 1.3 * (leg[1] - leg[0])])
            except Exception as e:  # noqa: BLE001
                cj = None
                logging.warning(f"[parceiro] caixa justa falhou ({type(e).__name__}: {e})")
            if cj:
                logging.info(f"[parceiro] caixa justa da legenda: y {cj[0]} x {cj[1]} (faixa da visão {leg})")
                leg, leg_x = cj
        logging.info(f"[parceiro] legenda ({'pixels' if pixels else 'visão' if visao else 'nenhuma'}): {leg}")
        # dono 26/10: sem legenda deles não vai tarja branca nenhuma (antes ia pro título fixo do topo)
        if txt:
            for f in txt["fixos"]:
                if f["fundo"] is None and (f["y"][0] + f["y"][1]) / 2 < 0.40 and not (leg and _cruza(f["y"], leg) > 0):
                    # 27/10 (8a49d5): título fixo deles no alto que fica na tela — o nosso gancho não pode ir em cima
                    topo_fixo = [min(topo_fixo[0], f["y"][0]), max(topo_fixo[1], f["y"][1])] if topo_fixo else list(f["y"])
                if f["fundo"] is None or (leg and _cruza(f["y"], leg) > 0) or \
                        (titulo_auto and _cruza(f["y"], titulo_auto) > 0):
                    continue
                x0, y0, x1, y1 = f["pintar"]
                limpar.append((int(x0 * W), int(y0 * H), int(x1 * W), int(y1 * H), np.array(f["fundo"], np.uint8)))
            if limpar:
                logging.info(f"[parceiro] texto fixo deles no letterbox apagado: {[l[:4] for l in limpar]}")
            # 04/11 (vigilância, Short zBBM1NwgfsA/Animescomia): o CTA FIXO do parceiro no rodapé ("FINALMENTE O
            # ALGORITMO TE TROUXE PRO CANAL CERTO! SE INSCREVE", fixo em 0,825–0,892, presente em 100%) ficava no nosso
            # Short o vídeo inteiro: só texto fixo sobre FUNDO LISO era apagado. Texto fixo sem fundo liso no RODAPÉ
            # (centro > 70% da altura, fora da legenda deles) = delogo sutil, igual ao da legenda (regra: nunca texto/
            # marca do parceiro no nosso vídeo).
            for f in txt["fixos"]:
                cy = (f["y"][0] + f["y"][1]) / 2
                if f["fundo"] is not None or cy <= 0.70 or (leg and _cruza(f["y"], leg) > 0):
                    continue
                x0, x1 = max(2, int(f["x"][0] * W) - 6), min(W - 3, int(f["x"][1] * W) + 6)
                y0, y1 = max(2, int(f["y"][0] * H) - 4), min(H - 3, int(f["y"][1] * H) + 4)
                if 0 < (y1 - y0) <= DELOGO_MAX_H * H and x1 > x0:
                    rodape_delogo.append(f"delogo=x={x0}:y={y0}:w={x1 - x0}:h={y1 - y0}")
            if rodape_delogo:
                logging.info(f"[parceiro] texto fixo deles no RODAPÉ (sobre a imagem) apagado: {rodape_delogo}")
    leg_px = _faixa_px(leg, H) if leg else None
    topo_px = _faixa_px(cob["titulo_topo"] if cob.get("titulo_topo") else titulo_auto, H) \
        if (cob.get("titulo_topo") or titulo_auto) else None
    alvo_tarja = topo_px or leg_px
    # a faixa da visão já vem com margem: a folga do kaijinre em cima dela deixava a tarja com 26% da tela (18/10);
    # a dos pixels é justa nas letras (só o contorno/sombra de folga)
    if titulo_auto and not cob.get("titulo_topo"):
        folga = (0.0, 0.0)  # o título fixo achado já vem com a margem
    else:
        # 26/10: a faixa da visão agora é a dos pixels (justa) — mesma folga pequena
        folga = (0.006, 0.006) if (pixels or visao) and not topo_px else TARJA_Y  # 27/10: justa (era 0,012)
    # 27/10 (dono: a "distorção" dos longos — delogo — no lugar da tarja branca; teste): cobertura "delogo" apaga só a
    # faixa da legenda deles (ffmpeg delogo na leitura) e a NOSSA legenda entra em cima; sem tarja e sem borrão
    cobertura = modo_cobertura(video)
    delogo, sem_borrao = None, False
    # 28/10 (dona, cansada: "as tarjas brancas continuam aparecendo mesmo em vídeo sem legenda ali pra tapar"): T2
    # encerrado pelo gosto dela -> cortes_ajustes cobertura_legenda="delogo" e vale também pro texto no ALTO (antes o
    # topo caía na tarja branca). Tarja branca só volta se alguém puser "tarja" no cortes_ajustes.
    if cobertura == "delogo" and leg_px:
        # 27/10 (dono: o delogo dos longos é "tão sutil que quase não dá pra perceber"): só a caixa das letras + 6/4 px
        x0 = max(2, int(leg_x[0] * W) - 6) if leg_x else int(W * 0.05)
        x1 = min(W - 3, int(leg_x[1] * W) + 6) if leg_x else int(W * 0.95)
        y0, y1 = max(2, leg_px[0] - 4), min(H - 3, leg_px[1] + 4)
        no_tempo = None
        try:  # 13/11: caixa que acompanha cada legenda (largura/altura do trecho; sem legenda = sem delogo)
            no_tempo = delogo_no_tempo(video, W, H, leg_px, leg_x)
        except Exception as e:  # noqa: BLE001
            logging.warning(f"[parceiro] delogo no tempo falhou ({type(e).__name__}: {e}) — caixa única")
        if no_tempo:
            delogo = no_tempo
        elif (y1 - y0) > DELOGO_MAX_H * H:
            # 30/10: faixa alta demais (visão folgada + linhas extras) = delogo de 35-50% da tela vira "vidro derretido"
            # o vídeo inteiro (betinha, gta-rp). Sem delogo nem borrão: a nossa legenda (cartão) entra em cima da deles.
            logging.warning(f"[parceiro] faixa da legenda deles alta demais ({(y1 - y0) / H:.0%} da tela) — sem delogo")
            delogo, sem_borrao = None, True
        else:
            delogo = f"delogo=x={x0}:y={y0}:w={x1 - x0}:h={y1 - y0}"
            logging.info(f"[parceiro] cobertura DELOGO na legenda deles: {delogo}")
    tarja = _tarja(W, H, alvo_tarja, titulo, folga, leg_x=None if topo_px else leg_x) \
        if titulo and alvo_tarja and leg_px and not delogo and not sem_borrao else None
    if titulo and not leg_px:
        logging.info("[parceiro] sem legenda deles: sem tarja branca")
    placa = leg_px if (tarja is not None and topo_px) else (None if tarja is not None else leg_px)
    placa_ret = placa
    if delogo or sem_borrao:
        placa = None  # o delogo já apagou: não borra por cima (a faixa volta no retorno pra nossa legenda ir lá)
    nossa = _nossa_marca(handle, int(H * 0.025)) if handle else None
    my = int(float(cob.get("marca_y", 0.30)) * H)
    if nossa is not None and "marca_y" not in cob:
        try:
            ev = [(tarja[1], tarja[1] + tarja[0].shape[0])] if tarja is not None else []
            if placa_ret:
                ev.append((placa_ret[0], placa_ret[1]))
            my = _y_marca(video, W, H, _dur, ev, nossa.shape[0])
        except Exception as e:  # noqa: BLE001
            logging.warning(f"[parceiro] posição da @ pela imagem falhou ({type(e).__name__}: {e}) — 30%")
    if nossa is not None and tarja is not None:
        # a nossa @ é fixa: se cair na altura da tarja, vai pra logo acima dela (abaixo, se em cima ficar a menos de
        # 11% do topo, que o corte e o zoom do fx_clips comem) — nunca por cima do título (dono 22/10)
        meia = nossa.shape[0] // 2 + int(H * 0.01)
        t0, t1 = tarja[1], tarja[1] + tarja[0].shape[0]
        if my + meia > t0 and my - meia < t1:
            my = t0 - meia if t0 - 2 * meia >= H * 0.11 else t1 + meia
    leitor = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(video), "-vf",
                               f"fps={fps_saida}" + (f",{delogo}" if delogo else "")
                               + "".join(f",{d}" for d in rodape_delogo), "-f", "rawvideo",
                               "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
    escritor = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                                 "-r", str(fps_saida), "-i", "-", "-i", str(video), "-map", "0:v", "-map", "1:a?",
                                 "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
                                 "-c:a", "copy", "-shortest", str(saida)], stdin=subprocess.PIPE)
    n = 0
    try:
        while True:
            buf = leitor.stdout.read(W * H * 3)
            if len(buf) < W * H * 3:
                break
            f = np.frombuffer(buf, np.uint8).reshape(H, W, 3).copy()
            for x0, y0, x1, y1, cor in limpar:
                f[y0:y1, x0:x1] = cor
            for x0, y0, x1, y1 in apagar:
                _borrar(f, x0, y0, x1, y1, sigma=18)
            if placa:  # legenda deles inteira na largura (a nossa entra em cima)
                _borrar(f, int(W * 0.04), placa[0] - 4, int(W * 0.96), placa[1] + 4, escurecer=0.35, sigma=12)
            if tarja is not None:
                _colar(f, tarja[0], W / 2, tarja[1] + tarja[0].shape[0] / 2)
            if nossa is not None:
                _colar(f, nossa, W / 2, my)
            escritor.stdin.write(f.tobytes())
            n += 1
    finally:
        leitor.stdout.close()
        leitor.wait()
        escritor.stdin.close()
        escritor.wait()
    ok = escritor.returncode == 0 and Path(saida).exists() and Path(saida).stat().st_size > 10000
    logging.info(f"[parceiro] canal novo coberto: {n} quadros -> {Path(saida).name} ({'ok' if ok else 'FALHOU'}) | "
                 f"tarja {'topo' if topo_px else 'legenda'} | placa {placa} | texto fixo apagado "
                 f"{len(limpar) + len(rodape_delogo)}")
    if not ok:
        return None
    t = [tarja[1], tarja[1] + tarja[0].shape[0]] if tarja is not None else None
    if topo_fixo:
        logging.info(f"[parceiro] texto fixo deles no alto (fica na tela): {topo_fixo}")
    return {"tarja": t, "placa": placa_ret, "H": H, "cobertura": "delogo" if delogo else ("tarja" if t else "nada"),
            "topo_fixo": _faixa_px(topo_fixo, H) if topo_fixo else None}


def centro_saida(y_px, H, crop=0.90):
    """Fração da altura NO VÍDEO FINAL de uma altura do vídeo-fonte (o fx_clips corta 10% e reescala)."""
    return round((y_px / H - (1 - crop) / 2) / crop, 4)
