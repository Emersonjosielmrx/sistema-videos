# -*- coding: utf-8 -*-
"""character_bank.py — Banco de personagens recorrentes por gênero.

Mantém descrições visuais fixas pra injetar nos prompts de imagem,
garantindo coerência visual entre cenas da mesma história.
"""
import json
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
BANK_DIR = PROJECT_DIR / "workspace" / "character_bank"
BANK_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_BANK = {
    "superacao": [
        {
            "id": "protagonista_m",
            "nome": "Lucas",
            "aparencia": "Homem jovem brasileiro, pele morena, cabelo preto curto, olhos castanhos determinados, estrutura magra mas forte",
            "roupa_padrao": "Camiseta simples branca, calça jeans surrada, tênis gasto",
            "roupa_sucesso": "Terno azul marinho bem cortado, gravata, sapato social",
            "estilo": "realismo cinematográfico com iluminação dramática",
        },
        {
            "id": "protagonista_f",
            "nome": "Ana",
            "aparencia": "Mulher jovem brasileira, pele parda, cabelo cacheado longo escuro, olhos expressivos, sorriso forte",
            "roupa_padrao": "Vestido simples floral, chinelo havaianas",
            "roupa_sucesso": "Jaleco branco de médica, estetoscópio, cabelo preso",
            "estilo": "realismo cinematográfico com iluminação dramática",
        },
    ],
    "terror": [
        {
            "id": "vitima",
            "nome": "Miguel",
            "aparencia": "Homem 25-30 anos, pele clara, cabelo castanho bagunçado, olhar assustado, suor no rosto",
            "roupa_padrao": "Moletom cinza escuro com capuz, calça de moletom, descalço",
            "estilo": "horror cinematográfico, sombras pesadas, granulado, tons frios",
        },
        {
            "id": "entidade",
            "nome": "A Sombra",
            "aparencia": "Figura humanóide alongada completamente preta, sem rosto definido, olhos como duas fendas brancas brilhantes, dedos longos e afilados",
            "roupa_padrao": "Nenhuma - é feita de escuridão pura, bordas dissolvendo em fumaça negra",
            "estilo": "horror cinematográfico, contraste extremo, silhueta contra luz fraca",
        },
    ],
    "misterio": [
        {
            "id": "detetive",
            "nome": "Rafael",
            "aparencia": "Homem 40 anos, barba por fazer, olheiras, cabelo grisalho nas têmporas, olhar penetrante e cansado",
            "roupa_padrao": "Camisa social amassada com mangas arregaçadas, colete, calça social escura",
            "estilo": "noir moderno, iluminação lateral, tons dessaturados com acentos âmbar",
        },
    ],
    "motivacional": [
        {
            "id": "mentor",
            "nome": "O Sábio",
            "aparencia": "Homem idoso com barba branca longa, pele enrugada mas olhos brilhantes e joviais, postura ereta",
            "roupa_padrao": "Túnica simples bege, sandálias de couro, cajado de madeira",
            "estilo": "ilustração épica dourada, raios de luz, composição inspiradora",
        },
    ],
    "curiosidades": [
        {
            "id": "narrador_visual",
            "nome": "Apresentador",
            "aparencia": "Não aparece - apenas cenários e objetos ilustrativos",
            "roupa_padrao": "N/A",
            "estilo": "infográfico cinematográfico, cores vibrantes, composição limpa e impactante",
        },
    ],
    "religioso": [
        {
            "id": "protagonista_biblico",
            "nome": "O Jovem",
            "aparencia": "Homem jovem do oriente médio antigo, pele oliveira, cabelo escuro ondulado até os ombros, barba curta, olhos bondosos",
            "roupa_padrao": "Túnica branca com faixa marrom na cintura, sandálias, manto bege sobre ombro",
            "estilo": "pintura épica bíblica, iluminação divina dourada, composição renascentista",
        },
    ],
}


def get_characters(genero, custom_file=None):
    """Retorna lista de personagens pro gênero. Prioriza arquivo custom se existir."""
    custom = BANK_DIR / f"{genero}.json"
    if custom.exists():
        return json.loads(custom.read_text(encoding="utf-8"))
    if custom_file and Path(custom_file).exists():
        return json.loads(Path(custom_file).read_text(encoding="utf-8"))
    return DEFAULT_BANK.get(genero, [])


def get_character_prompt(genero, char_id, scene_context=""):
    """Retorna string de prompt visual pra um personagem específico."""
    chars = get_characters(genero)
    for c in chars:
        if c["id"] == char_id:
            roupa = c.get("roupa_padrao", "")
            if "sucesso" in scene_context.lower() and c.get("roupa_sucesso"):
                roupa = c["roupa_sucesso"]
            return f"{c['aparencia']}. Wearing: {roupa}. Art style: {c['estilo']}"
    return ""


GENRE_STYLES = {
    "superacao": {
        "style": "warm golden hour cinematic lighting, vibrant saturated colors, lens flare, inspirational composition, shallow depth of field, professional photography",
        "negative": "dark, horror, desaturated, cold tones, blood, gore",
    },
    "terror": {
        "style": "dark cinematic horror, high contrast, desaturated cold tones, film grain, deep harsh shadows, fog, unsettling composition, found footage aesthetic",
        "negative": "bright, colorful, happy, cartoon, cute, warm colors",
    },
    "misterio": {
        "style": "neo-noir lighting, blue-teal color grading, volumetric fog, dramatic silhouettes, rain-slicked surfaces, moody atmospheric perspective",
        "negative": "bright, warm, cheerful, saturated, cartoon",
    },
    "motivacional": {
        "style": "bright clean modern studio lighting, uplifting composition, crisp focus, inspirational golden tones, minimalist elegant background",
        "negative": "dark, horror, cluttered, dirty, chaotic",
    },
    "curiosidades": {
        "style": "vibrant infographic style, clean composition, bold colors, modern flat design with depth, professional editorial photography",
        "negative": "dark, horror, people, characters, faces",
    },
    "religioso": {
        "style": "ethereal divine light rays, warm golden glow, renaissance painting composition, volumetric god rays, sacred atmosphere, oil painting texture",
        "negative": "modern, technology, dark horror, neon, cyberpunk",
    },
    "romance": {
        "style": "soft dreamy focus, pastel warm tones, bokeh background, intimate framing, golden hour skin tones, romantic atmosphere, film photography aesthetic",
        "negative": "horror, dark, cold, violent, blood, harsh lighting",
    },
    "comedia": {
        "style": "bright saturated colors, slightly exaggerated proportions, expressive dynamic poses, clean sharp rendering, cheerful warm lighting, cartoon-influenced realism",
        "negative": "dark, horror, realistic gore, muted, desaturated",
    },
    "drama": {
        "style": "cinematic anamorphic lens look, naturalistic lighting, earth tones with selective color, emotional close-ups, shallow depth of field, film grain",
        "negative": "cartoon, bright neon, fantasy, unrealistic, flat",
    },
    "fantasia": {
        "style": "epic fantasy digital art, magical particle effects, volumetric lighting, rich jewel tones, otherworldly atmosphere, concept art quality, detailed environments",
        "negative": "modern, realistic, urban, office, mundane, photography",
    },
}


def get_style_for_genre(genero, serie_id=None):
    """Retorna o estilo artístico padrão do gênero. Checa override de serie primeiro."""
    # Prioridade: serie override > genero default
    if serie_id:
        series_style = get_style_for_series(serie_id, genero)
        if series_style:
            return series_style

    gs = GENRE_STYLES.get(genero)
    if gs:
        return gs["style"]
    chars = get_characters(genero)
    if chars:
        return chars[0].get("estilo", "cinematic anime illustration")
    return "cinematic anime illustration"


def get_negative_prompt(genero):
    """Retorna negative prompt pro gênero (o que evitar na geração)."""
    gs = GENRE_STYLES.get(genero)
    if gs:
        return gs["negative"]
    return ""


# ─── ESTILOS VISUAIS POR SERIE ───────────────────────────────────────────────

SERIES_STYLES_FILE = BANK_DIR / "series_styles.json"


def _load_series_styles():
    """Carrega estilos customizados de series."""
    if SERIES_STYLES_FILE.exists():
        try:
            return json.loads(SERIES_STYLES_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save_series_styles(styles):
    """Salva estilos de series no JSON."""
    SERIES_STYLES_FILE.parent.mkdir(parents=True, exist_ok=True)
    SERIES_STYLES_FILE.write_text(
        json.dumps(styles, ensure_ascii=False, indent=2), encoding="utf-8")


def register_series_style(serie_id, style_override):
    """Registra um estilo visual customizado pra uma serie especifica.

    Args:
        serie_id: identificador unico da serie (ex: "o-ultimo-guerreiro")
        style_override: dict com campos opcionais:
            - style: prompt de estilo (substitui genero default)
            - negative: negative prompt override
            - color_palette: cores dominantes da serie
            - characters: lista de personagens customizados
            - notes: observacoes do criador

    Returns:
        dict salvo
    """
    styles = _load_series_styles()
    styles[serie_id] = {
        **(styles.get(serie_id) or {}),
        **style_override,
        "updated_at": __import__("datetime").datetime.now().isoformat(),
    }
    _save_series_styles(styles)
    return styles[serie_id]


def get_style_for_series(serie_id, genero=None):
    """Busca estilo visual customizado de uma serie.

    Retorna o style override da serie se existir, senao None (fallback pro genero).

    Args:
        serie_id: identificador da serie
        genero: genero fallback (nao usado se serie tem override)

    Returns:
        str com prompt de estilo ou None
    """
    styles = _load_series_styles()
    serie_data = styles.get(serie_id)
    if serie_data and serie_data.get("style"):
        return serie_data["style"]
    return None


def get_series_negative(serie_id, genero=None):
    """Busca negative prompt customizado de uma serie."""
    styles = _load_series_styles()
    serie_data = styles.get(serie_id)
    if serie_data and serie_data.get("negative"):
        return serie_data["negative"]
    # Fallback pro genero
    if genero:
        return get_negative_prompt(genero)
    return ""


def list_series_styles():
    """Lista todas as series com estilos customizados."""
    return _load_series_styles()


def save_custom_bank(genero, characters):
    """Salva banco customizado pra um gênero."""
    out = BANK_DIR / f"{genero}.json"
    out.write_text(json.dumps(characters, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


# ─── CONSISTÊNCIA DE PERSONAGEM ─────────────────────────────────────────────

def character_seed(name):
    """Gera seed numérica determinística a partir do nome do personagem."""
    import hashlib
    h = hashlib.md5(name.lower().strip().encode()).hexdigest()
    return int(h[:8], 16) % 2147483647


def build_consistency_block(genero, personagens_na_cena=None):
    """Monta bloco de prompt pra manter consistência visual entre cenas.

    Args:
        genero: gênero da história
        personagens_na_cena: lista de nomes de personagens que aparecem

    Returns:
        str com instruções de consistência pra injetar no prompt
    """
    chars = get_characters(genero)
    if not chars or not personagens_na_cena:
        return ""

    blocks = []
    for name in personagens_na_cena:
        name_lower = name.lower().strip()
        for c in chars:
            if c["nome"].lower() in name_lower or name_lower in c["nome"].lower():
                blocks.append(
                    f"Character '{c['nome']}': {c['aparencia']}. "
                    f"Wearing: {c.get('roupa_padrao', '')}. "
                    f"MUST maintain exact same appearance across all scenes."
                )
                break

    if not blocks:
        return ""
    return "VISUAL CONSISTENCY REQUIRED: " + " | ".join(blocks)

