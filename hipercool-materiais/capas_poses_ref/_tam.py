from PIL import Image
from pathlib import Path
r=Path(r'D:\hipercool-materiais\capas_poses_ref\recebidas')
for i in range(1,6):
    im=Image.open(r/f'e57270d3_{i}.png'); print(i, im.size)
