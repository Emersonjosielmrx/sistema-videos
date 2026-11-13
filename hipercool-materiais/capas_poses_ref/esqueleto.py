# Esqueleto OpenPose (corpo+mãos+rosto) de cada capa de pose, pro ControlNet copiar só a pose (não o corpo).
#   python esqueleto.py <pose.png> [...]   -> <pasta>\esqueleto\<nome>.png
import os
import sys
import types
from pathlib import Path

os.environ.setdefault("HF_HOME", r"D:\caches\huggingface")
# o __init__ do controlnet_aux importa o mediapipe_face, que quebra com o mediapipe novo: não usamos
sys.modules["controlnet_aux.mediapipe_face"] = types.SimpleNamespace(MediapipeFaceDetector=None)
from controlnet_aux.open_pose import OpenposeDetector  # noqa: E402
from PIL import Image  # noqa: E402

det = OpenposeDetector.from_pretrained("lllyasviel/Annotators")
for p in map(Path, sys.argv[1:]):
    im = Image.open(p).convert("RGB")
    im = im.resize((1344, int(1344 * im.height / im.width)))
    out = det(im, include_body=True, include_hand=True, include_face=True, detect_resolution=768,
              image_resolution=1344)
    d = p.parent / "esqueleto"
    d.mkdir(exist_ok=True)
    out.save(d / p.name)
    print("ok", d / p.name)
