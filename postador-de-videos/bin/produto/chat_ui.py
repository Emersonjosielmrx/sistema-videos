"""Conversa de WhatsApp ANIMADA mostrando o produto funcionando (aprendizado 8ebdb5ea: "recortes de interface para
contar a história" dão veracidade; aqui com selo "Simulação" — é exemplo, não print de cliente).

Cartão de chat na cor da marca: cabeçalho com avatar e "online", balões do cliente (esquerda, brancos) e da empresa
(direita, tom claro da cor da marca), "digitando…" antes de cada resposta, entrada com leve subida e escala.
Os quadros vão direto para o ffmpeg (rawvideo pelo stdin): nada de milhares de PNG no disco.

    render(kit, conversa, dur, saida, area=(x0, y0, x1, y1))  -> mp4 1080x1920 transparente? não: fundo da marca
"""
import math
import re
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

FF = r"D:\hipercool-materiais\bin\ffmpeg.exe"
UI = r"C:\Windows\Fonts\segoeui.ttf"
UI_SB = r"C:\Windows\Fonts\seguisb.ttf"
UI_B = r"C:\Windows\Fonts\segoeuib.ttf"
W, H, FPS = 1080, 1920, 30
_EMOJI = re.compile("[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F\u200D]")


def _f(caminho, tam):
    return ImageFont.truetype(caminho, tam)


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


def _mistura(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _ease(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


class _Bolha:
    def __init__(self, d, de, texto, largura_max, fonte, hora):
        self.de, self.hora = de, hora
        self.linhas = _quebrar(d, texto, fonte, largura_max - 60)
        self.lh = int(fonte.size * 1.32)
        larg_txt = max(d.textlength(ln, font=fonte) for ln in self.linhas)
        self.w = int(max(larg_txt, d.textlength(hora, font=fonte) * 0.75 + 30)) + 52
        self.h = self.lh * len(self.linhas) + 58


def render(kit, conversa, dur, saida, area=(70, 330, 1010, 1470), fundo=None, log=print):
    """Gera um mp4 1080x1920 de `dur` segundos: fundo (imagem PIL ou cor escura da marca) + cartão de chat em `area`."""
    x0, y0, x1, y1 = area
    cw, ch = x1 - x0, y1 - y0
    cor, escuro = kit["cor"], kit["escuro"]
    clara = _mistura(cor, (255, 255, 255), 0.78)     # balão da empresa
    papel = (236, 229, 221)                            # fundo do chat (bege de app de mensagem)
    # 26/10 (verificadores): letra pequena e cartão com 60% vazio -> mensagens e cabeçalho maiores
    from produto import ajustes  # botão do melhorador (padrão 52)
    f_msg, f_hora = _f(UI, ajustes.valor("chat_fonte_msg")), _f(UI, 30)
    f_nome, f_status, f_selo = _f(UI_B, 46), _f(UI, 34), _f(UI_SB, 30)

    base = (fundo.convert("RGB").resize((W, H)) if fundo is not None else Image.new("RGB", (W, H), escuro))
    if fundo is not None:
        base = Image.blend(base.filter(ImageFilter.GaussianBlur(18)), Image.new("RGB", (W, H), escuro), 0.55)
    # sombra do cartão (desenhada uma vez; acompanha a subida do cartão)
    sombra = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sombra).rounded_rectangle((x0 + 8, y0 + 18, x1 + 8, y1 + 18), radius=44, fill=(0, 0, 0, 150))
    sombra = sombra.filter(ImageFilter.GaussianBlur(22))
    # 27/10: a conversa mediu 1,98% de movimento (fundo e cartão fixos) -> fundo com zoom lento e cartão subindo
    zoom_fundo, subida = ajustes.valor("conversa_zoom"), ajustes.valor("conversa_subida")

    # cabeçalho fixo
    cab_h = 132
    cab = Image.new("RGBA", (cw, cab_h), cor + (255,))
    dc = ImageDraw.Draw(cab)
    dc.ellipse((28, 26, 108, 106), fill=_mistura(cor, (255, 255, 255), 0.85))
    ini = "".join(p[0] for p in kit["nome_produto"].split()[:2]).upper()
    dc.text((68 - dc.textlength(ini, font=_f(UI_B, 34)) / 2, 44), ini, font=_f(UI_B, 34), fill=cor)
    nome = f"{kit['nome_produto']}"
    dc.text((130, 22), nome, font=f_nome, fill=kit["texto"])
    dc.text((132, 74), "online • atendimento com IA", font=f_status, fill=_mistura(kit["texto"], cor, 0.25))
    selo = "Simulação"
    sw = dc.textlength(selo, font=f_selo) + 36
    dc.rounded_rectangle((cw - sw - 26, 46, cw - 26, 88), radius=21, fill=(0, 0, 0, 70))
    dc.text((cw - sw - 8, 51), selo, font=f_selo, fill=(255, 255, 255))

    d0 = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    msgs = []
    for i, m in enumerate(conversa):
        txt = " ".join(_EMOJI.sub("", m.get("texto", "")).split())
        if txt:
            msgs.append(_Bolha(d0, "empresa" if m.get("de") == "empresa" else "cliente", txt, int(cw * 0.74), f_msg,
                               f"19:{(12 + i * 2) % 60:02d}"))
    if not msgs:
        raise ValueError("conversa vazia")

    # linha do tempo: cada mensagem tem um instante de entrada; antes de cada resposta da empresa, "digitando…"
    n = len(msgs)
    util = max(dur - 1.0, 1.0)
    passo = util / n
    tempos, digitando = [], []
    t = 0.25
    for b in msgs:
        if b.de == "empresa":
            digitando.append((t, t + min(0.7, passo * 0.45)))
            t += min(0.7, passo * 0.45)
        tempos.append(t)
        t += passo * (0.55 if b.de == "empresa" else 0.75)
    # 26/10 (verificadores): só comprimia; com folga as mensagens acabavam cedo e a conversa ficava >2 s parada.
    # Agora a última mensagem entra ~0,6 s antes do fim da área útil (estica ou comprime)
    escala_t = max(util - 0.6, 0.5) / max(tempos[-1], 0.1)
    tempos = [x * escala_t for x in tempos]
    digitando = [(a * escala_t, b * escala_t) for a, b in digitando]

    proc = subprocess.Popen([FF, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r",
                             str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                             "-pix_fmt", "yuv420p", str(saida)], stdin=subprocess.PIPE)
    total = int(round(dur * FPS))
    try:
        for q in range(total):
            tt = q / FPS
            card = Image.new("RGBA", (cw, ch), papel + (255,))
            dd = ImageDraw.Draw(card)
            # padrão discreto do papel
            for yy in range(cab_h + 20, ch, 70):
                for xx in range((yy // 70) % 2 * 35, cw, 70):
                    dd.ellipse((xx, yy, xx + 5, yy + 5), fill=(226, 218, 208))
            visiveis = [(b, tm) for b, tm in zip(msgs, tempos) if tm <= tt]
            # empilha de baixo para cima; a mais nova entra subindo
            y = ch - 40
            dig = next(((a, b) for a, b in digitando if a <= tt < b), None)
            if dig:
                y -= 96
                bx = 34
                dd.rounded_rectangle((bx, y, bx + 150, y + 76), radius=30, fill=clara)
                for k in range(3):
                    fase = (tt * 3.2 - k * 0.33) % 1
                    r = 9 + 4 * max(0.0, math.sin(fase * math.pi))
                    cx, cy = bx + 42 + k * 34, y + 38
                    dd.ellipse((cx - r, cy - r, cx + r, cy + r), fill=_mistura(cor, (120, 120, 120), 0.4))
                y -= 22
            for b, tm in reversed(visiveis):
                prog = _ease((tt - tm) / 0.28)
                desl = int((1 - prog) * 40)
                bw, bh = b.w, b.h
                y_top = y - bh + desl
                # 25/10 17:53: balão meio escondido sob o cabeçalho a trava final leu como "mensagem cortada" ->
                # balão que não cabe inteiro abaixo do cabeçalho não é desenhado (some, como num chat rolando)
                if y_top < cab_h + 8:
                    break
                esquerda = b.de == "cliente"
                bx = 34 if esquerda else cw - 34 - bw
                camada = Image.new("RGBA", (bw + 20, bh + 20), (0, 0, 0, 0))
                dl = ImageDraw.Draw(camada)
                dl.rounded_rectangle((4, 6, bw + 4, bh + 6), radius=30, fill=(0, 0, 0, 40))
                dl.rounded_rectangle((0, 0, bw, bh), radius=30, fill=((255, 255, 255) if esquerda else clara) + (255,))
                ty = 22
                for ln in b.linhas:
                    dl.text((26, ty), ln, font=f_msg, fill=(25, 25, 25))
                    ty += b.lh
                hw = dl.textlength(b.hora, font=f_hora)
                dl.text((bw - hw - (58 if not esquerda else 24), bh - 40), b.hora, font=f_hora, fill=(120, 120, 120))
                if not esquerda:  # dois tiques "lido" desenhados (a Segoe UI não tem "✓": saía quadradinho)
                    tc = _mistura(cor, (0, 0, 0), 0.15)
                    for dx in (0, 11):
                        bx0, by0 = bw - 50 + dx, bh - 26
                        dl.line([(bx0, by0), (bx0 + 6, by0 + 7), (bx0 + 18, by0 - 8)], fill=tc, width=3)
                if prog < 1:
                    s = 0.88 + 0.12 * prog
                    camada = camada.resize((max(1, int(camada.width * s)), max(1, int(camada.height * s))))
                    alfa = camada.getchannel("A").point(lambda v, p=prog: int(v * p))
                    camada.putalpha(alfa)
                # 25/10: antes o balão que chegava no topo era PRESO na borda (max(y, cabeçalho)) e cobria a resposta
                # de baixo; agora ele continua subindo e some sob o cabeçalho (desenhado por cima depois)
                px_ = bx + (0 if esquerda else int((1 - (0.88 + 0.12 * prog)) * bw))
                if y_top < 0:
                    camada = camada.crop((0, -y_top, camada.width, camada.height))
                card.alpha_composite(camada, (px_, max(y_top, 0)))
                y = y_top - 22
            card.alpha_composite(cab, (0, 0))
            mask = Image.new("L", (cw, ch), 0)
            ImageDraw.Draw(mask).rounded_rectangle((0, 0, cw, ch), radius=44, fill=255)
            z = 1 + zoom_fundo * tt / dur
            if fundo is not None and z > 1.001:  # cor lisa: zoom não aparece, só gasta render (ideia da caixa 27/10)
                zw, zh = int(W * z), int(H * z)
                quadro = base.resize((zw, zh), Image.BILINEAR).crop(((zw - W) // 2, (zh - H) // 2,
                                                                      (zw - W) // 2 + W, (zh - H) // 2 + H)).convert("RGBA")
            else:
                quadro = base.convert("RGBA")
            deriva = int(subida * tt / dur)
            quadro.alpha_composite(sombra, (0, 0), (0, deriva))
            entrada = _ease(tt / 0.35)  # cartão entra subindo no começo do bloco
            quadro.paste(card, (x0, y0 + int((1 - entrada) * 60) - deriva), mask)
            proc.stdin.write(quadro.convert("RGB").tobytes())
    finally:
        proc.stdin.close()
        proc.wait(timeout=300)
    if proc.returncode or not Path(saida).exists():
        raise RuntimeError("ffmpeg da conversa falhou")
    return saida
