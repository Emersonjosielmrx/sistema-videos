# -*- coding: utf-8 -*-
"""POSES_HISTORIAS.py — Catálogo de poses de TERROR/DRAMA/SUPERAÇÃO para capas de histórias.

Diferente do manhwa (sensual) e anime (batalha épica), histórias usam poses de TENSÃO PSICOLÓGICA,
isolamento, ameaça implícita, decisão crucial. Cada pose retorna (min_personagens, prompt_en).
"""

# Poses principais — TERROR/DRAMA/SUPERAÇÃO (adequadas para YouTube)
POSES = {
    # === TERROR ===
    "sombra_ameacadora": (1, "A lone person stands in a dark room with their back to camera, a massive "
                             "menacing shadow looms on the wall behind them with glowing eyes, tense "
                             "atmosphere, dim cold lighting from a single window, cinematic horror composition"),

    "corredor_escuro": (1, "A person walks cautiously through a dark narrow corridor lit only by a distant "
                           "flickering light at the end, walls covered in peeling wallpaper, mysterious "
                           "silhouettes barely visible in doorways, atmospheric fog, tension and dread"),

    "olhar_janela": (1, "A person looks out a rainy window at night, their face reflecting fear and dread, "
                        "mysterious glowing eyes visible in the darkness outside the glass, raindrops on "
                        "window, moody blue lighting, psychological horror atmosphere"),

    "fuga_floresta": (1, "A person runs desperately through a dark misty forest at night, twisted bare trees "
                         "surrounding them, mysterious glowing lights between the trees in the distance, "
                         "dramatic motion blur, cinematic horror lighting"),

    "presenca_invisivel": (1, "A person sits alone in an empty dimly lit room, their body language showing "
                              "fear as they sense an unseen presence, objects slightly levitating in the "
                              "background, cold blue-green lighting, paranormal atmosphere"),

    # === SUPERAÇÃO ===
    "decisao_crucial": (1, "A person stands at a crossroads under dramatic stormy sky, two diverging paths "
                           "ahead with contrasting lighting (one dark and foggy, one with golden light "
                           "breaking through clouds), determined expression, life-changing choice moment"),

    "subida_montanha": (1, "A person climbs a steep rocky mountain path alone, dramatic clouds and sunbeams "
                           "breaking through above the peak, showing exhaustion but determination, wide "
                           "cinematic angle emphasizing the journey, motivational atmosphere"),

    "reflexo_espelho": (1, "A person faces a large mirror in a simple room, their reflection shows a stronger "
                           "more confident version of themselves glowing with inner light, symbolic of inner "
                           "transformation, dramatic lighting split between current self (dim) and reflection "
                           "(bright)"),

    # === AMBAS (terror E superação) ===
    "isolamento_urbano": (1, "A person stands alone in an empty urban street at night under a single street "
                             "lamp, tall buildings looming on both sides creating a narrow canyon, misty "
                             "atmosphere, feeling of vulnerability and solitude"),

    "porta_misteriosa": (1, "A person stands in front of an old mysterious door with ornate details, light "
                            "seeping from underneath, their hand reaching toward the handle with hesitation, "
                            "moment before a life-changing decision, dramatic chiaroscuro lighting"),

    "tempestade_emocional": (1, "A person stands in an open field during a dramatic thunderstorm, wind "
                                "blowing their clothes and hair wildly, lightning illuminating the dark sky, "
                                "arms spread wide facing the storm, cathartic emotional release moment"),

    "despertar_forca": (1, "A person kneels in darkness with head down, surrounded by swirling ethereal light "
                           "beginning to emanate from within them, symbolic of finding inner strength, "
                           "dramatic uplighting, moment of transformation and empowerment"),
}

# Poses por categoria (algumas servem para ambas)
POSES_CATEGORIA = {
    "sombra_ameacadora": {"terror"},
    "corredor_escuro": {"terror"},
    "olhar_janela": {"terror"},
    "fuga_floresta": {"terror"},
    "presenca_invisivel": {"terror"},

    "decisao_crucial": {"superacao"},
    "subida_montanha": {"superacao"},
    "reflexo_espelho": {"superacao"},

    "isolamento_urbano": {"terror", "superacao"},
    "porta_misteriosa": {"terror", "superacao"},
    "tempestade_emocional": {"terror", "superacao"},
    "despertar_forca": {"superacao", "terror"},
}

# Roupas comuns (não lingerie, não armadura)
ROUPAS_COMUNS = [
    "casual modern clothes (jeans and t-shirt)",
    "simple hoodie and pants",
    "business casual outfit (shirt and trousers)",
    "worn traveler's clothing",
    "simple long coat over casual clothes",
    # nada de uniforme escolar: limite inegociável das capas (cara de menor/uniforme = strike) — 16/10
]

# Regras de geração (seguras para YouTube)
REGRAS_HISTORIAS = (
    "All characters are adults in their twenties or older. "
    "Cinematic dramatic lighting, atmospheric composition, psychological tension. "
    "NO gore, NO blood, NO wounds, NO explicit violence, NO nudity, NO sexual content. "
    "NO text, NO letters, NO speech bubbles, NO logos, NO watermarks, NO UI elements. "
    "Professional cinematic illustration style for YouTube thumbnail, dramatic and engaging but safe for all audiences."
)
