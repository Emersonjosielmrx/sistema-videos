"""cortes_mascote.py — a waifu-mascote num CANTO do Short nos trechos em que a narração quase para (dona 28/10:
"com fundo branco pra recortar e colar durante trechos da narração que tiver pouco áudio; não deve ocupar a tela toda
e sim um dos cantos, aparecer de forma que não atrapalhe a história; se for impossível, borre a parte de trás").

- Fotos: hipercool-materiais\\mascote_waifu_v2\\cosplay (fundo branco) -> recorte por inundação a partir da borda
  (branco que encosta na borda some; branco dentro dela — meia, camisa — fica), cache em cosplay_recorte\\.
- Vídeo: workspace\\assets\\mascote_viva\\reacao_susto_*.webm (Veo já sem fundo), em loop enquanto ela está na tela.
- Quando: as maiores pausas entre palavras (word_times), depois do gancho (3,5 s), no máx 2, 10 s uma da outra.
- Onde: o canto com MENOS detalhe naquele instante, fora da faixa da nossa legenda (SUB_Y_CENTER). Canto todo cheio
  de detalhe = borra o retângulo atrás dela.
- Entra deslizando da lateral (0,25 s), balança de leve e sai deslizando. Teste T7 (CORTES_MASCOTE A|B).
"""
import hashlib
import json
import logging
import os
import subprocess
from pathlib import Path

FOTOS = Path(r"D:\hipercool-materiais\mascote_waifu_v2\cosplay")
RECORTES = FOTOS.parent / "cosplay_recorte"
VIVA = Path(__file__).resolve().parent.parent / "workspace" / "assets" / "mascote_viva"
SEM_FUNDO_BRANCO = ("07_",)  # praia: fundo de cenário, não recorta pelo branco
INICIO_S, FIM_S, PAUSA_MIN, ENTRE_S, MAX_VEZES = 3.5, 2.0, 0.35, 10.0, 2
DUR_S, DESLIZA_S = 2.4, 0.25
ALTURA = 0.30  # fração da altura do vídeo
BORRA_ACIMA = 22.0  # detalhe médio (gradiente) do canto acima disto = borra atrás dela


def _base(p):
    return p if p.exists() else Path("C" + str(p)[1:])  # PC2: hipercool-materiais no C:


def recortes():
    """[png RGBA] das fotos de cosplay (gera o que faltar)."""
    import cv2
    import numpy as np
    raiz = _base(FOTOS.parent)
    fotos, saida = raiz / FOTOS.name, raiz / RECORTES.name
    if not fotos.exists():  # PC2: só os recortes prontos foram copiados
        return sorted(saida.glob("*.png")) if saida.exists() else []
    saida.mkdir(exist_ok=True)
    out = []
    for f in sorted(fotos.glob("*.png")):
        if f.name.startswith(SEM_FUNDO_BRANCO):
            continue
        r = saida / f.name
        if not r.exists():
            img = cv2.imread(str(f))
            h, w = img.shape[:2]
            branco = (img.min(axis=2) > 232).astype(np.uint8)
            mask = np.zeros((h + 2, w + 2), np.uint8)
            fundo = branco.copy()
            for x, y in [(x, 0) for x in range(0, w, 7)] + [(x, h - 1) for x in range(0, w, 7)] + \
                        [(0, y) for y in range(0, h, 7)] + [(w - 1, y) for y in range(0, h, 7)]:
                if fundo[y, x] == 1:
                    cv2.floodFill(fundo, mask, (x, y), 2)
            alfa = np.where(fundo == 2, 0, 255).astype(np.uint8)
            alfa = cv2.GaussianBlur(cv2.erode(alfa, np.ones((3, 3), np.uint8)), (3, 3), 0)
            ys, xs = np.nonzero(alfa > 10)
            if not len(xs):
                continue
            rgba = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
            rgba[:, :, 3] = alfa
            cv2.imwrite(str(r), rgba[ys.min():ys.max() + 1, xs.min():xs.max() + 1])
        out.append(r)
    return out


def _quietos(video):
    """[(início, duração)] dos trechos em que o ÁUDIO do vídeo cai 8 dB abaixo da mediana por >= 0,3 s (janelas de
    0,1 s). 29/10: a narração clonada não gera tempos por palavra — sem isto a mascote nunca achava pausa (31 de 31)."""
    import math
    import re
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-vn", "-af",
                        "aresample=8000,asetnsamples=800,astats=metadata=1:reset=1,"
                        "ametadata=print:key=lavfi.astats.Overall.RMS_level:file=-", "-f", "null", "-"],
                       capture_output=True, text=True, timeout=300)
    rms = []
    for v in re.findall(r"RMS_level=(\S+)", r.stdout):
        try:
            x = float(v)
        except ValueError:
            x = -120.0
        rms.append(x if math.isfinite(x) else -120.0)
    if len(rms) < 20:
        return []
    mediana = sorted(rms)[len(rms) // 2]
    # 29/10 (Short real com clone): narração contínua + música; as quedas duram 0,1-0,3 s e raramente passam de 8 dB.
    # Então: média móvel de 0,5 s e os pontos mais baixos (>= 3 dB abaixo da mediana) = "trechos com pouco áudio".
    media = [sum(rms[k:k + 5]) / 5 for k in range(len(rms) - 4)]
    out = [(k / 10, round(mediana - m, 1)) for k, m in enumerate(media)
           if m <= mediana - 3 and m == min(media[max(0, k - 5):k + 6])]
    return out


def momentos(word_times, offsets, total, video=None):
    """Instantes de pouca fala: as maiores pausas entre palavras (quando há tempos por palavra) ou, sem eles, os
    trechos mais baixos do áudio do próprio vídeo."""
    pal = []
    for i, wt in enumerate(word_times or []):
        if wt and i < len(offsets):
            pal += [(offsets[i] + float(a), offsets[i] + float(b)) for a, b, *_ in wt]
    pal.sort()
    pausas = [(a[1], b[0] - a[1]) for a, b in zip(pal, pal[1:]) if b[0] - a[1] >= PAUSA_MIN]
    if not pausas and video:
        pausas = _quietos(video)
    pausas = [(t, g) for t, g in pausas if INICIO_S <= t <= total - FIM_S - DUR_S]
    escolhidos = []
    for t, g in sorted(pausas, key=lambda p: -p[1]):
        if len(escolhidos) >= MAX_VEZES:
            break
        if all(abs(t - e) >= ENTRE_S for e in escolhidos):
            escolhidos.append(t)
    return sorted(escolhidos)


def _canto(video, t, W, H, alt_px, larg_px):
    """(x, y, lado, detalhe) do canto mais calmo em t, fora da faixa da legenda."""
    import numpy as np
    w, h = 90, 160
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t + DUR_S / 2:.2f}", "-i", str(video), "-frames:v", "1",
                        "-vf", f"scale={w}:{h},format=gray", "-f", "rawvideo", "-"], capture_output=True, timeout=60)
    q = np.frombuffer(r.stdout, np.uint8)
    q = q.reshape(h, w).astype(float) if q.size == w * h else np.zeros((h, w))
    gy, gx = np.abs(np.diff(q, axis=0))[:, :-1], np.abs(np.diff(q, axis=1))[:-1, :]
    grad = gx + gy
    leg = float(os.environ.get("SUB_Y_CENTER") or 0.75)
    m = int(W * 0.02)
    cands = []
    # 30/10: área segura do Shorts — a UI cobre ~15% de baixo (título/canal) e a coluna direita ~12% (curtir/comentar);
    # antes os cantos de baixo iam a 0,67-0,97 da altura e o direito colava na borda (mascote meio escondida)
    for lado in ("esq", "dir"):
        x = m if lado == "esq" else min(W - larg_px - m, int(W * 0.88) - larg_px)
        for y in (int(H * 0.06), int(H * 0.84) - alt_px):
            y0, y1 = y / H, (y + alt_px) / H
            if y0 < leg + 0.06 and y1 > leg - 0.06:
                continue  # em cima da nossa legenda
            a, b = int(y0 * (h - 1)), int(y1 * (h - 1))
            c, d = int(x / W * (w - 1)), int((x + larg_px) / W * (w - 1))
            cands.append((float(grad[a:b, c:d].mean()) if b > a and d > c else 99.0, x, y, lado))
    if not cands:
        return min(W - larg_px - m, int(W * 0.88) - larg_px), int(H * 0.06), "dir", 99.0
    det, x, y, lado = min(cands)
    return x, y, lado, det


def aplicar(video_in, video_out, word_times, offsets):
    """Uma passada do ffmpeg com a mascote nos momentos de pouca fala. True se gravou video_out."""
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=width,height:format=duration", "-of", "json", str(video_in)],
                       capture_output=True, text=True, timeout=60)
    d = json.loads(r.stdout)
    W, H, total = int(d["streams"][0]["width"]), int(d["streams"][0]["height"]), float(d["format"]["duration"])
    ts = momentos(word_times, offsets, total, video_in)
    fotos = recortes()
    vivos = sorted(_base(VIVA).glob("reacao_*.webm")) if _base(VIVA).exists() else []
    if not ts or not (fotos or vivos):
        logging.info(f"[mascote] sem momento de pouca fala ({len(ts)}) ou sem imagem — Short sem mascote")
        return False
    sem = int(hashlib.md5(str(video_in).encode()).hexdigest(), 16)
    alt = int(H * ALTURA) // 2 * 2
    inputs, fc, last, usados = ["-i", str(video_in)], [], "[0:v]", []
    for k, t in enumerate(ts):
        vivo = vivos[(sem + k) % len(vivos)] if vivos and ((k + sem) % 2 == 0 or not fotos) else None
        foto = None
        if vivo:
            inputs += ["-stream_loop", "-1", "-c:v", "libvpx-vp9", "-i", str(vivo)]
            larg = int(alt * 718 / 960)
        else:
            foto = fotos[(sem // 7 + k) % len(fotos)]
            inputs += ["-loop", "1", "-i", str(foto)]
            from PIL import Image
            iw, ih = Image.open(foto).size
            larg = int(alt * iw / ih)
        larg = min(larg, int(W * 0.42))
        x, y, lado, det = _canto(video_in, t, W, H, alt, larg)
        i, t1 = k + 1, t + DUR_S
        if det > BORRA_ACIMA:  # canto cheio de história: borra o retângulo atrás dela
            fc.append(f"{last}split[b{i}a][b{i}b];[b{i}b]crop={larg}:{alt}:{x}:{y},boxblur=18:2[b{i}c];"
                      f"[b{i}a][b{i}c]overlay={x}:{y}:enable='between(t,{t:.3f},{t1:.3f})'[bb{i}]")
            last = f"[bb{i}]"
        fc.append(f"[{i}:v]scale={larg}:{alt},fps=30,format=yuva420p,trim=duration={DUR_S:.3f},"
                  f"setpts=PTS-STARTPTS+{t:.3f}/TB[m{i}]")
        fora = f"-{larg}" if lado == "esq" else "W"
        # desliza pra dentro, balança 6 px, desliza pra fora
        xe = (f"if(lt(t-{t:.3f},{DESLIZA_S}),{fora}+({x}-({fora}))*(t-{t:.3f})/{DESLIZA_S},"
              f"if(gt(t,{t1 - DESLIZA_S:.3f}),{x}+(({fora})-{x})*(t-{t1 - DESLIZA_S:.3f})/{DESLIZA_S},{x}))")
        ye = f"{y}+6*sin(2*PI*(t-{t:.3f})*1.2)"
        fc.append(f"{last}[m{i}]overlay=x='{xe}':y='{ye}':eof_action=pass:"
                  f"enable='between(t,{t:.3f},{t1:.3f})'[o{i}]")
        last = f"[o{i}]"
        usados.append(f"{t:.1f}s {lado}{'+borrão' if det > BORRA_ACIMA else ''} "
                      f"{(vivo or foto).stem}")
    cmd = ["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(fc), "-map", last, "-map", "0:a?",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "copy",
           "-t", f"{total:.3f}", str(video_out)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=max(600, int(total * 6)))
    ok = r.returncode == 0 and Path(video_out).exists() and Path(video_out).stat().st_size > 10000
    if ok:
        logging.info(f"[mascote] {len(usados)}x: " + " | ".join(usados))
    else:
        logging.warning(f"[mascote] ffmpeg falhou: {(r.stderr or '')[-300:]}")
    return ok
