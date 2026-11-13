"""Cenas desenhadas quadro a quadro (PIL -> ffmpeg).

  texto_atras  o assunto da foto é recortado (rembg) e o texto grande passa ATRÁS dele (efeito "profundidade" do
               vídeo do Tiago Lemos); se o recorte não acha um assunto claro, cai sozinho no kenburns
  kenburns     zoom lento no ponto de foco + texto grande na frente, com caixa escura para ler
Os dois: zoom suave rumo ao `foco` (x, y de 0 a 1, escolhido pelo Claude olhando a imagem) e texto que sobe e
aparece em 0,45 s. Nada de texto na faixa da legenda (y 1280..1580) nem na faixa da interface do Reels.
"""
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

sys.path.append(r"D:\postador-de-videos\bin")
from produto import kit as kit_mod  # noqa: E402
from produto.video import FF, FPS, H, W  # noqa: E402

# centro vertical do bloco de texto por posição (a legenda karaokê ocupa 1280..1580)
POSICOES = {"topo": 470, "meio": 820}
_sessao_rembg = None


def _fonte(tam):
    return ImageFont.truetype(kit_mod.FONTE_BLACK, tam)


def _quebrar(d, texto, f, largura):
    linhas, atual = [], ""
    for p in texto.split():
        t = (atual + " " + p).strip()
        if d.textlength(t, font=f) <= largura or not atual:
            atual = t
        else:
            linhas.append(atual)
            atual = p
    return linhas + ([atual] if atual else [])


def recorte(img):
    """Máscara L do assunto principal, ou None se não há um assunto claro (5%..80% da tela)."""
    global _sessao_rembg
    from rembg import new_session, remove
    if _sessao_rembg is None:
        _sessao_rembg = new_session("isnet-general-use")
    m = remove(img, session=_sessao_rembg, only_mask=True)
    m = m.convert("L").resize(img.size)
    cob = sum(m.point(lambda v: 255 if v > 128 else 0).histogram()[255:]) / (W * H)
    if not 0.05 <= cob <= 0.80:
        return None, cob
    return m.filter(ImageFilter.GaussianBlur(1.2)), cob


def bloco_texto(texto, cor, caixa, tamanho=1.0):
    """RGBA do texto grande (maiúsculas, até 3 linhas). caixa=True põe faixa escura atrás (texto na frente)."""
    im = Image.new("RGBA", (W, 700), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    tam = int(150 * tamanho)
    while True:
        f = _fonte(tam)
        linhas = _quebrar(d, texto.upper(), f, W - 140)
        if len(linhas) <= 3 and max(d.textlength(ln, font=f) for ln in linhas) <= W - 140 or tam <= 60:
            break
        tam -= 6
    alt_ln = int(tam * 1.08)
    alt = alt_ln * len(linhas)
    y0 = (700 - alt) // 2
    if caixa:
        larg = max(d.textlength(ln, font=f) for ln in linhas)
        d.rounded_rectangle(((W - larg) / 2 - 40, y0 - 30, (W + larg) / 2 + 40, y0 + alt + 30), radius=34,
                            fill=(0, 0, 0, 150))
    sombra = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ds = ImageDraw.Draw(sombra)
    for i, ln in enumerate(linhas):
        x = (W - d.textlength(ln, font=f)) / 2
        ds.text((x + 5, y0 + i * alt_ln + 8), ln, font=f, fill=(0, 0, 0, 170))
    im.alpha_composite(sombra.filter(ImageFilter.GaussianBlur(9)))
    for i, ln in enumerate(linhas):
        x = (W - d.textlength(ln, font=f)) / 2
        d.text((x, y0 + i * alt_ln), ln, font=f, fill=cor, stroke_width=3, stroke_fill=(0, 0, 0))
    return im


def _zoom(im, z, fx, fy):
    """Recorte da imagem ampliada z vezes centrado (o quanto der) no foco."""
    cw, ch = W / z, H / z
    x0 = min(max(fx * W - cw / 2, 0), W - cw)
    y0 = min(max(fy * H - ch / 2, 0), H - ch)
    return im.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + cw, y0 + ch))   # bicúbico: 2x mais lento, igual a olho


def cena(img, dur, saida, texto, cor, efeito="kenburns", posicao="topo", foco=(0.5, 0.5), tamanho=1.0,
         log=print):
    """Grava a cena em mp4. Devolve o efeito que de fato usou."""
    img = ImageOps.fit(img.convert("RGB"), (W, H), method=Image.LANCZOS)
    mask = None
    if efeito == "texto_atras":
        mask, cob = recorte(img)
        if mask is None:
            log(f"    [efeito] recorte sem assunto claro ({cob:.0%} da tela) — vira kenburns")
            efeito = "kenburns"
    txt = bloco_texto(texto, cor, caixa=(efeito != "texto_atras"), tamanho=tamanho) if texto else None
    cy = POSICOES.get(posicao, POSICOES["topo"])
    sujeito = None
    if mask is not None:
        sujeito = img.convert("RGBA")
        sujeito.putalpha(mask)
    n = int(round(dur * FPS))
    fx, fy = foco
    p = subprocess.Popen([FF, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r",
                          str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt",
                          "yuv420p", str(saida)], stdin=subprocess.PIPE)
    try:
        for q in range(n):
            t = q / FPS
            z = 1.0 + 0.09 * (t / max(dur, 0.1))
            quadro = _zoom(img, z, fx, fy).convert("RGBA")
            if txt is not None:
                a = min(max((t - 0.15) / 0.45, 0), 1)
                a = 1 - (1 - a) ** 3
                if a > 0:
                    camada = txt if a >= 1 else txt.copy()
                    if a < 1:
                        camada.putalpha(camada.getchannel("A").point(lambda v, k=a: int(v * k)))
                    quadro.alpha_composite(camada, (0, int(cy - 350 + 60 * (1 - a))))
            if sujeito is not None:
                quadro.alpha_composite(_zoom(sujeito, z, fx, fy))
            p.stdin.write(quadro.convert("RGB").tobytes())
    finally:
        p.stdin.close()
        p.wait(timeout=600)
    if p.returncode:
        raise RuntimeError("ffmpeg da cena falhou")
    return efeito
