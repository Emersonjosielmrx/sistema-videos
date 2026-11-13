"""Carrossel PROFISSIONAL de produto feito do MESMO roteiro aprovado do vídeo (agentes.py): a mensagem do Reel e do
carrossel fica igual, as imagens já aprovadas são reaproveitadas e a conversa do produto vira slide.

  capa  — pergunta de cliente grande sobre a imagem, selo da marca, "Arraste para o lado →"
  2..4  — "1 · O problema" / "2 · Como funciona" (com a conversa do produto) / "3 · O resultado"
  final — marca, o que o produto faz, "Link no perfil", @conta

Sai em D:\\video-fila\\carrosseis_marcas\\<conta>\\<data>_produto\\ no formato do carrossel_marca (meta.json +
slide_1..5.jpg): o carrossel_marca.postar() posta (carrossel de verdade com token; Reel de slides pelo navegador).
"""
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageOps

BIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BIN))
from produto import agentes, chat_ui, video  # noqa: E402
from produto import kit as kit_mod  # noqa: E402

W, H = 1080, 1350
DIR = Path(r"D:\video-fila\carrosseis_marcas")
FF = r"D:\hipercool-materiais\bin\ffmpeg.exe"


def _f(c, t):
    return video._f(c, t)


def _degrade(im, de_y, ate_y, alfa, cor, de_baixo=True):
    g = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(g)
    for y in range(de_y, ate_y):
        f = (y - de_y) / max(ate_y - de_y, 1)
        d.line([(0, y), (im.width, y)], fill=cor + (int(alfa * (f if de_baixo else 1 - f)),))
    return Image.alpha_composite(im, g)


def _selo(d, k, x, y, tam=36):
    f = _f(kit_mod.FONTE_BLACK, tam)
    lw = d.textlength(k["marca"], font=f)
    d.rounded_rectangle((x, y, x + lw + 56, y + tam + 32), radius=(tam + 32) // 2, fill=k["cor"])
    d.text((x + 28, y + 13), k["marca"], font=f, fill=k["texto"])


def _caber(d, texto, fonte, tam, larg, max_linhas, minimo=30):
    while True:
        f = _f(fonte, tam)
        ls = video._quebrar(d, texto, f, larg)
        if len(ls) <= max_linhas or tam <= minimo:
            return f, ls
        tam -= 2


def capa(k, pergunta, img, destino, centro_y=0.5):
    # centro_y > 0.5 sobe a foto (26/10: o rosto do dono ficava atrás do texto da pergunta)
    im = ImageOps.fit(img, (W, H), centering=(0.5, centro_y)).convert("RGBA")
    im = _degrade(im, int(H * 0.3), H, 240, k["escuro"])
    im = _degrade(im, 0, 230, 160, k["escuro"], de_baixo=False)
    d = ImageDraw.Draw(im)
    _selo(d, k, 50, 46)
    f, ls = _caber(d, pergunta, kit_mod.FONTE_BLACK, 96, W - 120, 4)
    y = H - 200 - len(ls) * int(f.size * 1.14)
    d.rectangle((60, y - 36, 230, y - 22), fill=k["cor"])
    for ln in ls:
        d.text((60, y), ln, font=f, fill="white")
        y += int(f.size * 1.14)
    d.text((60, H - 118), "Arraste para o lado  →", font=_f(kit_mod.FONTE_XBOLD, 38), fill=(228, 228, 228))
    im.convert("RGB").save(destino, quality=93)


def slide(k, n, rotulo, texto, img, destino, conversa=None):
    escuro = k["escuro"]
    im = Image.new("RGBA", (W, H), escuro + (255,))
    d = ImageDraw.Draw(im)
    if conversa:  # o último quadro da conversa animada, ocupando o alto do slide
        tmp = destino.with_suffix(".chat.mp4")
        chat_ui.render(k, conversa, 3.2, tmp, area=(70, 70, 1010, 760), fundo=img)
        png = destino.with_suffix(".chat.png")
        subprocess.run([FF, "-y", "-v", "error", "-sseof", "-0.1", "-i", str(tmp), "-frames:v", "1", str(png)],
                       check=True, timeout=120)
        alto = Image.open(png).convert("RGB").crop((0, 0, W, 800))
        im.paste(alto, (0, 0))
        tmp.unlink(missing_ok=True)
        png.unlink(missing_ok=True)
        y = 830
    else:
        alto = 700
        im.paste(ImageOps.fit(img, (W, alto)).convert("RGBA"), (0, 0))
        im = _degrade(im, alto - 230, alto, 255, escuro)
        d = ImageDraw.Draw(im)
        y = alto - 40
    d = ImageDraw.Draw(im)
    # número em círculo + rótulo
    d.ellipse((60, y, 140, y + 80), fill=k["cor"])
    num = str(n)
    fn = _f(kit_mod.FONTE_BLACK, 50)
    d.text((100 - d.textlength(num, font=fn) / 2, y + 10), num, font=fn, fill=k["texto"])
    fr, lr = _caber(d, rotulo, kit_mod.FONTE_BLACK, 64, W - 260, 1)
    d.text((165, y + 6), lr[0] if lr else rotulo, font=fr, fill="white")
    y += 120
    fx, lx = _caber(d, texto, kit_mod.FONTE_XBOLD, 50, W - 140, 6, minimo=36)
    for ln in lx:
        d.text((70, y), ln, font=fx, fill=(236, 236, 236))
        y += int(fx.size * 1.32)
    _selo(d, k, 60, H - 100, 28)
    fa = _f(kit_mod.FONTE_XBOLD, 32)
    d.text((W - 60 - d.textlength(k["arroba"], font=fa), H - 84), k["arroba"], font=fa, fill=(205, 205, 205))
    im.convert("RGB").save(destino, quality=93)


def final(k, img, destino):
    cartao = video.card_final(k, ImageOps.fit(img, (video.W, video.H)))
    ImageOps.fit(cartao, (W, H), centering=(0.5, 0.42)).save(destino, quality=93)


def do_roteiro(conta, r, imgs, log=print, base=None):
    """Gera o carrossel de um roteiro aprovado. imgs = imagens PIL dos blocos (None = banco/degradê).
    base = pasta de teste (fora da fila que o carrossel_marca posta)."""
    k = kit_mod.kit(conta)
    pasta = (Path(base) if base else DIR / conta) / (datetime.now().strftime("%Y%m%d_%H%M") + "_produto")
    pasta.mkdir(parents=True, exist_ok=True)
    def img_de(i):
        im = imgs[i] if i < len(imgs) and imgs[i] is not None else None
        if im is None:
            im, _ = video.do_banco(k)
        return im or video.fundo_marca(k)
    foto_dono = r["blocos"][0].get("foto_dono")
    if foto_dono and Path(foto_dono).exists():  # 25/10 (dono): ele na capa, no cenário do vídeo
        capa(k, r["pergunta_cliente"], Image.open(foto_dono).convert("RGB"), pasta / "slide_1.jpg", centro_y=0.8)
    else:
        capa(k, r["pergunta_cliente"], img_de(0), pasta / "slide_1.jpg")
    for i, b in enumerate(r["blocos"]):
        conv = b.get("conversa") if b.get("visual") == "conversa" else None
        slide(k, i + 1, b["rotulo"].strip().capitalize(), b["fala"], img_de(i), pasta / f"slide_{i + 2}.jpg",
              conversa=conv)
    final(k, img_de(0), pasta / "slide_5.jpg")
    meta = {"conta": conta, "marca": k["marca"], "capa": r["pergunta_cliente"], "origem": "roteiro do vídeo de produto",
            "slides": [{"titulo": b["rotulo"], "texto": b["fala"]} for b in r["blocos"]],
            "legenda": agentes.legenda_final(k, r), "gerado_em": datetime.now().isoformat(timespec="seconds")}
    (pasta / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), "utf-8")
    log(f"  [carrossel] {pasta}")
    return pasta


def pendente(conta, dias=4):
    """Carrossel de produto pronto e ainda não postado (o carrossel_marca posta este antes de gerar outro)."""
    import time
    pasta = DIR / conta
    if not pasta.exists():
        return None
    for p in sorted(pasta.glob("*_produto/meta.json"), reverse=True):
        try:
            m = json.loads(p.read_text("utf-8"))
        except Exception:  # noqa: BLE001
            continue
        if not m.get("postado") and p.stat().st_mtime > time.time() - dias * 86400:
            return p.parent
    return None
