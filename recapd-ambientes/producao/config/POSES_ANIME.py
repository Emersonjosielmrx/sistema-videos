# -*- coding: utf-8 -*-
"""POSES_ANIME.py — Catálogo de poses de AÇÃO/BATALHA para capas de anime recap.

Diferente do manhwa (sensual/harém), anime recap usa poses ÉPICAS de batalha, magia, confronto.
Cada pose retorna (min_personagens, prompt_en).
"""

# Poses principais — AÇÃO/BATALHA (adequadas para shonen/seinen)
POSES = {
    "espada_ar": (1, "HE swings a massive glowing sword in a dynamic mid-air action pose, a huge energy slash "
                     "trail cutting across the frame, debris and sparks flying around, fierce determined "
                     "expression, wind blowing his hair and coat; epic battle scene"),

    "contra_monstro": (1, "HE stands in heroic battle stance in the foreground while a gigantic monster with "
                          "glowing eyes towers over him from behind, dramatic scale contrast, dust and wind "
                          "effects, backlit silhouette; epic confrontation"),

    "magia_poderosa": (1, "HE casts an enormous glowing magic spell with both hands raised, swirling energy "
                          "runes and light circles around him, his hair and coat blown by the magical energy, "
                          "confident determined expression, ground cracking beneath"),

    "duelo_espadas": (1, "HE clashes blades with a shadowy rival in mid-air, massive sparks exploding between "
                         "the crossed swords, intense eye contact, speed lines radiating from the impact point, "
                         "dynamic diagonal composition"),

    "despertar_poder": (1, "HE awakens a massive glowing aura of power, eyes glowing bright, energy cracks "
                           "spreading in the ground around him, swirling geometric energy patterns and light "
                           "particles surrounding him, shocked/determined expression"),

    "esquiva_explosao": (1, "HE dodges in mid-air away from a massive explosion behind him, dynamic twisted "
                            "body pose, debris and fire in the background, intense focused expression, motion "
                            "blur on the edges"),

    "golpe_final": (1, "HE charges forward with a glowing fist pulled back ready to strike, energy trailing "
                       "from his body, dramatic low-angle perspective making him look powerful, speed lines "
                       "converging on the fist"),

    "dupla_batalha": (2, "HE and SHE stand back-to-back surrounded by enemies' shadows, both with weapons "
                         "drawn (he with sword, she with dual daggers), confident battle-ready expressions, "
                         "wind and dust swirling around; epic team battle"),

    "confronto_boss": (1, "HE faces a towering armored boss enemy in the center of a ruined battlefield, "
                          "small hero vs giant villain composition, dramatic lighting from behind the boss, "
                          "hero's silhouette determined and ready"),

    "transformacao": (1, "HE transforms in a burst of energy, half his body still normal and half glowing "
                         "with new power, dynamic energy waves radiating outward, shocked/fierce expression, "
                         "coat flowing in the energy wind"),

    # Fora da batalha (16/10): o Horimiya (romance escolar) saiu com "confronto_boss" (cavaleiro gigante) porque
    # o catálogo só tinha ação. Capa que promete luta num romance = clique enganado, retenção cai.
    "olhar_cumplice": (2, "HE and SHE stand close together, both blushing, exchanging a shy meaningful look, she "
                          "holds his sleeve, soft golden sunset light through a window behind them, warm romantic "
                          "mood, both fully dressed in casual clothes"),
    "segredo_revelado": (2, "SHE catches HIM by surprise and discovers his secret, he freezes with a shocked "
                            "embarrassed face and sweat drop, she points at him with a teasing smile, bright "
                            "everyday setting, comedic tension"),
    "reacao_comica": (1, "HE makes an exaggerated comedic shocked reaction, eyes wide, mouth open, sweat drops "
                         "flying, bright colorful background with comic speed lines, funny over-the-top anime "
                         "expression"),
    "chuva_drama": (1, "HE stands alone in the rain at night under a street lamp, soaked, looking down with a "
                       "heartbroken expression, reflections on the wet street, melancholic emotional mood"),
    "misterio_sombra": (1, "HE looks over his shoulder in a dim corridor, a tall unclear shadow stretching on "
                           "the wall behind him, cold blue light, tense suspicious expression, mystery mood"),
    "esporte_decisivo": (1, "HE is caught mid-motion in the decisive moment of a match, sweat in the air, "
                            "stadium lights and a blurred cheering crowd behind, intense focused expression, "
                            "dynamic sports composition"),
}

# Poses de batalha (o resto é de clima): decide regra/estilo do prompt
BATALHA = {"espada_ar", "contra_monstro", "magia_poderosa", "duelo_espadas", "despertar_poder",
           "esquiva_explosao", "golpe_final", "dupla_batalha", "confronto_boss", "transformacao"}

# Poses por gênero de anime (libera poses extras conforme o tema)
# Gêneros vêm de config/seo_palavras.json
POSES_GENERO = {
    "espada_ar": {"acao", "fantasia", "isekai", "aventura"},
    "contra_monstro": {"acao", "fantasia", "apocalipse", "isekai"},
    "magia_poderosa": {"fantasia", "isekai", "magia"},
    "duelo_espadas": {"acao", "fantasia", "samurai"},
    "despertar_poder": {"acao", "isekai", "sistema", "poder"},
    "esquiva_explosao": {"acao", "apocalipse"},
    "golpe_final": {"acao", "luta", "torneio"},
    "dupla_batalha": {"acao", "fantasia", "isekai"},
    "confronto_boss": {"acao", "fantasia", "isekai", "apocalipse"},
    "transformacao": {"acao", "poder", "isekai"},
    "olhar_cumplice": {"romance", "escolar", "slice"},
    "segredo_revelado": {"romance", "escolar", "comedia", "slice"},
    "reacao_comica": {"comedia", "escolar", "slice"},
    "chuva_drama": {"drama", "romance"},
    "misterio_sombra": {"misterio", "terror", "suspense"},
    "esporte_decisivo": {"esporte"},
}

# Regras pras poses fora da batalha (sem "action-packed")
REGRAS_GERAIS = (
    "All characters are grown-up adults in their twenties, fully dressed, no kissing, no suggestive pose. "
    "No gore, no blood, no wounds. "
    "No text, no letters, no speech bubbles, no logos, no watermarks, no UI elements, no emblems or symbols on "
    "clothes (franchise symbols = copyright). Clean professional anime illustration."
)

# Roupas de batalha (alternativas para os personagens)
ROUPAS_BATALHA = [
    "dark fantasy battle armor with glowing accents",
    "modern tactical combat outfit with weapon holsters",
    "flowing mage robe with magical energy effects",
    "sleek sci-fi bodysuit with tech panels",
    "traditional martial arts gi with battle damage",
    "adventurer's gear with leather straps and cape",
]

# Regras de geração (seguras para YouTube)
REGRAS_BATALHA = (
    "All characters are grown-up adults in their twenties. "
    "Action-packed anime art style, dynamic composition, cinematic lighting, no gore, no blood, no wounds. "
    "No text, no letters, no speech bubbles, no logos, no watermarks, no UI elements, no emblems or symbols on "
    "headbands, clothes or weapons (franchise symbols = copyright). "
    "Clean professional anime illustration in the style of popular shonen/seinen series."
)
