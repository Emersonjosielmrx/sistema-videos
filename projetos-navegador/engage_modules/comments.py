"""
comments.py — Banco de comentários por idioma para o bot.

OBJETIVO:
    Guarda os textos de comentários em ~10 idiomas.
    get_comment(lang, cfg) sorteia um comentário aleatório
    combinando a base fixa + extras opcionais do config.

COMO FUNCIONA:
    1. Tem um dicionário COMMENTS_BY_LANG com ~15-20 frases por idioma
    2. O config pode ter "comments_extra" com frases adicionais
    3. get_comment() junta as duas listas e sorteia uma

IDIOMAS SUPORTADOS:
    pt, en, es, fr, it, th, vi, hi, ru, id

DEPENDENCIAS:
    - random (stdlib)
"""
import random


# ============================================================
# COMENTÁRIOS BASE POR IDIOMA
# Cada lista tem frases genéricas positivas que servem pra qualquer vídeo.
# NÃO usar caracteres especiais (acentos podem falhar em alguns browsers).
# ============================================================

COMMENTS_BY_LANG = {
    "pt": [
        "Muito bom!", "Conteudo incrivel!", "Adorei esse video!",
        "Excelente trabalho!", "Parabens pelo conteudo!", "Top demais!",
        "Que video massa!", "Sensacional!", "Continue assim!",
        "Melhor canal!", "Amei!", "Show de bola!",
        "Conteudo de qualidade!", "Perfeito!", "Maravilhoso!",
        "Muito top!", "Incrivel demais!", "Arrasou!",
        "Nota 10!", "Simplesmente perfeito!",
    ],
    "en": [
        "Awesome video!", "Great content!", "I really enjoyed this!",
        "Fantastic work!", "Keep it up!", "Loved this!",
        "Amazing!", "So good!", "Brilliant!",
        "This is exactly what I needed!", "Outstanding!", "Well done!",
        "Top tier content!", "Thanks for sharing!",
        "Really well put together!", "Incredible work!",
        "This deserves more views!", "Subscribed!", "Pure gold!",
    ],
    "es": [
        "Excelente video!", "Me encanto!", "Muy buen contenido!",
        "Increible!", "Sigue asi!", "Genial!",
        "Fantastico trabajo!", "Lo mejor!", "Contenido de calidad!",
        "Maravilloso!", "Impresionante!", "Gran video!",
        "Me gusto mucho!", "Perfecto!", "Espectacular!",
        "Que bueno!", "Increible trabajo!", "Contenido top!", "Brutal!",
    ],
    "fr": [
        "Excellente video!", "J ai adore!", "Tres bon contenu!",
        "Incroyable!", "Continue comme ca!", "Genial!",
        "Fantastique!", "Le meilleur!", "Contenu de qualite!",
        "Merveilleux!", "Impressionnant!", "Super video!",
        "J ai beaucoup aime!", "Parfait!", "Magnifique!",
        "Bravo!", "Top qualite!", "Exceptionnel!", "Formidable!",
    ],
    "it": [
        "Video fantastico!", "Mi e piaciuto molto!", "Ottimo contenuto!",
        "Incredibile!", "Continua cosi!", "Geniale!",
        "Fantastico lavoro!", "Il migliore!", "Contenuto di qualita!",
        "Meraviglioso!", "Impressionante!", "Gran bel video!",
        "Bellissimo!", "Perfetto!", "Stupendo!",
        "Eccezionale!", "Complimenti!", "Bravissimo!", "Magnifico!",
    ],
    "th": [
        "Great video!", "Love it!", "Amazing content!",
        "Keep going!", "Wonderful!", "So good!",
        "Best channel!", "Fantastic!", "Love this!",
        "Incredible!", "Nice!", "Perfect!",
        "Well done!", "Excellent!", "Outstanding!",
    ],
    "vi": [
        "Video tuyet voi!", "Rat thich!", "Noi dung hay!",
        "Tuyet voi!", "Tiep tuc nhe!", "Xuat sac!",
        "Hay nhat!", "Chat luong cao!", "An tuong!",
        "Hoan hao!", "Sieu pham!", "Hay qua!",
        "Thich qua!", "Tuyet hao!", "Xuat chung!",
    ],
    "hi": [
        "Great video!", "Very nice!", "Amazing content!",
        "Keep it up!", "Wonderful!", "So good!",
        "Best!", "Fantastic!", "Love this!",
        "Incredible!", "Nice!", "Perfect!",
        "Well done!", "Excellent!", "Outstanding!",
    ],
    "ru": [
        "Otlichnoe video!", "Mne ochen ponravilos!", "Krutoi kontent!",
        "Neveroyatno!", "Prodolzhai!", "Genialno!",
        "Fantasticheska rabota!", "Luchshee!", "Kachestvennyi kontent!",
        "Zamechatelno!", "Vpechatlyayusche!", "Super video!",
        "Ochen ponravilos!", "Idealno!", "Velikolepno!",
    ],
    "id": [
        "Video keren!", "Sangat suka!", "Konten bagus!",
        "Luar biasa!", "Terus berkarya!", "Hebat!",
        "Kerja fantastis!", "Yang terbaik!", "Konten berkualitas!",
        "Menakjubkan!", "Memukau!", "Video bagus sekali!",
        "Suka banget!", "Sempurna!", "Mantap!",
    ],
}


def get_comment(lang, cfg, vid_key=None, title=None, channel=None, account=None):
    """
    Retorna um comentário. Tenta contextual via Gemini (80%), fallback pra genérico.

    Args:
        lang: código do idioma
        cfg: dict de config
        vid_key: URL do vídeo (pra cache do smart comment)
        title: título do vídeo (pra contextualizar)
        channel: handle do canal
        account: email da conta (pra personalidade)

    Returns:
        string com o comentário (pode incluir emoji contextual)
    """
    # Tenta comentário contextual (80% agora, era 30%)
    if vid_key and title and random.random() < 0.8:
        try:
            from .smart_comments import get_smart_comment
            smart = get_smart_comment(vid_key, title, channel or "", lang, account=account)
            if smart:
                # 40% chance de adicionar emoji contextual
                if random.random() < 0.4:
                    smart = _add_contextual_emoji(smart, title)
                return smart
        except:
            pass

    # Fallback: genérico
    extra = cfg.get("comments_extra", {})
    base = list(COMMENTS_BY_LANG.get(lang, COMMENTS_BY_LANG["en"]))

    if isinstance(extra, dict) and lang in extra:
        base.extend(extra[lang])
    elif isinstance(extra, list) and extra:
        base.extend(extra)

    comment = random.choice(base)

    # Adiciona emoji em 30% dos genéricos também
    if random.random() < 0.3:
        comment = _add_contextual_emoji(comment, title or "")

    return comment


def _add_contextual_emoji(comment, title):
    """Adiciona emoji contextual baseado em palavras-chave do título."""
    title_lower = title.lower() if title else ""

    # Mapeamento de palavras-chave → emojis
    emoji_map = [
        (["fire", "hot", "trending", "viral", "fogo", "quente"], ["🔥", "💥"]),
        (["love", "heart", "amor", "like"], ["❤️", "💖", "😍"]),
        (["funny", "lol", "haha", "engraçado", "meme"], ["😂", "🤣", "😆"]),
        (["amazing", "wow", "incredible", "incrível"], ["😱", "🤩", "✨"]),
        (["thanks", "thank", "obrigado", "gratidão"], ["🙏", "👏"]),
        (["perfect", "best", "top", "perfeito", "melhor"], ["👌", "💯", "⭐"]),
        (["fight", "battle", "luta", "guerra"], ["💪", "⚔️", "🥊"]),
        (["music", "song", "música"], ["🎵", "🎶", "🎸"]),
        (["food", "comida", "recipe"], ["🍕", "🍔", "🍰"]),
        (["game", "gaming", "jogo"], ["🎮", "🕹️", "👾"]),
        (["car", "carro", "speed"], ["🏎️", "🚗", "💨"]),
        (["money", "rich", "dinheiro"], ["💰", "💵", "🤑"]),
    ]

    for keywords, emojis in emoji_map:
        if any(kw in title_lower for kw in keywords):
            emoji = random.choice(emojis)
            # 50% no final, 50% no início
            if random.random() < 0.5:
                return f"{comment} {emoji}"
            else:
                return f"{emoji} {comment}"

    # Fallback: emojis universais
    universal = ["👍", "✨", "💯", "🔥", "❤️"]
    return f"{comment} {random.choice(universal)}"
