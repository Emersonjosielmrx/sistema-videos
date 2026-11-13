"""01/11 dona: elementos animados no estilo dos comerciais do Instagram (PRODUTOS_PARA_VER: crmchatwoot, disparoemmassa,
futebolcom, inovarecom) dentro dos longos e Shorts — "o máximo possível, sempre com o máximo de interação, se
movimentando, mudando de posição, nada comum com só uma faixa aparecendo".

Tudo em ASS (libass), na MESMA passada da legenda (fx_subtitles.burn_subtitles_ass): custo de render ~0.

Cartões (escolhidos pelo que a NARRAÇÃO fala, no tempo da palavra):
  personagem   1ª vez que um nome aparece: nome grande + selo + barras de PODER/PERIGO enchendo + estrela girando
  lugar        reino/academia/castelo...: alfinete caindo + nome digitando + sublinhado crescendo
  sistema      nível/habilidade/missão (manhwa): janela [ SISTEMA ] piscando + texto digitando + barra de XP
  chat         disse/perguntou/mensagem: balões entrando um por um no tempo da fala
  alerta       perigo/inimigo/ataque: cartão vermelho tremendo + triângulo pulsando + barra de ameaça
  antes_agora  virou/se tornou/despertou: ANTES (apaga) -> AGORA (acende)
  like         curtir/inscrever/comentar: botão que é apertado, coração fica vermelho, +1 subindo, INSCRITO ✓
Cada cartão entra deslizando de um lado com giro e quique, flutua devagar enquanto fica e sai por outro lado.
ANIME_CARTOES=0 desliga; ANIME_CARTOES_GAP_S = intervalo mínimo entre cartões (padrão 9 s)."""
import hashlib
import math
import os
import re

IN_S, OUT_S = 0.38, 0.32
FS_K = 1.3  # 01/11: no 1º teste as letras saíram pequenas dentro dos cartões

# cores ASS (&H00BBGGRR)
BRANCO, PRETO = "&H00FFFFFF", "&H00000000"
ESCURO = "&H00281A12"
CIANO = "&H00FFD000"
VERMELHO = "&H003C28FF"
VERDE = "&H0066D325"
OURO = "&H0028BEFF"
CINZA = "&H00909090"
ROXO = "&H00FF40B0"


def _ts(t):
    t = max(0.0, t)
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


def _esc(s):
    return str(s).replace("\\", "").replace("{", "(").replace("}", ")")


def _rr(w, h, r):
    """retângulo de cantos redondos (desenho ASS)"""
    r = max(1, min(r, w / 2, h / 2))
    w, h, r = int(w), int(h), int(r)
    return (f"m {r} 0 l {w - r} 0 b {w} 0 {w} 0 {w} {r} l {w} {h - r} b {w} {h} {w} {h} {w - r} {h} "
            f"l {r} {h} b 0 {h} 0 {h} 0 {h - r} l 0 {r} b 0 0 0 0 {r} 0")


def _elipse(cx, cy, rx, ry):
    k = 0.5523
    return (f"m {cx} {cy - ry} b {cx + rx * k:.0f} {cy - ry} {cx + rx} {cy - ry * k:.0f} {cx + rx} {cy} "
            f"b {cx + rx} {cy + ry * k:.0f} {cx + rx * k:.0f} {cy + ry} {cx} {cy + ry} "
            f"b {cx - rx * k:.0f} {cy + ry} {cx - rx} {cy + ry * k:.0f} {cx - rx} {cy} "
            f"b {cx - rx} {cy - ry * k:.0f} {cx - rx * k:.0f} {cy - ry} {cx} {cy - ry}")


def _estrela(cx=50, cy=50, r1=50, r2=21):
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        r = r1 if i % 2 == 0 else r2
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return "m %.0f %.0f " % pts[0] + " ".join("l %.0f %.0f" % p for p in pts[1:])


# ícones desenhados (caixa 100x100) — a fonte da nuvem não tem emoji, então tudo é desenho.
# cada ícone = [(caminho, cor, só_contorno)]; "m 0 0 m 100 100" prende a caixa pra todas as partes alinharem
_CAIXA = "m 0 0 m 100 100 "
ICONES = {
    "coracao": [("m 50 92 b 8 62 0 38 14 20 b 28 4 48 12 50 30 b 52 12 72 4 86 20 b 100 38 92 62 50 92", "&H004040FF", 0)],
    "estrela": [(_estrela(), OURO, 0)],
    "coroa": [("m 8 82 l 8 28 l 30 52 l 50 14 l 70 52 l 92 28 l 92 82 l 8 82", OURO, 0),
              (_elipse(50, 12, 7, 7), "&H004040FF", 0)],
    "chapeu": [("m 4 84 l 96 84 b 96 96 4 96 4 84", "&H00502030", 0),
               ("m 22 84 l 48 34 b 54 16 70 4 90 8 b 72 14 62 30 78 84 l 22 84", "&H00602A40", 0),
               ("m 30 72 l 70 72 l 72 80 l 28 80 l 30 72", ROXO, 0)],
    "corrente": [(_elipse(22, 50, 18, 11), CINZA, 1), (_elipse(50, 50, 18, 11), "&H00C0C0C0", 1),
                 (_elipse(78, 50, 18, 11), CINZA, 1)],
    "raio": [("m 58 0 l 18 56 l 44 56 l 32 100 l 82 38 l 56 38 l 72 0 l 58 0", "&H0000FFFF", 0)],
    "fogo": [("m 50 0 b 64 26 92 40 86 70 b 80 94 64 100 50 100 b 32 100 14 92 14 70 b 14 52 30 42 36 24 "
              "b 42 40 48 44 50 0", "&H000060FF", 0),
             ("m 50 46 b 58 60 72 68 68 82 b 64 96 54 98 50 98 b 40 98 32 92 32 82 b 32 70 44 64 50 46",
              "&H0000D8FF", 0)],
    "caveira": [(_elipse(50, 42, 38, 36), "&H00F0F0F0", 0), ("m 30 70 l 70 70 l 70 96 l 30 96 l 30 70", "&H00F0F0F0", 0),
                (_elipse(35, 44, 10, 11), PRETO, 0), (_elipse(65, 44, 10, 11), PRETO, 0),
                ("m 50 56 l 56 68 l 44 68 l 50 56", PRETO, 0)],
    "espadas": [("m 10 0 l 18 0 l 92 86 l 86 92 l 10 0", "&H00E0E0E0", 0),
                ("m 90 0 l 82 0 l 8 86 l 14 92 l 90 0", "&H00E0E0E0", 0),
                ("m 66 70 l 76 60 l 92 76 l 82 86 l 66 70", OURO, 0), ("m 34 70 l 24 60 l 8 76 l 18 86 l 34 70", OURO, 0)],
    "alfinete": [("m 50 100 b 22 62 12 48 12 36 b 12 12 30 0 50 0 b 70 0 88 12 88 36 b 88 48 78 62 50 100",
                  "&H003C28FF", 0), (_elipse(50, 36, 14, 14), BRANCO, 0)],
    "alerta": [("m 50 2 l 98 90 l 2 90 l 50 2", "&H0000D8FF", 0), ("m 45 28 l 55 28 l 53 64 l 47 64 l 45 28", PRETO, 0),
               (_elipse(50, 76, 6, 6), PRETO, 0)],
    "check": [("m 8 52 l 24 36 l 42 54 l 80 14 l 96 30 l 42 86 l 8 52", VERDE, 0)],
    "balao": [("m 10 10 l 90 10 b 98 10 98 10 98 18 l 98 62 b 98 70 98 70 90 70 l 40 70 l 20 92 l 24 70 l 10 70 "
               "b 2 70 2 70 2 62 l 2 18 b 2 10 2 10 10 10", VERDE, 0)],
}


def icone(nome, cx, cy, tam, layer=7, extra=""):
    """linhas de evento (sem tempo) de um ícone centrado em (cx, cy) com lado tam px: [(layer, tags, desenho)]"""
    out = []
    esc = tam
    for caminho, cor, contorno in ICONES.get(nome, []):
        if contorno:
            tags = "\\1a&HFF&\\bord%d\\3c%s" % (max(2, tam // 12), cor)
        else:
            tags = "\\1c%s\\bord%d\\3c&H00101010&" % (cor, max(1, tam // 40))
        out.append((layer, "\\an5\\fscx%d\\fscy%d\\shad0%s%s" % (esc, esc, tags, extra), "{\\p1}" + _CAIXA + caminho))
    return out


# ---------------------------------------------------------------------------------------------- montagem genérica
class Cartao:
    """um cartão = caixa w x h + elementos com posição relativa ao canto de cima-esquerda do cartão.
    elemento: dict(x, y, layer, tags, txt, an=5, delay=0, fim=None, mv=None, pop=False)"""

    def __init__(self, tipo, rotulo, w, h):
        self.tipo, self.rotulo, self.w, self.h = tipo, rotulo, w, h
        self.els = []

    def add(self, x, y, txt, tags="", layer=10, an=5, delay=0.0, fim=None, mv=None, pop=False):
        self.els.append(dict(x=x, y=y, txt=txt, tags=tags, layer=layer, an=an, delay=delay, fim=fim, mv=mv, pop=pop))

    def caixa(self, cor_fundo, cor_borda, u, alpha="20", brilho=True, layer=2):
        w, h = self.w, self.h
        if brilho:
            self.add(w / 2, h / 2, "{\\p1}" + _rr(w, h, 16 * u),
                     "\\1c%s\\1a&H90&\\bord%d\\3c%s\\3a&H40&\\blur%d\\shad0" % (cor_borda, int(5 * u), cor_borda, int(9 * u)),
                     layer=layer)
        self.add(w / 2, h / 2, "{\\p1}" + _rr(w, h, 16 * u),
                 "\\1c%s\\1a&H%s&\\bord%d\\3c%s\\shad%d\\4a&H60&" % (cor_fundo, alpha, max(2, int(2.5 * u)), cor_borda,
                                                                     int(4 * u)), layer=layer + 1)

    def texto(self, x, y, txt, fonte, fs, cor=BRANCO, an=5, layer=12, extra="", delay=0.0, digitar=False, fim=None,
              pop=False, mv=None, bord=None):
        fs = int(fs * FS_K)
        b = max(1, int(fs / 14)) if bord is None else bord
        if digitar:  # digita UMA vez, com o cartão já parado (o karaokê recomeça a cada evento)
            delay = max(delay, IN_S + 0.02)
        t ="\\fn%s\\fs%d\\1c%s\\bord%d\\3c&H00101010&\\shad0%s" % (fonte, fs, cor, b, extra)
        corpo = _esc(txt)
        if digitar:  # efeito máquina de escrever: cada letra aparece no seu tempo (karaokê com a 2ª cor invisível)
            passo = max(2, min(6, int(90 / max(1, len(corpo)))))
            t += "\\2a&HFF&"
            corpo = "".join("{\\ko%d}%s" % (passo, c) for c in corpo)  # ko = contorno também só aparece digitado
        self.add(x, y, corpo, t, layer=layer, an=an, delay=delay, fim=fim, pop=pop, mv=mv)

    def barra(self, x, y, w, h, cor, pct, u, delay=0.25, dur_ms=900, layer=8, piscar=False):
        """barra que enche da esquerda pra direita até pct"""
        self.add(x + w / 2, y, "{\\p1}" + _rr(w, h, h / 2), "\\1c&H00303030&\\1a&H30&\\bord0\\shad0", layer=layer)
        extra = ""
        if piscar:
            extra = "".join("\\t(%d,%d,\\1a&H70&)\\t(%d,%d,\\1a&H00&)" % (dur_ms + 250 * i, dur_ms + 250 * i + 120,
                                                                          dur_ms + 250 * i + 120, dur_ms + 250 * i + 250)
                            for i in range(6))
        self.add(x, y, "{\\p1}" + _rr(max(h, w * pct), h, h / 2),
                 "\\1c%s\\bord0\\shad0\\fscx0\\t(0,%d,\\fscx100)%s" % (cor, dur_ms, extra), layer=layer + 1, an=4,
                 delay=delay)

    def icone(self, nome, x, y, tam, layer=9, extra="", delay=0.0, pop=False, fim=None, mv=None):
        for ly, tags, des in icone(nome, 0, 0, tam, layer, extra):
            self.add(x, y, des, tags.replace("\\an5", ""), layer=ly, delay=delay, pop=pop, fim=fim, mv=mv)

    # ------------------------------------------------------------------ eventos com movimento
    def eventos(self, t0, t1, X, Y, entra, sai, deriva, giro):
        """X,Y = canto do cartão no lugar final; entra/sai = deslocamento (px) de onde vem/pra onde vai;
        deriva = quanto flutua enquanto fica; giro = graus na entrada (volta a 0) e na saída (o contrário)"""
        linhas = []
        ti, to_ = t0 + IN_S, t1 - OUT_S
        hold = max(0.01, to_ - ti)
        cx, cy = X + self.w / 2, Y + self.h / 2
        org = "\\org(%d,%d)" % (cx, cy)

        def pos(el, t):
            f = min(1.0, max(0.0, (t - ti) / hold))
            return X + el["x"] + deriva[0] * f, Y + el["y"] + deriva[1] * f

        for el in self.els:
            an = "\\an%d" % el["an"]
            ini = t0 + el["delay"]
            fim = t1 if el["fim"] is None else min(t1, t0 + el["fim"])
            if fim - ini < 0.05:
                continue
            base = an + el["tags"]
            _esc_b = re.search(r"\\fscx(\d+)\\fscy(\d+)", el["tags"])
            bx, by = (int(_esc_b.group(1)), int(_esc_b.group(2))) if _esc_b else (100, 100)
            barra = "\\fscx0" in el["tags"]  # barra enchendo: não mexe na escala dela
            if el["delay"] < 0.05:  # entra com o cartão: desliza + gira + quica
                x1, y1 = X + el["x"], Y + el["y"]
                quica = "" if barra else "\\fscx%d\\fscy%d\\t(0,%d,\\fscx%d\\fscy%d)\\t(%d,%d,\\fscx%d\\fscy%d)" % (
                    bx * 0.88, by * 0.88, int(IN_S * 700), bx * 1.06, by * 1.06, int(IN_S * 700), int(IN_S * 1000),
                    bx, by)
                linhas.append("Dialogue: %d,%s,%s,Cart,,0,0,0,,{%s\\move(%d,%d,%d,%d)%s\\frz%d\\t(0,%d,\\frz0)%s}%s" % (
                    el["layer"], _ts(t0), _ts(ti), base, x1 + entra[0], y1 + entra[1], x1, y1, org, giro,
                    int(IN_S * 700), quica, el["txt"]))
                ini = ti
            ini = max(ini, ti)
            fim_h = min(fim, to_)
            if fim_h - ini > 0.02:  # flutuando (com leve balanço)
                xa, ya = pos(el, ini)
                xb, yb = pos(el, fim_h)
                if el["mv"]:
                    xb, yb = xb + el["mv"][0], yb + el["mv"][1]
                pop = ""
                if el["pop"]:  # pula na tela relativo ao tamanho do próprio elemento (ícone já vem com fscx)
                    pop = "\\fscx%d\\fscy%d\\t(0,160,\\fscx%d\\fscy%d)\\t(160,260,\\fscx%d\\fscy%d)" % (
                        bx * 0.1, by * 0.1, bx * 1.18, by * 1.18, bx, by)
                elif el["delay"] >= 0.05 and ini - (t0 + el["delay"]) < 0.05:
                    pop = "\\fad(150,0)"
                d = int((fim_h - ini) * 1000)
                bal = "\\frz0\\t(0,%d,\\frz%.1f)" % (d, -giro / 6.0)
                sai_el = "\\t(%d,%d,\\alpha&HFF&)" % (max(0, d - 200), d) if el["fim"] is not None and fim < to_ else ""
                linhas.append("Dialogue: %d,%s,%s,Cart,,0,0,0,,{%s\\move(%d,%d,%d,%d)%s%s%s%s}%s" % (
                    el["layer"], _ts(ini), _ts(fim_h), base, xa, ya, xb, yb, org, bal, pop, sai_el, el["txt"]))
            if fim >= t1 - 0.01:  # sai com o cartão
                xa, ya = X + el["x"] + deriva[0], Y + el["y"] + deriva[1]
                if el["mv"]:
                    xa, ya = xa + el["mv"][0], ya + el["mv"][1]
                fim_esc = "" if barra else "\\fscx%d\\fscy%d" % (bx * 0.92, by * 0.92)
                tags_s = base.replace("\\fscx0", "\\fscx100") if barra else base  # barra sai cheia
                tags_s = re.sub(r"\\t\(\d+,\d+,\\fscx100\)", "", tags_s) if barra else tags_s
                linhas.append("Dialogue: %d,%s,%s,Cart,,0,0,0,,{%s\\move(%d,%d,%d,%d)%s\\frz%.1f"
                              "\\t(0,%d,\\frz%d%s\\alpha&HFF&)}%s" % (
                                  el["layer"], _ts(to_), _ts(t1), tags_s, xa, ya, xa + sai[0], ya + sai[1], org,
                                  -giro / 6.0, int(OUT_S * 1000), -giro, fim_esc,
                                  re.sub(r"\{\\ko?\d+\}", "", el["txt"])))
        return linhas


# ---------------------------------------------------------------------------------------------- cada tipo
def _seed(s):
    return int(hashlib.md5(s.encode("utf-8")).hexdigest()[:8], 16)


_FONTES_ARQ = {"Montserrat Black": "Montserrat-Black.ttf", "Montserrat ExtraBold": "Montserrat-ExtraBold.ttf",
               "Bangers": "Bangers-Regular.ttf", "Impact": "impact.ttf"}
_PASTA_FONTES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "workspace", "assets", "fonts")
_CACHE_F = {}


def _larg(txt, fs, k=0.62, fonte="Montserrat Black"):
    """largura real do texto (Pillow com a mesma fonte do libass); sem Pillow/fonte = estimativa"""
    fs = int(fs * FS_K)
    try:
        from PIL import ImageFont
        chave = (fonte, fs)
        if chave not in _CACHE_F:
            _CACHE_F[chave] = ImageFont.truetype(os.path.join(_PASTA_FONTES, _FONTES_ARQ[fonte]), fs)
        return _CACHE_F[chave].getlength(txt) * 1.06
    except Exception:  # noqa: BLE001
        return len(txt) * fs * k


def c_personagem(nome, selo, cor, u):
    fs_n = int(58 * u)
    w = max(300 * u, _larg(nome, fs_n, 0.5, "Bangers") + 120 * u)
    h = 168 * u
    c = Cartao("personagem", f"apresentação de personagem: {nome}", w, h)
    c.caixa(ESCURO, cor, u)
    c.add(10 * u, h / 2, "{\\p1}" + _rr(8 * u, h - 30 * u, 4 * u), "\\1c%s\\bord0\\shad0" % cor, layer=6)
    fs_s = int(15 * u)
    ws = _larg(selo, fs_s, 0.7) + 22 * u
    c.add(26 * u + ws / 2, 24 * u, "{\\p1}" + _rr(ws, 26 * u, 13 * u), "\\1c%s\\bord0\\shad0" % cor, layer=6)
    c.texto(26 * u + ws / 2, 24 * u, selo, "Montserrat Black", fs_s, PRETO, bord=0)
    c.texto(26 * u, 66 * u, nome, "Bangers", fs_n, BRANCO, an=4, extra="\\fsp2", digitar=True, delay=0.0)
    c.icone("estrela", w - 34 * u, 30 * u, int(36 * u), extra="\\t(0,4000,\\frz360)")
    sd = _seed(nome)
    for i, (rot, pct) in enumerate((("PODER", 0.62 + (sd % 36) / 100), ("PERIGO", 0.45 + (sd // 7 % 50) / 100))):
        y = 112 * u + i * 30 * u
        c.texto(26 * u, y, rot, "Montserrat Black", int(14 * u), "&H00C8C8C8", an=4, bord=0)
        c.barra(110 * u, y, w - 140 * u, 12 * u, cor, min(0.98, pct), u, delay=0.35 + 0.25 * i)
    return c


def c_lugar(texto, u):
    fs = int(36 * u)
    w = max(280 * u, _larg(texto, fs) + 110 * u)
    h = 110 * u
    c = Cartao("lugar", f"apresentação de lugar: {texto}", w, h)
    c.caixa(ESCURO, OURO, u)
    c.icone("alfinete", 44 * u, h / 2 + 4 * u, int(56 * u), delay=0.25, pop=True)
    c.texto(84 * u, 30 * u, "LOCAL", "Montserrat Black", int(14 * u), OURO, an=4, bord=0, extra="\\fsp4")
    c.texto(84 * u, 66 * u, texto, "Montserrat Black", fs, BRANCO, an=4, digitar=True)
    c.add(84 * u, 92 * u, "{\\p1}" + _rr(w - 110 * u, 5 * u, 2 * u),
          "\\1c%s\\bord0\\shad0\\fscx0\\t(0,700,\\fscx100)" % OURO, layer=8, an=4, delay=0.4)
    return c


def c_sistema(cabeca, linha, u):
    fs = int(26 * u)
    w = max(360 * u, _larg(linha, fs) + 60 * u)
    h = 150 * u
    c = Cartao("sistema", f"janela de sistema: {linha}", w, h)
    c.caixa("&H00301808", CIANO, u, alpha="30")
    pulsa = "".join("\\t(%d,%d,\\3a&HA0&)\\t(%d,%d,\\3a&H00&)" % (i * 600, i * 600 + 300, i * 600 + 300, i * 600 + 600)
                    for i in range(8))
    c.add(w / 2, h / 2, "{\\p1}" + _rr(w + 8 * u, h + 8 * u, 18 * u),
          "\\1a&HFF&\\bord%d\\3c%s\\blur%d\\shad0%s" % (int(3 * u), CIANO, int(6 * u), pulsa), layer=1)
    c.texto(w / 2, 26 * u, f"[ {cabeca} ]", "Montserrat Black", int(18 * u), CIANO, bord=0, extra="\\fsp6")
    c.add(w / 2, 46 * u, "{\\p1}" + _rr(w - 40 * u, 2 * u, 1), "\\1c%s\\1a&H60&\\bord0\\shad0" % CIANO, layer=6)
    c.texto(w / 2, 82 * u, linha, "Montserrat Black", fs, BRANCO, digitar=True, delay=0.1)
    c.texto(30 * u, 122 * u, "XP", "Montserrat Black", int(14 * u), CIANO, an=4, bord=0)
    c.barra(66 * u, 122 * u, w - 100 * u, 10 * u, CIANO, 1.0, u, delay=0.6, dur_ms=1400, piscar=True)
    return c


def c_chat(baloes, u, t0):
    """baloes = [(tempo_abs, texto)]"""
    fs = int(22 * u)
    w = max(360 * u, max(_larg(b, fs, 0.55, "Montserrat ExtraBold") for _t, b in baloes) + 90 * u)
    hb = 50 * u
    h = 56 * u + len(baloes) * (hb + 12 * u) + 6 * u
    c = Cartao("chat", "chat com a fala: " + " / ".join(b for _t, b in baloes), w, h)
    c.caixa("&H00101810", VERDE, u, alpha="30")
    c.icone("balao", 30 * u, 28 * u, int(30 * u))
    c.texto(54 * u, 28 * u, "CONVERSA", "Montserrat Black", int(15 * u), VERDE, an=4, bord=0, extra="\\fsp3")
    for i, (tb, txt) in enumerate(baloes):
        y = 56 * u + i * (hb + 12 * u) + hb / 2
        wb = _larg(txt, fs, 0.55, "Montserrat ExtraBold") + 36 * u
        x = 20 * u + wb / 2 if i % 2 == 0 else w - 20 * u - wb / 2
        cor = "&H00403020" if i % 2 == 0 else "&H00305A1F"
        d = max(0.0, tb - t0)
        c.add(x, y, "{\\p1}" + _rr(wb, hb, 14 * u), "\\1c%s\\bord0\\shad%d\\4a&H60&" % (cor, int(3 * u)),
              layer=6, delay=d, pop=True)
        c.texto(x, y, txt, "Montserrat ExtraBold", fs, BRANCO, delay=d, pop=True, bord=0)
    return c


def c_alerta(palavra, u):
    fs = int(44 * u)
    w = max(320 * u, _larg(palavra, int(30 * u)) + 140 * u)
    h = 150 * u
    c = Cartao("alerta", f"alerta: {palavra}", w, h)
    c.caixa("&H00100830", VERMELHO, u, alpha="20")
    treme = "".join("\\t(%d,%d,\\frz%d)" % (i * 70, i * 70 + 70, 3 if i % 2 else -3) for i in range(10)) + \
        "\\t(700,760,\\frz0)"
    c.icone("alerta", 52 * u, 54 * u, int(64 * u),
            extra="".join("\\t(%d,%d,\\fscx%d\\fscy%d)" % (i * 300, i * 300 + 300, 115 if i % 2 == 0 else 100,
                                                            115 if i % 2 == 0 else 100) for i in range(10)))
    c.texto(98 * u, 40 * u, "ALERTA", "Bangers", fs, "&H0000D8FF", an=4, extra=treme + "\\fsp3")
    c.texto(98 * u, 84 * u, palavra, "Montserrat Black", int(28 * u), BRANCO, an=4, digitar=True, delay=0.2)
    c.texto(26 * u, 124 * u, "AMEAÇA", "Montserrat Black", int(13 * u), "&H008080FF", an=4, bord=0)
    c.barra(104 * u, 124 * u, w - 130 * u, 12 * u, VERMELHO, 1.0, u, delay=0.3, dur_ms=800, piscar=True)
    return c


def c_antes_agora(antes, agora, u, d_agora):
    fs = int(26 * u)
    w = max(340 * u, max(_larg(antes, fs), _larg(agora, fs)) + 60 * u)
    hb = 84 * u
    h = hb * 2 + 16 * u
    c = Cartao("antes_agora", f"antes/agora: {antes} -> {agora}", w, h)
    # ANTES (cinza) — apaga quando o AGORA chega
    apaga = "\\t(%d,%d,\\alpha&H90&)" % (int(d_agora * 1000), int(d_agora * 1000) + 300)
    c.add(w / 2, hb / 2, "{\\p1}" + _rr(w, hb, 14 * u),
          "\\1c&H00303030&\\1a&H20&\\bord%d\\3c%s\\shad0%s" % (int(2 * u), CINZA, apaga), layer=3)
    c.texto(20 * u, 22 * u, "ANTES", "Montserrat Black", int(14 * u), CINZA, an=4, bord=0, extra=apaga + "\\fsp4")
    c.texto(20 * u, 54 * u, antes, "Montserrat Black", fs, "&H00D0D0D0", an=4, extra=apaga)
    y2 = hb + 16 * u
    c.add(w / 2, y2 + hb / 2, "{\\p1}" + _rr(w + 10 * u, hb + 10 * u, 18 * u),
          "\\1a&HFF&\\bord%d\\3c%s\\blur%d\\shad0" % (int(5 * u), VERDE, int(10 * u)), layer=2, delay=d_agora, pop=True)
    c.add(w / 2, y2 + hb / 2, "{\\p1}" + _rr(w, hb, 14 * u),
          "\\1c&H00183018&\\1a&H10&\\bord%d\\3c%s\\shad0" % (int(3 * u), VERDE), layer=3, delay=d_agora, pop=True)
    c.texto(20 * u, y2 + 22 * u, "AGORA", "Montserrat Black", int(14 * u), VERDE, an=4, bord=0, delay=d_agora,
            extra="\\fsp4")
    c.texto(20 * u, y2 + 54 * u, agora, "Montserrat Black", fs, BRANCO, an=4, delay=d_agora, digitar=True)
    c.icone("raio", w - 34 * u, y2 + hb / 2, int(44 * u), delay=d_agora + 0.15, pop=True)
    return c


def c_like(u):
    w, h = 330 * u, 150 * u
    c = Cartao("like", "botão de like/inscrição animado", w, h)
    hp = 58 * u
    # pílula CURTIR: branca, é apertada em 0.9 s e o coração fica vermelho
    aperta = "\\t(900,1000,\\fscx88\\fscy88)\\t(1000,1150,\\fscx108\\fscy108)\\t(1150,1250,\\fscx100\\fscy100)"
    c.add(w / 2, hp / 2, "{\\p1}" + _rr(w, hp, hp / 2), "\\1c%s\\bord0\\shad%d\\4a&H50&%s" % (BRANCO, int(4 * u), aperta),
          layer=4)
    c.add(52 * u, hp / 2, "{\\p1}" + _CAIXA + ICONES["coracao"][0][0],
          "\\fscx%d\\fscy%d\\1c&H00A0A0A0&\\bord0\\shad0%s\\t(950,1050,\\1c&H004040FF&)" % (int(38 * u), int(38 * u), aperta),
          layer=6)
    c.texto(w / 2 + 20 * u, hp / 2, "CURTIR", "Montserrat Black", int(24 * u), "&H00202020", bord=0, extra=aperta)
    for i in range(4):  # +1 subindo
        c.texto(60 * u + i * 40 * u, hp / 2 - 10 * u, "+1", "Bangers", int(26 * u), "&H004040FF", delay=1.0 + i * 0.22,
                fim=1.0 + i * 0.22 + 0.9, mv=(0, -70 * u))
    # pílula INSCREVER-SE vermelha que vira INSCRITO ✓ cinza
    y2 = hp + 22 * u + hp / 2
    c.add(w / 2, y2, "{\\p1}" + _rr(w, hp, hp / 2),
          "\\1c%s\\bord0\\shad%d\\4a&H50&\\t(1900,2050,\\1c&H00505050&)" % ("&H000000E6", int(4 * u)),
          layer=4, delay=0.6, pop=True)
    c.texto(w / 2, y2, "INSCREVER-SE", "Montserrat Black", int(24 * u), BRANCO, bord=0, delay=0.6, fim=1.95, pop=True)
    c.texto(w / 2 - 16 * u, y2, "INSCRITO", "Montserrat Black", int(24 * u), BRANCO, bord=0, delay=1.95, pop=True)
    c.icone("check", w / 2 + 92 * u, y2, int(28 * u), delay=2.05, pop=True)
    return c


def c_triunfo(palavra, u):
    """aprendizado b450f844: flare/brilho divino no momento de triunfo — raios girando + estrela + VITÓRIA"""
    w, h = 420 * u, 220 * u
    c = Cartao("triunfo", f"brilho de triunfo: {palavra}", w, h)
    raios = " ".join("m 100 100 l %.0f %.0f l %.0f %.0f" % (
        100 + 100 * math.cos(a - 0.09), 100 + 100 * math.sin(a - 0.09), 100 + 100 * math.cos(a + 0.09),
        100 + 100 * math.sin(a + 0.09)) for a in (i * math.pi / 8 for i in range(16)))
    tam = int(260 * u / 2)
    c.add(w / 2, h / 2, "{\\p1}" + raios, "\\fscx%d\\fscy%d\\1c%s\\1a&H50&\\bord0\\blur%d\\shad0\\t(0,4000,\\frz120)" % (
        tam, tam, OURO, int(3 * u)), layer=1)
    c.add(w / 2, h / 2, "{\\p1}" + _elipse(50, 50, 50, 50),
          "\\fscx%d\\fscy%d\\1c&H00C0F8FF&\\1a&H40&\\bord0\\blur%d\\shad0" % (int(150 * u), int(150 * u), int(18 * u)),
          layer=2)
    c.icone("estrela", w / 2, h / 2 - 30 * u, int(70 * u), extra="\\t(0,3000,\\frz-200)")
    c.texto(w / 2, h / 2 + 40 * u, "VITÓRIA!", "Bangers", int(50 * u), OURO, extra="\\fsp4\\3c&H00004080&",
            pop=True, delay=0.15)
    c.texto(w / 2, h / 2 + 82 * u, palavra, "Montserrat Black", int(18 * u), BRANCO, bord=2, delay=0.5, digitar=True)
    return c


def c_gps(palavra, u, seed):
    """aprendizado 1e25c542: mapa estilo GPS em investigação/perseguição — trilha de pontos acendendo até o alfinete"""
    w, h = 380 * u, 230 * u
    c = Cartao("gps", f"mapa GPS: {palavra}", w, h)
    c.caixa("&H00201A14", "&H00FFB040", u, alpha="20")
    for i in range(1, 6):  # quadriculado do mapa
        c.add(w * i / 6, h / 2 + 12 * u, "{\\p1}" + _rr(1.5 * u, h - 60 * u, 1), "\\1c&H00FFB040&\\1a&HC0&\\bord0\\shad0",
              layer=4)
    for i in range(1, 4):
        c.add(w / 2, 40 * u + (h - 40 * u) * i / 4, "{\\p1}" + _rr(w - 20 * u, 1.5 * u, 1),
              "\\1c&H00FFB040&\\1a&HC0&\\bord0\\shad0", layer=4)
    c.texto(20 * u, 24 * u, "RASTREANDO...", "Montserrat Black", int(15 * u), "&H00FFB040&", an=4, bord=0,
            extra="\\fsp3" + "".join("\\t(%d,%d,\\alpha&H80&)\\t(%d,%d,\\alpha&H00&)" % (
                i * 500, i * 500 + 250, i * 500 + 250, i * 500 + 500) for i in range(8)))
    pts, n = [], 9
    sd = seed
    for i in range(n):  # trilha em zigue-zague de baixo-esquerda até cima-direita
        x = 40 * u + (w - 110 * u) * i / (n - 1)
        y = h - 40 * u - (h - 120 * u) * i / (n - 1) + (((sd >> i) & 3) - 1.5) * 14 * u
        pts.append((x, y))
    for i, (x, y) in enumerate(pts[:-1]):
        c.add(x, y, "{\\p1}" + _elipse(50, 50, 50, 50), "\\fscx%d\\fscy%d\\1c&H0000D8FF&\\bord0\\shad0" % (
            int(10 * u), int(10 * u)), layer=7, delay=0.45 + i * 0.12, pop=True)
    xf, yf = pts[-1]
    c.icone("alfinete", xf, yf - 18 * u, int(46 * u), delay=0.45 + n * 0.12, pop=True)
    c.texto(xf - 10 * u, yf + 22 * u, palavra, "Montserrat Black", int(15 * u), BRANCO, an=6, bord=2,
            delay=0.6 + n * 0.12, pop=True)
    return c


def c_seta(palavra, u, seed):
    """aprendizado 64e54485: seta amarela cartoon apontando um detalhe quando o narrador manda reparar ("repara",
    "olha", "detalhe") — sem caixa, só a seta grossa com contorno preto quicando na direção do centro + 1 palavra"""
    w, h = 300 * u, 190 * u
    c = Cartao("seta", f"seta apontando: {palavra}", w, h)
    # ângulo na TELA (y pra baixo) apontando pro centro a partir do lugar do _lugar (n % 4: cima-esq, cima-dir,
    # meio-esq, meio-dir). Os pontos giram no próprio desenho: o \frz do elemento é sobrescrito pelo balanço do cartão
    ang = math.radians((25, 155, 0, 180)[seed % 4])
    pts = [(0, 40), (60, 40), (60, 10), (100, 50), (60, 90), (60, 60), (0, 60)]
    rot = [(50 + (x - 50) * math.cos(ang) - (y - 50) * math.sin(ang),
            50 + (x - 50) * math.sin(ang) + (y - 50) * math.cos(ang)) for x, y in pts]
    seta = "m %.0f %.0f " % rot[0] + " ".join("l %.0f %.0f" % p for p in rot[1:]) + " l %.0f %.0f" % rot[0]
    tam = int(150 * u)
    c.add(w / 2, h / 2 - 10 * u, "{\\p1}" + _CAIXA + seta,
          "\\fscx%d\\fscy%d\\1c&H0000E0FF&\\bord%d\\3c&H00101010&\\shad%d\\4a&H70&" % (
              tam, tam, max(3, int(5 * u)), int(4 * u)), layer=8, pop=True,
          mv=(18 * u * math.cos(ang), 18 * u * math.sin(ang)))  # desliza na direção que aponta
    c.texto(w / 2, h - 18 * u, palavra, "Bangers", int(52 * u), "&H0000E0FF&", bord=max(3, int(4 * u)), delay=0.2,
            pop=True, extra="\\fsp2")
    return c


def c_obra_fixado(u):
    """L-10 (LONGOS_MELHORIAS, 01/11): aos ~5 min do longo, 3 s, sem pausar a fala — "nome da obra no comentário
    fixado" com a seta descendo (PADROES_COMUNS item 8). O comentário fixado em si é do extras_ledger."""
    fs = int(26 * u)
    txt = "NOME DA OBRA NO COMENTÁRIO FIXADO"
    w = max(360 * u, _larg(txt, fs) + 120 * u)
    h = 96 * u
    c = Cartao("obra_fixado", "nome da obra no comentário fixado", w, h)
    c.caixa("&H00201010", OURO, u, alpha="10")
    c.icone("alfinete", 44 * u, h / 2, int(50 * u), delay=0.2, pop=True)
    c.texto(86 * u, 36 * u, txt, "Montserrat Black", fs, BRANCO, an=4, digitar=True)
    seta = "m 50 100 l 0 50 l 30 50 l 30 0 l 70 0 l 70 50 l 100 50 l 50 100"
    quica = "".join("\\t(%d,%d,\\fscy%d)" % (i * 300, i * 300 + 150, int(30 * u) if i % 2 == 0 else int(24 * u))
                    for i in range(10))
    c.add(86 * u + 14 * u, 70 * u, "{\\p1}" + _CAIXA + seta,
          "\\fscx%d\\fscy%d\\1c%s\\bord0\\shad0%s" % (int(24 * u), int(24 * u), OURO, quica), layer=9, delay=0.4)
    c.texto(120 * u, 70 * u, "olha lá embaixo", "Montserrat ExtraBold", int(15 * u), OURO, an=4, bord=0, delay=0.5)
    return c


def c_comentario(abertura, u):
    """01/11 dona: o comentário pessoal do narrador ganha um balão — o espectador vê que é o narrador falando por ele"""
    fs = int(26 * u)
    txt = abertura.upper().rstrip(",:")
    w = max(300 * u, _larg(txt, fs) + 110 * u)
    h = 92 * u
    c = Cartao("comentario", f"comentário do narrador: {abertura}", w, h)
    c.caixa("&H00402010", "&H00FFC040", u, alpha="10")
    c.icone("balao", 44 * u, h / 2, int(52 * u),
            extra="".join("\\t(%d,%d,\\frz%d)" % (i * 400, i * 400 + 400, 8 if i % 2 == 0 else -8) for i in range(15)))
    c.texto(84 * u, 34 * u, txt, "Montserrat Black", fs, BRANCO, an=4, digitar=True)
    c.texto(84 * u, 66 * u, "comentário do narrador", "Montserrat ExtraBold", int(14 * u), "&H00FFC040&", an=4, bord=0,
            delay=0.3)
    return c


# ---------------------------------------------------------------------------------------------- o que a narração fala
_PARADA = {"Ele", "Ela", "Eles", "Elas", "Mas", "Depois", "Então", "Quando", "Enquanto", "Agora", "Porém", "Isso",
           "Esse", "Essa", "Este", "Esta", "Aqui", "Ali", "Lá", "Nesse", "Nessa", "Com", "Sem", "Para", "Pra", "Por",
           "Que", "Como", "Mesmo", "Até", "Sim", "Não", "Deus", "Rei", "Rainha", "Sistema", "Senhor", "Senhora",
           "Mestre", "Capítulo", "Parte", "Episódio", "Inscreva", "Curta", "Comente", "Você", "Vocês", "Nós", "Tudo",
           "Nada", "Todos", "Todas", "Cada", "Seu", "Sua", "Meu", "Minha", "Nosso", "Nossa", "Uma", "Um", "Os", "As",
           "No", "Na", "Do", "Da", "De", "Em", "Mais", "Muito", "Pois", "Só", "Ainda", "Logo", "Assim", "Ou", "Se"}
_RE_NOME = re.compile(r"^[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõçà]{2,14}$")
_RE_LUGAR = re.compile(r"^(reino|academia|castelo|cidade|vila|aldeia|floresta|masmorra|império|imperio|escola|"
                       r"palácio|palacio|torre|capital|templo|montanha|deserto|ilha|prisão|prisao|mansão|mansao|"
                       r"dungeon|guilda|continente|mundo|caverna|arena|fortaleza)$", re.I)
_RE_SISTEMA = re.compile(r"^(n[íi]vel|level|lvl|rank\w*|sistema|habilidade\w*|status|xp|experi[êe]ncia|miss[ãa]o|"
                         r"quest|recompensa|evolu\w*|atributo\w*|classe)$", re.I)
_RE_CHAT = re.compile(r"^(disse|falou|perguntou|gritou|respondeu|avisou|ordenou|prometeu|confessou|sussurrou|"
                      r"mensagem|carta|declarou|anunciou|pediu)[:,]?$", re.I)
_RE_ALERTA = re.compile(r"^(perigo|amea[çc]a\w*|inimig\w*|chefe|ataque|atac\w*|invas\w*|ex[ée]rcito|emboscada|"
                        r"batalha|guerra|monstr\w*|dem[ôo]ni\w*|assassin\w*|drag[ãa]o)$", re.I)
_RE_VIRA = re.compile(r"^(virou|tornou|transform\w*|evoluiu|despertou|renasceu|reencarn\w*)$", re.I)
_RE_TRIUNFO = re.compile(r"^(venceu|vit[óo]ria|derrotou|conseguiu|triunf\w*|campe[ãa]o?|esmagou|aniquilou|"
                         r"humilhou)$", re.I)
_RE_GPS = re.compile(r"^(investig\w*|procur\w*|rastre\w*|pista\w*|persegu\w*|fugiu|viajou|escondeu|desapareceu|"
                     r"seguiu|ca[çc]ou|ca[çc]ada)$", re.I)
_RE_LIKE = re.compile(r"^(curt\w*|like|inscrev\w*|coment\w*|sininho)$", re.I)
_RE_SETA = re.compile(r"^(repar[ae]\w*|percebe\w*|notou|detalhe\w*|olha)$", re.I)
_FIM_FRASE = re.compile(r"[.!?…]$")


def _limpa(w):
    return re.sub(r"^[^\wÀ-ÿ]+|[^\wÀ-ÿ]+$", "", w)


def _trecho(pal, i, n, ate_frase=True):
    out = []
    for j in range(i, min(len(pal), i + n)):
        out.append(_limpa(pal[j][2]))
        if ate_frase and _FIM_FRASE.search(pal[j][2]):
            break
    return [o for o in out if o]


def candidatos(pal):
    """pal = [(t0, t1, palavra)] do vídeo todo -> [(t, prioridade, tipo, dados)]"""
    cands = []
    inicio = [True] + [bool(_FIM_FRASE.search(p[2])) for p in pal[:-1]]
    cont = {}
    for t0, t1, w in pal:
        lw = _limpa(w)
        if _RE_NOME.match(lw) and lw not in _PARADA:
            cont[lw] = cont.get(lw, 0) + 1
    nomes = sorted((n for n, k in cont.items() if k >= 3), key=lambda n: -cont[n])[:6]
    vezes = {}
    for i, (t0, t1, w) in enumerate(pal):
        lw = _limpa(w)
        if lw in nomes and vezes.get(lw, 0) < 4:  # até 4 chances: se a 1ª cair em cima de outro cartão, vai na próxima
            vezes[lw] = vezes.get(lw, 0) + 1
            selo = "PROTAGONISTA" if lw == nomes[0] else ("PERSONAGEM" if nomes.index(lw) > 2 else "IMPORTANTE")
            cands.append((t0, 9 - nomes.index(lw), "personagem", {"nome": lw.upper(), "selo": selo}))
    try:  # comentário pessoal do narrador (abertura fixa do roteiro) — sempre ganha o balão
        from climas_voz import ABRE_COMENTARIO
        for i, (t0, t1, w) in enumerate(pal):
            if not inicio[i]:
                continue
            ini = " ".join(p[2] for p in pal[i:i + 4])
            m = ABRE_COMENTARIO.match(ini)
            if m:
                j = i
                while j + 1 < len(pal) and not _FIM_FRASE.search(pal[j][2]) and j - i < 40:
                    j += 1
                cands.append((t0, 10, "comentario", {"abertura": m.group(1), "fim": pal[j][1]}))
    except Exception:  # noqa: BLE001
        pass
    lug_vistos = set()
    sist = any(_limpa(p[2]).lower() == "sistema" for p in pal)
    for i, (t0, t1, w) in enumerate(pal):
        lw = _limpa(w)
        if _RE_LUGAR.match(lw) and lw.lower() not in lug_vistos and len(lug_vistos) < 4:
            txt = [lw]
            if i + 2 < len(pal) and _limpa(pal[i + 1][2]).lower() in ("de", "do", "da", "dos", "das") and \
                    _RE_NOME.match(_limpa(pal[i + 2][2])):
                txt += [_limpa(pal[i + 1][2]), _limpa(pal[i + 2][2])]
            elif i + 1 < len(pal) and _RE_NOME.match(_limpa(pal[i + 1][2])) and _limpa(pal[i + 1][2]) not in _PARADA:
                txt.append(_limpa(pal[i + 1][2]))
            lug_vistos.add(lw.lower())
            cands.append((t0, 6, "lugar", {"texto": " ".join(txt).upper()}))
        elif _RE_SISTEMA.match(lw):
            tr = _trecho(pal, i, 4)
            if len(tr) >= 2:
                cands.append((t0, 5, "sistema", {"cabeca": "SISTEMA" if sist else "STATUS", "linha": " ".join(tr).upper()}))
        elif _RE_CHAT.match(lw):
            fala = []
            for j in range(i + 1, min(len(pal), i + 13)):
                fala.append((pal[j][0], _limpa(pal[j][2])))
                if _FIM_FRASE.search(pal[j][2]):
                    break
            fala = [(t, x) for t, x in fala if x]
            if len(fala) >= 3:
                baloes = []
                for k in range(0, len(fala), 4):
                    grupo = fala[k:k + 4]
                    baloes.append((grupo[0][0], " ".join(x for _t, x in grupo)))
                cands.append((t0, 4, "chat", {"baloes": baloes[:3]}))
        elif _RE_ALERTA.match(lw):
            cands.append((t0, 3, "alerta", {"palavra": lw.upper()}))
        elif _RE_VIRA.match(lw):
            antes = [x for x in (_limpa(p[2]) for p in pal[max(0, i - 3):i]) if x]
            agora = _trecho(pal, i + 1, 3)
            if antes and agora and i + 1 < len(pal):
                cands.append((t0, 5, "antes_agora", {"antes": " ".join(antes).upper(), "agora": " ".join(agora).upper(),
                                                     "t_agora": pal[i + 1][0]}))
        elif _RE_LIKE.match(lw):
            cands.append((t0, 8, "like", {}))
        elif _RE_TRIUNFO.match(lw):
            cands.append((t0, 6, "triunfo", {"palavra": lw.upper()}))
        elif _RE_GPS.match(lw):
            cands.append((t0, 4, "gps", {"palavra": lw.upper()}))
        elif _RE_SETA.match(lw):  # aprendizado 64e54485
            cands.append((t0, 4, "seta", {"palavra": "OLHA ISSO" if lw.lower() == "olha" else lw.upper()}))
    return cands


DUR = {"personagem": 3.6, "lugar": 3.2, "sistema": 3.8, "alerta": 2.8, "antes_agora": 4.2, "like": 3.6,
       "triunfo": 3.0, "gps": 3.6, "obra_fixado": 3.2, "seta": 2.4}


def gerar(pal, vw, vh, cor=OURO, dur_video=None):
    """-> (estilos, linhas, marcas). marcas = [(t0, tipo, rótulo)] pro relatório da prévia."""
    if os.environ.get("ANIME_CARTOES", "1") == "0" or not pal:
        return [], [], []
    try:
        gap = float(os.environ.get("ANIME_CARTOES_GAP_S", "9"))
    except ValueError:
        gap = 9.0
    retrato = vh > vw
    u = min(vw, vh) / 720.0 * (1.3 if retrato else 1.55)  # 01/11: no 1º teste os cartões saíram miúdos
    cands = candidatos(pal)
    fim_video = dur_video or (pal[-1][1] + 1)
    # L-10: só no longo deitado (> 8 min): 1 vez aos ~5 min, no começo da 1ª frase depois dos 300 s
    if not retrato and fim_video > 480 and os.environ.get("ANIME_CARTAO_OBRA", "1") != "0":
        inicio = [True] + [bool(_FIM_FRASE.search(p[2])) for p in pal[:-1]]
        t5 = next((p[0] for k, p in enumerate(pal) if p[0] >= 300 and inicio[k]), None)
        if t5:
            cands.append((t5, 11, "obra_fixado", {}))
    cands = sorted(cands, key=lambda c: (c[0], -c[1]))
    escolhidos, livre = [], 2.5
    usados = {}
    LIMITE = {"like": 3, "sistema": 8, "alerta": 8, "chat": 8, "antes_agora": 5}
    fim_ult = 0.0
    for t, pr, tipo, dados in cands:
        if tipo == "like" and usados.get("like", 0) < LIMITE["like"]:
            # 01/11 dona: o CTA sempre aparece (a mascote entra junto) — tira o cartão comum que estiver em cima
            while escolhidos and escolhidos[-1][0] + escolhidos[-1][1] > t and escolhidos[-1][2] not in ("comentario", "like"):
                escolhidos.pop()
            if escolhidos and escolhidos[-1][0] + escolhidos[-1][1] > t:
                continue
            escolhidos.append((t, DUR["like"], tipo, dados))
            usados["like"] = usados.get("like", 0) + 1
            fim_ult, livre = t + DUR["like"], t + DUR["like"] + gap
            continue
        if tipo == "obra_fixado":  # L-10: sempre sai — tira o cartão comum que estiver em cima
            while escolhidos and escolhidos[-1][0] + escolhidos[-1][1] > t and escolhidos[-1][2] not in ("comentario",
                                                                                                         "like"):
                escolhidos.pop()
            if escolhidos and escolhidos[-1][0] + escolhidos[-1][1] > t:
                t = escolhidos[-1][0] + escolhidos[-1][1] + 0.3
            escolhidos.append((t, DUR[tipo], tipo, dados))
            fim_ult, livre = t + DUR[tipo], t + DUR[tipo] + gap
            continue
        if tipo == "comentario":  # não espera o intervalo: só não pode cair em cima de outro cartão
            if t < fim_ult:
                continue
            dur = min(7.0, max(2.5, dados["fim"] - t + 0.4))
            escolhidos.append((t, dur, tipo, dados))
            fim_ult = t + dur
            livre = max(livre, t + dur + 2.0)
            continue
        if t < livre or usados.get(tipo, 0) >= LIMITE.get(tipo, 99):
            continue
        if tipo == "personagem":
            if dados["nome"] in usados:
                continue
            usados[dados["nome"]] = 1
        if tipo == "chat":
            dur = min(7.0, dados["baloes"][-1][0] - t + 2.0)
        else:
            dur = DUR[tipo]
        if t + dur > fim_video - 0.5:
            continue
        if any(t < te + de and t + dur > te for te, de, tp, _d in escolhidos if tp == "comentario"):
            continue  # caiu durante um comentário
        escolhidos.append((t, dur, tipo, dados))
        usados[tipo] = usados.get(tipo, 0) + 1
        livre = t + dur + gap
        fim_ult = max(fim_ult, t + dur)
    linhas, marcas = [], []
    for n, (t, dur, tipo, d) in enumerate(escolhidos):
        if tipo == "personagem":
            c = c_personagem(d["nome"], d["selo"], cor, u)
        elif tipo == "lugar":
            c = c_lugar(d["texto"], u)
        elif tipo == "sistema":
            c = c_sistema(d["cabeca"], d["linha"], u)
        elif tipo == "chat":
            c = c_chat(d["baloes"], u, t)
        elif tipo == "alerta":
            c = c_alerta(d["palavra"], u)
        elif tipo == "antes_agora":
            c = c_antes_agora(d["antes"], d["agora"], u, max(0.8, d["t_agora"] - t))
        elif tipo == "comentario":
            c = c_comentario(d["abertura"], u)
        elif tipo == "triunfo":
            c = c_triunfo(d["palavra"], u)
        elif tipo == "gps":
            c = c_gps(d["palavra"], u, _seed(d["palavra"] + str(int(t))))
        elif tipo == "obra_fixado":
            c = c_obra_fixado(u)
        elif tipo == "seta":
            c = c_seta(d["palavra"], u, n)
        else:
            c = c_like(u)
        # cartão maior que a tela (texto comprido) encolhe junto
        lim_w = vw * (0.92 if retrato else 0.50)
        if c.w > lim_w:
            k = lim_w / c.w
            c = _encolher(c, k)
        X, Y, entra, sai, deriva, giro = _lugar(n, c, vw, vh, retrato, tipo)
        linhas += c.eventos(t, t + dur, X, Y, entra, sai, deriva, giro)
        marcas.append((t, tipo, c.rotulo))
    estilos = ["Style: Cart,Montserrat Black,30,&H00FFFFFF,&H00FFFFFF,&H00101010,&H64000000,0,0,0,0,100,100,0,0,1,0,0,"
               "7,0,0,0,1"]
    return estilos, linhas, marcas


def _encolher(c, k):
    """escala o cartão inteiro (posições + fonte/desenho via fscx/fscy no cartão todo não dá por elemento: refaz
    escalando posições e as tags de tamanho)"""
    novo = Cartao(c.tipo, c.rotulo, c.w * k, c.h * k)
    for el in c.els:
        tags = re.sub(r"\\fs(\d+)", lambda m: "\\fs%d" % max(8, int(int(m.group(1)) * k)), el["tags"])
        icon = re.search(r"\\fscx\d+\\fscy\d+", tags)
        tags = re.sub(r"\\fscx(\d+)\\fscy(\d+)", lambda m: "\\fscx%d\\fscy%d" % (int(int(m.group(1)) * k),
                                                                               int(int(m.group(2)) * k)), tags, count=1)
        txt = el["txt"]
        if txt.startswith("{\\p1}") and not icon:  # caixa/barra: escala os números do próprio desenho
            txt = "{\\p1}" + re.sub(r"-?\d+(\.\d+)?", lambda m: str(int(float(m.group(0)) * k)), txt[5:])
        e2 = dict(el)
        e2.update(x=el["x"] * k, y=el["y"] * k, tags=tags, txt=txt, mv=(el["mv"][0] * k, el["mv"][1] * k) if el["mv"] else None)
        novo.els.append(e2)
    return novo


def _lugar(n, c, vw, vh, retrato, tipo):
    """posição + trajetória: cada cartão vem de um lado diferente, flutua pro centro e sai por outro lado"""
    m = 0.03
    if retrato:
        X = (vw - c.w) / 2
        ys = (0.12, 0.30, 0.20)
        Y = vh * ys[n % len(ys)]
        vias = (((-vw, 0), (vw, -40)), ((vw, 0), (-vw, 0)), ((0, -vh * 0.4), (0, -vh * 0.4)), ((-vw, 60), (0, vh)))
        entra, sai = vias[n % len(vias)]
        return X, Y, entra, sai, (0, 18), (-8, 6, -5, 9)[n % 4]
    if tipo == "comentario":  # embaixo à esquerda, logo acima da legenda; sobe, balança e desce
        X, Y = vw * m, vh * 0.62 - c.h
        return X, Y, (0, vh * 0.45), (0, vh * 0.45), (vw * 0.01, -vh * 0.015), -4
    if tipo == "like":
        X, Y = vw * (1 - m) - c.w, vh * 0.42
        return X, Y, (vw * 0.4, vh * 0.25), (vw * 0.4, 0), (-vw * 0.02, -vh * 0.02), 8
    lados = [
        (vw * m, vh * 0.06, (-vw * 0.5, 0), (-vw * 0.5, -vh * 0.1), (vw * 0.025, vh * 0.012), -7),
        (vw * (1 - m) - c.w, vh * 0.06, (vw * 0.5, 0), (vw * 0.5, -vh * 0.1), (-vw * 0.025, vh * 0.012), 7),
        (vw * m, vh * 0.30, (-vw * 0.3, vh * 0.4), (0, -vh * 0.6), (vw * 0.03, -vh * 0.02), -10),
        (vw * (1 - m) - c.w, vh * 0.30, (vw * 0.3, -vh * 0.4), (vw * 0.5, vh * 0.1), (-vw * 0.03, vh * 0.015), 10),
    ]
    X, Y, entra, sai, deriva, giro = lados[n % len(lados)]
    Y = min(Y, vh * 0.74 - c.h)  # nunca na faixa da legenda de baixo
    return X, max(vh * 0.02, Y), entra, sai, deriva, giro
