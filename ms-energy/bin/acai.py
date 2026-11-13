# -*- coding: utf-8 -*-
r"""acai.py — Instagram do AÇAÍ O PRECIOSO (@acai_oprecioso, Paragominas-PA). Dona 05/11/2026 00h: "adicione no das
empresas, analise todo o perfil e comece as postagens... no perfil não tem foto do dono, então os vídeos de Veo vão ser
como o que tem lá; adicione as máscaras dos destaques; até as 8 h já ter várias postagens, bonito e homogêneo com
carrosséis, vídeos e capas".

Identidade medida nas artes do próprio perfil (assets\acai\perfil): roxo (125,22,123) + verde (122,173,13), letras
Anton/Montserrat. Produtos reais: açaí nativo em litro e 500 ml, açaí papa (encomendas), açaí com peixe frito/camarão,
copo com frutas. Endereço Av. Antero Bonifácio, 138 — Promissão I; WhatsApp (91) 99366-8986. Sem preço nas artes.
Conta antiga do cliente recém-logada no PC1 (aparelho novo): ritmo de 1 post a cada 60-90 min (feedback_instagram_aparelho_novo).
Posta por HTTP com a sessão do cofre ig_acai_no_litro (InstagramPostar("acai_no_litro")). Rodar com D:\veo\venv.
    python acai.py destaques          # 5 capas de destaque (stories + destaque)
    python acai.py carrossel [n]      # gera e posta o carrossel n (ou o próximo da fila)
    python acai.py reel               # Veo a partir de uma foto real do perfil + texto + cartão final, e posta
    python acai.py proximo            # alterna carrossel/reel (pra tarefa agendada)
    python acai.py --so-gerar ...     # gera sem postar (prévia)
"""
import json
import random
import subprocess
import sys
import textwrap
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

CONTA_COFRE = "acai_no_litro"          # InstagramPostar usa o perfil do cofre ig_<isto>
ARROBA = "@acai_oprecioso"
EMPRESA = "Açaí O PRECIOSO @acai_oprecioso"
ZAP = "(91) 99366-8986"
ENDERECO = "Av. Antero Bonifácio, 138 — Promissão I"
CIDADE = "Paragominas — PA"
ROXO = (125, 22, 123)
ROXO_ESC = (70, 10, 72)
VERDE = (122, 173, 13)
AMARELO = (255, 214, 0)
BASE = Path(r"D:\ms-energy")
FOTOS = BASE / "assets" / "acai" / "perfil"
SAIDA = BASE / "videos" / "acai"
ESTADO = BASE / "cache" / "acai_estado.json"
LOG = BASE / "logs" / "acai.log"
FONTES = Path(r"D:\hipercool-materiais\assets\fonts")
ANTON = r"D:\ms-energy\assets\fontes\Anton-Regular.ttf"
MONT = str(FONTES / "Montserrat-ExtraBold.ttf")
MONT_B = str(FONTES / "Montserrat-Black.ttf")
# fotos reais de produto do perfil (sem preço/texto grande): copo, açaí com frito, litros no gelo, fachada
PRODUTO = ["DKkOmIOMiir_0.jpg", "DKQJ1LVPKMx_4.jpg", "DKzTAP5sBBY_5.jpg", "DMxdQ_qMC-Q_0.jpg", "DLr4k-GsyL1_4.jpg"]
HASHTAGS = "#açaí #açainativo #paragominas #paragominaspa #acaidopara #açaíparaense #acaioprecioso"

CARROSSEIS = [
    {"id": "nativo", "foto": "DKkOmIOMiir_0.jpg", "capa": "O VERDADEIRO SABOR DO AÇAÍ NATIVO",
     "slides": [("PURO E GROSSO", "Açaí nativo batido na hora, grosso, do jeito que o paraense gosta."),
                ("CHEIO DE ENERGIA", "Grosso, fresquinho e sem enrolação: é açaí de verdade."),
                ("NA TIGELA OU NO LITRO", "Pra tomar na hora na tigela ou levar o litro pra casa.")],
     "legenda": "O verdadeiro sabor do açaí nativo 💜 Puro e grosso, na tigela ou no litro. Já provou o nosso?"},
    {"id": "frito", "foto": "DKQJ1LVPKMx_4.jpg", "capa": "AÇAÍ COM PEIXE FRITO? AQUI TEM!",
     "slides": [("A COMBINAÇÃO DO PARÁ", "Açaí grosso com peixe frito crocante: almoço de paraense."),
                ("ACOMPANHAMENTOS", "Peixe, camarão e charque preparados na hora."),
                ("PRA MATAR A FOME", "Chama no Zap e garanta o seu almoço com açaí.")],
     "legenda": "Açaí com peixe frito é paixão paraense 😋 Acompanhamentos preparados na hora. Qual é o seu favorito?"},
    {"id": "litro", "foto": "DKzTAP5sBBY_5.jpg", "capa": "LEVE O AÇAÍ PRA CASA",
     "slides": [("LITRO E 500 ML", "O açaí que você gosta, no tamanho que a família precisa."),
                ("SEMPRE GELADINHO", "Embalado com cuidado pra chegar perfeito na sua casa."),
                ("PEÇA JÁ O SEU", "Faça seu pedido pelo WhatsApp e retire ou receba.")],
     "legenda": "Açaí nativo no litro e no 500 ml pra levar pra casa 💜 Peça pelo WhatsApp!"},
    {"id": "encomenda", "foto": "DMxdQ_qMC-Q_0.jpg", "capa": "RECEBEMOS ENCOMENDAS",
     "slides": [("FESTA? REUNIÃO?", "Encomende o açaí pra família, a festa ou o almoço de domingo."),
                ("AÇAÍ PAPA", "O açaí grosso, do jeito tradicional, sob encomenda."),
                ("É SÓ CHAMAR", "Combine a quantidade e o horário pelo WhatsApp.")],
     "legenda": "Recebemos encomendas de açaí 💜 Festa, almoço de domingo ou reunião de família: chama no Zap!"},
    {"id": "onde", "foto": "DLr4k-GsyL1_4.jpg", "capa": "VEM PRO AÇAÍ O PRECIOSO",
     "slides": [("ONDE ESTAMOS", f"{ENDERECO}, {CIDADE}."),
                ("PRÊMIO MASTER", "Açaí premiado aqui em Paragominas. Venha provar!"),
                ("ATENDIMENTO NO ZAP", f"Pedidos e encomendas: {ZAP}.")],
     "legenda": f"Vem provar o açaí premiado de Paragominas 💜 📍 {ENDERECO}."},
]
DESTAQUES = [("CARDÁPIO", "☰"), ("PEDIDOS", "✆"), ("ONDE ESTAMOS", "⌖"), ("ENCOMENDAS", "★"), ("CLIENTES", "♥")]


def log(m):
    linha = f"[{datetime.now():%d/%m %H:%M:%S}] {m}"
    print(linha, flush=True)
    LOG.parent.mkdir(exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(linha + "\n")


def _estado():
    try:
        return json.loads(ESTADO.read_text("utf-8"))
    except (OSError, ValueError):
        return {"carrosseis": [], "reels": [], "destaques": False, "ultimo": None}


def _salvar(e):
    ESTADO.parent.mkdir(exist_ok=True)
    ESTADO.write_text(json.dumps(e, ensure_ascii=False, indent=1), "utf-8")


def _f(c, t):
    return ImageFont.truetype(c, t)


def _cobrir(foto, w, h):
    im = Image.open(foto).convert("RGB")
    r = max(w / im.width, h / im.height)
    im = im.resize((int(im.width * r) + 1, int(im.height * r) + 1), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((x, y, x + w, y + h))


def _texto_centro(d, txt, fonte, y, w, cor, max_larg, sombra=True, linha=1.08):
    linhas, atual = [], ""
    for p in txt.split():
        t = (atual + " " + p).strip()
        if d.textlength(t, font=fonte) <= max_larg:
            atual = t
        else:
            linhas.append(atual)
            atual = p
    linhas.append(atual)
    alt = int(fonte.size * linha)
    for i, l in enumerate(linhas):
        x = (w - d.textlength(l, font=fonte)) / 2
        if sombra:
            d.text((x + 5, y + i * alt + 5), l, font=fonte, fill=ROXO_ESC)
        d.text((x, y + i * alt), l, font=fonte, fill=cor)
    return y + len(linhas) * alt


def _selo(d, w, h):
    f = _f(MONT_B, 34)
    t = f"AÇAÍ O PRECIOSO  •  {ARROBA}"
    d.text(((w - d.textlength(t, font=f)) / 2, h - 70), t, font=f, fill="white")


def slide_capa(c, w=1080, h=1350):
    im = _cobrir(FOTOS / c["foto"], w, h)
    faixa = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dd = ImageDraw.Draw(faixa)
    for i in range(520):  # degradê roxo embaixo
        a = int(235 * (i / 520) ** 1.2)
        dd.line([(0, h - 520 + i), (w, h - 520 + i)], fill=ROXO + (a,))
    im = Image.alpha_composite(im.convert("RGBA"), faixa).convert("RGB")
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([60, h - 470, 360, h - 410], 28, fill=VERDE)
    d.text((80, h - 466), "AÇAÍ NATIVO", font=_f(MONT_B, 36), fill="white")
    _texto_centro(d, c["capa"], _f(ANTON, 104), h - 390, w, "white", w - 120)
    _selo(d, w, h)
    return im


def slide_texto(n, titulo, texto, foto, w=1080, h=1350):
    im = Image.new("RGB", (w, h), ROXO)
    d = ImageDraw.Draw(im)
    for i in range(0, w + h, 90):  # textura leve de listras
        d.line([(i, 0), (i - h, h)], fill=(133, 30, 131), width=30)
    ft = _cobrir(FOTOS / foto, 760, 560)
    m = Image.new("L", ft.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, ft.width, ft.height], 48, fill=255)
    im.paste(ft, ((w - 760) // 2, 120), m)
    d.ellipse([w // 2 - 60, 620, w // 2 + 60, 740], fill=VERDE)
    d.text((w // 2 - d.textlength(str(n), font=_f(ANTON, 90)) / 2, 628), str(n), font=_f(ANTON, 90), fill="white")
    y = _texto_centro(d, titulo, _f(ANTON, 96), 780, w, AMARELO, w - 140)
    _texto_centro(d, texto, _f(MONT, 50), y + 30, w, "white", w - 180, sombra=False, linha=1.25)
    _selo(d, w, h)
    return im


SIMBOLOS = r"C:\Windows\Fonts\seguisym.ttf"


def slide_cta(w=1080, h=1350):
    im = Image.new("RGB", (w, h), ROXO)
    d = ImageDraw.Draw(im)
    d.ellipse([w // 2 - 120, 150, w // 2 + 120, 390], fill=VERDE)
    fz = _f(SIMBOLOS, 150)
    bb = d.textbbox((0, 0), "✆", font=fz)
    d.text((w // 2 - (bb[2] - bb[0]) / 2 - bb[0], 270 - (bb[3] - bb[1]) / 2 - bb[1]), "✆", font=fz, fill="white")
    y = _texto_centro(d, "PEÇA JÁ O SEU!", _f(ANTON, 120), 450, w, "white", w - 120)
    d.rounded_rectangle([110, y + 40, w - 110, y + 170], 60, fill=VERDE)
    d.text(((w - d.textlength(ZAP, font=_f(ANTON, 90))) / 2, y + 55), ZAP, font=_f(ANTON, 90), fill="white")
    y = _texto_centro(d, ENDERECO, _f(MONT, 46), y + 230, w, "white", w - 160, sombra=False, linha=1.3)
    _texto_centro(d, CIDADE, _f(MONT_B, 46), y + 10, w, AMARELO, w - 160, sombra=False)
    _selo(d, w, h)
    return im


def gerar_carrossel(c):
    pasta = SAIDA / f"carrossel_{c['id']}_{datetime.now():%Y%m%d_%H%M}"
    pasta.mkdir(parents=True, exist_ok=True)
    fotos = [p for p in PRODUTO if p != c["foto"]]
    random.shuffle(fotos)
    imgs = [slide_capa(c)] + [slide_texto(i + 1, t, x, fotos[i % len(fotos)]) for i, (t, x) in enumerate(c["slides"])]
    imgs.append(slide_cta())
    arqs = []
    for i, im in enumerate(imgs):
        a = pasta / f"{i + 1}.jpg"
        im.save(a, quality=93)
        arqs.append(a)
    leg = f"{c['legenda']}\n\n📲 Pedidos e encomendas: {ZAP}\n📍 {ENDERECO} — {CIDADE}\n\n{HASHTAGS}"
    (pasta / "legenda.txt").write_text(leg, "utf-8")
    log(f"carrossel {c['id']} gerado: {pasta}")
    return pasta, arqs, leg


def _postar():
    sys.path.insert(0, r"D:\projeto-navegador-sem-navegador")
    from services.instagram.postar import InstagramPostar
    return InstagramPostar(CONTA_COFRE)


def carrossel(n=None, so_gerar=False):
    e = _estado()
    if n is None:
        feitos = e["carrosseis"]
        n = next((i for i, c in enumerate(CARROSSEIS) if c["id"] not in feitos), len(feitos) % len(CARROSSEIS))
    c = CARROSSEIS[int(n)]
    pasta, arqs, leg = gerar_carrossel(c)
    if so_gerar:
        return pasta
    r = _postar().carrossel([str(a) for a in arqs], leg)
    log(f"PUBLICADO carrossel {c['id']}: {r}")
    e["carrosseis"].append(c["id"])
    e["ultimo"] = datetime.now().isoformat(timespec="seconds")
    _salvar(e)
    return r


SIMBOLOS = r"C:\Windows\Fonts\seguisym.ttf"


def capa_destaque(titulo, icone, w=1080, h=1920):
    """O Instagram mostra só o CÍRCULO do centro na capa do destaque: ícone + título dentro dele."""
    im = Image.new("RGB", (w, h), ROXO)
    d = ImageDraw.Draw(im)
    cx, cy, r = w // 2, h // 2, 380
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=VERDE)
    d.ellipse([cx - r + 18, cy - r + 18, cx + r - 18, cy + r - 18], outline="white", width=10)
    fi = _f(SIMBOLOS, 260)
    bb = d.textbbox((0, 0), icone, font=fi)
    d.text((cx - (bb[2] - bb[0]) / 2 - bb[0], cy - 250 - bb[1]), icone, font=fi, fill="white")
    ft = _f(ANTON, 96 if len(titulo) <= 9 else 74)
    d.text((cx - d.textlength(titulo, font=ft) / 2, cy + 70), titulo, font=ft, fill="white")
    return im


def destaques(so_gerar=False):
    pasta = SAIDA / "destaques"
    pasta.mkdir(parents=True, exist_ok=True)
    arqs = []
    for t, ic in DESTAQUES:
        a = pasta / f"{t.lower().replace(' ', '_')}.jpg"
        capa_destaque(t, ic).save(a, quality=93)
        arqs.append((t, a))
    if so_gerar:
        return pasta
    ig = _postar()
    for t, a in arqs:
        pk = ig.story(str(a))
        try:
            ig.criar_destaque(t.title(), [pk])
            log(f"destaque '{t}' criado (story {pk})")
        except Exception as ex:  # noqa: BLE001 — story saiu; destaque fica pra conferir
            log(f"story '{t}' ok ({pk}), destaque falhou: {ex}")
    e = _estado()
    e["destaques"] = True
    _salvar(e)

# 05/11 08h dona: "o açaí deles NÃO é sorvete: vende por litro açaí puro ou pra consumo na hora na tigela" —
# o reel do copo com frutas (cara de sorvete) saiu da rotação; tudo agora é açaí PURO (grosso, paraense), litro e tigela.
NAO_SORVETE = (" It is PURE thick Amazonian acai (Para style, like a dense purple puree), served plain in a bowl — "
               "NOT ice cream, NOT sorbet, NOT acai cream, no scoops, no whipped toppings, no fruit toppings.")
REELS = [
    {"id": "litro", "foto": "DKzTAP5sBBY_5.jpg", "gancho": "AÇAÍ PURO NO LITRO PRA LEVAR PRA CASA",
     "prompt": "Vertical 9:16 product commercial. Slow cinematic orbit around these exact acai packages (1 liter and "
               "500 ml) resting on ice, cold mist, condensation drops, fresh, no people, keep packages and labels "
               "exactly as in the photo, no new text. Soft ice sounds." + NAO_SORVETE,
     "legenda": "Açaí puro no litro e no 500 ml, do jeito paraense 💜 Leve pra casa! Peça pelo WhatsApp."},
    {"id": "tigela", "foto": "DKQJ1LVPKMx_4.jpg", "gancho": "AÇAÍ NA TIGELA COM PEIXE FRITO, NA HORA",
     "prompt": "Vertical 9:16 food commercial. Slow top-down camera drift over this exact table: a bowl of thick pure "
               "dark purple acai, crispy fried fish, shrimp and dried beef, warm light, appetizing, no people, no "
               "text, keep the food exactly as in the photo. Ambient kitchen sounds." + NAO_SORVETE,
     "legenda": "Açaí puro na tigela com peixe frito, servido na hora 😋 O almoço do paraense. Vem pro Precioso!"},
    {"id": "litros2", "foto": "DMxdQ_qMC-Q_0.jpg", "gancho": "O VERDADEIRO AÇAÍ NATIVO DE PARAGOMINAS",
     "prompt": "Vertical 9:16 product commercial. Gentle slow push-in on these exact acai packages, cold and fresh, "
               "subtle mist, premium look, no people, keep packages and labels exactly as in the photo, no new text."
               + NAO_SORVETE,
     "legenda": "Açaí nativo, puro e grosso, no litro ou no 500 ml 💜 Encomendas pelo WhatsApp!"},
]


def _veo(prompt, foto, saida):
    """1 clipe do Veo (mesmo rodízio de contas das solares). Devolve o caminho ou None."""
    sys.path.insert(0, r"D:\ms-energy\bin")
    sys.path.insert(0, r"D:\veo\beta")
    import gerar_short_veo as g
    from cron_gerar_video_llm import escolher_sessao, aplicar_sessao, marcar_conta_fora, marcar_creditos_esgotados
    import time
    tentativas, espera = 0, 0
    while tentativas < 6:
        s = escolher_sessao()
        if s is None:
            log("Veo: sem conta livre")
            return None
        aplicar_sessao(s)
        log(f"Veo: conta {s['session']}")
        ok = g.gerar_video_robusto(prompt, foto, str(saida), log=log)
        if ok is True:
            return saida
        if ok == "MAQUINA_OCUPADA" and espera < 45 * 60:  # como as solares: espera a vez sem gastar tentativa
            time.sleep(90)
            espera += 90
            continue
        tentativas += 1
        if isinstance(ok, tuple):
            marcar_creditos_esgotados(s["session"], padrao_texto=ok[1] if len(ok) > 1 else "")
        elif ok == "SESSAO":
            marcar_conta_fora(s["session"], "login caiu no Flow (acai)", horas=6)
    return None


def _cartao_final(w=1080, h=1920):
    im = Image.new("RGB", (w, h), ROXO)
    d = ImageDraw.Draw(im)
    d.ellipse([w // 2 - 140, 330, w // 2 + 140, 610], fill=VERDE)
    fz = _f(SIMBOLOS, 170)
    bb = d.textbbox((0, 0), "✆", font=fz)
    d.text((w // 2 - (bb[2] - bb[0]) / 2 - bb[0], 470 - (bb[3] - bb[1]) / 2 - bb[1]), "✆", font=fz, fill="white")
    y = _texto_centro(d, "PEÇA JÁ O SEU!", _f(ANTON, 130), 700, w, "white", w - 120)
    d.rounded_rectangle([100, y + 50, w - 100, y + 190], 66, fill=VERDE)
    d.text(((w - d.textlength(ZAP, font=_f(ANTON, 96))) / 2, y + 66), ZAP, font=_f(ANTON, 96), fill="white")
    y = _texto_centro(d, ENDERECO, _f(MONT, 50), y + 260, w, "white", w - 160, sombra=False, linha=1.3)
    _texto_centro(d, CIDADE, _f(MONT_B, 50), y + 10, w, AMARELO, w - 160, sombra=False)
    _selo(d, w, h - 80)
    return im


def _faixa_gancho(txt, w=1080, h=1920):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    f = _f(ANTON, 92)
    linhas = textwrap.wrap(txt, 18)
    alt = 104 * len(linhas) + 60
    d.rounded_rectangle([50, 210, w - 50, 210 + alt], 40, fill=ROXO + (235,))
    for i, l in enumerate(linhas):
        d.text(((w - d.textlength(l, font=f)) / 2, 236 + i * 104), l, font=f, fill="white")
    d.rounded_rectangle([w // 2 - 230, h - 300, w // 2 + 230, h - 220], 40, fill=VERDE + (240,))
    t = ARROBA
    d.text(((w - d.textlength(t, font=_f(MONT_B, 44))) / 2, h - 290), t, font=_f(MONT_B, 44), fill="white")
    return im


def montar_reel(clip, r, pasta):
    gancho, cartao = pasta / "gancho.png", pasta / "cartao.jpg"
    _faixa_gancho(r["gancho"]).save(gancho)
    _cartao_final().save(cartao, quality=93)
    out = pasta / f"reel_{r['id']}.mp4"
    # 05/11 04:30: a foto quadrada fez o Veo devolver o vídeo quadrado com faixa preta (crop=720:720:0:280) e o overlay
    # da imagem em loop deixava o 1º trecho infinito (o cartão final nunca aparecia). Tira a faixa preta (cropdetect),
    # preenche o vertical com o próprio vídeo desfocado e o gancho termina junto com o clipe (shortest=1).
    cd = subprocess.run(["ffmpeg", "-hide_banner", "-ss", "2", "-i", str(clip), "-vf", "cropdetect=24:2:0",
                         "-frames:v", "12", "-f", "null", "-"], capture_output=True, text=True).stderr
    import re as _re
    m = _re.findall(r"crop=(\d+:\d+:\d+:\d+)", cd)
    corte = f"crop={m[-1]}," if m else ""
    filtro = (f"[0:v]{corte}split[a][b];"
              "[b]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30:2,eq=brightness=-0.08[bg];"
              "[a]scale=1080:1920:force_original_aspect_ratio=decrease[fg];"
              "[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1,fps=30[v];"
              "[v][1:v]overlay=0:0:enable='lte(t,6)':shortest=1[vg];"
              "[2:v]scale=1080:1920,setsar=1,fps=30,format=yuv420p[c];"
              "[vg]format=yuv420p[vv];[vv][c]concat=n=2:v=1:a=0[outv];"
              "[0:a]apad=pad_dur=3[outa]")
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(clip), "-loop", "1", "-i", str(gancho),
           "-loop", "1", "-t", "3", "-i", str(cartao), "-filter_complex", filtro, "-map", "[outv]", "-map", "[outa]",
           "-c:v", "h264_qsv", "-global_quality", "21", "-c:a", "aac", "-b:a", "160k", "-shortest",
           "-movflags", "+faststart", str(out)]
    if subprocess.run(cmd, capture_output=True).returncode != 0:
        cmd[cmd.index("h264_qsv"):cmd.index("h264_qsv") + 3] = ["libx264", "-crf", "20"]
        subprocess.run(cmd, check=True, capture_output=True)
    return out


def reel(so_gerar=False):
    e = _estado()
    # reel já montado (ex.: a prévia) e não postado = reaproveita, sem gastar Veo de novo
    pronto = next((p for p in sorted(SAIDA.glob("reel_*"), key=lambda p: p.stat().st_mtime)
                   if p.is_dir() and list(p.glob("reel_*.mp4")) and not (p / "postado.json").exists()), None)
    if pronto:
        rid = pronto.name.split("_")[1]
        r = next((x for x in REELS if x["id"] == rid), REELS[0])
        pasta, out = pronto, next(pronto.glob("reel_*.mp4"))
    else:
        r = next((x for x in REELS if x["id"] not in e["reels"]), REELS[len(e["reels"]) % len(REELS)])
        pasta = SAIDA / f"reel_{r['id']}_{datetime.now():%Y%m%d_%H%M}"
        pasta.mkdir(parents=True, exist_ok=True)
        # foto quadrada vira VERTICAL (fundo desfocado) antes do Veo, senão ele devolve o vídeo quadrado com faixa preta
        foto9 = pasta / "foto_9x16.jpg"
        base = Image.open(FOTOS / r["foto"]).convert("RGB")
        fundo = _cobrir(FOTOS / r["foto"], 1080, 1920).filter(ImageFilter.GaussianBlur(40))
        base.thumbnail((1080, 1920))
        fundo.paste(base, ((1080 - base.width) // 2, (1920 - base.height) // 2))
        fundo.save(foto9, quality=94)
        clip = _veo(r["prompt"], foto9, pasta / "veo.mp4")
        if not clip:
            log(f"reel {r['id']}: sem clipe do Veo")
            return None
        out = montar_reel(clip, r, pasta)
    leg = f"{r['legenda']}\n\n📲 Pedidos e encomendas: {ZAP}\n📍 {ENDERECO} — {CIDADE}\n\n{HASHTAGS}"
    log(f"reel {r['id']} montado: {out}")
    if so_gerar:
        return out
    code = _postar().reel(str(out), leg)
    log(f"PUBLICADO reel {r['id']}: https://www.instagram.com/reel/{code}/")
    (pasta / "postado.json").write_text(json.dumps({"code": code, "em": datetime.now().isoformat(timespec="seconds")}),
                                        "utf-8")
    e = _estado()
    e["reels"].append(r["id"])
    e["ultimo"] = datetime.now().isoformat(timespec="seconds")
    _salvar(e)
    return code


INTERVALO_MIN = 55  # conta recém-logada (aparelho novo): ~1 post/hora. 05/11: era 60 e a tarefa de 30 em 30 min caía em 59,x min e pulava 1 h inteira


def proximo():
    """Tarefa agendada (Acai_Postar): destaques 1x; depois alterna reel e carrossel, >= 60 min entre posts.
    Reel sem clipe do Veo = carrossel no lugar (o horário não fica vazio)."""
    e = _estado()
    if e.get("ultimo"):
        passou = (datetime.now() - datetime.fromisoformat(e["ultimo"])).total_seconds() / 60
        if passou < INTERVALO_MIN:
            log(f"último post há {passou:.0f} min — espero ({INTERVALO_MIN} min)")
            return None
    if not e.get("destaques"):
        destaques()
        e = _estado()
        e["ultimo"] = datetime.now().isoformat(timespec="seconds")
        _salvar(e)
        return "destaques"
    vez_reel = len(e["reels"]) < len(e["carrosseis"])
    if vez_reel:
        r = reel()
        if r:
            return r
    return carrossel()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    a = [x for x in sys.argv[1:] if x != "--so-gerar"]
    so = "--so-gerar" in sys.argv
    cmd = a[0] if a else "proximo"
    if cmd == "destaques":
        print(destaques(so))
    elif cmd == "reel":
        print(reel(so))
    elif cmd == "carrossel":
        print(carrossel(a[1] if len(a) > 1 else None, so))
    else:
        print(proximo())


# ── ESTILO DA REFERÊNCIA (dona 05/11 12h: @pontodoacai_pgmcentral + perfis-acai-puro.csv) ───────────────────────────
# Informativos limpos: fundo creme/bege, roxo uva, letra condensada (Anton), faixas roxas com texto creme — como o
# "5 benefícios do açaí" e o "Onde estamos" da referência. A marca do Precioso (verde) só no selo/CTA.
CREME = (236, 228, 214)
UVA = (93, 32, 92)
UVA_CLARO = (138, 74, 136)


def _ref_base(w=1080, h=1350):
    im = Image.new("RGB", (w, h), CREME)
    d = ImageDraw.Draw(im)
    for y in range(0, h, 6):  # textura de papel bem leve
        d.line([(0, y), (w, y)], fill=(231, 222, 207) if (y // 6) % 2 else CREME)
    return im, d


def _ref_selo(d, w, h):
    f = _f(MONT_B, 30)
    t = f"AÇAÍ O PRECIOSO  •  {ARROBA}  •  {ZAP}"
    d.text(((w - d.textlength(t, font=f)) / 2, h - 64), t, font=f, fill=UVA)


def ref_lista(titulo, itens, w=1080, h=1350):
    """Ex.: '5 BENEFÍCIOS DO AÇAÍ' + faixas numeradas."""
    im, d = _ref_base(w, h)
    y = _texto_centro(d, titulo, _f(ANTON, 118), 110, w, UVA, w - 140, sombra=False)
    y += 50
    fi = _f(ANTON, 64)
    for i, t in enumerate(itens, 1):
        txt = f"{i}. {t}"
        lw = d.textlength(txt, font=fi) + 70
        x0 = (w - lw) / 2
        d.rectangle([x0, y, x0 + lw, y + 100], fill=UVA)
        d.text((x0 + 35, y + 14), txt, font=fi, fill=CREME)
        y += 130
    _ref_selo(d, w, h)
    return im


def ref_foto_titulo(foto, titulo, sub, w=1080, h=1350):
    """Foto real em cima (cantos arredondados) + título grande roxo + subtítulo, fundo creme."""
    im, d = _ref_base(w, h)
    ft = _cobrir(FOTOS / foto, w - 120, 760)
    m = Image.new("L", ft.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, ft.width, ft.height], 40, fill=255)
    im.paste(ft, (60, 70), m)
    y = _texto_centro(d, titulo, _f(ANTON, 100), 870, w, UVA, w - 120, sombra=False)
    _texto_centro(d, sub, _f(MONT, 44), y + 20, w, UVA_CLARO, w - 160, sombra=False, linha=1.25)
    _ref_selo(d, w, h)
    return im


def ref_onde_estamos(w=1080, h=1350):
    im, d = _ref_base(w, h)
    y = _texto_centro(d, "ONDE ESTAMOS?", _f(ANTON, 130), 150, w, UVA, w - 120, sombra=False)
    d.ellipse([w // 2 - 120, y + 50, w // 2 + 120, y + 290], fill=UVA)
    fz = _f(SIMBOLOS, 150)
    bb = d.textbbox((0, 0), "⌖", font=fz)
    d.text((w // 2 - (bb[2] - bb[0]) / 2 - bb[0], y + 170 - (bb[3] - bb[1]) / 2 - bb[1]), "⌖", font=fz, fill=CREME)
    y = _texto_centro(d, ENDERECO, _f(ANTON, 66), y + 340, w, UVA, w - 140, sombra=False)
    y = _texto_centro(d, CIDADE, _f(MONT_B, 50), y + 10, w, UVA_CLARO, w - 160, sombra=False)
    d.rounded_rectangle([160, y + 60, w - 160, y + 170], 55, fill=UVA)
    t = f"ZAP {ZAP}"
    d.text(((w - d.textlength(t, font=_f(ANTON, 70))) / 2, y + 76), t, font=_f(ANTON, 70), fill=CREME)
    _ref_selo(d, w, h)
    return im


def amostras_referencia():
    pasta = SAIDA / "amostras_estilo_referencia"
    pasta.mkdir(parents=True, exist_ok=True)
    ref_lista("5 BENEFÍCIOS DO AÇAÍ", ["Fonte de energia", "Ação antioxidante", "Rico em fibras",
                                       "Ajuda na imunidade", "Gorduras boas"]).save(pasta / "1_beneficios.jpg", quality=93)
    ref_foto_titulo("DKzTAP5sBBY_5.jpg", "AÇAÍ PURO NO LITRO", "Grosso, batido na hora, do jeito paraense.").save(
        pasta / "2_litro.jpg", quality=93)
    ref_foto_titulo("DKQJ1LVPKMx_4.jpg", "TIGELA NA HORA", "Com peixe frito, camarão ou charque.").save(
        pasta / "3_tigela.jpg", quality=93)
    ref_onde_estamos().save(pasta / "4_onde_estamos.jpg", quality=93)
    ref_lista("COMO PEDIR", ["Chama no Zap", "Escolha litro ou tigela", "Retire ou receba"]).save(
        pasta / "5_como_pedir.jpg", quality=93)
    return pasta
