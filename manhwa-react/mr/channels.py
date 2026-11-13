"""Kit de canal: foto de perfil (com sua foto), banner, marca d'agua 150x150, descricao e configuracao sugerida.

Fundo: arte gerada por IA (ch["arte"] = {"perfil": prompt, "banner": prompt}, ver mr/imagem.py) ou degrade na cor do canal.
Rosto: sempre a foto REAL do criador por composicao (o modelo de imagem nao copia rosto de referencia)."""
import json
import glob
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
from .common import log


def _hex(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _font(cfg, name, size):
    p = Path(cfg["paths"]["assets"]) / "fonts" / name
    try:
        return ImageFont.truetype(str(p), size)
    except Exception:  # noqa: BLE001
        return ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", size)


def _gradient(size, c1, c2):
    w, h = size
    row = np.linspace(0, 1, w, dtype=np.float32)[None, :, None]
    col = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    t = (row + col) / 2
    a = np.array(c1, np.float32)[None, None, :]
    b = np.array(c2, np.float32)[None, None, :]
    arr = (a + (b - a) * t).astype(np.uint8)
    return Image.fromarray(arr, "RGB")


def _initials(name):
    caps = [c for c in name if c.isupper()]
    return "".join(caps[:2]) if len(caps) >= 2 else name[:2].upper()


# ----------------------------------------------------------------------------- foto
def _load_photo(path):
    im = Image.open(path)
    im = ImageOps.exif_transpose(im).convert("RGB")
    return im


def _face_box(cfg, im):
    """Caixa do rosto (x0,y0,x1,y1) via MediaPipe; None se nao achar."""
    try:
        import mediapipe as mp
        from mediapipe.tasks import python as mpp
        from mediapipe.tasks.python import vision
        model = str(Path(cfg["paths"]["assets"]) / "models" / "face_landmarker.task")
        opts = vision.FaceLandmarkerOptions(base_options=mpp.BaseOptions(model_asset_path=model), running_mode=vision.RunningMode.IMAGE, num_faces=1)
        lm = vision.FaceLandmarker.create_from_options(opts)
        small = im.copy()
        small.thumbnail((800, 800))
        sx, sy = im.width / small.width, im.height / small.height
        r = lm.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.array(small)))
        lm.close()
        if not r.face_landmarks:
            return None
        xs = [p.x * small.width * sx for p in r.face_landmarks[0]]
        ys = [p.y * small.height * sy for p in r.face_landmarks[0]]
        return (min(xs), min(ys), max(xs), max(ys))
    except Exception as e:  # noqa: BLE001
        log(f"rosto: mediapipe indisponivel ({e})")
        return None


def face_crop(cfg, im, size, zoom=2.1, y_bias=0.42):
    """Recorte quadrado centrado no rosto (zoom = quantas vezes o rosto cabe no quadrado)."""
    box = _face_box(cfg, im)
    if box:
        fx0, fy0, fx1, fy1 = box
        fw, fh = fx1 - fx0, fy1 - fy0
        side = int(max(fw, fh) * zoom)
        cx = (fx0 + fx1) / 2
        cy = fy0 + fh * y_bias
    else:
        side = min(im.width, im.height)
        cx, cy = im.width / 2, im.height * 0.4
    if side > min(im.width, im.height):
        # selfie muito proxima: estende a foto com ela mesma desfocada (no maximo +25%), emenda suavizada
        side = min(side, int(min(im.width, im.height) * 1.25))
        pad = int((side - min(im.width, im.height)) / 2) + 24
        fundo = im.resize((im.width + 2 * pad, im.height + 2 * pad), Image.LANCZOS).filter(ImageFilter.GaussianBlur(28))
        borda = Image.new("L", im.size, 0)
        f = max(8, pad // 2)
        ImageDraw.Draw(borda).rectangle([f, f, im.width - f, im.height - f], fill=255)
        fundo.paste(im, (pad, pad), borda.filter(ImageFilter.GaussianBlur(f / 2)))
        im, cx, cy = fundo, cx + pad, cy + pad
    side = int(min(side, im.width, im.height))
    x0 = int(max(0, min(im.width - side, cx - side / 2)))
    y0 = int(max(0, min(im.height - side, cy - side / 2)))
    return im.crop((x0, y0, x0 + side, y0 + side)).resize((size, size), Image.LANCZOS)


def _circle(im, border=0, color=(255, 255, 255)):
    s = im.width
    mask = Image.new("L", (s * 4, s * 4), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, s * 4 - 1, s * 4 - 1], fill=255)
    mask = mask.resize((s, s), Image.LANCZOS)
    out = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    out.paste(im, (0, 0), mask)
    if border:
        d = ImageDraw.Draw(out)
        d.ellipse([border // 2, border // 2, s - border // 2 - 1, s - border // 2 - 1], outline=color, width=border)
    return out


def pick_photo(cfg, ch):
    """Foto do canal: ch['photo'] (caminho ou indice na pasta de retratos) ou a primeira da pasta."""
    folder = Path(cfg["paths"].get("photos_dir", ""))
    spec = ch.get("photo")
    if spec and Path(str(spec)).exists():
        return Path(spec)
    files = sorted(glob.glob(str(folder / "*.jpg")) + glob.glob(str(folder / "*.jpeg")) + glob.glob(str(folder / "*.png")))
    if not files:
        return None
    if isinstance(spec, int) and 0 <= spec < len(files):
        return Path(files[spec])
    return Path(files[0])



def _arte(cfg, ch, peca, aspect):
    """Arte de fundo gerada por IA (cache em assets/ai_cache); None sem prompt ou se o gateway falhar."""
    prompt = (ch.get("arte") or {}).get(peca)
    if not prompt:
        return None
    from .imagem import gerar
    p = gerar(cfg, prompt, aspect=aspect)
    return Image.open(p).convert("RGB") if p else None


def _cover(im, w, h):
    esc = max(w / im.width, h / im.height)
    im = im.resize((int(im.width * esc + 0.5), int(im.height * esc + 0.5)), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((x, y, x + w, y + h))


def _brilho(size, raio, col):
    """Aura na cor do canal atras da foto redonda."""
    g = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(g).ellipse([size / 2 - raio - 18, size / 2 - raio - 18, size / 2 + raio + 18, size / 2 + raio + 18], fill=col + (200,))
    return g.filter(ImageFilter.GaussianBlur(26))


# ----------------------------------------------------------------------------- pecas
def make_profile(cfg, ch, out, photo):
    S = 800
    col = _hex(ch["color"])
    arte = _arte(cfg, ch, "perfil", "1:1")
    if arte:
        bg = _cover(arte, S, S).filter(ImageFilter.GaussianBlur(1))
    else:
        bg = _gradient((S, S), tuple(max(0, c - 110) for c in col), col).filter(ImageFilter.GaussianBlur(2))
        d = ImageDraw.Draw(bg)
        for i in range(-S, S * 2, 90):
            d.line([(i, 0), (i + S, S)], fill=tuple(min(255, c + 25) for c in col), width=2)
    canvas = bg.convert("RGBA")
    d = ImageDraw.Draw(canvas)
    if photo:
        face = face_crop(cfg, _load_photo(photo), S - 150, zoom=2.2, y_bias=0.4)
        canvas.alpha_composite(_brilho(S, (S - 150) // 2 + 14, col), (0, 0))
        canvas.alpha_composite(_circle(face, border=12, color=col), (75, 75))
    else:
        d.ellipse([70, 70, S - 70, S - 70], fill=(14, 14, 20), outline=(255, 255, 255), width=6)
        f = _font(cfg, "Montserrat-Black.ttf", 300)
        ini = _initials(ch["name"])
        tw = d.textlength(ini, font=f)
        d.text(((S - tw) / 2, S / 2 - 200), ini, font=f, fill=(255, 255, 255))
    d = ImageDraw.Draw(canvas)
    f2 = _font(cfg, "Montserrat-ExtraBold.ttf", 46)
    label = ch["name"].upper()
    tw2 = d.textlength(label, font=f2)
    d.rounded_rectangle([(S - tw2) / 2 - 28, S - 150, (S + tw2) / 2 + 28, S - 76], radius=36, fill=col)
    d.text(((S - tw2) / 2, S - 140), label, font=f2, fill=(255, 255, 255))
    canvas.convert("RGB").save(out, quality=95)


def make_banner(cfg, ch, out, photo):
    W, H = 2560, 1440
    col = _hex(ch["color"])
    arte = _arte(cfg, ch, "banner", "16:9")
    if arte:
        img = _cover(arte, W, H).convert("RGBA")
        # escurece a faixa do texto (area segura) para ler em qualquer fundo
        sombra = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(sombra).rounded_rectangle([(W - 1640) // 2, (H - 520) // 2, (W + 1640) // 2, (H + 520) // 2], radius=60, fill=(0, 0, 0, 120))
        img.alpha_composite(sombra.filter(ImageFilter.GaussianBlur(40)))
    else:
        img = _gradient((W, H), (12, 12, 18), tuple(max(0, c - 120) for c in col)).convert("RGBA")
        d = ImageDraw.Draw(img)
        for i in range(-H, W + H, 160):
            d.line([(i, 0), (i + H, H)], fill=tuple(min(255, c // 3 + 20) for c in col), width=3)
    sx, sy = (W - 1546) // 2, (H - 423) // 2   # area segura (celular/TV)
    # foto circular dentro da area segura, a esquerda
    tx = sx + 40
    if photo:
        face = face_crop(cfg, _load_photo(photo), 390, zoom=2.2, y_bias=0.4)
        brilho = _brilho(520, 209, col)
        img.alpha_composite(brilho, (sx + 20 + 195 - 260, sy + 16 + 195 - 260))
        img.alpha_composite(_circle(face, border=10, color=col), (sx + 20, sy + 16))
        tx = sx + 20 + 390 + 60
    d = ImageDraw.Draw(img)
    f1 = _font(cfg, "Montserrat-Black.ttf", 132)
    f2 = _font(cfg, "Montserrat-ExtraBold.ttf", 52)
    f3 = _font(cfg, "Montserrat-ExtraBold.ttf", 36)
    name = ch["name"]
    largura = sx + 1546 - tx - 10  # o nome cabe inteiro na area segura (diminui a letra se precisar)
    size = 132
    while size > 70 and d.textlength(name, font=f1) > largura:
        size -= 6
        f1 = _font(cfg, "Montserrat-Black.ttf", size)
    while d.textlength(ch.get("tagline", ""), font=f2) > largura and f2.size > 34:
        f2 = _font(cfg, "Montserrat-ExtraBold.ttf", f2.size - 4)
    d.text((tx + 6, sy + 36), name, font=f1, fill=(0, 0, 0))
    d.text((tx, sy + 30), name, font=f1, fill=(255, 255, 255), stroke_width=4, stroke_fill=(0, 0, 0))
    claro = tuple(min(255, int(c * 0.6 + 255 * 0.4)) for c in col)
    d.text((tx, sy + 200), ch.get("tagline", ""), font=f2, fill=claro, stroke_width=5, stroke_fill=(0, 0, 0))
    pill = ch.get("pill", "NOVO SHORT TODO DIA") + "  |  " + ch["handle"]
    tw3 = d.textlength(pill, font=f3)
    d.rounded_rectangle([tx, sy + 290, tx + tw3 + 60, sy + 356], radius=33, fill=(255, 255, 255))
    d.text((tx + 30, sy + 302), pill, font=f3, fill=(12, 12, 18))
    img.convert("RGB").save(out, quality=92)


def make_watermark(cfg, ch, out):
    """Marca d'agua do YouTube (150x150, PNG com transparencia): circulo na cor do canal + iniciais."""
    S = 150
    col = _hex(ch["color"])
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([2, 2, S - 3, S - 3], fill=col + (235,), outline=(255, 255, 255, 255), width=4)
    f = _font(cfg, "Montserrat-Black.ttf", 66)
    ini = _initials(ch["name"])
    tw = d.textlength(ini, font=f)
    d.text(((S - tw) / 2, S / 2 - 44), ini, font=f, fill=(255, 255, 255, 255))
    img.save(out)


def write_docs(cfg, ch, folder):
    kw = ch.get("keywords", [])
    (folder / "descricao.txt").write_text(ch.get("description", "") + "\n", encoding="utf-8")
    (folder / "palavras_chave.txt").write_text(", ".join(kw) + "\n", encoding="utf-8")
    md = [f"# {ch['name']} ({ch['handle']})", "",
          *( [f"**Projeto que produz os videos:** `{ch['projeto']}`", ""] if ch.get("projeto") else [] ),
          *( [f"**Atencao:** {ch['nota']}", ""] if ch.get("nota") else [] ),
          f"**Nicho:** {ch['niche']}", "", f"**Slogan:** {ch.get('tagline', '')}", "",
          "## Descricao do canal (tambem em descricao.txt)", "", ch.get("description", ""), "",
          "## Palavras-chave do canal (tambem em palavras_chave.txt)", "", ", ".join(kw), "",
          "## Arquivos", "", "- `perfil.png` - foto de perfil 800x800 com a sua foto",
          "- `banner.png` - banner 2560x1440 (foto e texto dentro da area segura 1546x423)",
          "- `marca_dagua.png` - marca d'agua 150x150 (YouTube Studio > Personalizacao > Marca > Marca d'agua do video)", "",
          "## Padrao de postagem", "",
          "- 1 a 2 Shorts por dia, horarios fixos (ex.: 12h e 19h), aprovacao humana antes de publicar.",
          "- Titulo com 2 hashtags (#shorts + tema); descricao com 10-15 hashtags; 12-20 tags (meta.txt de cada video).",
          f"- Faixa no video: `{ch['handle']}`; cor da marca: `{ch['color']}`.",
          "- Fixar comentario com pergunta pro publico (engajamento nos primeiros minutos).", "",
          "## Checklist de criacao", "",
          "1. Criar o canal no YouTube com este nome e tentar o handle acima (ou variacao: BR, Oficial).",
          "2. Subir `perfil.png`, `banner.png` e `marca_dagua.png`; colar `descricao.txt` e `palavras_chave.txt`.",
          "3. Pais: Brasil; idioma: Portugues (Brasil); categoria padrao: Entretenimento.",
          "4. Gerar o token OAuth (`D:\\credenciais-canais\\relogin_canal.py`) e registrar em `youtube_canais.json` com o nome exato acima.",
          ""]
    (folder / "canal.md").write_text("\n".join(md), encoding="utf-8")
    cfg_doc = {"nome": ch["name"], "handle": ch["handle"], "slug": ch["slug"], "cor": ch["color"], "nicho": ch["niche"],
               "descricao": ch.get("description", ""), "palavras_chave": kw, "pais": "BR", "idioma": "pt-BR", "categoria_youtube": "24",
               "tem_upload": False, "youtube_canais_nome": ch["name"], "foto": str(pick_photo(cfg, ch) or "")}
    (folder / "canal.json").write_text(json.dumps(cfg_doc, ensure_ascii=False, indent=1), encoding="utf-8")


def generate_kits(cfg, so=None):
    """Kits de todos os canais (config channels = rede de react; channels_outros = canais de outros projetos).
    so = lista de slugs para gerar so esses."""
    root = Path(cfg["paths"].get("channels_dir", "canais"))
    root.mkdir(parents=True, exist_ok=True)
    index = []
    for ch in cfg.get("channels", []) + cfg.get("channels_outros", []):
        if so and ch["slug"] not in so:
            continue
        folder = root / ch["slug"]
        folder.mkdir(exist_ok=True)
        photo = pick_photo(cfg, ch)
        make_profile(cfg, ch, folder / "perfil.png", photo)
        make_banner(cfg, ch, folder / "banner.png", photo)
        make_watermark(cfg, ch, folder / "marca_dagua.png")
        write_docs(cfg, ch, folder)
        index.append({"slug": ch["slug"], "nome": ch["name"], "handle": ch["handle"], "pasta": str(folder), "foto": str(photo or "")})
        log(f"canal: {ch['name']} -> {folder} (foto: {Path(photo).name if photo else 'sem'})")
    if so and (root / "canais.json").exists():
        antigos = [c for c in json.loads((root / "canais.json").read_text(encoding="utf-8")) if c["slug"] not in so]
        index = antigos + index
    (root / "canais.json").write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    (root / "LEIA.md").write_text(
        "# Canais\n\nUm subdiretorio por canal com perfil.png, banner.png, marca_dagua.png, descricao.txt, palavras_chave.txt, canal.md e canal.json.\n"
        "Para adicionar um canal: inclua em `config.json > channels` (campo `photo` = indice ou caminho da foto) e rode `scripts\\canais.bat`.\n"
        "O editorial escolhe o canal de cada video pelo tema; o video pronto vai para `D:\\hipercool-materiais\\manhwa-react\\shorts\\<slug>\\`.\n", encoding="utf-8")
    return index


import numpy as np  # noqa: E402  (usado em _gradient e _face_box)
