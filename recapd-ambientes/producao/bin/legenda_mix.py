"""01/11 dona: legenda cinética em MIX — o padrão aprovado pra TODOS os vídeos (projeto Veo/MS Energy:
D:\\ms-energy\\bin\\montagem_ms.py, exemplos em D:\\ms-energy\\testes_legendas\\solar_20261101_000310 e \\MIX).

Lá é PNG (Pillow); aqui é ASS (libass) na MESMA passada da legenda do longo, custo ~0. Cada palavra forte vira um
ADESIVO e as curtas ("de/a/com") sobem num adesivo menor em cima dela. Cada adesivo tem um DESENHO:
  degrade         preenchimento claro em cima -> cor embaixo (2 faixas com \\clip), contorno escuro e brilho da cor
  sombra          degradê + sombra projetada
  contorno_duplo  contorno escuro + contorno BRANCO por fora + brilho
  recorte         figurinha: borda branca grossa + contorno escuro fino + sombra
  caixa           palavra branca dentro de caixa colorida arredondada
nunca o mesmo desenho 2x seguidas; efeitos: sublinhado, pop de entrada (1,18/1,35/1,40), giro maior, rastro (a
palavra anterior fica a 35% enquanto a nova entra, só se não encostam). Dois modos sorteados por vídeo e medidos:
"inteligente" (palavra forte/emoção/nome -> recorte/caixa, cor quente, pop 1,40) e "livre" (tudo sorteado).
ANIME_LEGENDA_MIX=0 volta pra versão anterior; ANIME_LEGENDA_MIX_MODO=inteligente|livre força o modo."""
import hashlib
import os
import random
import re

ULTIMO_MODO = None  # o fx_subtitles grava nas marcas (placar compara views por modo)

FONTES = ("Luckiest Guy", "Bangers", "Impact", "Montserrat Black")
ESCALA = {"Bangers": 1.25, "Montserrat Black": 0.85, "Luckiest Guy": 0.95}
_ARQ = {"Luckiest Guy": "LuckiestGuy-Regular.ttf", "Bangers": "Bangers-Regular.ttf", "Impact": "impact.ttf",
        "Montserrat Black": "Montserrat-Black.ttf"}
_PASTA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "workspace", "assets", "fonts")
CORES = [(60, 200, 255), (255, 214, 10), (255, 80, 170), (255, 70, 50), (70, 120, 255), (60, 230, 120),
         (255, 150, 30), (255, 255, 255)]
QUENTES = [(255, 214, 10), (255, 70, 50), (255, 80, 170), (255, 150, 30)]
CONTORNO = (14, 18, 40)
CURTAS = {"a", "o", "e", "é", "de", "do", "da", "dos", "das", "em", "no", "na", "nos", "nas", "um", "uma", "que",
          "com", "pra", "para", "por", "se", "seu", "sua", "te", "eu", "ao", "à", "os", "as", "ou", "mas", "não",
          "já", "tem", "vai", "só", "isso", "essa", "esse", "ela", "ele", "me", "mais", "muito", "quem", "como",
          "lhe", "foi", "era", "seus", "suas", "nem", "até", "num", "numa"}
# longo: emoção/ação (o resto do "forte" vem do _PESADAS do fx_subtitles e dos nomes com maiúscula)
EMOCAO = re.compile(r"^(amor|am(ou|ava)|paix[ãa]o|beij\w*|chor\w*|l[áa]grima\w*|medo|raiva|[óo]dio|ci[úu]me\w*|"
                    r"humilh\w*|vergonha|traiu|trai[çc][ãa]o|vingan[çc]a|morte|morreu|matou|sangue|grit\w*|"
                    r"desesper\w*|sozinh\w*|abandon\w*|segredo|verdade|mentira|nunca|jamais|tudo|nada|poder\w*|"
                    r"bruxa\w*|prisioneir\w*|escrav\w*|rei|rainha|deus\w*|dem[ôo]ni\w*|monstro\w*|lend[áa]ri\w*|"
                    r"despert\w*|explod\w*|destru\w*|venceu|derrotou|esmag\w*|fur(ia|ioso|iosa)|chocad\w*|"
                    r"incr[íi]vel|imposs[íi]vel|absurd\w*|insan\w*)$", re.I)
_LUG_DEITADO = [(0.50, 0.30), (0.28, 0.26), (0.72, 0.30), (0.30, 0.56), (0.70, 0.58), (0.50, 0.46), (0.24, 0.42),
                (0.76, 0.44)]
# 01/11: no vertical os cartões animados ficam na metade de cima — a legenda MIX vive da metade pra baixo
_LUG_RETRATO = [(0.50, 0.58), (0.36, 0.52), (0.64, 0.62), (0.50, 0.68), (0.40, 0.48), (0.62, 0.55)]
GIROS = (-7, 5, -3, 8, -5, 3, -8, 6)
_CACHE = {}


def _ts(t):
    t = max(0.0, t)
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


def _bgr(c, a=None):
    return "&H%s%02X%02X%02X&" % ("" if a is None else "%02X" % a, c[2], c[1], c[0])


def _clarear(c, k=0.55):
    return tuple(int(v + (255 - v) * k) for v in c)


def _larg(txt, fonte, tam):
    """largura real do texto (Pillow com a mesma fonte do libass); sem Pillow = estimativa"""
    try:
        from PIL import ImageFont
        ch = (fonte, tam)
        if ch not in _CACHE:
            _CACHE[ch] = ImageFont.truetype(os.path.join(_PASTA, _ARQ[fonte]), tam)
        return _CACHE[ch].getlength(txt)
    except Exception:  # noqa: BLE001
        return len(txt) * tam * 0.58


def _rr(w, h, r):
    w, h, r = int(w), int(h), int(max(1, min(r, w / 2, h / 2)))
    return (f"m {r} 0 l {w - r} 0 b {w} 0 {w} 0 {w} {r} l {w} {h - r} b {w} {h} {w} {h} {w - r} {h} "
            f"l {r} {h} b 0 {h} 0 {h} 0 {h - r} l 0 {r} b 0 0 0 0 {r} 0")


def _limpa(w):
    return re.sub(r"^[^\wÀ-ÿ]+|[^\wÀ-ÿ!?%]+$", "", w)


def peso(w, pesada=None):
    lw = _limpa(w)
    if (pesada and pesada(lw)) or EMOCAO.match(lw) or w.rstrip().endswith(("!", "?")) or \
            (lw[:1].isupper() and len(lw) >= 3 and lw.lower() not in CURTAS):
        return 3
    return 2 if len(lw) >= 7 else 1


def blocos(alinhadas):
    """[(curtas_em_cima, forte, ini, fim)] — curtas se juntam à próxima forte; cada bloco fica até o próximo."""
    bl, pre = [], []
    for w, s, e in alinhadas:
        if _limpa(w).lower() in CURTAS and len(pre) < 3:
            pre.append((w, s, e))
            continue
        bl.append(([x[0] for x in pre], w, pre[0][1] if pre else s, e))
        pre = []
    if pre:
        bl.append(([x[0] for x in pre[:-1]], pre[-1][0], pre[0][1], pre[-1][2]))
    res = []
    for i, (cima, forte, s, e) in enumerate(bl):
        prox = bl[i + 1][2] if i + 1 < len(bl) else e + 0.5
        res.append((cima, forte, s, max(min(prox, e + 0.5), s + 0.3)))
    return res


def escolher_modo(semente):
    forc = os.environ.get("ANIME_LEGENDA_MIX_MODO", "").strip().lower()
    if forc in ("inteligente", "livre"):
        return forc
    return random.Random("modo" + str(semente)).choice(["inteligente", "livre"])


def plano(bl, semente, modo, pesada=None):
    rng = random.Random(str(semente))
    nomes = ["degrade", "sombra", "contorno_duplo", "recorte", "caixa"]
    out, ant = [], None
    for i, (cima, forte, s, e) in enumerate(bl):
        p = peso(forte, pesada)
        if modo == "livre":
            ops, cor = nomes, rng.choice(CORES)
            pop_k, giro_k = rng.choice((1.18, 1.35, 1.40)), rng.choice((1.0, 1.0, 1.7))
            sub, rastro = rng.random() < 0.25, rng.random() < 0.35
        else:
            ops = {3: ["recorte", "caixa", "contorno_duplo"], 2: ["recorte", "contorno_duplo", "sombra", "degrade"],
                   1: ["degrade", "sombra", "recorte"]}[p]
            cor = rng.choice(QUENTES) if p == 3 else CORES[(i * 3) % len(CORES)]
            pop_k = {3: 1.40, 2: 1.35, 1: 1.18}[p]
            giro_k = 1.7 if p == 3 and rng.random() < 0.5 else 1.0
            sub = p >= 2 and rng.random() < (0.5 if p == 3 else 0.25)
            rastro = i > 0 and s - bl[i - 1][3] < 0.25 and not (out and out[-1]["rastro"]) and rng.random() < 0.5
        des = rng.choice([d for d in ops if d != ant] or ops)
        if des == "caixa":
            sub = False
        cima_des = "caixa" if des != "caixa" and rng.random() < 0.35 else ("recorte" if des == "caixa" else des)
        out.append({"desenho": des, "cima_desenho": cima_des, "cor": cor, "pop_k": pop_k, "giro_k": giro_k,
                    "sublinhado": sub, "rastro": bool(rastro) and i > 0, "peso": p})
        ant = des
    return out


# V-18 (04/11, pesquisa iart-ai/motion-skills — só a IDEIA, nada instalado; dona: "implantar nos curtos"): entradas de
# palavra novas na MIX, além do pop. Só tags do libass (\move, \t, \fsc, \fry, \blur, \alpha): custo ~0 na mesma
# passada. Por palavra; nunca a mesma 2x seguidas. ANIME_LEGENDA_ENTRADAS=0 = só o pop (como antes).
ENTRADAS = ("pop", "queda", "deslize", "estica", "desfoque", "giro3d")
_ENTRADA_PARADA = ("pop", "estica", "desfoque", "giro3d")  # não mudam o lugar: servem pra caixa/sublinhado


def _entrada_tags(entrada, x, y, tam, pop_k, estica_k=165):
    """(posição, tags de entrada) — a posição vira \\move nas entradas que andam."""
    pos = "\\pos(%d,%d)" % (x, y)
    if entrada == "queda":
        return "\\move(%d,%d,%d,%d,0,140)" % (x, y - int(tam * 0.7), x, y), "\\alpha&HFF&\\t(0,70,\\alpha&H00&)"
    if entrada == "deslize":
        dx = int(tam * 1.1) * (1 if (x // 7) % 2 else -1)
        return "\\move(%d,%d,%d,%d,0,130)" % (x + dx, y, x, y), "\\alpha&HFF&\\t(0,60,\\alpha&H00&)"
    if entrada == "estica":
        return pos, "\\fscx%d\\fscy60\\t(0,90,\\fscx90\\fscy115)\\t(90,170,\\fscx100\\fscy100)" % estica_k
    if entrada == "desfoque":
        return pos, "\\blur10\\alpha&H70&\\fscx112\\fscy112\\t(0,160,\\blur0\\alpha&H00&\\fscx100\\fscy100)"
    if entrada == "giro3d":  # 85° a perspectiva do libass AUMENTAVA a palavra e cortava na borda (teste 04/11): 55° + 80%
        return pos, "\\fry55\\fscx80\\fscy80\\t(0,170,\\fry0\\fscx100\\fscy100)"
    pop = "\\fscx%d\\fscy%d\\t(0,130,\\fscx100\\fscy100)" % (pop_k * 100, pop_k * 100) if pop_k > 1 else ""
    return pos, pop


_VW = [1080]  # largura do vídeo (gerar() acerta)


def _adesivo(txt, fonte, tam, cor, des, x, y, giro, t0, t1, pop_k, extra, camada=10, sublinhado=False, entrada="pop"):
    """linhas ASS de um adesivo centrado em (x, y). extra = tags de tempo (entrada/saída/alpha) comuns."""
    L = []
    # 04/11 17:25 (Short sem-obra-d6952d: caixa "ESCURO,E" cortada na borda ESQUERDA; 15:20 "PACIENTE" na direita):
    # a palavra (com caixa/contorno, ~12% a mais) nunca passa da tela — o centro anda pra dentro o que faltar.
    meia = _larg(txt, fonte, tam) * 0.56 + tam * 0.25
    x = int(min(max(x, meia + 24), _VW[0] - meia - 24)) if meia * 2 + 48 < _VW[0] else _VW[0] // 2
    if des == "caixa" or sublinhado:  # a caixa/sublinhado são desenhos à parte: entrada que anda separaria os dois
        entrada = entrada if entrada in _ENTRADA_PARADA else "pop"
    # 04/11 15:20 (Short bleach_cap1: "PACIENTE" estourou a borda direita): o "estica" abre a 165% de largura; em palavra
    # comprida passa da tela. Limita ao que cabe (x = centro ~ metade da tela); não cabe nem 110% = "pop".
    estica_k = 165
    if entrada == "estica":
        estica_k = int(min(165, 100 * 2 * x * 0.94 / max(1.0, _larg(txt, fonte, tam))))
        if estica_k < 110:
            entrada = "pop"
    lugar, pop = _entrada_tags(entrada, x, y, tam, pop_k, estica_k)  # V-18
    pos = "\\an5%s\\frz%.1f\\fn%s\\fs%d" % (lugar, giro, fonte, tam)
    s = max(3, tam // 9)
    a, b = _ts(t0), _ts(t1)
    w = _larg(txt, fonte, tam)

    def ev(ly, tags, texto=txt):
        L.append("Dialogue: %d,%s,%s,Cria,,0,0,0,,{%s%s%s%s}%s" % (camada + ly, a, b, pos, pop, tags, extra, texto))

    leve = os.environ.get("ANIME_LEGENDA_LEVE") == "1"  # 04/11: variante de TESTE (dona compara antes de decidir)

    def preench(cor_):
        if leve:  # 1 camada de cor (sem as 2 faixas com \clip do degradê)
            ev(5, "\\1c%s\\bord0\\shad0" % _bgr(cor_))
            return
        # degradê: faixa de cima mais clara (clip na tela, cobre o pop inteiro)
        meio = int(y - tam * 0.08)
        ev(5, "\\1c%s\\bord0\\shad0\\clip(0,%d,99999,99999)" % (_bgr(cor_), meio))
        ev(6, "\\1c%s\\bord0\\shad0\\clip(0,0,99999,%d)" % (_bgr(_clarear(cor_)), meio))

    if des == "caixa":
        if cor == (255, 255, 255):
            cor = (255, 70, 50)
        bw, bh = w + tam * 0.55, tam * 1.05
        L.append("Dialogue: %d,%s,%s,Cria,,0,0,0,,{\\an5\\pos(%d,%d)\\frz%.1f%s\\1c%s\\bord%d\\3c%s\\shad%d\\4a&H60&"
                 "%s}{\\p1}%s" % (camada + 1, a, b, x, y + tam * 0.04, giro, pop, _bgr(cor), max(3, tam // 22),
                                  _bgr(CONTORNO), max(4, tam // 14), extra, _rr(bw, bh, tam * 0.28)))
        ev(4, "\\1c&HFFFFFF&\\bord%d\\3c%s\\shad0" % (max(2, tam // 16), _bgr(CONTORNO)))
        return L
    if des in ("degrade", "sombra", "contorno_duplo") and not leve:  # brilho da cor (\blur: o mais caro no libass)
        ev(1, "\\1a&HFF&\\bord%d\\3c%s\\3a&H50&\\blur%d\\shad0" % (s * 2, _bgr(cor), s * 2))
    if des == "contorno_duplo":
        ev(2, "\\1a&HFF&\\bord%d\\3c&HFFFFFF&\\shad0" % (s + max(3, s // 2) + s // 2))
    if des == "recorte":
        b_ = max(8, tam // 6)
        ev(2, "\\1c&HFFFFFF&\\bord%d\\3c&HFFFFFF&\\shad%d\\4c&H000000&\\4a&H60&" % (b_ + s // 2, max(4, tam // 14)))
        s = max(3, tam // 14)
    sombra = "\\shad%d\\4a&H60&" % max(4, tam // 12) if des == "sombra" else "\\shad0"
    ev(3, "\\1c%s\\bord%d\\3c%s%s" % (_bgr(CONTORNO), s, _bgr(CONTORNO), sombra))
    preench(cor)
    if sublinhado:
        L.append("Dialogue: %d,%s,%s,Cria,,0,0,0,,{\\an5\\pos(%d,%d)\\frz%.1f\\1c%s\\bord%d\\3c%s\\shad0"
                 "\\fscx0\\t(0,220,\\fscx100)%s}{\\p1}%s" % (camada + 7, a, b, x, y + tam * 0.52, giro, _bgr(cor),
                                                            max(2, tam // 30), _bgr(CONTORNO), extra,
                                                            _rr(w * 0.9, max(6, tam * 0.1), tam * 0.05)))
    return L


def gerar(cartoes, vw, vh, cor_cena=None, eh_abertura=True, pesada=None, elementos=None, decoracao=None):
    """cartoes = [[(t0, palavra), ..., fim], ...] (mesmo formato do anime_gancho.legenda_criativa)."""
    _VW[0] = int(vw or 1080)
    global ULTIMO_MODO
    retrato = vh > vw
    base = int((0.10 if retrato else 0.15) * vh)
    alinhadas = []
    for cart in cartoes:
        ps, fim = list(cart[:-1]), float(cart[-1])
        for j, (t0, w) in enumerate(ps):
            e = float(ps[j + 1][0]) if j + 1 < len(ps) else fim
            alinhadas.append((w, float(t0), e))
    if not alinhadas:
        return [], []
    semente = int(hashlib.md5(" ".join(w for w, _s, _e in alinhadas[:12]).encode("utf-8")).hexdigest()[:8], 16)
    modo = escolher_modo(semente)
    ULTIMO_MODO = modo
    bl = blocos(alinhadas)
    pl = plano(bl, semente, modo, pesada)
    lugares = _LUG_RETRATO if retrato else _LUG_DEITADO
    estilos = ["Style: Cria,Impact,%d,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,1,0,1,0,0,5,"
               "20,20,0,1" % base]
    elems = list(elementos or {})
    linhas, ant = [], None
    ant_ent = None  # V-18: entrada da palavra anterior (nunca 2x seguidas)
    for n, ((cima, forte, s, e), est) in enumerate(zip(bl, pl)):
        txt = _limpa(forte).upper() or forte.upper()
        fonte = FONTES[(n + semente) % len(FONTES)]
        tam = int(base * {1: 0.80, 2: 0.95, 3: 1.18}[est["peso"]] * ESCALA.get(fonte, 1.0))
        lmax = vw * (0.80 if est["desenho"] in ("degrade", "sombra") else 0.72)
        while _larg(txt, fonte, tam) > lmax and tam > 30:
            tam -= 4
        w = _larg(txt, fonte, tam)
        giro = GIROS[n % len(GIROS)] * est["giro_k"]
        fx, fy = lugares[(n + semente) % len(lugares)]
        x = int(min(max(fx * vw, w / 2 + vw * 0.04), vw - w / 2 - vw * 0.04))
        y = int(min(max(fy * vh, tam * 1.3), vh * 0.70))
        caixa = (x - w / 2, y - tam * 0.6, x + w / 2, y + tam * 0.6)
        if cima:
            caixa = (caixa[0], caixa[1] - tam * 0.7, caixa[2], caixa[3])
        d = int((e - s) * 1000)
        # entrada: elemento (choque/fogo/água) na abertura, senão pop; saída rápida
        entra, sai_x = "", "\\t(%d,%d,\\alpha&HFF&)" % (max(0, d - 90), d)
        if eh_abertura and elems and n % 2 == 0:
            _b, ent, sm = elementos[elems[n % len(elems)]]
            entra = ent
            sai_x = sm.format(d=d, d1=max(0, d - 180), d2=max(0, d - 140), d3=max(0, d - 100))
        # V-18: entrada da palavra — "inteligente" casa com o peso (forte: estica/pop; médio: queda/giro3d; leve:
        # deslize/desfoque); "livre" sorteia; nunca igual à anterior; elemento da abertura (choque/fogo) manda
        if os.environ.get("ANIME_LEGENDA_ENTRADAS", "1") == "0" or entra:
            ent_pal = "pop"
        else:
            r_ent = random.Random(semente * 7919 + n)
            opc = {3: ("estica", "pop"), 2: ("queda", "giro3d", "pop"), 1: ("deslize", "desfoque", "queda")}[
                est["peso"]] if modo == "inteligente" else ENTRADAS
            opc = [o for o in opc if o != ant_ent] or list(opc)
            ent_pal = r_ent.choice(opc)
        ant_ent = ent_pal
        linhas += _adesivo(txt, fonte, tam, est["cor"], est["desenho"], x, y, giro, s, e, est["pop_k"],
                           entra + sai_x, camada=10, sublinhado=est["sublinhado"], entrada=ent_pal)
        if cima:  # curtas: adesivo menor, outra fonte e cor, em cima e deslocado
            ct = " ".join(_limpa(c) for c in cima).upper()
            fc = FONTES[(n + semente + 1) % len(FONTES)]
            tc = max(24, int(tam * 0.55 * ESCALA.get(fc, 1.0) / ESCALA.get(fonte, 1.0)))
            wc = _larg(ct, fc, tc)
            xc = int(min(max(x + w * 0.12 * (-1 if n % 2 else 1), wc / 2 + vw * 0.04), vw - wc / 2 - vw * 0.04))
            linhas += _adesivo(ct, fc, tc, CORES[(n * 3 + 2) % len(CORES)], est["cima_desenho"], xc,
                               int(y - tam * 0.78), giro * 0.6, s, e, est["pop_k"], sai_x, camada=20)
        if decoracao:
            ic = decoracao(_limpa(forte).lower())
            if ic:
                import anime_cartoes as _ac
                for _ly, _tags, _des in _ac.icone(ic, 0, 0, int(tam * 0.75), 6):
                    linhas.append("Dialogue: 36,%s,%s,Cria,,0,0,0,,{%s\\pos(%d,%d)%s}%s" % (
                        _ts(s), _ts(e), _tags, x + w * 0.5 + tam * 0.2, y - tam * 0.75, sai_x, _des))
        # rastro: o bloco anterior fica a 35% enquanto este entra (só se não encostam)
        if est["rastro"] and ant and os.environ.get("ANIME_LEGENDA_LEVE") != "1":
            a0, a1, a2, a3 = ant["caixa"]
            if a2 + 20 < caixa[0] or caixa[2] + 20 < a0 or a3 + 20 < caixa[1] or caixa[3] + 20 < a1:
                linhas.append("Dialogue: 9,%s,%s,Cria,,0,0,0,,{\\an5\\pos(%d,%d)\\frz%.1f\\fn%s\\fs%d\\1c%s\\bord%d"
                              "\\3c%s\\shad0\\alpha&HA6&\\t(%d,%d,\\alpha&HFF&)}%s" % (
                                  _ts(s), _ts(min(e, s + 0.9)), ant["x"], ant["y"], ant["giro"], ant["fonte"],
                                  ant["tam"], _bgr(ant["cor"]), max(3, ant["tam"] // 9), _bgr(CONTORNO),
                                  max(0, int(min(e - s, 0.9) * 1000) - 150), int(min(e - s, 0.9) * 1000), ant["txt"]))
        ant = {"caixa": caixa, "x": x, "y": y, "giro": giro, "fonte": fonte, "tam": tam, "cor": est["cor"], "txt": txt}
    return estilos, linhas
