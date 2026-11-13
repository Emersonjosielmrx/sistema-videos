# -*- coding: utf-8 -*-
"""fx_detect.py — "QUE TIPO DE CENA É ESTE PAINEL?" + escolha de efeito/SFX.

Parte do motor de efeitos (ver mapa completo em effects_engine.py).
Lê a descrição do painel (e a fala) e decide o que aplicar.

  is_impact_panel / is_tension_panel / is_sensual_panel   classificam a cena
        por KEYWORDS (IMPACT_/TENSION_/SENSUAL_KEYWORDS).
  pick_sfx(categoria)         escolhe um SFX sem repetir o último (impact/
        transition/page_tear). Guarda estado em _last_sfx_used.
  get_transition_and_sfx      transição + SFX de base pra um corte.
  get_event_package           versão RICA: casa keywords de EVENT_PACKAGES
        (fogo/susto/rasgar/romântico...) -> transição + SFX + overlay + luma.
  overlay_for_mood / detect_mood_from_text / pick_luma_transition  overlay
        atmosférico e transição luma conforme o clima.

Não importa outro fx_* (fx_music depende DELE, não o contrário).
Mexa aqui pra: mudar quando entra shake/glitch/sfx, nova palavra-gatilho,
novo pacote de evento, ou trocar overlay por clima.
"""
import random
import subprocess
import os
import re
from pathlib import Path


IMPACT_KEYWORDS = [
    "soco", "punch", "chute", "kick", "explosão", "explosion", "impacto",
    "impact", "quebr", "smash", "crash", "bate", "hit", "golpe", "strike",
    "pow", "bang", "slam", "ataque", "attack", "destr", "sangue", "blood",
    "grito", "scream", "tiro", "shot", "cai", "fall", "queda", "drop",
    "esmaga", "crush", "rasga", "rip", "corta", "cut", "faca", "knife",
    "espada", "sword", "luta", "fight", "morre", "kill", "rage", "fúria",
]


def is_impact_panel(description: str) -> bool:
    """Detecta se o painel tem contexto de ação/impacto pela descrição do Claude."""
    if not description:
        return False
    desc_lower = description.lower()
    return any(kw in desc_lower for kw in IMPACT_KEYWORDS)


SFX_DIR = Path(__file__).parent.parent / "workspace" / "assets" / "sfx"


# Categorias de SFX por contexto
SFX_IMPACT = [
    "impact.wav", "bass_hit.wav", "snap.wav",
    "new_impact_1.wav", "new_impact_2.wav",
    "whoosh_heavy.wav", "punch.wav", "thud.wav",
    "reverse_impact.wav", "deep_boom.wav",
]


SFX_TRANSITION = [
    "woosh.wav", "page_turn.wav", "riser.wav",
    "new_transition_1.wav", "new_transition_2.wav",
    "slide.wav", "swoosh_light.wav", "magic_sparkle.wav",
    "cinema_whoosh.wav", "paper_slide.wav", "subtle_click.wav",
    "dramatic_riser.wav", "tension_string.wav",
]


SFX_PAGE_TEAR = [
    "page_tear_1.wav", "page_tear_2.wav",
]


_last_sfx_used = None  # Anti-repetição: nunca repetir o mesmo SFX consecutivo


def pick_sfx(sfx_category=None):
    """Escolhe um SFX aleatório de uma categoria específica (IMPACT, TRANSITION, PAGE_TEAR).
    Garante que nunca repete o mesmo SFX consecutivamente."""
    global _last_sfx_used
    pool = SFX_TRANSITION # Default
    if sfx_category == "impact":
        pool = SFX_IMPACT
    elif sfx_category == "page_tear":
        pool = SFX_PAGE_TEAR

    # Tenta escolher um SFX do pool específico (diferente do último usado)
    sfx_file = None
    if pool:
        candidates = [SFX_DIR / f for f in pool if (SFX_DIR / f).exists()]
        # Filtrar o último usado pra não repetir
        if _last_sfx_used and len(candidates) > 1:
            candidates = [c for c in candidates if str(c) != _last_sfx_used] or candidates
        if candidates:
            sfx_file = random.choice(candidates)

    # Fallback: qualquer SFX disponível se o pool específico falhou ou era vazio
    if not sfx_file:
        available = [f for f in SFX_DIR.glob("*.wav") if str(f) != _last_sfx_used]
        if not available:
            available = list(SFX_DIR.glob("*.wav"))
        if available:
            sfx_file = random.choice(available)

    if sfx_file:
        _last_sfx_used = str(sfx_file)

    return str(sfx_file) if sfx_file else None


# Tensão keywords (shake + glitch em momentos tensos, não só impacto)
TENSION_KEYWORDS = [
    "tensão", "tenso", "nervos", "medo", "assust", "choque", "revela",
    "segredo", "surpres", "descobre", "traição", "mentir", "ameaça",
    "confronto", "encurralad", "perigo", "desespero", "pânico", "furioso",
    "raiva", "ciúme", "obsess", "stalker", "persegu", "escuro", "sombr",
]


def is_tension_panel(description: str) -> bool:
    """Detecta se o painel tem tensão dramática."""
    if not description:
        return False
    desc_lower = description.lower()
    return any(kw in desc_lower for kw in TENSION_KEYWORDS)


# Reação no rosto (vira CLOSE no rosto — fx_parallax modo "close")
REACAO_KEYWORDS = [
    "surpres", "chocad", "choque", "assustad", "espant", "arregal", "olhos", "olhar", "expressão",
    "rosto", "sorri", "sorriso", "chora", "lágrima", "corad", "corou", "envergonh", "vergonha",
    "nervos", "suando", "suor", "confus", "perplex", "irritad", "raiva", "furios", "boquiabert",
    "incrédul", "pensativ", "sério", "encara", "piscou", "pisca", "careta", "?!", "!?", "o quê",
    "como assim", "hã", "hein",
]
# Deslocamento (personagem "anda" pela cena — modo "andar")
MOVIMENTO_KEYWORDS = [
    "andando", "anda ", "caminh", "corre", "correndo", "chega", "chegou", "entra", "entrou", "saindo",
    "sai ", "saiu", "passos", "segue", "seguindo", "aproxima", "vai embora", "volta", "voltando",
    "atravessa", "sobe", "desce", "rua", "corredor", "beco",
]
# Objeto em destaque (CLOSE no objeto quando o recorte acha uma coisa pequena e sem rosto)
OBJETO_KEYWORDS = [
    "celular", "telefone", "carta", "envelope", "foto", "dinheiro", "chave", "anel", "faca", "arma",
    "contrato", "documento", "cartão", "mensagem", "tela", "livro", "caixa", "presente", "garrafa",
    "copo", "cigarro", "relógio", "colar", "bolsa", "mala", "papel", "bilhete", "cheque",
    "espada", "lâmina", "katana", "adaga", "punhal", "machado", "escudo", "pistola", "revólver",
    "cristal", "amuleto", "pergaminho", "medalh", "coroa", "joia", "jóia", "pedra", "câmera", "máquina",
    "poção", "frasco", "sangue", "ferida", "cicatriz", "tatuagem", "símbolo", "emblema", "mapa",
    "lança", "arco", "flecha", "bastão", "cajado", "cetro", "luva", "máscara", "capacete",
]
# Poder/energia em destaque (CLOSE na mancha colorida e clara do golpe/magia — fx_parallax.brilho_principal).
# Palavra inteira: "poder" casaria com "poderia", "chama" com "chamar", "aura" com "restaurante".
PODER_RE = re.compile(r"\b(poderes|energia|magia|mágic\w*|feitiç\w*|aura|raios?|relâmpagos?|trovão|fogo|"
                      r"chamas|explos\w*|habilidades?|golpes?|rajadas?|esferas?|portal|mana|"
                      r"barreira|maldição|selo|invocaç\w*|vórtice|escuridão)\b")


def _tem(texto, palavras):
    t = (texto or "").lower()
    return any(kw in t for kw in palavras)


def is_reacao_panel(description: str, texto: str = "") -> bool:
    """Painel de reação (expressão/emoção no rosto) pela descrição da visão ou pela fala."""
    return _tem(f"{description} {texto}", REACAO_KEYWORDS)


def is_movimento_panel(description: str, texto: str = "") -> bool:
    """Personagem se deslocando na cena."""
    return _tem(f"{description} {texto}", MOVIMENTO_KEYWORDS)


def is_objeto_panel(description: str, texto: str = "") -> bool:
    """Objeto importante em destaque."""
    return _tem(f"{description} {texto}", OBJETO_KEYWORDS)


def is_poder_panel(description: str, texto: str = "") -> bool:
    """Poder, magia ou energia em destaque."""
    return bool(PODER_RE.search(f"{description} {texto}".lower()))


# Sensual/+18 keywords. "cena intensa"/"intensa" é o marcador deixado pela
# sanitização da visão quando o painel tinha conteúdo adulto explícito.
SENSUAL_KEYWORDS = [
    "cena intensa", "intensa", "beijo", "beij", "abraç", "carícia", "caric",
    "toque", "toca", "sedut", "seduz", "sensual", "provocan", "provoca",
    "desejo", "tesão", "paixão", "íntim", "intim", "corpo", "pele",
    "quente", "ofegant", "suspiro", "gemid", "cama", "lençol", "nu ",
    "deitad", "abraçad", "colo", "peito", "coxa", "cintura", "vermelh",
    "nervos", "tímid", "noona", "amante", "romance", "romântic",
]

NSFW_KEYWORDS = [
    "cena intensa", "transava", "transar", "gemid", "ofegant",
    "nudez", "pelad", "nua", "nu ", "sem roupa", "corpo expost",
    "seio", "seios", "peito expost", "lingerie", "calcinha", "sutiã",
    "sexu", "eroti", "excitad", "orgasm", "prazer carnal",
    "seduz", "sedut", "carícia", "caric", "lençol", "cama ",
    "tesão", "desejo carnal", "amante",
]


def is_sensual_panel(description: str = "", text: str = "") -> bool:
    """Detecta momentos sensuais/+18 (pra aplicar voz sensual no TTS).

    Olha tanto a descrição visual (sanitizada -> 'cena intensa') quanto o texto
    da narração, que costuma ter as pistas românticas/provocantes.
    """
    blob = f"{description} {text}".lower()
    if not blob.strip():
        return False
    return any(kw in blob for kw in SENSUAL_KEYWORDS)


def is_nsfw_panel(description: str = "", text: str = "") -> bool:
    """Reserva por TEXTO da detecção +18 (só quando Sightengine/NudeNet faltam — a censura
    principal é por visão, em censura_visual.py).

    "Cena intensa" na descrição é marca da sanitização do Gemini — o original era +18.
    Para o texto, exige 2+ keywords para distinguir romance leve de cena sexual.
    """
    desc = (description or "").lower()
    txt = (text or "").lower()
    if "cena intensa" in desc:
        return True
    hits = sum(1 for kw in NSFW_KEYWORDS if kw in f"{desc} {txt}")
    return hits >= 2


PROPAGANDA_KEYWORDS = ["promocional", "lançamento antecipado", "lancamento antecipado", "acesso antecipado",
                       "lançado primeiro", "lancado primeiro", "leia primeiro", "blackout", "discord",
                       "link está no site", "site oficial", "grupo de scan", "scanlator"]


def is_propaganda(description: str = "", text: str = "") -> bool:
    """Painel de propaganda/créditos do grupo de scan NO MEIO do capítulo (a visão transcreve o texto
    da página). Sem isso a narração "dubla" o anúncio ("o link está no site oficial")."""
    blob = f"{description} {text}".lower()
    return any(k in blob for k in PROPAGANDA_KEYWORDS)


MEMES_DIR = SFX_DIR.parent / "sfx_memes"
_memes = None


def pick_meme(categoria="comedia"):
    """Um áudio de meme da categoria (índice assets/sfx_memes_categorized.json), ou None."""
    global _memes
    if _memes is None:
        import json
        try:
            idx = json.loads((SFX_DIR.parent / "sfx_memes_categorized.json").read_text(encoding="utf-8"))
            _memes = {}
            for nome, cat in idx.get("files", {}).items():
                if (MEMES_DIR / nome).exists():
                    _memes.setdefault(cat, []).append(MEMES_DIR / nome)
        except (OSError, ValueError):
            _memes = {}
    lista = _memes.get(categoria) or []
    return str(random.choice(lista)) if lista else None


def get_transition_and_sfx(panel_idx, descriptions):
    """Determina o tipo de transição e o SFX para um painel específico.

    Transições FREQUENTES e VARIADAS (estilo Shorts) — quase todo corte tem efeito:
    - impacto -> flash vermelho / branco / zoom punch / whip + SFX de impacto
    - tensão  -> glitch / blur-in / fade preto / rasgar página / rebobinar + SFX de transição
    - normal  -> variedade (fade/blur/pixel/whip/flash) + uns cortes secos + SFX de transição
    """
    if panel_idx == 0:
        return None, None

    desc = descriptions[panel_idx] if panel_idx < len(descriptions) else ""
    impact = is_impact_panel(desc)
    tension = is_tension_panel(desc)

    transition_type = None
    sfx_category = "transition" # default
    sfx_file = None

    if impact:
        transition_type = random.choice(["flashred", "flash", "flashgold", "zoomin", "whip", "glitch", "punch", "snap"])
        sfx_category = "impact"
    elif tension:
        # Adiciona o efeito 'rasgar página' ou 'rebobinar' ou transições normais
        r_val = random.random()
        if r_val < 0.25:
            transition_type = "pagetear"
            sfx_category = "page_tear"
        elif r_val < 0.50:
            transition_type = "rewind"
            sfx_file = str(SFX_DIR / "rezero_rewind.wav")
        else:
            transition_type = random.choice(["glitch", "blurin", "fade", "flashblue", "zoomin", "snap"])
            sfx_category = "transition"
    else:
        # variedade pros cortes normais; ~2/8 ficam corte seco pra dar respiro
        if random.random() < 0.25: # 25% de chance de corte seco
            transition_type = None # Corte seco
            sfx_category = None # Sem SFX para corte seco
        else:
            transition_type = random.choice([
                "fade", "dissolve", "wipeleft", "wiperight", "slideleft", "slideright",
                "pixelize", "zoomin", "squeezeh", "squeezev", "fadefast", "fadeslow", "snap"
            ])
            sfx_category = "transition"

    if sfx_file is None:
        sfx_file = pick_sfx(sfx_category)

    return transition_type, sfx_file


# (palavras, {luma, overlay, transition, sfx_category})
#   luma:       True -> usa um transition_*.mp4 (fumaça/fogo) no corte
#   overlay:    nome do overlay atmosférico (clip inteiro) ou None
#   transition: efeito procedural no corte (do SIMPLE/SPLIT_TRANS) ou None
#   sfx:        categoria de SFX (impact/transition/page_tear)
EVENT_PACKAGES = [
    ("tensao", {
        # Expressões idiomáticas de tensão — ANTES de "rasgar" (que tem "corta"/"faca"
        # genéricos), pra "cortar com uma faca" não virar rasgar literal.
        "kws": ["cortar com uma faca", "cortar com faca", "pesado que chumbo",
                "tensão é palpável", "ar ficou pesado", "clima denso",
                "tensão no ar", "silêncio sepulcral", "dá para cortar"],
        "luma": False, "overlay": "sparks", "transition": "blurin", "sfx": "transition",
    }),
    ("fogo", {
        "kws": ["pegou fogo", "pega fogo", "incêndio", "incendi", "chama",
                "calor infernal", "brasa", "em chamas", "queima", "ardend",
                "fervendo", "ferver", "explos"],
        "luma": True, "overlay": "sparks", "transition": "flashgold", "sfx": "impact",
    }),
    ("susto", {
        "kws": ["susto", "choque", "arregal", "tremble", "tremor", "treme",
                "pânico", "pavor", "gasp", "espant", "assust", "gritando",
                "grito", "grita", "desespero", "em choque"],
        "luma": False, "overlay": None, "transition": "punch", "sfx": "impact",
    }),
    ("eletrico", {
        "kws": ["pop!", "bzzzt", "curto-circuito", "luzes piscam", "piscando",
                "elétric", "eletrôni", "static", "glitch", "tela treme"],
        "luma": False, "overlay": None, "transition": "glitch", "sfx": "transition",
    }),
    ("romantico", {
        "kws": ["pétala", "petala", "cerejeira", "romântic", "romantic", "beijo",
                "coração dispar", "paixão", "carinho", "abraço"],
        "luma": False, "overlay": "petals", "transition": "dissolve", "sfx": "transition",
    }),
    ("rasgar", {
        # Genérico de corte físico — por último entre os de ação.
        "kws": ["rasga", "rip", "rasgar", "despeda", "fatia", "lâmina",
                "shatter", "estilha", "corta a tela", "corta a página"],
        "luma": True, "overlay": None, "transition": "pagetear", "sfx": "page_tear",
    }),
]


def get_event_package(panel_idx, descriptions, texts=None):
    """Decide o pacote de efeitos do painel: (transition_type, sfx_file, overlay_video, luma_video).

    Procura uma situação específica (fogo/susto/rasgar/...) nas keywords da descrição
    + locução. Se nenhuma casar, delega ao get_transition_and_sfx atual (comportamento
    de base preservado) e sem overlay/luma.
    """
    if panel_idx == 0:
        return None, None, None, None

    desc = descriptions[panel_idx] if panel_idx < len(descriptions) else ""
    text = ""
    if texts and panel_idx < len(texts):
        text = texts[panel_idx] or ""
    blob = f"{desc} {text}".lower()

    for _name, pkg in EVENT_PACKAGES:
        if any(kw in blob for kw in pkg["kws"]):
            transition_type = pkg["transition"]
            sfx_file = pick_sfx(pkg["sfx"])
            overlay_video = _overlay_path(pkg["overlay"]) if pkg["overlay"] else None
            luma_video = pick_luma_transition() if pkg["luma"] else None
            return transition_type, sfx_file, overlay_video, luma_video

    # Nenhum evento específico -> comportamento de base + overlay por mood
    transition_type, sfx_file = get_transition_and_sfx(panel_idx, descriptions)
    mood = detect_mood_from_text(blob)
    overlay_video = overlay_for_mood(mood)
    return transition_type, sfx_file, overlay_video, None


OVERLAYS_DIR = Path(__file__).parent.parent / "workspace" / "assets" / "overlays"


# Versões pré-escaladas pra 720x1280 (geradas uma vez; remove o scale por frame).
OVERLAYS_720_DIR = OVERLAYS_DIR / "scaled720"


LUMA_TRANS_DIR = OVERLAYS_DIR / "transitions" / "scaled720"


# mood -> overlay (partícula que combina com o clima)
MOOD_OVERLAY = {
    "sad_emotional": "rain",
    "romantic_sexy": "petals",
    "tense_dramatic": "sparks",
    "calm_chill": "snow",
}


def _overlay_path(name):
    """Caminho do overlay atmosférico (prefere a versão pré-escalada 720p)."""
    if not name:
        return None
    scaled = OVERLAYS_720_DIR / f"{name}.mp4"
    if scaled.exists():
        return scaled
    orig = OVERLAYS_DIR / f"{name}.mp4"
    return orig if orig.exists() else None


def overlay_for_mood(mood, chance=0.5):
    """Retorna o caminho do overlay atmosférico que combina com o mood, ou None.

    REATIVADO: o bug de cor roxa era do blend rodar nos planos de croma U/V (YUV).
    Agora `_append_overlay` blenda em RGB (gbrp), preservando a cor do painel.
    """
    name = MOOD_OVERLAY.get(mood)
    if not name or random.random() > chance:
        return None
    return _overlay_path(name)


def pick_luma_transition():
    """Escolhe um vídeo de luma de transição (fumaça/fogo crescendo) aleatório."""
    if not LUMA_TRANS_DIR.exists():
        return None
    candidates = sorted(LUMA_TRANS_DIR.glob("transition_*.mp4"))
    return random.choice(candidates) if candidates else None


def detect_mood_from_text(text):
    """Detecta o mood/clima dominante de um texto usando keywords."""
    text_lower = text.lower()

    # Contagem de keywords por mood
    mood_scores = {
        "tense_dramatic": 0,
        "sad_emotional": 0,
        "romantic_sexy": 0,
        "funny_lighthearted": 0,
        "calm_chill": 0,
        "neutral_chill": 0,
    }

    keywords = {
        "tense_dramatic": ["luta", "batalha", "ataque", "medo", "terror", "perigo",
                          "tensão", "tenso", "choque", "explosão", "morte", "sangue",
                          "grita", "foge", "corre", "persegu"],
        "sad_emotional": ["chora", "lágrima", "triste", "dor", "sofr", "angúst",
                         "perdeu", "morreu", "saudade", "solidão", "abandonad"],
        "romantic_sexy": ["amor", "beijo", "abraço", "coração", "paixão", "seduz",
                         "provocan", "sensual", "carinho", "intens", "quente",
                         "vermelho", "nervoso", "tímid", "noona"],
        "funny_lighthearted": ["rir", "risada", "engraçad", "piada", "humor",
                              "fofinho", "bobo", "zueira", "brincadeir", "idiota"],
        "calm_chill": ["calmo", "paz", "tranquil", "sereno", "suave", "gentil",
                      "silêncio", "descansa", "dormi"],
    }

    for mood, words in keywords.items():
        for word in words:
            if word in text_lower:
                mood_scores[mood] += 1

    # Retornar o mood com maior score (ou neutral se nenhum detectado)
    best = max(mood_scores, key=mood_scores.get)
    if mood_scores[best] == 0:
        return "neutral_chill"
    return best

