r"""hero_quadros.py — quadros do topo das landings (28/10, dona: "imagens no topo como no Hermes Call, que vão trocando
ao rolar e dão a ilusão de movimento, tipo Apple; sem foto do produto, crie imagens que simulem").

Para cada produto: a conversa SIMULADA (conversas.json) é animada pelo MESMO chat_ui dos vídeos de produto
(postador-de-videos\bin\produto\chat_ui.py, cores do site), viram N quadros e cada quadro é montado num fundo largo
1600x1000: celular à direita, girando de leve e chegando perto conforme a rolagem avança, brilho na cor do site.
Saída: site\<slug>\quadros\q00.webp ... (o gerar.py monta o hero com eles).

    D:\veo\venv\Scripts\python.exe hero_quadros.py [slug ...]
"""
import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

BASE = Path(__file__).resolve().parent
sys.path.insert(0, r"D:\postador-de-videos\bin")
from produto import chat_ui  # noqa: E402

FF = r"D:\hipercool-materiais\bin\ffmpeg.exe"
N = 30                      # quadros por produto
DUR = 6.0                   # segundos da conversa animada
LW, LH = 1600, 1000         # quadro final (cobre a tela; no celular o CSS mostra a parte do aparelho)
PRIMARIA, SECUNDARIA = (79, 70, 229), (15, 97, 228)
AREA = (200, 230, 880, 1650)  # cartão do chat no vídeo 1080x1920 do chat_ui (proporção de celular)


def fundo():
    im = Image.new("RGB", (LW, LH), (5, 5, 8))
    brilho = Image.new("RGB", (LW, LH), (0, 0, 0))
    d = ImageDraw.Draw(brilho)
    d.ellipse((900, 80, 1500, 900), fill=PRIMARIA)
    d.ellipse((1050, 300, 1650, 1100), fill=SECUNDARIA)
    return Image.blend(im, brilho.filter(ImageFilter.GaussianBlur(160)), 0.8)


def aparelho(quadro):
    """Recorta o cartão do chat (com a folga da subida) e põe moldura de celular."""
    x0, y0, x1, y1 = AREA
    tela = quadro.crop((x0 - 10, y0 - 70, x1 + 10, y1 + 20)).convert("RGBA")
    m = 26
    cel = Image.new("RGBA", (tela.width + 2 * m, tela.height + 2 * m), (0, 0, 0, 0))
    d = ImageDraw.Draw(cel)
    d.rounded_rectangle((0, 0, cel.width - 1, cel.height - 1), radius=90, fill=(18, 18, 24, 255),
                        outline=(70, 70, 90, 255), width=4)
    mascara = Image.new("L", tela.size, 0)
    ImageDraw.Draw(mascara).rounded_rectangle((0, 0, tela.width - 1, tela.height - 1), radius=66, fill=255)
    cel.paste(tela, (m, m), mascara)
    return cel


def montar(cel, p, base):
    """p 0..1: o aparelho gira de -9° a 0°, sobe e cresce de 0,82 a 1 (efeito de vitrine da Apple)."""
    e = 1 - (1 - p) ** 2
    alt = int(LH * (0.80 + 0.14 * e))
    c = cel.resize((int(cel.width * alt / cel.height), alt), Image.LANCZOS).rotate(-9 * (1 - e), expand=True,
                                                                                    resample=Image.BICUBIC)
    im = base.copy().convert("RGBA")
    sombra = Image.new("RGBA", im.size, (0, 0, 0, 0))
    cx, cy = int(LW * 0.72), int(LH * 0.54 - 30 * e)
    sx, sy = cx - c.width // 2, cy - c.height // 2
    ImageDraw.Draw(sombra).rounded_rectangle((sx + 30, sy + 50, sx + c.width + 10, sy + c.height + 40), radius=90,
                                             fill=(0, 0, 0, 170))
    im = Image.alpha_composite(im, sombra.filter(ImageFilter.GaussianBlur(40)))
    im.alpha_composite(c, (sx, sy))
    return im.convert("RGB")


def gerar(slug, nome, conversa):
    pasta = BASE / "site" / slug / "quadros"
    pasta.mkdir(parents=True, exist_ok=True)
    kit = {"cor": PRIMARIA, "escuro": (5, 5, 8), "texto": (255, 255, 255), "nome_produto": nome}
    with tempfile.TemporaryDirectory() as tmp:
        mp4 = Path(tmp) / "conversa.mp4"
        chat_ui.render(kit, [{"de": de, "texto": t} for de, t in conversa], DUR, mp4, area=AREA)
        subprocess.run([FF, "-v", "error", "-y", "-i", str(mp4), "-vf", f"fps={N / DUR}", "-frames:v", str(N),
                        str(Path(tmp) / "f%02d.png")], check=True)
        base = fundo()
        for i in range(N):
            q = Image.open(Path(tmp) / f"f{i + 1:02d}.png").convert("RGB")
            montar(aparelho(q), i / (N - 1), base).save(pasta / f"q{i:02d}.webp", quality=72, method=5)
    return N


def main():
    conv = json.loads((BASE / "conversas.json").read_text(encoding="utf-8"))
    nomes = {p["slug"]: p["nome"] for p in json.loads((BASE / "conteudo.json").read_text(encoding="utf-8"))["produtos"]}
    for slug in (sys.argv[1:] or [s for s in conv if not s.startswith("_")]):
        n = gerar(slug, nomes[slug], conv[slug])
        kb = sum(f.stat().st_size for f in (BASE / "site" / slug / "quadros").glob("*.webp")) // 1024
        print(f"{slug}: {n} quadros ({kb} KB)", flush=True)


if __name__ == "__main__":
    main()
