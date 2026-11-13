"""diretor_cena.py — planeja o MOVIMENTO do video inteiro antes do render.

Antes: toda cena tentava RECORTE primeiro (quase toda cena com personagem virava
"fundo borrado + personagem por cima"), o resto era sorteio por palavra-chave, as 17
transicoes de 2 imagens nunca rodavam (o pipeline nao passava img2) e o log nao dizia
qual efeito saiu. Agora um plano por video, com arco narrativo e variedade:

  - cena 0 (gancho): efeito forte (recorte que salta / impacto de camera)
  - impacto/acao no texto: impacto de camera ou recorte forte (+ tremor no pipeline)
  - virada de tempo/lugar: transicao com a imagem ANTERIOR -> atual (grupo FX2)
  - lugar/paisagem: profundidade (camadas por depth) ou pan
  - final: afastamento/subida lenta
  - recorte em ate ~40% das cenas e nunca 2 seguidos; GIRO (charturn, spinin...) ~1 a cada 4
  - nenhum efeito repete dentro de 6 cenas; humor da cena puxa a familia certa
  - rasgo (fx_divisoria) no fim de 1-2 cenas, nas maiores viradas

Flag: DIRETOR_CENA=1 (default). Deterministico por story_id. O catalogo abaixo so tem
efeitos que renderizam (testados em lote em 2026-10-02: 132/133; `rewind` estoura a
memoria). Efeitos ruins em cena longa ficam em CURTOS (so em cena <= 4.5s).
"""
import os
import random
import re

import panel_effects as pe

# ── catalogo por familia ──────────────────────────────────────────────────────
FAMILIAS = {
    "recorte_forte": ["popout", "launchout", "risehero", "pushincut", "impactrecoil", "charslidein",
                      "charapproach", "falldrop", "charbounce", "squashjump", "freezechar",
                      "shakefear", "heartbeatcut"],
    "recorte_suave": ["charfloat", "charsway", "charzoomdrift", "breathcut", "float", "parallaxcut",
                      "bgblurfocus", "tiltshiftcut", "fogbehind", "shadowlift", "spotlightcut",
                      "outlineglow", "popframe", "charwalk", "charretreat"],
    "recorte_giro": ["charturn", "charorbit", "charlean", "parallaxtilt"],
    "recorte_estilo": ["crowdclone", "doubleexpose", "duplicateclones", "ghosttrail", "bgslidedepth"],
    "camera_impacto": ["freezeimpact", "shockwave", "speedlineszoom", "snapzoom", "whipzoom",
                       "crashzoomout", "flashcut", "shakeonhit", "lightningflash", "panelshatter",
                       "strobeaccent", "aspectpunch", "doubletake"],
    "camera_giro": ["spinin", "rollcw", "tiltdutch", "spinblur", "orbit", "perspectivetilt",
                    "perspectiveswing"],
    "camera_suave": ["dollypush", "facezoom", "breathing", "handheld", "pulsezoom", "panLR", "panUP",
                     "kenburnsdiag", "driftLR", "riseup", "tensionhold", "punchin", "slowpull",
                     "dollyzoom", "heartbeatzoom", "pulsebeat", "beatpump", "motionsmear", "echotrail"],
    "atmosfera": ["heathaze", "underwater", "ripple", "rackfocus", "vignettepulse", "lightsweep",
                  "scanlines", "blockglitch", "strobetrail", "shakeglitch", "bulge", "irisopen",
                  "letterboxin", "spotlightsearch", "spotlightfollow", "glowpulse", "waterreflection",
                  "mirrorsplit", "kaleidoscope", "pixelresolve", "graindissolve"],
    "profundidade": ["parallax3layer", "lightraysdepth", "fogdepth", "dofpull", "snowdepth",
                     "sliderevealcut", "depthdolly"],
    "transicao": ["mangaslide", "pagecurl", "crackreveal", "zoomtransition", "splitreveal",
                  "tumbletransition", "wipediag", "barndoor", "blinds", "cardflip", "clockwipe",
                  "scratchreveal", "filmstrip", "stackcascade", "pipinset", "splitscreen2", "gridmontage"],
}

# Efeitos com animacao "de prototipo" (2.5s) que degradam em cena longa: so em cena curta.
CURTOS = {"dispersion", "slowmoin", "frameclosein", "irisclose", "comicgrid", "borderglow",
          "pixeldissolve", "stutter", "dooropen", "ganglineup", "twocharface"}
# Fora do sorteio — QA visual de cada efeito em cena de 7s (2026-10-02):
#   cor estragada (blend em todos os planos): aspectpunch, frameclosein, irisopen, letterboxin,
#     spotlightfollow (verde), spotlightsearch, speedlineszoom (rosa), vignettepulse (oval branco)
#   ficam PRETOS depois de ~2s: irisclose, panelshatter, dispersion
#   clones/rosto deformado: ganglineup, twocharface, kaleidoscope, mirrorsplit
#   mostram a PROXIMA cena no meio da narracao: dooropen, sliderevealcut
#   enquadramento ruim/rosto duplicado (depth): depthdolly, fogdepth, dofpull
#   rewind: estoura a memoria (reverse guarda o clip inteiro)
#   parece video corrompido (quadro conferido 16/10, teste do elevador, cena 6): shakeglitch
FORA = {"rewind", "aspectpunch", "frameclosein", "irisopen", "irisclose", "letterboxin",
        "spotlightfollow", "spotlightsearch", "speedlineszoom", "vignettepulse", "panelshatter",
        "dispersion", "ganglineup", "twocharface", "kaleidoscope", "mirrorsplit", "dooropen",
        "sliderevealcut", "depthdolly", "fogdepth", "dofpull", "shakeglitch"}
# Caros (depth): no maximo 1 por video.
CAROS = {"depthdolly", "fogdepth", "dofpull"}
# Efeitos que TRAZEM um elemento (neve, agua, calor...): so se a cena fala dele
# (no teste, snowdepth pos neve caindo numa sala ensolarada).
REQUER_TEXTO = {
    "snowdepth": r"\bnev|inverno|nevasca|floco|\bsnow|winter",
    "underwater": r"[aá]gua|\bmar\b|oceano|submers|afog|mergulh|piscina|\bwater|ocean|underwater",
    "waterreflection": r"lago|reflexo|po[cç]a|espelho d|\blake|reflection|puddle",
    "heathaze": r"calor|deserto|sol escaldante|quente|\bheat|desert",
    "lightraysdepth": r"\bsol\b|luz|raio|amanhec|janela|igreja|templo|\bsun|light|ray|window|dawn",
    "fogbehind": r"n[eé]voa|neblina|fuma[cç]a|\bfog|mist|smoke",
}

# humor da cena -> pesos por familia
PESO_HUMOR = {
    "tense_dramatic": {"camera_impacto": 3, "recorte_forte": 2, "camera_giro": 1.5, "atmosfera": 1.2,
                       "camera_suave": 1, "recorte_giro": 1, "profundidade": 0.6},
    "sad_emotional": {"camera_suave": 3, "recorte_suave": 2, "atmosfera": 1, "profundidade": 1,
                      "recorte_giro": 0.6},
    "calm_chill": {"camera_suave": 2.5, "profundidade": 2, "recorte_suave": 1.5, "atmosfera": 0.6,
                   "recorte_giro": 0.8},
    "neutral_chill": {"camera_suave": 2.5, "profundidade": 1.5, "recorte_suave": 1.5, "recorte_giro": 1},
    "funny_lighthearted": {"recorte_forte": 3, "camera_giro": 2, "camera_impacto": 1.5,
                           "recorte_estilo": 1.5, "recorte_giro": 1.5, "camera_suave": 0.6},
    "romantic_sexy": {"recorte_suave": 2.5, "camera_suave": 2, "atmosfera": 1, "recorte_giro": 1},
    "mysterious": {"atmosfera": 2.5, "profundidade": 2, "recorte_suave": 1.5, "camera_suave": 1},
}

_NUM = (r"\d+|um|uma|dois|duas|tr[eê]s|quatro|cinco|seis|sete|oito|nove|dez|onze|doze|quinze|"
        r"vinte|trinta|cem|alguns|algumas|muitos|muitas|poucos|poucas|v[aá]rios|v[aá]rias")
_RE_VIRADA = re.compile(
    rf"\b(?:{_NUM})\s+(?:anos|meses|semanas|dias|horas|minutos)\s+(?:depois|mais tarde|se passaram)|"
    r"\b(?:n[ao]\s+|naquel[ae]\s+)?(?:dia|manh[aã]|noite|semana|tarde)\s+seguinte|naquela noite|"
    r"enquanto isso|mais tarde|anos se passaram|o tempo passou|de volta ao|em outro lugar|"
    r"do outro lado|tempos depois|certo dia|um dia,|finalmente chegou", re.I)
_RE_LUGAR = re.compile(r"\b(cidade|paisagem|vila|aldeia|floresta|montanha|praia|mar|deserto|rua|"
                       r"estrada|campo|horizonte|c[eé]u|castelo|pr[eé]dio|templo|igreja|escola)\b", re.I)


def ativo():
    return os.environ.get("DIRETOR_CENA", "1") == "1"


def _disponiveis():
    todos = set(pe.PANEL_FX) | set(pe.CUTOUT_FX) | set(pe.SENDCMD_FX) | set(pe.FX2) | set(pe.ADVFX)
    return todos - FORA


def familia_de(fx):
    for fam, lst in FAMILIAS.items():
        if fx in lst:
            return fam
    return "outro"


def _texto(cena):
    return (cena.get("narracao") or cena.get("texto") or "").strip()


def eh_virada(cena):
    return bool(_RE_VIRADA.search(_texto(cena)))


def texto_virada(cena):
    """Texto da cartela narrativa tirado da PROPRIA narracao ('Cinco anos depois...').
    None se a cena nao abre com passagem de tempo/lugar (ai nao ha cartela: o texto
    sorteado de antes podia nao ter nada a ver com a historia)."""
    if cena.get("transicao"):
        return cena["transicao"]
    m = _RE_VIRADA.search(_texto(cena))
    if not m:
        return None
    frase = m.group(0).strip(" ,.;")
    return frase[:1].upper() + frase[1:] + "..."


def _impacto(texto):
    """So palavra-chave (instantaneo e deterministico). O is_impact_panel do fx_detect
    consulta a IA a cada chamada — no plano do video inteiro isso travava."""
    try:
        from fx_detect import IMPACT_KEYWORDS
        t = (texto or "").lower()
        return any(kw in t for kw in IMPACT_KEYWORDS)
    except Exception:
        return False


def _sorteio_ponderado(pesos, rnd):
    """Ordena as familias por sorteio ponderado sem reposicao (a 1a e a escolhida)."""
    restantes = dict(pesos)
    ordem = []
    while restantes:
        tot = sum(restantes.values())
        r = rnd.uniform(0, tot)
        acc = 0.0
        for fam, w in restantes.items():
            acc += w
            if r <= acc:
                ordem.append(fam)
                del restantes[fam]
                break
    return ordem


def _keyword_fx(texto, disp):
    """Efeito sugerido pelas palavras da narracao (tabela FX_KEYWORDS do panel_effects)."""
    t = texto.lower()
    for fx, kws in pe.FX_KEYWORDS:
        if fx in disp and any(k in t for k in kws):
            return fx
    return None


def planejar(cenas, genero=None, seed=None, duracoes=None):
    """Plano por cena: {idx, fx, familia, motivo, usa_anterior, rasgo_fim, alternativas}.

    duracoes: segundos de audio de cada cena (pra evitar efeitos CURTOS em cena longa).
    usa_anterior=True: efeito de transicao (FX2) — renderizar com img=anterior, img2=atual.
    rasgo_fim=True: aplicar fx_divisoria.aplicar_rasgo no fim do clip (para a proxima)."""
    rnd = random.Random(str(seed or "x"))
    disp = _disponiveis()
    n = len(cenas)
    plano = []
    recentes = []          # ultimos efeitos (anti-repeticao em janela de 6)
    usados_caros = 0
    desde_giro = 3
    recortes = 0

    def candidatos(fam, dur, txt=""):
        out = []
        for fx in FAMILIAS.get(fam, []):
            if fx not in disp or fx in recentes[-6:]:
                continue
            if fx in REQUER_TEXTO and not re.search(REQUER_TEXTO[fx], txt, re.I):
                continue
            if fx in CURTOS and dur > 4.5:
                continue
            if fx in CAROS and usados_caros >= 1:
                continue
            out.append(fx)
        return out

    for i, cena in enumerate(cenas):
        texto = _texto(cena)
        mood = cena.get("mood") or "neutral_chill"
        dur = float((duracoes or {}).get(i, 6.0) if isinstance(duracoes, dict) else
                    (duracoes[i] if duracoes and i < len(duracoes) else 6.0))
        prev_recorte = bool(plano) and plano[-1]["familia"].startswith("recorte")
        teto_recorte = recortes >= max(1, round(0.4 * n))

        # 1) motivo da cena
        if i == 0:
            motivo = "gancho"
        elif i > 0 and eh_virada(cena) and i < n:
            motivo = "virada"
        elif _impacto(texto):
            motivo = "impacto"
        elif i == n - 1:
            motivo = "final"
        elif _RE_LUGAR.search(texto):
            motivo = "lugar"
        else:
            motivo = "humor"

        # 2) familias candidatas por motivo
        if motivo == "gancho":
            fams = ["recorte_forte", "camera_impacto", "recorte_giro"]
        elif motivo == "virada":
            fams = ["transicao"]
        elif motivo == "impacto":
            fams = ["camera_impacto", "recorte_forte", "camera_giro"]
        elif motivo == "final":
            fams = ["camera_suave", "recorte_suave"]
        elif motivo == "lugar":
            fams = ["profundidade", "camera_suave"]
        else:
            fams = _sorteio_ponderado(PESO_HUMOR.get(mood, PESO_HUMOR["neutral_chill"]), rnd)
            # profundidade (camadas por depth) so em cena de LUGAR: em retrato o QA mostrou
            # o rosto empurrado pra borda
            fams = [f for f in fams if f != "profundidade"]
        # gancho/impacto/final: a ordem fixa vira sorteio entre as 2 primeiras
        if motivo in ("gancho", "impacto", "final", "lugar") and len(fams) > 1 and rnd.random() < 0.45:
            fams = [fams[1], fams[0]] + fams[2:]
        # meta de ~35% de recorte: atrasado -> recorte na frente
        if motivo in ("humor", "lugar") and recortes < 0.35 * i and rnd.random() < 0.7:
            fams = [rnd.choice(["recorte_suave", "recorte_forte", "recorte_giro", "recorte_estilo"])] + fams
        # giro de tempos em tempos (pedido da dona: "girando")
        if desde_giro >= 4 and motivo in ("humor", "impacto", "gancho") and rnd.random() < 0.6:
            fams = (["recorte_giro"] if not prev_recorte and not teto_recorte else []) + ["camera_giro"] + fams
        # limites do recorte
        if prev_recorte or teto_recorte:
            fams = [f for f in fams if not f.startswith("recorte")] or ["camera_suave"]

        # 3) palavra-chave da narracao: so em cena comum e as vezes (senao "olhou/disse/
        #    cidade" puxam sempre facezoom/dollypush/panLR, a monotonia de antes)
        escolhido = None
        kw = _keyword_fx(texto, disp) if motivo == "humor" and rnd.random() < 0.3 else None
        if kw in REQUER_TEXTO and not re.search(REQUER_TEXTO[kw], f"{texto} {cena.get('image_prompt', '')}", re.I):
            kw = None
        if kw and kw not in recentes[-6:] and familia_de(kw) in fams \
                and not (kw in CURTOS and dur > 4.5):
            escolhido = kw
        alternativas = []
        _txt = f"{texto} {cena.get('image_prompt', '')}"
        for fam in fams:
            c = candidatos(fam, dur, _txt)
            rnd.shuffle(c)
            alternativas += c
        if not escolhido and alternativas:
            escolhido = alternativas[0]
        if not escolhido:
            escolhido = "dollypush"
        # cena 0 nao tem anterior: transicao vira impacto
        if familia_de(escolhido) == "transicao" and i == 0:
            escolhido = (candidatos("camera_impacto", dur, _txt) or ["whipzoom"])[0]
        alternativas = [a for a in alternativas if a != escolhido][:4]
        if "dollypush" not in alternativas:
            alternativas.append("dollypush")

        fam = familia_de(escolhido)
        plano.append({"idx": i, "fx": escolhido, "familia": fam, "motivo": motivo, "mood": mood,
                      "usa_anterior": fam == "transicao", "rasgo_fim": False,
                      "alternativas": alternativas})
        recentes.append(escolhido)
        if fam.startswith("recorte"):
            recortes += 1
        if escolhido in CAROS:
            usados_caros += 1
        desde_giro = 0 if fam in ("recorte_giro", "camera_giro") else desde_giro + 1

    # 4) rasgo (divisoria) no fim da cena ANTES das maiores viradas (sem transicao FX2 la)
    try:
        import fx_divisoria
        if fx_divisoria.ativo() and n >= 4:
            alvo = max(1, min(2, n // 5))
            viradas = [p["idx"] - 1 for p in plano if p["motivo"] == "virada" and p["idx"] >= 1]
            # sem viradas no texto: maior troca de humor
            trocas = [i for i in range(n - 1) if plano[i]["mood"] != plano[i + 1]["mood"]]
            escolhas = []
            for i in viradas + trocas + [n // 2 - 1]:
                if i < 0 or i >= n - 1 or i in escolhas:
                    continue
                if plano[i + 1]["usa_anterior"]:      # ja ha transicao FX2 nessa emenda
                    continue
                if any(abs(i - j) < 3 for j in escolhas):
                    continue
                escolhas.append(i)
                if len(escolhas) >= alvo:
                    break
            for i in escolhas:
                plano[i]["rasgo_fim"] = True
    except Exception:
        pass
    return plano


def resumo(plano):
    """Linha curta pro log: 'gancho:popout | humor:facezoom+rasgo | ...'."""
    return " | ".join(f"{p['idx']}:{p['fx']}{'+rasgo' if p['rasgo_fim'] else ''}" for p in plano)
