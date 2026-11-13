import sys
from PIL import Image, ImageDraw
from pathlib import Path
r = Path(r"D:\hipercool-materiais\capas_proximo_G1_iPga6nLg\proximos")
fs = [r / a for a in sys.argv[1:]]
W, H = 640, 360
sh = Image.new("RGB", (W * 3, H * ((len(fs) + 2) // 3)))
for i, f in enumerate(fs):
    im = Image.open(f).convert("RGB").resize((W, H))
    ImageDraw.Draw(im).text((8, 8), f.parent.parent.name[:6] + " " + f.parent.name[:14] + " " + f.stem, fill="yellow")
    sh.paste(im, ((i % 3) * W, (i // 3) * H))
sh.save(r"D:\hipercool-materiais\_folha_novas.jpg", quality=85)
