"""Folhas de quadros para conferir videos antes de aprovar: 5 quadros por video, 3 videos por folha (com rotulo).
Uso: python testes/folhas_quadros.py <lista.json com [{id, mp4, titulo}]> <pasta_saida>"""
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FFMPEG = "D:/hipercool-materiais/bin/ffmpeg.exe"
FFPROBE = "D:/hipercool-materiais/bin/ffprobe.exe"
W, H, N, POR_FOLHA, ROT = 216, 384, 5, 3, 26


def quadro(mp4, t):
    vf = f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2"  # deitado cabe sem achatar
    r = subprocess.run([FFMPEG, "-v", "error", "-ss", f"{t:.2f}", "-i", mp4, "-frames:v", "1", "-vf", vf,
                        "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True)
    from io import BytesIO
    return Image.open(BytesIO(r.stdout)).convert("RGB") if r.stdout else Image.new("RGB", (W, H), "red")


def main():
    lista = json.load(open(sys.argv[1], encoding="utf-8"))
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    fonte = ImageFont.truetype("arial.ttf", 16)
    for f in range(0, len(lista), POR_FOLHA):
        grupo = lista[f:f + POR_FOLHA]
        folha = Image.new("RGB", (W * N, (H + ROT) * len(grupo)), "white")
        d = ImageDraw.Draw(folha)
        for i, v in enumerate(grupo):
            dur = float(subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", v["mp4"]],
                                       capture_output=True, text=True).stdout.strip() or 0)
            y = i * (H + ROT)
            d.text((4, y + 4), f"{f + i + 1}. {v['id']} ({dur:.0f}s) | {v.get('titulo', '')[:70]}", fill="black", font=fonte)
            for k in range(N):
                folha.paste(quadro(v["mp4"], dur * (k + 0.5) / N), (k * W, y + ROT))
        folha.save(out / f"folha_{f // POR_FOLHA + 1:02d}.jpg", quality=85)
        print(out / f"folha_{f // POR_FOLHA + 1:02d}.jpg", flush=True)


if __name__ == "__main__":
    main()
