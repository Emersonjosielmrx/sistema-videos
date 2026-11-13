# COMUM — fonte única: D:\hipercool-materiais\comum\contextual_motion.py. Mudou esta cópia? python D:\hipercool-materiais\bin\recursos.py subir contextual_motion.py --de <projeto>
"""contextual_motion.py — movimento do painel dirigido pela EMOÇÃO da narração (T7).

Porte do CONTEXTUAL_PATTERNS + EFFECT_TYPE_MAP do fluxo n8n "3-cria video pequeno".
O n8n é 16:9; aqui NÃO se porta a filter-string, só a LÓGICA: texto → effectType → preferência
de movimento (speed/shake). O effects_engine já tem MOVEMENTS por 'speed' e build_clip_with_shake;
este módulo só DECIDE qual perfil de movimento combina com o tom da fala.

Uso: detect_context(text) → effectType; motion_pref(effectType) → dict {speed, shake, zoom}.
Flag de uso no caller: CONTEXT_MOTION=1. Anti-repetição fica no caller (pick_movement já tem).
"""
import re

# 15 padrões (regex PT) → effectType. forceEffect: True = sempre aplica; ordem importa
# (mais específico/intenso primeiro). Portado do CONTEXTUAL_PATTERNS do n8n.
CONTEXTUAL_PATTERNS = [
    ("action_heavy",  r"explos|destruiç|destruic|estrondo|violent|crash|desaba|terremoto|tremor|impacto forte|colisão|colisao", "shake_heavy"),
    ("action_medium", r"soco|chute|golpe|impacto|\bbam\b|\bpow\b|batida|choque|murro|pancada|esmaga", "shake_medium"),
    ("action_light",  r"tombo|\bcai\b|tropeç|tropec|escorrega|empurr|trombada", "shake_light"),
    ("battle",        r"batalha|combate|guerra|duelo|enfrentamento|luta final|confronto", "vertical_fast"),
    ("speed",         r"corre|foge|rápido|rapido|veloz|escapar|persegu|corrida|velocidade|sprint|disparada", "vertical_fast"),
    ("suspense",      r"medo|terror|surpresa|choque|assustad|grito|perigo|ameaç|ameac|tenso|apreensiv", "zoom_suspense"),
    ("dramatic",      r"revelaç|revelac|verdade|descoberta|segredo|confiss|admite|revela|descobr", "zoom_delay"),
    ("romance",       r"amor|beijo|abraç|abrac|carinho|coração|coracao|paixão|paixao|romântic|romantic|ternura|apaixon|crush", "soft_float"),
    ("tension",       r"nervos|ansios|preocupad|inquiet|pressão|pressao|estress|aflit", "breathing_heavy"),
    ("memory",        r"lembr|passado|flashback|memória|memoria|antigamente|recordar|nostalgia", "breathing"),
    ("mystery",       r"mistério|misterio|enigma|suspeit|investigaç|investigac|pista|intriga", "kenburns_drift"),
    ("calm",          r"calmo|\bpaz\b|tranquil|seren|silêncio|silencio|quiet|relaxad|pacífic|pacific", "vertical_glacial"),
    ("reading_slow",  r"leitura|texto|carta|papel|documento|livro|\blê\b|\bler\b|escrito|bilhete", "vertical_slow"),
    ("dialogue_calm", r"conversa|\bfala\b|\bdiz\b|responde|pergunta|comenta|explica|conta|relata", "vertical_medium"),
]

# effectType → preferência de movimento NO NOSSO formato.
#   speed: casa com o atributo 'speed' dos MOVEMENTS (ultra_slow|slow|medium|fast)
#   shake: 0 nenhum | 1 leve | 2 médio | 3 pesado (usa build_clip_with_shake)
#   zoom: True = prefere movimento de zoom (facial/dramático)
EFFECT_MOTION = {
    "shake_heavy":   {"speed": "fast",       "shake": 3, "zoom": False},
    "shake_medium":  {"speed": "medium",     "shake": 2, "zoom": False},
    "shake_light":   {"speed": "medium",     "shake": 1, "zoom": False},
    "vertical_fast": {"speed": "fast",       "shake": 0, "zoom": False},
    "vertical_medium":{"speed": "medium",    "shake": 0, "zoom": False},
    "vertical_slow": {"speed": "slow",       "shake": 0, "zoom": False},
    "vertical_glacial":{"speed": "ultra_slow","shake": 0, "zoom": False},
    "zoom_suspense": {"speed": "slow",       "shake": 0, "zoom": True},
    "zoom_delay":    {"speed": "slow",       "shake": 0, "zoom": True},
    "soft_float":    {"speed": "ultra_slow", "shake": 0, "zoom": True},
    "breathing":     {"speed": "ultra_slow", "shake": 0, "zoom": True},
    "breathing_heavy":{"speed": "medium",    "shake": 1, "zoom": False},
    "kenburns_drift":{"speed": "slow",       "shake": 0, "zoom": True},
}

_DEFAULT = {"speed": "medium", "shake": 0, "zoom": False}


def detect_context(text):
    """Retorna effectType pelo tom da narração, ou None (sem match → movimento livre)."""
    t = (text or "").lower()
    if not t.strip():
        return None
    for _name, rgx, eff in CONTEXTUAL_PATTERNS:
        if re.search(rgx, t):
            return eff
    return None


def motion_pref(text):
    """Texto → dict de preferência de movimento {speed, shake, zoom, effect}. None se sem match."""
    eff = detect_context(text)
    if eff is None:
        return None
    pref = dict(EFFECT_MOTION.get(eff, _DEFAULT))
    pref["effect"] = eff
    return pref
