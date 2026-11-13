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


def _tarja(W, H, faixa, titulo):
    """(BGRA, y0) da TARJA BRANCA com o título chamativo em preto (dono 17/10: "um desses canais coloca uma tarja
    branca em cima da legenda e um título extremamente chamativo, tipo 'essa garota fez isso'"). Cobre a faixa da
    legenda deles com folga; título em até 2 linhas, o maior que couber."""
    from PIL import Image, ImageDraw, ImageFont
    y0 = max(0, int(faixa[0] - TARJA_Y[0] * H))
    y1 = min(H, int(faixa[1] + TARJA_Y[1] * H))
    # 80% da largura: o fx_clips corta 5% de cada lado e o movimento de câmera dá zoom de até 12% — com 94% o título
    # saía cortado nas pontas (17/10, "...ARCISISTA")
    larg, alt = int(W * 0.80), y1 - y0
    img = Image.new("RGBA", (larg, alt), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, larg - 1, alt - 1], radius=int(alt * 0.18), fill=(255, 255, 255, 255))
    palavras = titulo.upper().split()
    melhor = None
    for tam in range(int(alt * 0.62), 10, -2):
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


def cobrir(video, saida, handle, det=None, fps_saida=30, titulo=None):
    """Cobre a legenda deles (só a largura das palavras de cada quadro) e a marca (só o retângulo dela, com a nossa
    marca escrita por cima). Com `titulo`: em vez do borrão, TARJA BRANCA fixa com o título sobre a faixa da legenda
    (a nossa legenda vai pra outro lugar). Devolve Path(saida) ou None."""
    det = det or detectar(video, fps_saida=fps_saida)
    W, H = det["W"], det["H"]
    tarja = _tarja(W, H, det["faixa"], titulo) if titulo and det.get("faixa") else None
    leg_x = det.get("legenda_x") or []
    marca = det.get("marca")
    if marca:
        tt = np.array([p[0] for p in marca["trilha"]])
        yy = np.array([p[1] for p in marca["trilha"]])
        mw, mh, mx = int(marca["w"] * W), int(marca["h"] * H), int(marca["x"] * W)
        nossa = _nossa_marca(handle, mh) if handle else None
    faixa = det.get("faixa")
    leitor = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(video), "-vf", f"fps={fps_saida}", "-f", "rawvideo",
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
            if tarja is not None:
                _colar(f, tarja[0], W / 2, tarja[1] + tarja[0].shape[0] / 2)
            elif faixa and n < len(leg_x) and leg_x[n]:  # legenda deles: só onde tem palavra (janela de ±0,23 s)
                y0, y1 = faixa
                x0, x1 = leg_x[n]
                _borrar(f, x0 - 20, y0 - 4, x1 + 20, y1 + 4, escurecer=0.35, sigma=10)
            if marca:
                my = int(float(np.interp(t, tt, yy)) * H)
                _borrar(f, mx - 8, my - 6, mx + mw + 8, my + mh + 6, sigma=7)
                if nossa is not None:
                    _colar(f, nossa, mx + mw / 2, my + mh / 2)
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
#   "apagar": [[x0, y0, x1, y1], ...] marcas d'água, logos, avisos ("No were harmed...") — borrados o vídeo inteiro
#   "marca_y": altura da NOSSA @ (padrão 0.30)
def _faixa_px(fr, H):
    return [max(0, int(fr[0] * H)), min(H, int(fr[1] * H))]


def cobrir_canal(video, saida, handle, cob, titulo=None, fps_saida=30):
    """Cobre um vídeo de canal parceiro NOVO pela configuração do canal. Devolve {"tarja": [y0,y1] px | None,
    "placa": [y0,y1] px | None, "H": H} (pro anime_auto saber onde pôr a nossa legenda) ou None se falhou."""
    W, H, _fps, _dur = _dims(video)
    leg = cob.get("legenda")
    if leg == "auto":
        try:
            from anime_hardsub_detect import detect_hardsub_band
            b = detect_hardsub_band(str(video))
            leg = [b[0] - 0.01, b[0] + b[1] + 0.01] if b else None
            logging.info(f"[parceiro] legenda por visão: {leg}")
        except Exception as e:  # noqa: BLE001
            logging.warning(f"[parceiro] visão da legenda falhou ({type(e).__name__}) — sem faixa")
            leg = None
    leg_px = _faixa_px(leg, H) if leg else None
    topo_px = _faixa_px(cob["titulo_topo"], H) if cob.get("titulo_topo") else None
    alvo_tarja = topo_px or leg_px
    tarja = _tarja(W, H, alvo_tarja, titulo) if titulo and alvo_tarja else None
    placa = leg_px if (tarja is not None and topo_px) else (None if tarja is not None else leg_px)
    apagar = [[int(r[0] * W), int(r[1] * H), int(r[2] * W), int(r[3] * H)] for r in cob.get("apagar") or []]
    nossa = _nossa_marca(handle, int(H * 0.025)) if handle else None
    my = int(float(cob.get("marca_y", 0.30)) * H)
    leitor = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(video), "-vf", f"fps={fps_saida}", "-f", "rawvideo",
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
                 f"tarja {'topo' if topo_px else 'legenda'} | placa {placa}")
    if not ok:
        return None
    t = [tarja[1], tarja[1] + tarja[0].shape[0]] if tarja is not None else None
    return {"tarja": t, "placa": placa, "H": H}


def centro_saida(y_px, H, crop=0.90):
    """Fração da altura NO VÍDEO FINAL de uma altura do vídeo-fonte (o fx_clips corta 10% e reescala)."""
    return round((y_px / H - (1 - crop) / 2) / crop, 4)
