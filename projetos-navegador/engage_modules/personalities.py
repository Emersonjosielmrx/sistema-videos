"""
personalities.py — Personalidades de comentário por conta.

Cada conta ganha um "perfil" de escrita persistente baseado no hash
do email, com variações de estilo: casual, entusiasta, técnico,
minimalista, questionador, storyteller.
"""
import hashlib

PERSONALITIES = {
    "casual": {
        "style": "fala de boa, descontraído, usa gírias leves",
        "emoji_freq": 0.6,
        "avg_length": "curto",
        "prefixes": ["mano ", "cara ", "opa ", "eita ", ""],
        "suffixes": [" haha", " kkk", " rs", " 😄", ""],
    },
    "entusiasta": {
        "style": "super animado, usa caps e exclamações, tudo é incrível",
        "emoji_freq": 0.8,
        "avg_length": "médio",
        "prefixes": ["QUE ", "MUITO ", "SIM! ", "CARAMBA ", ""],
        "suffixes": ["!!!", "!! 🔥", "! top demais", "! sensacional", "!"],
    },
    "tecnico": {
        "style": "analítico, foca em detalhes técnicos, menos emocional",
        "emoji_freq": 0.15,
        "avg_length": "médio-longo",
        "prefixes": ["interessante, ", "bom ponto — ", "vale notar que ", ""],
        "suffixes": [".", ". boa!", ". faz sentido.", ""],
    },
    "minimalista": {
        "style": "poucas palavras, direto ao ponto, sem enrolação",
        "emoji_freq": 0.3,
        "avg_length": "curto",
        "prefixes": [""],
        "suffixes": [" 👍", ".", " top", ""],
    },
    "questionador": {
        "style": "sempre faz perguntas, demonstra curiosidade",
        "emoji_freq": 0.25,
        "avg_length": "médio",
        "prefixes": ["será que ", "como ", "por que ", "e se ", ""],
        "suffixes": ["?", "? 🤔", "? quero saber!", "?"],
    },
    "storyteller": {
        "style": "conta experiência própria, conecta o vídeo com a vida real",
        "emoji_freq": 0.4,
        "avg_length": "longo",
        "prefixes": ["lembrei que ", "isso me faz pensar em ", "uma vez ", ""],
        "suffixes": [" — e é por isso que esse vídeo é tão bom", " 🙏", ""],
    },
}

PERSONALITY_NAMES = list(PERSONALITIES.keys())


def get_personality(account: str) -> dict:
    """Retorna personalidade persistente pra uma conta (baseada no hash)."""
    h = hashlib.md5(account.encode()).hexdigest()
    idx = int(h[:4], 16) % len(PERSONALITY_NAMES)
    name = PERSONALITY_NAMES[idx]
    return {"name": name, **PERSONALITIES[name]}


def get_personality_prompt(account: str) -> str:
    """Retorna instrução de estilo pra incluir no prompt do smart_comments."""
    p = get_personality(account)
    return (
        f"ESTILO DE ESCRITA: {p['style']}. "
        f"Tom: {p['name']}. "
        f"Tamanho preferido: {p['avg_length']}. "
        f"{'Use emoji quando fizer sentido.' if p['emoji_freq'] > 0.4 else 'Evite emojis.'}"
    )
