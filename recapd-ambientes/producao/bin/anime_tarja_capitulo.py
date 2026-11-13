"""anime_tarja_capitulo.py — TARJA de capítulo do recap LONGO por cima da legenda queimada da fonte.

Dona 25/10/2026: "o borrão só deve ir quando há legenda ... como é dos Cortes, que põe uma tarja fixa com um título em
cima, a legenda em outro lugar; no caso, como é um vídeo longo, a tarja deve ir mudando numa taxa ideal, da melhor
maneira possível, como se fosse a apresentação de um capítulo".

Só existe quando a fonte TEM legenda (anime_legenda_fonte): placa BRANCA arredondada (a tarja dos Cortes,
parceiro_marca._tarja) cobrindo a faixa da legenda deles; dentro, o selo "CAPÍTULO N" e o título do capítulo em preto.
A cada capítulo (os mesmos do capitulos.json da descrição) a placa pisca amarelo e pulsa, o selo entra estalando e o
título sobe; a placa nunca encolhe nem some (a legenda deles nunca aparece). A nossa legenda vai logo acima da placa.
Tudo entra no ASS da legenda (fx_subtitles.burn_subtitles_ass): nenhuma passada de render a mais.

  placa(rect_env)            -> (y0, y1) em fração da altura do vídeo FINAL
  centro_legenda(placa)      -> SUB_Y_CENTER da nossa legenda (None = lugar de sempre)
  extras(capitulos, placa)   -> fn(vw, vh, dur) -> (estilos, eventos)
"""
import logging
import os
from pathlib import Path

CROP = 0.90       # fx_clips: o descaracterizador corta 5% em cima e 5% embaixo antes de escalar
FOLGA = 0.012     # placa um pouco maior que a faixa borrada
ALT_MIN = 0.12    # altura mínima da placa (fração da altura): selo + título legíveis
LARG = 0.88       # largura da placa (fração da largura); o borrão por baixo vai de ponta a ponta
AMARELO = "&H3CD6FF&"
PRETO = "&H0A0A0A&"
_FONTES = [Path(__file__).resolve().parent.parent / "workspace" / "assets" / "fonts" / "impact.ttf",
           Path(r"C:\Windows\Fonts\impact.ttf")]


def placa(rect_env):
    """'y,h' da faixa da legenda deles (fração da altura da FONTE, ANIME_HARDSUB_RECT) -> (y0, y1) no vídeo final."""
    ry, rh = (float(x) for x in str(rect_env).split(",")[:2])
    y0 = (ry - (1 - CROP) / 2) / CROP - FOLGA
    y1 = (ry + rh - (1 - CROP) / 2) / CROP + FOLGA
    if y1 - y0 < ALT_MIN:
        c = (y0 + y1) / 2
        y0, y1 = c - ALT_MIN / 2, c + ALT_MIN / 2
    if y1 > 0.994:   # o pé fica livre pra barra de progresso
        y0, y1 = y0 - (y1 - 0.994), 0.994
    if y0 < 0.01:
        y0, y1 = 0.01, y1 + (0.01 - y0)
    return round(y0, 4), round(min(y1, 0.994), 4)


def centro_legenda(p):
    """Placa na metade de baixo: a nossa legenda logo acima dela. Placa em cima: legenda no lugar de sempre."""
    y0, y1 = p
    return round(y0 - 0.068, 4) if (y0 + y1) / 2 >= 0.5 else None


def _medidor():
    """fn(texto, tamanho_ass) -> largura em px no libass (o tamanho do ASS é a altura ascendente+descendente)."""
    try:
        from PIL import ImageFont
        arq = next(str(f) for f in _FONTES if f.exists())
        asc, desc = ImageFont.truetype(arq, 100).getmetrics()
        fator = 100.0 / (asc + desc)
        cache = {}

        def medir(txt, tam):
            em = max(4, int(round(tam * fator)))
            if em not in cache:
                cache[em] = ImageFont.truetype(arq, em)
            return cache[em].getlength(txt)
        return medir
    except Exception:  # noqa: BLE001 — sem a fonte: estimativa (Impact ~0,46 da altura por letra maiúscula)
        return lambda txt, tam: 0.46 * tam * len(txt)


def _ts(t):
    t = max(0.0, t)
    cs = int(round(t * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def _esc(t):
    return (t or "").replace("\\", "/").replace("{", "(").replace("}", ")").replace("\n", " ")


def _ret(w, h, r):
    """Retângulo arredondado (desenho ASS, origem no canto de cima à esquerda)."""
    k = round(r * 0.4477)   # curva de Bézier ~ quarto de círculo
    return (f"m {r} 0 l {w - r} 0 b {w - k} 0 {w} {k} {w} {r} l {w} {h - r} b {w} {h - k} {w - k} {h} {w - r} {h} "
            f"l {r} {h} b {k} {h} 0 {h - k} 0 {h - r} l 0 {r} b 0 {k} {k} 0 {r} 0")


def extras(capitulos, p, rotulo="CAPÍTULO"):
    """capitulos = [[segundo_no_vídeo_final, título], ...] (o 1º em 0); p = placa(...)."""
    caps = [(float(s), str(t).strip()) for s, t in capitulos if str(t).strip()]

    def fn(vw, vh, dur):
        try:
            return _eventos(caps, p, rotulo, vw, vh, dur)
        except Exception as e:  # noqa: BLE001 — o fx_subtitles engole erro de extra calado: avisa aqui
            logging.warning(f"[tarja] eventos não montados ({type(e).__name__}: {e}) — sem tarja")
            return [], []
    return fn


def _eventos(caps, p, rotulo, vw, vh, dur):
    y0, y1 = int(round(p[0] * vh)), int(round(p[1] * vh))
    hp = y1 - y0
    wp = int(round(vw * LARG)) // 2 * 2
    x0 = (vw - wp) // 2
    cx, cy = vw // 2, (y0 + y1) // 2
    fonte = os.environ.get("ANIME_SUB_FONT_ASS") or "Impact"
    medir = _medidor()
    f_rot = max(14, int(hp * 0.22))
    y_rot = y0 + int(hp * 0.27)
    y_tit = y0 + int(hp * 0.66)
    estilos = [
        "Style: TarjaPlaca,Arial,20,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1",
        f"Style: TarjaRot,{fonte},{f_rot},&H003CD6FF,&H003CD6FF,&H00000000,&H00000000,0,0,0,0,100,100,1,0,1,0,0,5,0,0,0,1",
        f"Style: TarjaTit,{fonte},{int(hp * 0.46)},&H000A0A0A,&H000A0A0A,&H00000000,&H00000000,"
        "0,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1",
    ]
    desenho_placa = _ret(wp, hp, max(4, int(hp * 0.18)))
    ev = []
    for k, (ini, titulo) in enumerate(caps):
        fim = caps[k + 1][0] if k + 1 < len(caps) else max(dur, ini + 1)
        if fim - ini < 1.0:
            continue
        s, e = _ts(ini), _ts(fim)
        # placa: pisca amarelo e pulsa (sempre >= 100%: nunca descobre a legenda deles); a 1ª entra direto
        anim = (f"\\c{AMARELO}\\fscx103\\fscy110\\t(60,420,\\c&HFFFFFF&\\fscx100\\fscy100)" if k else "\\c&HFFFFFF&")
        ev.append(f"Dialogue: 1,{s},{e},TarjaPlaca,,0,0,0,,{{\\an5\\pos({cx},{cy})\\p1\\bord2\\3c&H000000&\\shad0{anim}}}"
                  f"{desenho_placa}{{\\p0}}")
        # selo "CAPÍTULO N": pílula preta + texto amarelo, entram estalando
        txt_rot = f"{rotulo} {k + 1}"
        pw = int(medir(txt_rot, f_rot) + f_rot * 1.3)
        ph = int(f_rot * 1.35)
        pop = "\\fscx15\\fscy15\\t(40,200,\\fscx112\\fscy112)\\t(200,300,\\fscx100\\fscy100)"
        ev.append(f"Dialogue: 2,{s},{e},TarjaPlaca,,0,0,0,,{{\\an5\\pos({cx},{y_rot})\\p1\\bord0\\shad0\\c{PRETO}{pop}}}"
                  f"{_ret(pw, ph, ph // 2)}{{\\p0}}")
        ev.append(f"Dialogue: 3,{s},{e},TarjaRot,,0,0,0,,{{\\an5\\pos({cx},{y_rot}){pop}}}{_esc(txt_rot)}")
        # título: o maior que couber numa linha (até 46% da placa), sobe de dentro da placa
        tit = _esc(titulo.upper())
        f_tit = int(hp * 0.46)
        while f_tit > 14 and medir(tit, f_tit) > wp * 0.92:
            f_tit -= 1
        t_ini = ini + (0.15 if k else 0.0)
        desce = int(hp * 0.16)
        ev.append(f"Dialogue: 3,{_ts(t_ini)},{e},TarjaTit,,0,0,0,,{{\\an5\\fs{f_tit}\\clip({x0},{y0},{x0 + wp},{y1})"
                  f"\\move({cx},{y_tit + desce},{cx},{y_tit},0,260)\\fad(200,150)}}{tit}")
    logging.info(f"[tarja] {len(caps)} capítulos na tarja | placa {p[0]:.3f}-{p[1]:.3f} da altura ({hp}px)")
    return estilos, ev


def juntar(*fns):
    """Vários extra(vw, vh, dur) num só (gancho/barra + tarja)."""
    fns = [f for f in fns if f]

    def fn(vw, vh, dur):
        estilos, eventos = [], []
        for f in fns:
            a, b = f(vw, vh, dur)
            estilos += a
            eventos += b
        return estilos, eventos
    return fn if fns else None
