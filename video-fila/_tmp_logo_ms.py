import os
from PIL import Image, ImageFilter
src = r"D:\ms-energy\assets\logo\perfil_instagram.jpg"
out = r"D:\ms-energy\assets\logo\sem_fundo"
os.makedirs(out, exist_ok=True)
im = Image.open(src).convert("RGB")
# amplia 5x antes de recortar (bordas mais limpas)
big = im.resize((im.width * 5, im.height * 5), Image.LANCZOS)
px = big.load()
alpha = Image.new("L", big.size)
ap = alpha.load()
for y in range(big.height):
    for x in range(big.width):
        r, g, b = px[x, y]
        m = max(r, g, b)
        # fundo preto/quase preto -> transparente; borda suave entre 25 e 70
        a = 0 if m < 25 else 255 if m > 70 else int((m - 25) / 45 * 255)
        ap[x, y] = a
alpha = alpha.filter(ImageFilter.GaussianBlur(0.8))
rgba = big.convert("RGBA")
rgba.putalpha(alpha)
bbox = alpha.point(lambda v: 255 if v > 40 else 0).getbbox()
rgba = rgba.crop(bbox)
alpha_c = rgba.split()[3]
rgba.save(os.path.join(out, "ms_energy_logo_original.png"))
for nome, cor in (("branca", (255, 255, 255)), ("preta", (0, 0, 0)), ("vermelha", (200, 30, 40))):
    lisa = Image.new("RGBA", rgba.size, cor + (255,))
    lisa.putalpha(alpha_c)
    lisa.save(os.path.join(out, f"ms_energy_logo_{nome}.png"))
print(rgba.size)
