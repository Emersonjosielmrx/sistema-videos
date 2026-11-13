#!/usr/bin/env python3
"""elemental_transitions.py — transições ELEMENTAIS (fogo/água/gelo/rasgar) no boundary.

NÃO toca no áudio nem no concat single-pass (evita o bug dos 69% mudos). Recebe o
MP4 JÁ concatenado (vídeo+áudio em sync) e sobrepõe overlays alpha (MOV ProRes 4444
das compositions HyperFrames) nos cortes onde a cena é elemental. Áudio = copy.

Fluxo:
  pick_transitions(descriptions, abs_starts) -> [{t, element, file}]  (qual corte, qual efeito)
  apply(in_mp4, out_mp4, picks)                                       (overlay alpha via ffmpeg)

Detecção por keyword PT/EN na descrição do painel DE DESTINO (painel B do corte).
Anti-repetição consecutiva. force_all=ELEMENTAL_FORCE força um efeito em todo corte
(ciclo fire->water->ice->tear) pra teste visual.
"""
import re
import os
import subprocess
import sys
from pathlib import Path

PROJ = Path(__file__).resolve().parent.parent
ELEM_DIR = PROJ / "workspace" / "assets" / "overlays" / "elemental"

# keyword -> elemento. Ordem importa: mais específico primeiro.
ELEMENT_KEYWORDS = {
    "fire": ["fogo", "chama", "chamas", "queima", "queimou", "incêndio", "incendio",
             "labareda", "ardendo", "flame", "fire", "burn", "blaze"],
    "water": ["água", "agua", "chuva", "mergulh", "afoga", "rio", "mar", "onda",
              "molh", "inund", "water", "rain", "wave", "flood", "splash", "lágrima", "lagrima"],
    "ice": ["gelo", "congel", "frio", "gélid", "gelid", "cristal de gelo",
            "ice", "frozen", "freeze", "frost", "gelado"],
    "snow": ["neve", "nevar", "nevando", "nevasca", "floco", "snow", "inverno", "nevou", "branco de neve"],
    "tear": ["rasg", "despeda", "parte ao meio", "rip", "tear"],
    "smoke": ["fumaça", "fumaca", "smoke", "névoa", "nevoa", "vapor", "neblina", "fog"],
    "lightning": ["raio", "relâmpago", "relampago", "trovão", "trovao", "elétric", "eletric",
                  "lightning", "thunder", "choque elétrico", "faísca elétrica"],
    "shockwave": ["explos", "explod", "impacto", "soco", "bomba", "detonou", "shockwave",
                  "blast", "boom", "onda de choque", "estrondo"],
    "disintegrate": ["desintegr", "destrói", "destroi", "destru", "estilhaç", "estilhac",
                     "quebr", "shatter", "smash", "crack", "break", "pó", "poeira",
                     "esfarel", "desfaz", "sumiu", "desaparec", "disintegrate", "dissolv"],
    "glitch": ["glitch", "digital", "erro", "falha", "bug", "distorç", "distorc", "corromp"],
    "tvoff": ["tv", "televisão", "televisao", "tela", "sinal", "estática", "estatica",
              "desligou", "apagou a tela", "static"],
    # --- elementos de ROMANCE / emoção (2026-06-30 tarde) ---
    "hearts": ["amor", "ama", "amando", "apaixon", "paixão", "paixao", "coração", "coracao",
               "beij", "abraç", "abrac", "carinho", "romance", "romântic", "romantic",
               "love", "heart", "kiss", "crush", "querid", "fofo", "ternura"],
    "petals": ["pétala", "petala", "flor", "flores", "cereje", "sakura", "jardim",
               "primavera", "petal", "blossom", "flower", "romântic"],
    "sparkle": ["brilho", "brilha", "brilhante", "encant", "deslumbr", "lind", "belíssim",
                "belissim", "maravilh", "fascin", "radiante", "sparkle", "shine", "glitter",
                "sonh"],
    "divine": ["divin", "sagrad", "celest", "anjo", "céu se abr", "luz divina", "milagr",
               "abençoa", "abencoa", "holy", "heaven", "divine", "blessing", "salvaç"],
    "wind": ["vento", "brisa", "ventania", "rajada", "sopr", "wind", "breeze", "gust", "folhas ao vento"],
    "snow": ["neve", "nevar", "nevando", "nevasca", "floco", "snow", "inverno", "nevou", "branco de neve"],
    # --- elementos de DRAMA / ação (2026-06-30 tarde) ---
    "blood": ["sangue", "sangr", "ferid", "ferimento", "machuc", "corte", "facad", "esfaque",
              "blood", "wound", "bleed", "morte sangrenta", "violênci", "violenci", "apanh"],
    "shadow": ["sombra", "escurid", "trevas", "medo", "terror", "sinistro", "maligno", "mal",
               "demôni", "demoni", "pesadelo", "shadow", "darkness", "evil", "dread", "tens"],
    "quake": ["terremoto", "tremor", "abalo", "tremeu", "chão racha", "chao racha", "desmoron",
              "earthquake", "quake", "rumble", "colaps", "desab"],
    "impact": ["impacto", "choque", "surpres", "chocad", "atônit", "atonit", "pasm", "revel",
               "de repente", "subitamente", "flagr", "impact", "shock", "sudden", "reveal", "twist"],
    "portal": ["portal", "dimensão", "dimensao", "teletransport", "magia", "mágic", "magic",
               "feitiço", "feitico", "invoca", "vortex", "warp", "summon", "spell"],
    # --- anime/manhwa emoção (PARTE 2) ---
    "blush": ["vergonha", "envergonh", "corou", "rubor", "ruboriz", "tímid", "timid", "encabul",
              "constrang", "fica vermelh", "ficou vermelh", "blush", "shy", "embarrass"],
    "anger": ["raiva", "furioso", "furiosa", "irritad", "ódio", "odio", "bravo", "brava", "enfurec",
              "revolt", "puto", "com raiva", "rangeu os dentes", "angry", "furious", "rage"],
    "sweatdrop": ["sem graça", "sem-graça", "constrangid", "nervos", "suando frio",
                  "desconcert", "awkward", "nervous"],
    "question": ["confus", "não entend", "nao entend", "perdid", "hein", "perplex", "como assim",
                 "que isso", "sem entender", "puzzled", "confused"],
    "flashback": ["lembr", "memória", "memoria", "flashback", "no passado", "recorda", "antigamente",
                  "naquele dia", "quando era criança", "quando era crianca", "reminisc", "memory"],
    "exclaim": ["susto", "assust", "chocad", "chocou", "inacreditável", "inacreditavel",
                "não pode ser", "nao pode ser", "o quê", "revelaç", "plot twist", "shock"],
    # === CAT3a reforço narrativo SOBRE o painel (PARTE 4) ===
    # ⚠ POSICIONAMENTO: pointer/zoomdetail/objectglow saem no CENTRO fixo. Idealmente o alvo
    #   varia por painel — precisam de detecção de posição (ver AJUSTES_POSICIONAMENTO_CAT3a.md).
    #   Até lá, keyword VAZIA: NÃO disparam por cena (evita apontar o vazio). Só via force/manual.
    "pointer": [],
    "onomatopeia": ["gritou", "grito", "estrondo", "barulho", "som de", "batida", "explodiu", "bang"],
    "zoomdetail": [],
    "objectglow": [],
    "heartbeat": ["coração disparou", "coracao disparou", "coração batendo", "gelou", "suor frio", "prendeu a respiração"],
    "location": ["chegou em", "chegou na", "chegou no", "na escola", "em casa", "no quarto", "no restaurante", "no hospital"],
    "keyphrase": ["eu prometo", "prometo", "jamais", "eu juro", "juro", "nunca vou", "sempre vou", "é uma promessa"],
    "zoompunch": [],
    # === LEVA 2026-06-30 tarde: 12 transições/overlays + 6 anime + 11 categorias ===
    # CAT1 transição (no corte) — novas
    "swipelight": [],
    "inkblot": [],
    "blinds": [],
    "cinebars": ["cinematográfic", "cinematografic", "dramático", "dramatico", "momento épico", "epico"],
    "radialzoom": [],
    "speedlines": ["corre", "correndo", "disparou", "veloz", "rápido", "rapido", "ação", "acao",
                   "perseguição", "perseguicao", "fuga", "run", "chase", "rush", "fast"],
    "pageturn": ["capítulo", "capitulo", "página", "pagina", "nova fase", "começa", "comeca", "page"],
    "shatter": ["estilhaç", "quebrou tudo", "despedaç", "vidro", "shatter", "quebrar vidro"],
    "brushstroke": ["pincel", "tinta", "pintura", "arte", "sumi", "brush"],
    # CAT2 overlay atmosférico — novas
    "bubbles": ["bolha", "bolhas", "piscina", "aquário", "aquario", "submers", "mergulho",
                "embaixo d'água", "embaixo da agua", "bubble", "underwater", "pool"],
    "rain": ["chuva", "chovendo", "chuvoso", "tempestade", "garoa", "rain", "rainy", "storm", "downpour"],
    "fireworks": ["fogos", "fogos de artifício", "fogos de artificio", "ano novo", "fireworks"],
    "leaves": ["outono", "folhas caem", "folhas caindo", "folha seca", "passagem de tempo",
               "anos depois", "tempo passa", "autumn", "fall leaves"],
    "bokeh": ["aconcheg", "sonho", "sonhad", "nostálg", "nostalg", "calor do lar", "bokeh", "dreamy", "cozy"],
    "starburst": ["alegria", "feliz", "euforia", "vitória", "vitoria", "conquist", "triunf",
                  "radiante de", "explosão de alegria", "joy", "victory", "yay"],
    "nightsky": ["noite", "escuridão da noite", "lua", "estrelado", "céu noturno", "ceu noturno", "madrugada", "night"],
    "godrays": ["sol", "ensolarad", "luz do dia", "manhã", "manha", "raios de sol", "amanhecer", "sunlight", "sunny"],
    "confetti": ["festa", "comemora", "celebra", "aniversário", "aniversario", "parabéns", "parabens", "party"],
    "neon": ["cidade à noite", "cidade a noite", "balada", "boate", "neon", "luzes da cidade", "night club", "downtown"],
    # CAT3 engajamento — disparo por cadência/manual (keyword vazia evita falso positivo)
    "likeburst": [],
    "subscribe": [],
    "followarrow": [],
    "emojirain": [],
    # CTA extras (PARTE 5) — engajamento por cadência/manual, keyword vazia
    "save": [],
    "share": [],
    "comment": [],
    "part2": [],
    "watchtoend": [],
    "notify": [],
    # MASCOTE — keyword vazia (disparo manual/cadência, parcimônia)
    "mascot": [],
}


# elemento -> arquivo MOV alpha em elemental/. fire usa a V2 (movimento real).
ASSET_FILE = {
    "fire": "fx_fire_v2.mov",
    "water": "trans_water.mov",
    "ice": "trans_ice.mov",
    "tear": "trans_tear.mov",
    "smoke": "fx_smoke.mov",
    "lightning": "fx_lightning.mov",
    "shockwave": "fx_shockwave.mov",
    "disintegrate": "fx_disintegrate.mov",
    "glitch": "fx_glitch.mov",
    "tvoff": "fx_tvoff.mov",
    # romance / emoção
    "hearts": "fx_hearts.mov",
    "petals": "fx_petals.mov",
    "sparkle": "fx_sparkle.mov",
    "divine": "fx_divine.mov",
    "wind": "fx_wind.mov",
    "snow": "fx_snow.mov",
    # drama / ação
    "blood": "fx_blood.mov",
    "shadow": "fx_shadow.mov",
    "quake": "fx_quake.mov",
    "impact": "fx_impact.mov",
    "portal": "fx_portal.mov",
    # anime/manhwa emoção (PARTE 2)
    "blush": "fx_blush.mov", "anger": "fx_anger.mov", "sweatdrop": "fx_sweatdrop.mov",
    "question": "fx_question.mov", "flashback": "fx_flashback.mov", "exclaim": "fx_exclaim.mov",
    # CAT3a reforço narrativo (PARTE 4)
    "pointer": "fx_pointer.mov", "onomatopeia": "fx_onomatopeia.mov", "zoomdetail": "fx_zoomdetail.mov",
    "objectglow": "fx_objectglow.mov", "heartbeat": "fx_heartbeat.mov", "location": "fx_location.mov",
    "keyphrase": "fx_keyphrase.mov", "zoompunch": "fx_zoompunch.mov",
    "swipelight": "fx_swipelight.mov", "inkblot": "fx_inkblot.mov", "blinds": "fx_blinds.mov",
    "cinebars": "fx_cinebars.mov", "radialzoom": "fx_radialzoom.mov", "speedlines": "fx_speedlines.mov",
    "pageturn": "fx_pageturn.mov", "shatter": "fx_shatter.mov", "brushstroke": "fx_brushstroke.mov",
    # CAT2 overlay atmosférico
    "bubbles": "fx_bubbles.mov", "rain": "fx_rain.mov", "fireworks": "fx_fireworks.mov",
    "leaves": "fx_leaves.mov", "bokeh": "fx_bokeh.mov", "starburst": "fx_starburst.mov",
    "nightsky": "fx_nightsky.mov", "godrays": "fx_godrays.mov", "confetti": "fx_confetti.mov",
    "neon": "fx_neon.mov",
    # CAT3 engajamento (poll REPROVADO, fora)
    "likeburst": "fx_likeburst.mov", "subscribe": "fx_subscribe.mov",
    "followarrow": "fx_followarrow.mov", "emojirain": "fx_emojirain.mov",
    # CTA extras (PARTE 5)
    "save": "fx_save.mov", "share": "fx_share.mov", "comment": "fx_comment.mov",
    "part2": "fx_part2.mov", "watchtoend": "fx_watchtoend.mov", "notify": "fx_notify.mov",
    # MASCOTE garota-propaganda (CAT3, parcimônia 1-2x/vídeo; poses extras via fx_mascot_*)
    "mascot": "fx_mascot.mov",
    "mascot_point": "fx_mascot_point.mov", "mascot_surprise": "fx_mascot_surprise.mov",
    "mascot_thumbsup": "fx_mascot_thumbsup.mov",
}

# aliases p/ o force_efeito do PREVIEW (aceita nomes soltos)
ALIASES = {
    "fogo": "fire", "agua": "water", "água": "water", "gelo": "ice",
    "rasgar": "tear", "rasgo": "tear", "fumaca": "smoke", "fumaça": "smoke",
    "raio": "lightning", "relampago": "lightning", "choque": "shockwave",
    "explosao": "shockwave", "explosão": "shockwave", "desintegrar": "disintegrate",
    "desintegra": "disintegrate", "tv": "tvoff", "tvantiga": "tvoff",
    "fire_v2": "fire",
    # novos
    "coracao": "hearts", "coração": "hearts", "coracoes": "hearts", "amor": "hearts",
    "petala": "petals", "pétala": "petals", "petalas": "petals", "flor": "petals", "sakura": "petals",
    "brilho": "sparkle", "sparkles": "sparkle", "magia": "sparkle",
    "divino": "divine", "luz": "divine", "ceu": "divine", "céu": "divine",
    "vento": "wind", "brisa": "wind",
    "neve": "snow", "floco": "snow",
    "sangue": "blood", "sangrento": "blood",
    "sombra": "shadow", "trevas": "shadow", "escuridao": "shadow", "escuridão": "shadow",
    "terremoto": "quake", "tremor": "quake", "abalo": "quake",
    "impacto": "impact", "surpresa": "impact",
    "vortex": "portal", "dimensao": "portal", "dimensão": "portal",
    # anime/manhwa emoção (PARTE 2)
    "rubor": "blush", "vergonha": "blush", "raiva": "anger", "furia": "anger", "fúria": "anger",
    "suor": "sweatdrop", "gota": "sweatdrop", "confusao": "question", "confusão": "question",
    "interrogacao": "question", "duvida": "question", "memoria": "flashback", "lembranca": "flashback",
    "susto": "exclaim", "exclamacao": "exclaim",
    # CAT3a reforço narrativo (PARTE 4)
    "seta_aponta": "pointer", "apontar": "pointer", "pow": "onomatopeia",
    "zoom_detalhe": "zoomdetail", "foco": "zoomdetail", "brilho_objeto": "objectglow", "item": "objectglow",
    "batida": "heartbeat", "pulso": "heartbeat", "local": "location", "placa": "location",
    "frase": "keyphrase", "fala_chave": "keyphrase", "punch": "zoompunch", "soco_zoom": "zoompunch",
    "luz": "swipelight", "tinta": "inkblot", "persianas": "blinds", "cinema": "cinebars",
    "zoom": "radialzoom", "velocidade": "speedlines", "pagina": "pageturn", "virar_pagina": "pageturn",
    "vidro": "shatter", "estilhacar": "shatter", "pincel": "brushstroke",
    "bolha": "bubbles", "bolhas": "bubbles", "chuva": "rain", "fogos": "fireworks",
    "folhas": "leaves", "outono": "leaves", "sonho": "bokeh", "estrelas": "nightsky",
    "noite": "nightsky", "sol": "godrays", "raios_sol": "godrays", "festa": "confetti",
    "confete": "confetti", "cidade": "neon", "balada": "neon",
    "like": "likeburst", "curtir": "likeburst", "inscrever": "subscribe", "inscreva": "subscribe",
    "seguir": "followarrow", "seta": "followarrow", "emoji": "emojirain",
    # CTA extras (PARTE 5)
    "salvar": "save", "salva": "save", "compartilhar": "share", "compartilha": "share", "enviar": "share",
    "comentar": "comment", "comenta": "comment", "parte2": "part2", "parte_2": "part2", "continua": "part2",
    "assistir_fim": "watchtoend", "ate_o_fim": "watchtoend", "sininho": "notify", "notificacao": "notify",
}

# ciclo do ELEMENTAL_FORCE (todos os efeitos, pra showcase) — 58 no total
ELEMENTS = ["fire", "water", "ice", "snow", "tear", "smoke", "lightning",
            "shockwave", "disintegrate", "glitch", "tvoff",
            "hearts", "petals", "sparkle", "divine", "wind",
            "blood", "shadow", "quake", "impact", "portal",
            "blush", "anger", "sweatdrop", "question", "flashback", "exclaim",
            "swipelight", "inkblot", "blinds", "cinebars", "radialzoom", "speedlines",
            "pageturn", "shatter", "brushstroke",
            "bubbles", "rain", "fireworks", "leaves", "bokeh", "starburst",
            "nightsky", "godrays", "confetti", "neon",
            "likeburst", "subscribe", "followarrow", "emojirain",
            "pointer", "onomatopeia", "zoomdetail", "objectglow", "heartbeat",
            "location", "keyphrase", "zoompunch",
            "save", "share", "comment", "part2", "watchtoend", "notify",
            "mascot"]


# CATEGORIA de cada efeito (taxonomia da usuária — TAXONOMIA_EFEITOS_3_CATEGORIAS.md):
#   1 = transição REAL no corte (cobre/varre/revela na troca A→B) — centrado no boundary
#   2 = overlay atmosférico SOBRE o painel (clima/partículas) — roda DURANTE o painel
#   3 = reativo/engajamento SOBRE o painel (reação anime, CTA) — roda DURANTE o painel
# Default 1 (transição) p/ qualquer efeito não listado.
EFFECT_CAT = {
    "fire": 1, "water": 1, "ice": 1, "tear": 1, "disintegrate": 1, "glitch": 1,
    "tvoff": 1, "portal": 1, "impact": 1, "shockwave": 1, "exclaim": 1, "flashback": 1,
    "swipelight": 1, "inkblot": 1, "blinds": 1, "cinebars": 1, "radialzoom": 1,
    "speedlines": 1, "pageturn": 1, "shatter": 1, "brushstroke": 1,
    "snow": 2, "rain": 2, "smoke": 2, "leaves": 2, "petals": 2, "bokeh": 2, "wind": 2,
    "bubbles": 2, "sparkle": 2, "starburst": 2, "fireworks": 2, "divine": 2, "shadow": 2,
    "lightning": 2, "blood": 2, "quake": 2, "nightsky": 2, "godrays": 2, "confetti": 2, "neon": 2,
    "hearts": 3, "blush": 3, "anger": 3, "sweatdrop": 3, "question": 3,
    "likeburst": 3, "subscribe": 3, "followarrow": 3, "emojirain": 3, "pointer": 3,
    "onomatopeia": 3, "zoomdetail": 3, "objectglow": 3, "heartbeat": 3, "location": 3,
    "keyphrase": 3, "zoompunch": 3, "save": 3, "share": 3, "comment": 3,
    "part2": 3, "watchtoend": 3, "notify": 3, "mascot": 3,
}


def log(m):
    print(f"[elem] {m}", file=sys.stderr)


def _norm(element):
    """Normaliza nome (aliases) -> chave canônica."""
    if not element:
        return None
    e = element.strip().lower()
    return ALIASES.get(e, e)


def effect_cat(element):
    """Categoria (1/2/3) do efeito. Default 1 (transição no corte)."""
    return EFFECT_CAT.get(_norm(element), 1)


def _asset(element):
    element = _norm(element)
    fn = ASSET_FILE.get(element)
    if not fn:
        return None
    p = ELEM_DIR / fn
    return p if p.exists() else None


def detect_element(desc):
    """Retorna o efeito detectado pela descrição do painel, ou None."""
    if not desc:
        return None
    d = desc.lower()
    for element, kws in ELEMENT_KEYWORDS.items():
        if _rx_elemento(element, kws).search(d):
            return element
    return None


# 13/11: era "kw in d" (pedaço de palavra): "marido"/"território"/"vários" davam ÁGUA (mar, rio), "animal"/"normal"
# davam SOMBRA (mal), "ferro"/"terror" davam GLITCH (erro), "índice" dava GELO (ice), "floresta" dava PÉTALAS (flor),
# "soldado" dava SOL, "socorro" dava SOCO, "aguardou" dava ÁGUA. Agora a palavra-chave casa no COMEÇO da palavra
# (radical: "mergulh" pega "mergulhou") e as curtas que também são começo de outra palavra só casam INTEIRAS.
_SO_INTEIRA = frozenset(
    "ama mar rio mal tv ice pó rip tear fog bug onda tela erro sinal sol lua run page joy shy yay arte corte corre flor "
    "fast manha manhã neve soco acao ação bang boom chama juro puto hein corou bomba agua pool cozy neon evil holy gust "
    "warp rain snow wind love kiss fire burn mana gelo fogo frio medo raio flores".split())
_RX_ELEMENTO = {}


def _rx_elemento(element, kws):
    rx = _RX_ELEMENTO.get(element)
    if rx is None:
        letra = "0-9a-zà-öø-ÿ"
        partes = [re.escape(k.lower()) + (rf"s?(?![{letra}])" if k.lower() in _SO_INTEIRA else "")
                  for k in sorted(kws, key=len, reverse=True) if k]
        # elemento sem palavra-chave (lista vazia) não pode casar: "(?:)" casaria em qualquer texto
        rx = _RX_ELEMENTO[element] = re.compile(rf"(?<![{letra}])(?:" + "|".join(partes) + ")" if partes else r"(?!)")
    return rx


def _probe_dur(path):
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=duration", "-of",
             "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True, timeout=15)
        return float(r.stdout.strip())
    except Exception:
        return 0.9


def pick_transitions(descriptions, abs_starts, sensual=None):
    """Decide quais cortes recebem transição elemental.

    descriptions[i] = descrição do painel i. O corte i->i+1 usa abs_starts[i+1] como
    tempo (início do painel de destino). force=ELEMENTAL_FORCE força efeitos em todo
    corte pra teste. Anti-repetição consecutiva.

    PREVIEW: se workspace/_PREVIEW.json tem force_efeito, força ESSE efeito em todo
    corte (sobrepõe o ciclo). Permite testar 1 efeito específico sem editar código.
    """
    force = os.environ.get("ELEMENTAL_FORCE", "0") == "1"
    preview_fx = None
    try:
        import preview_config
        preview_fx = preview_config.force_efeito()
    except Exception:
        preview_fx = None
    if preview_fx:
        preview_fx = _norm(preview_fx)
        force = True

    picks = []
    last = None
    n = min(len(descriptions), len(abs_starts))
    forced_i = 0
    _sens = set(sensual or [])  # painéis +18 → NÃO recebem efeito (serão censurados)
    for i in range(1, n):  # corte antes do painel i (destino = painel i)
        if i in _sens:
            continue  # painel +18: pula efeito (não vale gastar no que vai ser censurado)
        if preview_fx:
            element = preview_fx
        else:
            element = detect_element(descriptions[i])
            if element is None and force:
                element = ELEMENTS[forced_i % len(ELEMENTS)]
                forced_i += 1
        if element is None:
            continue
        if element == last and not preview_fx:
            # evita repetir; tenta o próximo do ciclo
            alt = ELEMENTS[(ELEMENTS.index(element) + 1) % len(ELEMENTS)] if element in ELEMENTS else element
            element = alt
        f = _asset(element)
        if f is None:
            log(f"asset ausente p/ {element}, pulando corte {i}")
            continue
        dur = _probe_dur(f)
        # POSICIONAMENTO POR CATEGORIA (taxonomia da usuária):
        #   CAT1 (transição) → centrado no CORTE (começa um pouco antes do painel destino)
        #   CAT2/CAT3 (overlay/reativo) → DURANTE o painel destino (logo após o corte),
        #     pra dar clima/reação sobre a cena, não varrer a troca.
        cat = effect_cat(element)
        if cat == 1:
            t = max(0.0, abs_starts[i] - dur * 0.5)
        else:
            t = abs_starts[i] + 0.15  # entra logo depois do corte, sobre o painel
        picks.append({"t": t, "element": element, "file": f, "dur": dur, "cat": cat})
        last = element
    return picks


def _apply_lote(in_mp4, out_mp4, picks, bw, bh):
    """Aplica UM lote pequeno de overlays (evita filter_complex gigante → OOM). True/False."""
    in_mp4, out_mp4 = Path(in_mp4), Path(out_mp4)
    inputs = ["-i", str(in_mp4)]
    for p in picks:
        inputs += ["-i", str(p["file"])]
    fc = []
    last_lbl = "[0:v]"
    for idx, p in enumerate(picks, start=1):
        t0 = p["t"]
        t1 = t0 + p["dur"]
        pos = p.get("pos")
        if pos:
            try:
                fx, fy = float(pos[0]), float(pos[1])
            except Exception:
                fx, fy = 0.5, 0.5
            sc = float(p.get("pos_scale", 0.4))
            ow, oh = int(bw * sc), int(bh * sc)
            ox = max(0, min(bw - ow, int(fx * bw - ow / 2)))
            oy = max(0, min(bh - oh, int(fy * bh - oh / 2)))
            fc.append(f"[{idx}:v]scale={ow}:{oh}:flags=bicubic,setpts=PTS-STARTPTS+{t0:.3f}/TB[ov{idx}]")
            out_lbl = f"[c{idx}]"
            fc.append(f"{last_lbl}[ov{idx}]overlay={ox}:{oy}:enable='between(t,{t0:.3f},{t1:.3f})'{out_lbl}")
        else:
            fc.append(f"[{idx}:v]scale={bw}:{bh}:flags=bicubic,setpts=PTS-STARTPTS+{t0:.3f}/TB[ov{idx}]")
            out_lbl = f"[c{idx}]"
            fc.append(f"{last_lbl}[ov{idx}]overlay=0:0:enable='between(t,{t0:.3f},{t1:.3f})'{out_lbl}")
        last_lbl = out_lbl
    cmd = ["ffmpeg", "-y", *inputs,
           "-filter_complex", ";".join(fc),
           "-map", last_lbl, "-map", "0:a?",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "veryfast",
           "-c:a", "copy", str(out_mp4)]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
        if r.returncode != 0:
            log(f"ffmpeg lote falhou: {r.stderr[-400:]}")
            return False
    except Exception as e:
        log(f"erro ffmpeg lote: {e}")
        return False
    return out_mp4.exists() and out_mp4.stat().st_size > 0


def apply(in_mp4, out_mp4, picks):
    """Sobrepõe os overlays alpha no vídeo, EM LOTES (evita OOM do ffmpeg com muitos overlays).
    Áudio = copy. Retorna True/False."""
    in_mp4, out_mp4 = Path(in_mp4), Path(out_mp4)
    if not picks:
        log("sem transições elementais a aplicar")
        return False
    # resolução da base
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height", "-of", "csv=p=0:s=x", str(in_mp4)],
            capture_output=True, text=True, timeout=15)
        bw, bh = (int(x) for x in r.stdout.strip().split("x"))
    except Exception as e:
        log(f"não consegui medir base: {e}")
        return False

    LOTE = int(os.environ.get("ELEM_BATCH", "6"))  # overlays por passada (evita OOM)
    log(f"aplicando {len(picks)} transições em lotes de {LOTE}: " +
        ", ".join(f"{p['element']}@{p['t']:.1f}s" for p in picks[:12]) + (" ..." if len(picks) > 12 else ""))
    src = in_mp4
    tmps = []
    ok_any = False
    for i in range(0, len(picks), LOTE):
        lote = picks[i:i + LOTE]
        dst = out_mp4 if (i + LOTE >= len(picks)) else out_mp4.with_name(f"{out_mp4.stem}_lote{i}.mp4")
        if not _apply_lote(src, dst, lote, bw, bh):
            log(f"  ⚠ lote {i//LOTE} falhou — mantendo o que já foi aplicado")
            # se um lote falha, usa o src atual como saída final (o que já aplicou vale)
            if src != in_mp4 and src.exists():
                try:
                    src.replace(out_mp4)
                    ok_any = True
                except Exception:
                    pass
            break
        ok_any = True
        if src != in_mp4:
            tmps.append(src)
        src = dst
    # limpar temporários de lotes intermediários
    for t in tmps:
        try:
            Path(t).unlink()
        except Exception:
            pass
    return ok_any and out_mp4.exists() and out_mp4.stat().st_size > 0

