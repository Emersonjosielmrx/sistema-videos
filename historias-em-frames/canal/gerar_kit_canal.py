"""Kit do canal Historias em Frames: foto de perfil, banner, marca d'agua, logo e textos.

Uso (regera tudo; troque NOME/HANDLE/FOTO aqui em cima se mudar):
    PYTHONUTF8=1 ..\\venv\\Scripts\\python.exe gerar_kit_canal.py

Banner 2560x1440 com tudo que importa dentro da AREA SEGURA 1546x423 (o que aparece no
celular). A faixa de pelicula atravessa a largura toda (aparece inteira no PC/TV).
"""
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

AQUI = Path(__file__).resolve().parent
FONTES = Path(r"D:\hipercool-materiais\assets\fonts")
FOTOS = Path(r"D:\fotos para videos\fotos\Fotos minhas retrato")

NOME = "Histórias em Frames"
HANDLE = "@HistoriasEmFrames"
SLOGAN = "Histórias que prendem do primeiro ao último frame"
SELO = "NOVA HISTÓRIA TODO DIA"
FOTO_PRINCIPAL = "Screenshot_20250710_195106_Photos.jpg"          # #13 (recorte mais limpo)
FOTOS_OPCOES = ["Screenshot_20250710_195742_Photos.jpg",            # #28
                "Screenshot_20250710_195448_Photos.jpg"]            # #19

OURO = (255, 200, 61)
OURO_ESC = (176, 120, 20)
NOITE = (8, 10, 18)
AZUL = (24, 32, 60)

IMG = Path(r"D:\historias-em-frames\workspace\images")
CENAS = [  # vitrine da pelicula (genero variado, sem texto torto na imagem)
    "terror_470c534a55/scene_03_final.png", "romance_5b24e057dd/scene_07_final.png",
    "superacao_6f80bb78c6/scene_02_final.png", "fantasia_1e96626bb2/scene_05_final.png",
    "comedia_99b06e49e7/scene_00_final.png", "misterio_4224521dcc/scene_03_final.png",
    "religioso_9de340ddc8/scene_03_final.png", "fantasia_d5008b105a/scene_04_final.png",
    "drama_e87609d10c/scene_07_final.png", "fantasia_2e8a044722/scene_01_final.png",
    "motivacional_e5645ea0f6/scene_02_final.png", "religioso_ce0f0001d2/scene_00_final.png",
]


def fonte(nome, tam):
    return ImageFont.truetype(str(FONTES / nome), tam)


# ----------------------------------------------------------------------------- recorte



def _so_a_pessoa(cut):
    """Mantem so a MAIOR area continua da mascara (a pessoa): pedacos soltos de fundo
    que o removedor deixa (placa, cortina) somem."""
    try:
        import cv2
        a = np.asarray(cut)[:, :, 3]
        n, lab, st, _ = cv2.connectedComponentsWithStats((a > 40).astype(np.uint8), 8)
        if n <= 2:
            return cut
        maior = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
        keep = (lab == maior)
        arr = np.asarray(cut).copy()
        arr[:, :, 3] = np.where(keep, arr[:, :, 3], 0)
        out = Image.fromarray(arr, "RGBA")
        bb = out.getbbox()
        return out.crop(bb) if bb else cut
    except Exception:
        return cut


def recorte(foto):
    """Pessoa sem fundo (RGBA), cortada no conteudo. Cache em _cache/."""
    cache = AQUI / "_cache" / (Path(foto).stem + "_cut.png")
    if cache.exists():
        return _so_a_pessoa(Image.open(cache).convert("RGBA"))
    from rembg import new_session, remove
    im = ImageOps.exif_transpose(Image.open(foto)).convert("RGB")
    if im.height > 1600:   # menos memoria (a maquina anda com pouca RAM livre)
        im = im.resize((int(im.width * 1600 / im.height), 1600), Image.LANCZOS)
    cut = None
    import os
    modelos = os.environ.get("RECORTE_MODELOS", "birefnet-portrait,u2net_human_seg").split(",")
    for modelo in modelos:   # birefnet: melhor cabelo/oculos (mas pesado: ~1 GB)
        try:
            sess = new_session(modelo)
            cut = remove(im, session=sess).convert("RGBA")
            print(f"recorte com {modelo}: {Path(foto).name}")
            break
        except Exception as e:
            print(f"recorte: {modelo} falhou ({str(e)[:60]}), tentando o proximo")
    if cut is None:
        raise RuntimeError("nenhum modelo de recorte funcionou")
    a = np.asarray(cut)[:, :, 3]
    ys, xs = np.where(a > 40)
    cut = cut.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
    cache.parent.mkdir(exist_ok=True)
    cut.save(cache)
    return _so_a_pessoa(cut)


def _cabeca(cut):
    """(cx, topo, largura) da cabeca pela SILHUETA do recorte: topo da mascara e largura
    das primeiras linhas (antes dos ombros alargarem). Sem detector de rosto: o Haar nao
    existe mais no OpenCV 5 e o YuNet precisaria baixar modelo."""
    a = np.asarray(cut)[:, :, 3] > 40
    # linha "valida" = pelo menos 4% da largura opaca (ignora pixel solto no topo)
    ys = np.where(a.sum(axis=1) > max(3, cut.width * 0.04))[0]
    if not len(ys):
        return None
    topo = int(ys[0])
    alt = int(ys[-1]) - topo
    larg = a.sum(axis=1).astype(np.float32)
    faixa = larg[topo: topo + max(10, int(alt * 0.22))]
    cab_w = float(np.percentile(faixa, 90)) if len(faixa) else cut.width * 0.4
    linhas = a[topo: topo + max(10, int(cab_w * 1.1))]
    xs = np.where(linhas)[1]
    cx = float(xs.mean()) if len(xs) else cut.width / 2
    return cx, topo, cab_w


def busto(cut, largura_rel=1.0):
    """Cabeca + ombros enquadrados pela cabeca (antes cortava pelo topo do recorte e, se
    o recorte trazia sobra de fundo, saia so testa/teto)."""
    w, h = cut.size
    cab = _cabeca(cut)
    if not cab:
        return cut.crop((0, 0, w, min(h, int(w * 1.15))))
    cx, topo, cab_w = cab
    alto = cab_w * 3.0 * largura_rel
    # largura TODA da silhueta (cortar dos lados deixava os ombros com borda reta)
    b = cut.crop((0, int(max(0, topo - cab_w * 0.12)), w, int(min(h, topo + alto))))
    # base esfumada (o corte reto do peito some no fundo)
    arr = np.asarray(b).copy()
    n = max(2, int(b.height * 0.14))
    rampa = np.linspace(1.0, 0.0, n, dtype=np.float32)[:, None]
    arr[-n:, :, 3] = (arr[-n:, :, 3].astype(np.float32) * rampa).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


def sombra(rgba, raio=18, deslocamento=(0, 10), opac=150):
    a = rgba.split()[3]
    s = Image.new("RGBA", rgba.size, (0, 0, 0, 0))
    s.putalpha(a.point(lambda v: v * opac // 255))
    s = s.filter(ImageFilter.GaussianBlur(raio))
    out = Image.new("RGBA", (rgba.width + 2 * raio, rgba.height + 2 * raio), (0, 0, 0, 0))
    out.alpha_composite(s, (raio + deslocamento[0], raio + deslocamento[1]))
    out.alpha_composite(rgba, (raio, raio))
    return out


def brilho_borda(rgba, cor=OURO, raio=10, forca=200):
    """Contorno de luz dourada atras da pessoa (rim light)."""
    a = rgba.split()[3].filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(raio))
    g = Image.new("RGBA", rgba.size, cor + (0,))
    g.putalpha(a.point(lambda v: min(255, v * forca // 255)))
    g.alpha_composite(rgba)
    return g


# ----------------------------------------------------------------------------- fundos
def radial(tam, centro, c_in, c_out, raio):
    w, h = tam
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt((xx - centro[0]) ** 2 + (yy - centro[1]) ** 2) / raio
    t = np.clip(d, 0, 1)[..., None]
    a = np.array(c_in, np.float32)
    b = np.array(c_out, np.float32)
    return Image.fromarray((a + (b - a) * t).astype(np.uint8), "RGB")


def pelicula(largura, altura, cenas, quadro_w):
    """Faixa de pelicula: fundo preto, furos em cima/embaixo e as cenas nos quadros."""
    fita = Image.new("RGBA", (largura, altura), (10, 10, 12, 255))
    d = ImageDraw.Draw(fita)
    furo_h = int(altura * 0.075)
    margem = int(altura * 0.04)
    passo = int(furo_h * 1.9)
    for x in range(8, largura, passo):
        for y in (margem, altura - margem - furo_h):
            d.rounded_rectangle([x, y, x + int(furo_h * 1.25), y + furo_h], radius=4, fill=(236, 230, 218, 255))
    qy0 = margem * 2 + furo_h
    qh = altura - 2 * qy0
    gap = int(quadro_w * 0.06)
    x = -int(quadro_w * 0.35)
    i = 0
    while x < largura:
        im = Image.open(cenas[i % len(cenas)]).convert("RGB")
        q = ImageOps.fit(im, (quadro_w, qh), Image.LANCZOS, centering=(0.5, 0.4))
        fita.paste(q, (x, qy0))
        x += quadro_w + gap
        i += 1
    return fita


# ----------------------------------------------------------------------------- pecas
def perfil(foto, saida, tam=800):
    base = radial((tam, tam), (tam / 2, tam * 0.42), (46, 58, 100), NOITE, tam * 0.62)
    base = base.convert("RGBA")
    d = ImageDraw.Draw(base)
    # anel de pelicula (o YouTube mostra o perfil em circulo)
    r = tam * 0.47
    c = tam / 2
    d.ellipse([c - r, c - r, c + r, c + r], outline=OURO + (255,), width=int(tam * 0.022))
    n = 36
    for k in range(n):
        ang = 2 * np.pi * k / n
        px, py = c + (r - tam * 0.045) * np.cos(ang), c + (r - tam * 0.045) * np.sin(ang)
        s = tam * 0.012
        d.rounded_rectangle([px - s, py - s * 0.7, px + s, py + s * 0.7], radius=2, fill=(255, 200, 61, 150))
    # pessoa: escala pela LARGURA DA CABECA (cabeca sempre do mesmo tamanho e centrada)
    cut = busto(recorte(foto), 1.0)
    cx, topo, cab_w = _cabeca(cut)
    esc = (tam * 0.40) / max(cab_w, 1)
    p = brilho_borda(cut.resize((int(cut.width * esc), int(cut.height * esc)), Image.LANCZOS),
                     raio=8, forca=170)
    # mascara circular pra pessoa nao vazar o anel
    camada = Image.new("RGBA", (tam, tam), (0, 0, 0, 0))
    camada.alpha_composite(p, (int(tam / 2 - cx * esc), int(tam * 0.14 - topo * esc)))
    m = Image.new("L", (tam, tam), 0)
    ImageDraw.Draw(m).ellipse([c - r + tam * 0.012, c - r + tam * 0.012, c + r - tam * 0.012, c + r - tam * 0.012], fill=255)
    camada.putalpha(Image.fromarray(np.minimum(np.asarray(camada.split()[3]), np.asarray(m))))
    base.alpha_composite(camada)
    base.convert("RGB").save(saida, quality=95)


def banner(foto, saida):
    W, H = 2560, 1440
    sx0, sy0, sw, sh = (W - 1546) // 2, (H - 423) // 2, 1546, 423   # area segura
    cenas = [IMG / c for c in CENAS if (IMG / c).exists()]
    # fundo (TV mostra a altura toda): mosaico desfocado e escuro das cenas
    fundo = Image.new("RGB", (W, H), NOITE)
    tw = W // 6
    for i in range(6):
        for j in range(2):
            im = ImageOps.fit(Image.open(cenas[(i + j * 6) % len(cenas)]).convert("RGB"), (tw, H // 2))
            fundo.paste(im, (i * tw, j * H // 2))
    fundo = fundo.filter(ImageFilter.GaussianBlur(26))
    fundo = Image.blend(fundo, Image.new("RGB", (W, H), NOITE), 0.72).convert("RGBA")
    # pelicula na faixa central (o que aparece no PC)
    fita_h = 470
    fita = pelicula(W, fita_h, cenas, quadro_w=300)
    fundo.alpha_composite(fita, (0, (H - fita_h) // 2))
    # escurece a area de texto pra ler bem (gradiente horizontal suave)
    vel = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    a = np.zeros((H, W), np.float32)
    xs = np.arange(W, dtype=np.float32)
    cx = W / 2
    a[:, :] = np.clip(1 - np.abs(xs - cx) / (sw * 0.62), 0, 1)[None, :] ** 0.7 * 215
    vel.putalpha(Image.fromarray(a.astype(np.uint8)))
    vel = Image.composite(Image.new("RGBA", (W, H), NOITE + (255,)), Image.new("RGBA", (W, H), (0, 0, 0, 0)), vel.split()[3])
    fundo.alpha_composite(vel)
    d = ImageDraw.Draw(fundo)
    # linhas douradas finas acima/abaixo da faixa
    for y in ((H - fita_h) // 2 - 6, (H + fita_h) // 2 + 2):
        d.rectangle([0, y, W, y + 3], fill=OURO + (255,))
    # pessoa recortada "saindo" da pelicula, dentro da faixa segura
    cut = busto(recorte(foto), 1.05)
    cx, topo, cab_w = _cabeca(cut)
    esc = (sh * 0.50) / max(cab_w, 1)          # cabeca ~50% da altura da faixa segura
    p = sombra(brilho_borda(cut.resize((int(cut.width * esc), int(cut.height * esc)), Image.LANCZOS),
                            raio=10, forca=190), raio=16)
    cab_x = sx0 + 215                            # centro da cabeca dentro da area segura
    fundo.alpha_composite(p, (int(cab_x - cx * esc) - 16, int(sy0 + 6 - topo * esc) - 16))
    # textos (cabem na faixa segura, a direita do ombro)
    tx = int(cab_x + cab_w * esc * 1.25 + 30)
    larg_txt = sx0 + sw - tx - 10
    t1, t2 = "HISTÓRIAS", "EM FRAMES"
    tam = 150
    while tam > 60:
        f = fonte("Montserrat-Black.ttf", tam)
        if d.textlength(t1 + " ", font=f) + d.textlength(t2, font=f) <= larg_txt:
            break
        tam -= 4
    f = fonte("Montserrat-Black.ttf", tam)
    ty = sy0 + 70
    w1 = d.textlength(t1 + " ", font=f)
    d.text((tx + 4, ty + 6), t1, font=f, fill=(0, 0, 0, 160))
    d.text((tx, ty), t1, font=f, fill=(255, 255, 255, 255))
    d.text((tx + w1 + 4, ty + 6), t2, font=f, fill=(0, 0, 0, 160))
    d.text((tx + w1, ty), t2, font=f, fill=OURO + (255,))
    fs = fonte("Montserrat-ExtraBold.ttf", int(tam * 0.30))
    d.text((tx + 4, ty + tam + 24), SLOGAN, font=fs, fill=(235, 228, 214, 255))
    fp = fonte("Montserrat-ExtraBold.ttf", int(tam * 0.24))
    selo = f"{SELO}  |  {HANDLE}"
    bw = d.textlength(selo, font=fp) + 56
    by = ty + tam + 24 + int(tam * 0.30) + 34
    d.rounded_rectangle([tx, by, tx + bw, by + int(tam * 0.24) + 30], radius=40, fill=OURO + (255,))
    d.text((tx + 28, by + 13), selo, font=fp, fill=NOITE + (255,))
    fundo.convert("RGB").save(saida, quality=95)


def monograma(tam, fundo=True):
    """Logo 'HF' num quadro de pelicula com play (marca d'agua/logo)."""
    im = Image.new("RGBA", (tam, tam), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if fundo:
        d.ellipse([0, 0, tam - 1, tam - 1], fill=NOITE + (235,), outline=OURO + (255,), width=max(2, tam // 40))
    m = tam * 0.2
    x0, y0, x1, y1 = m, m * 1.15, tam - m, tam - m * 1.15
    d.rounded_rectangle([x0, y0, x1, y1], radius=tam // 30, outline=OURO + (255,), width=max(2, tam // 45))
    furo = tam * 0.035
    for k in range(5):
        fx = x0 + (x1 - x0) * (k + 0.5) / 5 - furo / 2
        for fy in (y0 + furo * 0.7, y1 - furo * 1.7):
            d.rectangle([fx, fy, fx + furo, fy + furo], fill=OURO + (255,))
    f = fonte("Montserrat-Black.ttf", int(tam * 0.30))
    txt = "HF"
    w = d.textlength(txt, font=f)
    d.text(((tam - w) / 2, tam * 0.5 - tam * 0.19), txt, font=f, fill=(255, 255, 255, 255))
    return im


def textos(pasta):
    descricao = (
        f"{NOME}: histórias curtas que prendem do primeiro ao último frame. Superação, mistério, "
        "terror, romance, comédia, fé e fantasia, contadas com imagem, voz e trilha de cinema.\n\n"
        "Todo dia tem história nova: algumas pra arrepiar, outras pra emocionar e outras pra "
        "rir. Se você gosta de uma boa história, se inscreve e ativa o sininho.\n\n"
        "As imagens e a narração são produzidas com ajuda de inteligência artificial; o roteiro e "
        "a edição passam por revisão antes de publicar.\n\n"
        "Comenta qual tipo de história você quer ver no próximo vídeo!"
    )
    palavras = ("histórias, histórias curtas, histórias emocionantes, histórias de superação, "
                "histórias de terror, histórias de mistério, histórias reais e fictícias, contos, "
                "narração, histórias narradas, shorts de histórias, histórias com ia, "
                "histórias para dormir, histórias que emocionam, histórias em frames")
    playlists = {
        "Superação que emociona": "superacao",
        "Terror e arrepios": "terror",
        "Mistérios sem explicação": "misterio",
        "Histórias de amor": "romance",
        "Pra rir": "comedia",
        "Fé e esperança": "religioso",
        "Mundos de fantasia": "fantasia",
        "Drama da vida real": "drama",
        "Curiosidades que viram história": "curiosidades",
        "Motivação diária": "motivacional",
    }
    hashtags = {
        "superacao": "#superação #históriasdesuperação #motivação #histórias #shorts",
        "terror": "#terror #históriasdeterror #creepypasta #medo #shorts",
        "misterio": "#mistério #suspense #histórias #enigma #shorts",
        "romance": "#romance #históriasdeamor #amor #histórias #shorts",
        "comedia": "#comédia #humor #engraçado #histórias #shorts",
        "religioso": "#fé #esperança #deus #históriasreais #shorts",
        "fantasia": "#fantasia #magia #aventura #histórias #shorts",
        "drama": "#drama #emocionante #históriasreais #histórias #shorts",
        "curiosidades": "#curiosidades #vocêsabia #fatos #histórias #shorts",
        "motivacional": "#motivação #reflexão #superação #histórias #shorts",
    }
    (pasta / "descricao.txt").write_text(descricao + "\n", encoding="utf-8")
    (pasta / "palavras_chave.txt").write_text(palavras + "\n", encoding="utf-8")
    bios = (
        "== YouTube (nome / handle) ==\n"
        f"{NOME}  {HANDLE}\n"
        "Alternativas se o handle estiver ocupado: @HistoriasEmFramesBR, @HistoriasEmFrame, "
        "@HistoriasEmFramesOficial, @FramesDeHistorias\n\n"
        "== TikTok / Kwai (80 caracteres) ==\n"
        "Histórias que prendem do 1º ao último frame. Nova todo dia 🎬\n\n"
        "== Instagram (150 caracteres) ==\n"
        "🎬 Histórias curtas que prendem do primeiro ao último frame\n"
        "Superação • Mistério • Terror • Amor\n"
        "Nova história todo dia 👇\n\n"
        "== Facebook (página) ==\n"
        f"{NOME} | Histórias curtas narradas: superação, mistério, terror, romance e muito mais. "
        "Uma história nova todo dia.\n"
    )
    (pasta / "bios_redes_sociais.txt").write_text(bios, encoding="utf-8")
    coment = (
        "Modelos de comentário fixado (troque a cada vídeo):\n\n"
        "1. Você teria feito o mesmo no lugar dele(a)? Me conta aqui 👇\n"
        "2. De 0 a 10, quanto essa história te pegou?\n"
        "3. Qual parte te deixou mais arrepiado(a)?\n"
        "4. Quer a parte 2? Comenta \"PARTE 2\" que eu faço.\n"
        "5. Que tipo de história você quer ver amanhã: terror, superação ou romance?\n"
    )
    (pasta / "comentarios_fixados.txt").write_text(coment, encoding="utf-8")
    modelo = ["Modelo de descrição de vídeo (o pipeline já gera título/descrição; use como referência):\n",
              "{gancho de 1 linha da história}\n",
              f"{SLOGAN}. Se inscreve em {HANDLE} pra não perder a próxima.\n",
              "As imagens e a narração foram produzidas com ajuda de IA.\n",
              "\nHashtags por gênero:\n"]
    modelo += [f"- {g}: {h}\n" for g, h in hashtags.items()]
    modelo += ["\nPlaylists sugeridas (nome -> gênero do pipeline):\n"]
    modelo += [f"- {n}  ->  {g}\n" for n, g in playlists.items()]
    (pasta / "modelo_descricao_e_playlists.txt").write_text("".join(modelo), encoding="utf-8")
    (pasta / "canal.json").write_text(json.dumps({
        "nome": NOME, "handle": HANDLE, "slogan": SLOGAN, "watermark": HANDLE,
        "cores": {"ouro": "#FFC83D", "noite": "#080A12"}, "idioma": "pt-BR", "pais": "BR",
        "categoria": "Entretenimento", "playlists": playlists, "hashtags": hashtags,
    }, indent=1, ensure_ascii=False), encoding="utf-8")
    return descricao, palavras


def main():
    AQUI.mkdir(exist_ok=True)
    foto = FOTOS / FOTO_PRINCIPAL
    perfil(foto, AQUI / "perfil.png")
    for i, nome in enumerate(FOTOS_OPCOES, start=2):
        perfil(FOTOS / nome, AQUI / f"perfil_opcao{i}.png")
    banner(foto, AQUI / "banner.png")
    monograma(150).save(AQUI / "marca_dagua.png")
    monograma(1024).save(AQUI / "logo.png")
    monograma(1024, fundo=False).save(AQUI / "logo_sem_fundo.png")
    textos(AQUI)
    print("kit gerado em", AQUI)


if __name__ == "__main__":
    main()
