from PIL import Image
p = r"D:\ms-energy\assets\logo\sem_fundo\ms_energy_logo_original.png"
im = Image.open(p).convert("RGBA")
px = im.load()
for y in range(im.height):
    for x in range(im.width):
        r, g, b, a = px[x, y]
        if 0 < a < 255:  # tira o preto misturado na borda (fundo era preto): cor / alfa
            f = 255.0 / a
            px[x, y] = (min(255, int(r * f)), min(255, int(g * f)), min(255, int(b * f)), a)
im.save(p)
c = Image.new("RGBA", (im.width + 20, im.height + 20), (235, 235, 235, 255))
c.alpha_composite(im, (10, 10))
c.convert("RGB").save(r"D:\video-fila\_tmp_logo_prova.jpg")
