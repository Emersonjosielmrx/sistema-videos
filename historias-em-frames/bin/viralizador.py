# -*- coding: utf-8 -*-
"""viralizador.py — Gera títulos virais + hashtags otimizadas pro YouTube.

Usa Gemini pra gerar variações de título sem nome de obra (copyright-safe),
com hooks emocionais e curiosidade. Cache por story_id.
"""
import os
import json
import hashlib
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = PROJECT_DIR / "workspace" / "viral_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

HASHTAGS_BASE = [
    "#shorts", "#historia", "#motivacao", "#superacao",
    "#anime", "#manhwa", "#viral", "#fyp", "#storytelling",
    "#drama", "#romance", "#acao", "#terror", "#comedia",
]

GENERO_HASHTAGS = {
    "superacao": ["#motivacao", "#superacao", "#inspiracao", "#nuncadesista"],
    "romance": ["#romance", "#amor", "#casal", "#historia_de_amor"],
    "terror": ["#terror", "#medo", "#suspense", "#arrepio", "#creepy"],
    "comedia": ["#comedia", "#humor", "#engracado", "#risada"],
    "acao": ["#acao", "#luta", "#batalha", "#epico"],
    "drama": ["#drama", "#emocao", "#chorando", "#triste"],
    "fantasia": ["#fantasia", "#magia", "#rpg", "#aventura"],
    "ficscifi": ["#ficcaocientifica", "#futuro", "#tecnologia", "#scifi"],
}

# Dicionário anti-ban: palavras que YT pode flagrar/desmonetizar
ANTI_BAN_WORDS = {
    "matar": "eliminar",
    "matou": "eliminou",
    "morrer": "partir",
    "morreu": "partiu",
    "morte": "fim",
    "suicidio": "desespero",
    "suicídio": "desespero",
    "sangue": "marca vermelha",
    "assassino": "vilão",
    "assassina": "vilã",
    "droga": "substância",
    "drogas": "substâncias",
    "cocaína": "pó branco",
    "heroína": "substância pesada",
    "crack": "pedra",
    "arma": "objeto",
    "armas": "objetos",
    "tiro": "disparo",
    "bala": "projétil",
    "bomba": "explosão",
    "terrorista": "extremista",
    "estupro": "violência",
    "abuso": "trauma",
    "nu": "exposto",
    "nua": "exposta",
    "sexo": "intimidade",
    "pornografia": "conteúdo adulto",
    "pedofilia": "crime hediondo",
    "racismo": "preconceito",
    "nazismo": "ideologia extrema",
    "hitler": "ditador",
    "suicida": "desesperado",
}


def sanitize_title(title):
    """Remove palavras que podem causar flag/desmonetização no YT."""
    result = title
    for banned, safe in sorted(ANTI_BAN_WORDS.items(), key=lambda x: -len(x[0])):
        import re
        result = re.sub(re.escape(banned), safe, result, flags=re.IGNORECASE)
    return result


def generate_viral_titles(titulo_original, genero="superacao", n=5):
    """Gera N variações virais do título usando Gemini. Retorna lista de strings."""
    cache_key = hashlib.md5(f"{titulo_original}_{genero}_{n}".encode()).hexdigest()
    cache_file = CACHE_DIR / f"{cache_key}.json"

    if cache_file.exists():
        try:
            return json.loads(cache_file.read_text(encoding="utf-8"))
        except Exception:
            pass

    try:
        import gemini_llm
        prompt = (
            f"Gere {n} títulos VIRAIS para YouTube Shorts sobre esta história:\n"
            f"'{titulo_original}'\n"
            f"Gênero: {genero}\n\n"
            "Regras:\n"
            "- Máximo 60 caracteres cada\n"
            "- Use HOOKS emocionais (curiosidade, choque, empatia)\n"
            "- NÃO mencione nomes de obras/animes/manhwas (copyright)\n"
            "- NÃO use palavras proibidas (violência explícita, termos sexuais)\n"
            "- Use emojis com moderação (máx 1-2 por título)\n"
            "- Formato: um título por linha, sem numeração\n"
        )
        resp = gemini_llm.generate(prompt)
        if resp:
            titles = [sanitize_title(l.strip()) for l in resp.strip().splitlines() if l.strip()]
            titles = [t for t in titles if len(t) > 5][:n]
            if titles:
                cache_file.write_text(json.dumps(titles, ensure_ascii=False), encoding="utf-8")
                return titles
    except Exception:
        pass

    return [sanitize_title(titulo_original)]


def get_hashtags(genero="superacao", extra=None):
    """Retorna string de hashtags otimizadas pro gênero."""
    tags = GENERO_HASHTAGS.get(genero, [])[:4]
    base = ["#shorts", "#historia", "#viral", "#fyp"]
    if extra:
        tags.extend(extra[:3])
    all_tags = list(dict.fromkeys(base + tags))
    return " ".join(all_tags[:12])


def generate_description(titulo, genero="superacao"):
    """Gera descrição curta pro YT."""
    hashtags = get_hashtags(genero)
    return (
        f"{titulo}\n\n"
        f"Uma história original de {genero} que vai te surpreender.\n"
        f"Se gostou, inscreva-se e ative o sininho!\n\n"
        f"{hashtags}"
    )


def generate_full_description(titulo, genero, cenas, serie_info=None):
    """Gera descricao SEO completa pro YouTube.

    Inclui:
    - Hook nas primeiras 2 linhas
    - Resumo da historia (3 linhas)
    - Timestamps se >10 cenas
    - Hashtags (max 15)
    - CTA (inscreva-se + link proxima parte se serie)
    - Disclaimer "Gerado por IA"

    Args:
        titulo: titulo do video
        genero: genero da historia
        cenas: lista de dicts com narracao/texto
        serie_info: dict opcional {nome, parte, total, playlist_url}
    """
    lines = []

    # Hook (primeiras 2 linhas — aparecem antes do "mostrar mais")
    hooks = {
        "terror": "Voce nao vai dormir depois de ver isso...",
        "romance": "Uma historia de amor que vai fazer voce chorar...",
        "superacao": "Essa historia vai mudar a forma como voce ve a vida...",
        "misterio": "Ninguem esperava esse final...",
        "comedia": "Prepare-se pra rir MUITO com essa...",
        "drama": "Uma decisao que mudou tudo...",
        "fantasia": "Um mundo que voce nunca imaginou...",
        "motivacional": "As vezes tudo o que voce precisa e acreditar...",
        "acao": "A batalha mais intensa que voce ja viu...",
        "curiosidades": "Voce NAO sabia disso...",
    }
    hook = hooks.get(genero, "Essa historia vai te surpreender...")
    lines.append(hook)
    lines.append(f"{sanitize_title(titulo)}")
    lines.append("")

    # Resumo (3 linhas baseadas nas primeiras cenas)
    lines.append("SOBRE ESTA HISTORIA:")
    if cenas and len(cenas) >= 3:
        # Pegar texto das primeiras 3 cenas pra resumo (sem spoiler)
        resumo_textos = []
        for c in cenas[:3]:
            texto = c.get("narracao") or c.get("texto", "")
            if texto:
                # Pegar primeira frase
                frase = texto.split(".")[0].strip()
                if len(frase) > 10:
                    resumo_textos.append(sanitize_title(frase) + "...")
        if resumo_textos:
            for r in resumo_textos[:3]:
                lines.append(f"  {r}")
        else:
            lines.append(f"  Uma historia original de {genero} narrada com IA.")
    else:
        lines.append(f"  Uma historia original de {genero} narrada com IA.")
    lines.append("")

    # Timestamps (se >10 cenas)
    if cenas and len(cenas) > 10:
        lines.append("MOMENTOS:")
        # Estimar timestamps (~5s por cena como media)
        avg_duration = 5.0
        for i, c in enumerate(cenas):
            if i % 3 == 0:  # A cada 3 cenas, um timestamp
                ts_sec = int(i * avg_duration)
                ts_min = ts_sec // 60
                ts_remainder = ts_sec % 60
                label = c.get("narracao", c.get("texto", f"Parte {i+1}"))
                # Primeira frase curta
                label = label.split(".")[0][:40].strip()
                if label:
                    lines.append(f"  {ts_min}:{ts_remainder:02d} — {sanitize_title(label)}")
        lines.append("")

    # CTA
    lines.append("─" * 30)
    if serie_info:
        nome = serie_info.get("nome", "")
        parte = serie_info.get("parte", 1)
        total = serie_info.get("total", "?")
        lines.append(f"Serie: {nome} (Parte {parte}/{total})")
        if serie_info.get("playlist_url"):
            lines.append(f"Playlist completa: {serie_info['playlist_url']}")
        lines.append(f"Proximo episodio em BREVE — INSCREVA-SE pra nao perder!")
    else:
        lines.append("Gostou? INSCREVA-SE e ative o SINO pra mais historias!")
    lines.append("Deixe seu LIKE e COMENTE qual genero quer ver a seguir!")
    lines.append("")

    # Hashtags (max 15)
    genre_tags = GENERO_HASHTAGS.get(genero, [])[:5]
    base_tags = ["#shorts", "#historia", "#viral", "#fyp", "#storytelling"]
    extra_tags = ["#anime", "#narrativa", "#suspense", "#emocao", "#originalstory"]
    all_tags = list(dict.fromkeys(base_tags + genre_tags + extra_tags))[:15]
    lines.append(" ".join(all_tags))
    lines.append("")

    # Disclaimer
    lines.append("─" * 30)
    lines.append("Todas as imagens e narracao foram geradas por Inteligencia Artificial.")
    lines.append("Nenhum conteudo real foi utilizado na producao deste video.")

    return "\n".join(lines)
