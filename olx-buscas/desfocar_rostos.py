# -*- coding: utf-8 -*-
"""Desfoca rostos (YuNet) nas fotos de anúncio. Uso: python desfocar_rostos.py <pasta_entrada> <pasta_saida>"""
import sys, cv2
from pathlib import Path
MODELO = r"D:\hipercool-materiais\models\rosto\yunet.onnx"
ent, sai = Path(sys.argv[1]), Path(sys.argv[2])
sai.mkdir(parents=True, exist_ok=True)
for f in sorted(ent.glob("*.jpg")):
    img = cv2.imread(str(f))
    h, w = img.shape[:2]
    escala = min(1.0, 1280 / max(h, w))
    peq = cv2.resize(img, (int(w * escala), int(h * escala)))
    det = cv2.FaceDetectorYN.create(MODELO, "", (peq.shape[1], peq.shape[0]), 0.6)
    _, faces = det.detect(peq)
    n = 0
    for fc in (faces if faces is not None else []):
        x, y, fw, fh = [int(v / escala) for v in fc[:4]]
        m = int(max(fw, fh) * 0.35)
        x0, y0, x1, y1 = max(0, x - m), max(0, y - m), min(w, x + fw + m), min(h, y + fh + m)
        roi = img[y0:y1, x0:x1]
        k = max(31, (max(fw, fh) // 2) | 1)
        img[y0:y1, x0:x1] = cv2.GaussianBlur(roi, (k, k), 0)
        n += 1
    cv2.imwrite(str(sai / f.name), img, [cv2.IMWRITE_JPEG_QUALITY, 92])
    print(f.name, "rostos desfocados:", n)
