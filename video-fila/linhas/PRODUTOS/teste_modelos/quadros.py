"""Folha de quadros do vídeo de teste nos instantes pedidos (para a análise da sessão Opus)."""
import subprocess
import sys
from pathlib import Path

from PIL import Image

FF = r"D:\hipercool-materiais\bin\ffmpeg.exe"
mp4, saida = sys.argv[1], Path(sys.argv[2])
ts = [float(x) for x in sys.argv[3].split(",")]
ims = []
for t in ts:
    p = saida.with_name(f"q_{t:05.2f}.png")
    subprocess.run([FF, "-v", "error", "-y", "-ss", str(t), "-i", mp4, "-frames:v", "1", str(p)], check=True)
    ims.append(Image.open(p).convert("RGB").resize((270, 480)))
    p.unlink()
folha = Image.new("RGB", (270 * len(ims), 480))
for i, im in enumerate(ims):
    folha.paste(im, (i * 270, 0))
folha.save(saida, quality=85)
