"""Atividade labial na regiao da webcam (MediaPipe FaceLandmarker): separa a fala do criador do audio do conteudo.

Feature usada: media do |delta| da abertura da boca entre amostras consecutivas (15 fps). Fala = oscilacao rapida
(silabas), boca parada ou sorriso = valor baixo. Nos testes: criador >= 0.0024, audio do conteudo <= 0.0007.
"""
import numpy as np
import cv2
from .common import log


def mouth_series(cfg, video, webcam_box, sample_fps=None):
    """Retorna lista [(t, abertura_relativa|None)] amostrada a sample_fps."""
    import mediapipe as mp
    from mediapipe.tasks import python as mpp
    from mediapipe.tasks.python import vision
    sample_fps = sample_fps or cfg.get("lips", {}).get("sample_fps", 15)
    model = str(cfg["paths"]["assets"]).replace("\\", "/") + "/models/face_landmarker.task"
    opts = vision.FaceLandmarkerOptions(base_options=mpp.BaseOptions(model_asset_path=model),
                                        running_mode=vision.RunningMode.VIDEO, num_faces=1)
    lm = vision.FaceLandmarker.create_from_options(opts)
    x0, y0, x1, y1 = webcam_box
    cap = cv2.VideoCapture(str(video))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    step = max(1, int(round(fps / sample_fps)))
    out = []
    i = 0
    while True:
        ok, f = cap.read()
        if not ok:
            break
        if i % step == 0:
            crop = f[y0:y1, x0:x1]
            img = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))
            r = lm.detect_for_video(img, int(i / fps * 1000))
            val = None
            if r.face_landmarks:
                L = r.face_landmarks[0]
                d = lambda a, b: float(np.hypot(L[a].x - L[b].x, L[a].y - L[b].y))
                val = d(13, 14) / max(d(10, 152), 1e-6)
            out.append((round(i / fps, 3), val))
        i += 1
    cap.release()
    lm.close()
    found = sum(1 for _, v in out if v is not None)
    log(f"labios: {len(out)} amostras a {sample_fps} fps, rosto em {found} ({100*found/max(1,len(out)):.0f}%)")
    return out


def activity(series, a, b):
    """Media do |delta| da abertura da boca entre a e b (None se sem rosto suficiente)."""
    sel = [v for t, v in series if a <= t < b and v is not None]
    if len(sel) < 4:
        return None
    return float(np.mean(np.abs(np.diff(np.array(sel)))))


def tag_words(cfg, series, words, segments):
    """Marca cada palavra e segmento com speaker='creator'|'content' pela atividade labial."""
    Lc = cfg.get("lips", {})
    thr = float(Lc.get("threshold", 0.0014))
    pad = float(Lc.get("pad", 0.4))
    for w in words:
        w["lip"] = activity(series, w["s"] - pad, w["e"] + pad)
    for s in segments:
        s["lip"] = activity(series, s["start"], s["end"])
    raw = [None if w["lip"] is None else (w["lip"] >= thr) for w in words]
    tags = []
    for i in range(len(raw)):
        win = [r for r in raw[max(0, i - 2):i + 3] if r is not None]
        tags.append(True if not win else (sum(win) >= len(win) / 2))
    for w, t in zip(words, tags):
        w["speaker"] = "creator" if t else "content"
    for s in segments:
        votes = [w["speaker"] for w in words if s["start"] - 0.01 <= w["s"] <= s["end"] + 0.01]
        if votes:
            s["speaker"] = "creator" if votes.count("creator") >= len(votes) / 2 else "content"
        else:
            s["speaker"] = "creator" if (s["lip"] is None or s["lip"] >= thr) else "content"
    n_c = sum(1 for w in words if w["speaker"] == "creator")
    log(f"labios: limiar={thr}; palavras do criador={n_c}/{len(words)}")
    return thr
