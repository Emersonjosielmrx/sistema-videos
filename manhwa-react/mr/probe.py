"""Sondagem do video: metadados, loudness e deteccao automatica do layout (webcam em cima / conteudo embaixo).

Deteccao com pouca memoria: acumula media e variancia temporal por pixel em vez de empilhar frames.
"""
import re
import numpy as np
import cv2
from .common import ffprobe_json, run, log


def probe(cfg, path):
    info = ffprobe_json(cfg, path)
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    a = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    num, den = v.get("r_frame_rate", "30/1").split("/")
    fps = float(num) / float(den or 1)
    return {
        "path": str(path),
        "duration": float(info["format"]["duration"]),
        "width": int(v["width"]), "height": int(v["height"]), "fps": fps,
        "vcodec": v["codec_name"],
        "audio": None if a is None else {"codec": a["codec_name"], "sr": int(a["sample_rate"]), "channels": int(a["channels"])},
    }


def measure_loudness(cfg, path):
    res = run([cfg["paths"]["ffmpeg"], "-hide_banner", "-i", str(path), "-af", "ebur128=peak=true", "-f", "null", "-"], check=False)
    out = res.stderr
    m = re.search(r"I:\s+(-?[\d.]+) LUFS", out)
    lra = re.search(r"LRA:\s+([\d.]+) LU", out)
    pk = re.search(r"Peak:\s+(-?[\d.]+) dBFS", out)
    return {"lufs": float(m.group(1)) if m else None, "lra": float(lra.group(1)) if lra else None, "peak": float(pk.group(1)) if pk else None}


def _groups(idx):
    g = []
    for i in idx:
        if g and i == g[-1][1] + 1:
            g[-1][1] = i
        else:
            g.append([i, i])
    return g


def _temporal_stats(path, samples=15):
    """Media e desvio-padrao temporal por pixel (H,W,3) sem empilhar frames."""
    cap = cv2.VideoCapture(str(path))
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    s1 = np.zeros((H, W, 3), np.float64)
    s2 = np.zeros((H, W, 3), np.float64)
    k = 0
    for t in np.linspace(0.05, 0.95, samples):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(n * t))
        ok, f = cap.read()
        if not ok:
            continue
        f = f.astype(np.float32)
        s1 += f
        s2 += f * f
        k += 1
    cap.release()
    k = max(k, 1)
    mean = s1 / k
    var = np.maximum(s2 / k - mean * mean, 0)
    return W, H, mean.astype(np.float32), np.sqrt(var).astype(np.float32)


def _pip_scores(bx, by):
    """Para webcam no canto superior direito, com mapas binarios de linha vertical (bx) e horizontal (by):
    score de cada (y1 = borda de baixo, x0 = borda esquerda) = fracao continua da coluna x0 (linhas 0..y1) que e linha
    + fracao da linha y1 (colunas x0..W) que e linha. Moldura de janela ~2.0; texto/logo fica picotado."""
    sh, sw = bx.shape
    cx = np.cumsum(bx, axis=0)                      # cx[y, x] = soma de bx[0:y+1, x]
    ry = np.cumsum(by[:, ::-1], axis=1)[:, ::-1]    # ry[y, x] = soma de by[y, x:]
    # janela de webcam = no maximo metade da largura e 60% da altura (senao a mesma moldura casa com o canto oposto)
    ys = np.arange(int(sh * 0.12), int(sh * 0.6))
    xs = np.arange(int(sw * 0.5), int(sw * 0.93))
    left = cx[ys - 1][:, xs] / ys[:, None]
    bottom = ry[ys][:, xs] / (sw - xs)[None, :]
    return ys, xs, left, bottom


def _refinar_margens(bx, by, x0, y1):
    """Janela que nao encosta na borda do quadro: acha a borda de cima (y0) e a da direita (x1), se existirem.
    So procura perto da beira (ate 5% do quadro): mais para dentro, linhas paradas do cenario da webcam enganam."""
    sh, sw = bx.shape
    y0 = 0
    cand = [(by[y, x0:sw].mean(), y) for y in range(0, max(1, min(int(y1 * 0.3), int(sh * 0.05))))]
    if cand and max(cand)[0] >= 0.6:
        y0 = max(cand)[1]
    x1 = sw
    cand = [(bx[y0:y1, x].mean(), x) for x in range(max(x0 + 1, sw - int(sw * 0.05)), sw)]
    if cand and max(cand)[0] >= 0.6:
        x1 = max(cand)[1] + 1
    return y0, x1


def _detect_pip(cfg, path, samples=24, corner="auto"):
    """Webcam em janela (picture-in-picture) num canto da gravacao deitada. A moldura da janela fica parada enquanto o
    resto muda, entao aparece na media do gradiente de muitos frames. Retorna ([x0, y0, x1, y1], canto, z) ou None."""
    cap = cv2.VideoCapture(str(path))
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    sw = 480
    sh = int(round(H * sw / W))
    gx = np.zeros((sh, sw), np.float32)
    gy = np.zeros((sh, sw), np.float32)
    k = 0
    for t in np.linspace(0.03, 0.97, samples):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(n * t))
        ok, f = cap.read()
        if not ok:
            continue
        g = cv2.cvtColor(cv2.resize(f, (sw, sh), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY).astype(np.float32)
        gx += np.abs(cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=3))
        gy += np.abs(cv2.Sobel(g, cv2.CV_32F, 0, 1, ksize=3))
        k += 1
    cap.release()
    if not k:
        return None
    # so linhas finas e constantes: tira a media local (bordas de conteudo que se repetem viram fundo) e binariza
    gx = np.maximum(gx / k - cv2.blur(gx / k, (15, 1)), 0)
    gy = np.maximum(gy / k - cv2.blur(gy / k, (1, 15)), 0)
    lx = (gx > max(np.percentile(gx, 98), 4.0)).astype(np.float32)
    ly = (gy > max(np.percentile(gy, 98), 4.0)).astype(np.float32)
    lx = np.maximum(lx, np.roll(lx, 1, axis=1))  # tolera a moldura oscilar 1 px entre colunas vizinhas
    ly = np.maximum(ly, np.roll(ly, 1, axis=0))
    cantos = ["top_right", "top_left", "bottom_right", "bottom_left"] if corner == "auto" else [corner]
    best = None
    for c in cantos:
        fx, fy = c.endswith("left"), c.startswith("bottom")
        ax, ay = lx[:, ::-1] if fx else lx, ly[:, ::-1] if fx else ly
        ax, ay = (ax[::-1] if fy else ax), (ay[::-1] if fy else ay)
        ys, xs, left, bottom = _pip_scores(ax, ay)
        sc = np.minimum(left, bottom) * 2  # as DUAS bordas precisam existir
        i, j = np.unravel_index(int(np.argmax(sc)), sc.shape)
        score = float(sc[i, j])
        if best is None or score > best[0]:
            y1, x0 = int(ys[i]), int(xs[j])
            y0, x1 = _refinar_margens(ax, ay, x0, y1)
            bx0, bx1 = (sw - x1, sw - x0) if fx else (x0, x1)
            by0, by1 = (sh - y1, sh - y0) if fy else (y0, y1)
            best = (score, c, [bx0, by0, bx1, by1])
    z, c, (bx0, by0, bx1, by1) = best
    if z < float(cfg["layout"].get("pip_min_score", 1.2)):
        log(f"layout: janela da webcam nao encontrada com seguranca (score={z:.2f})")
        return None
    s = W / sw
    pad = 2  # fica por dentro da moldura
    box = [int(bx0 * s) + pad, int(by0 * s) + pad, int(bx1 * s) - pad, int(by1 * s) - pad]
    box = [min(max(v, 0), lim) // 2 * 2 for v, lim in zip(box, (W, H, W, H))]
    return box, c, round(z, 1)


def _layout_pip(cfg, path, W, H, mean_frame, tstd):
    """Gravacao deitada com a webcam num canto: webcam = a janela; conteudo = o quadro inteiro (menos faixas pretas)."""
    L = cfg["layout"]
    manual = L.get("pip")
    if manual:  # [x0, y0, x1, y1] em fracao do quadro, calibrado a mao
        box = [int(manual[0] * W) // 2 * 2, int(manual[1] * H) // 2 * 2, int(manual[2] * W) // 2 * 2, int(manual[3] * H) // 2 * 2]
        canto, z = "manual", None
    else:
        r = _detect_pip(cfg, path, corner=L.get("pip_corner", "auto"))
        if not r:
            return None
        box, canto, z = r
    row_bright = mean_frame.mean(axis=(1, 2))
    row_var = tstd.mean(axis=(1, 2))
    dark = (row_bright < 45) & (row_var < 6)
    c_top = next((y for y in range(H) if not dark[y]), 0)
    c_bot = H - next((y for y in range(H) if not dark[H - 1 - y]), 0)
    if c_top > H * 0.2 or H - c_bot > H * 0.2:
        c_top, c_bot = 0, H
    layout = {"width": W, "height": H, "mode": "pip", "pip_corner": canto, "content_x0": 0, "content_x1": W, "has_webcam": True,
              "contrast": z, "trimmed": {}, "divider": 0, "webcam": box, "content": [0, int(c_top), W, int(c_bot)]}
    log(f"layout: gravacao deitada, webcam no canto {canto} {box} (z={z}), conteudo {layout['content']}")
    return layout


def detect_layout(cfg, path, samples=15):
    """Detecta a linha divisoria entre webcam (estatica, em cima) e conteudo (dinamico, embaixo), as faixas laterais
    estaticas da UI do celular e faixas pretas estaticas (logo/titulo do video original). Regioes em pixels do original.
    Gravacao deitada (ou layout.mode = "pip"): webcam numa janela no canto, ver _layout_pip."""
    W, H, mean_frame, tstd = _temporal_stats(path, samples)
    mode = cfg["layout"].get("mode", "auto")
    sem_cam = False
    if mode == "pip" or (mode == "auto" and W > H):
        lay = _layout_pip(cfg, path, W, H, mean_frame, tstd)
        if lay:
            return lay
        log("layout: sem webcam no canto; tratando como video sem webcam")
        sem_cam = True
    col_var = tstd.mean(axis=(0, 2))
    x0, x1 = 0, W
    if cfg["layout"].get("ui_strip_detect", True):
        static_cols = [x for x in range(W) if col_var[x] < 4.0]
        for a, b in _groups(static_cols):
            if a == 0 and b - a >= 4:
                x0 = b + 1
            if b == W - 1 and b - a >= 4:
                x1 = a
    row_var = tstd[:, x0:x1].mean(axis=(1, 2))
    sm = np.convolve(row_var, np.ones(15) / 15, mode="same")
    best = (0.0, None)
    lo, hi = int(H * 0.18), int(H * 0.65)
    for y in range(lo, hi):
        d = sm[y + 8:y + 40].mean() - sm[y - 40:y - 8].mean()
        if d > best[0]:
            best = (d, y)
    contrast, div = best
    has_webcam = not sem_cam and div is not None and contrast > 12 and sm[:div - 10].mean() < 25
    row_bright = mean_frame[:, x0:x1].mean(axis=(1, 2))
    dark_static = (row_bright < 45) & (row_var < 6)

    def _block(rng, reverse=False, tol=14):
        """Tamanho do bloco de linhas escuras/estaticas a partir da borda, tolerando ate `tol` linhas de transicao."""
        n = 0
        gap = 0
        last = 0
        for y in (reversed(rng) if reverse else rng):
            n += 1
            if dark_static[y]:
                gap = 0
                last = n
            else:
                gap += 1
                if gap > tol:
                    break
        return last if last >= 16 else 0

    layout = {"width": W, "height": H, "content_x0": int(x0), "content_x1": int(x1), "has_webcam": bool(has_webcam),
              "contrast": round(float(contrast or 0), 1), "trimmed": {}}
    if has_webcam:
        div = int(div)
        web_bottom = div
        n = _block(range(0, div), reverse=True)
        if 16 <= n <= int(H * 0.25):
            web_bottom = div - n
            layout["trimmed"]["webcam_bottom"] = n
        c_top, c_bot = div, H
        n = _block(range(div, H))
        if 16 <= n <= int((H - div) * 0.45):  # faixa preta estatica no video inteiro = borda (clipe deitado no meio da tela)
            c_top = div + n
            layout["trimmed"]["content_top"] = n
        n = _block(range(c_top, H), reverse=True)
        if 16 <= n <= int((H - div) * 0.45):
            c_bot = H - n
            layout["trimmed"]["content_bottom"] = n
        layout.update({"divider": div, "webcam": [0, 0, W, int(web_bottom)], "content": [int(x0), int(c_top), int(x1), int(c_bot)]})
    else:
        c_top, c_bot = 0, H
        n = _block(range(0, H))
        if 16 <= n <= int(H * 0.2):
            c_top = n
        n = _block(range(c_top, H), reverse=True)
        if 16 <= n <= int(H * 0.2):
            c_bot = H - n
        layout.update({"divider": 0, "webcam": None, "content": [int(x0), int(c_top), int(x1), int(c_bot)]})
    log(f"layout: webcam={'sim' if has_webcam else 'nao'} divisor={layout['divider']} conteudo_x={x0}-{x1} contraste={layout['contrast']}"
        + (f" faixas pretas cortadas {layout['trimmed']}" if layout["trimmed"] else ""))
    return layout


def plan_output_layout(cfg, layout):
    """Calcula as regioes de saida (1080x1920): webcam em cima, faixa, conteudo preenchendo o resto (cover-crop)."""
    OW, OH = cfg["output"]["width"], cfg["output"]["height"]
    L = cfg["layout"]
    plan = {"out_w": OW, "out_h": OH}
    if layout["has_webcam"]:
        wx0, wy0, wx1, wy1 = layout["webcam"]
        wh = wy1 - wy0
        trim = L.get("pip_bottom_trim", 0.0) if layout.get("mode") == "pip" else L["webcam_bottom_trim"]
        keep_h = int(round(wh * (1 - trim)))
        scale = OW / (wx1 - wx0)
        web_out_h = int(round(keep_h * scale))
        max_h = int(OH * L["webcam_max_share"])
        if web_out_h > max_h:
            web_out_h = max_h
            keep_h = int(round(web_out_h / scale))
        web_out_h -= web_out_h % 2
        keep_h -= keep_h % 2
        plan["webcam"] = {"crop": [wx0, wy0, wx1 - wx0, keep_h], "out_h": web_out_h}
        plan["divider_out"] = web_out_h
    else:
        plan["webcam"] = None
        plan["divider_out"] = 0
    band_h = 0
    B = cfg.get("band", {})
    D = cfg.get("divider", {})
    seam_style = D.get("style", "electric") if layout["has_webcam"] else None
    if B.get("enabled") and layout["has_webcam"] and seam_style in (None, "none", "flat"):
        band_h = int(B.get("height", 64)) // 2 * 2
    plan["band"] = {"y": plan["divider_out"], "h": band_h}
    overlap = int(D.get("overlap", 56)) if (layout["has_webcam"] and band_h == 0) else 0
    plan["seam"] = {"y": plan["divider_out"], "overlap": overlap, "edge": D.get("edge", "tear"), "style": seam_style}
    cx0, cy0, cx1, cy1 = layout["content"]
    cw, ch = cx1 - cx0, cy1 - cy0
    area_h = OH - plan["divider_out"] - band_h + overlap
    scaled_h = int(round(ch * OW / cw))
    if scaled_h >= area_h:
        crop_h = int(round(area_h * cw / OW))
        off = int(round((ch - crop_h) * L["content_top_bias"]))
        crop = [cx0, cy0 + off, cw, crop_h]
    else:
        crop_w = int(round(ch * OW / area_h))
        offx = (cw - crop_w) // 2
        if layout.get("mode") == "pip":
            # desloca o recorte do conteudo o minimo para nao pegar a janela da webcam (quando cabe)
            px0, _, px1, _ = layout["webcam"]
            if px0 > cw / 2 and cx0 + offx + crop_w > px0 and px0 - cx0 - crop_w >= 0:
                offx = px0 - cx0 - crop_w
            elif px1 < cw / 2 and cx0 + offx < px1 and px1 - cx0 + crop_w <= cw:
                offx = px1 - cx0
        crop = [cx0 + offx, cy0, crop_w, ch]
    crop[2] -= crop[2] % 2
    crop[3] -= crop[3] % 2
    plan["content"] = {"crop": crop, "scale": [OW, area_h], "out_y": plan["divider_out"] + band_h - overlap}
    return plan
