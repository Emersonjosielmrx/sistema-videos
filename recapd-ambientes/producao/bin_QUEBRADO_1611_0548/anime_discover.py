"""anime_discover.py — descobre recaps de anime populares no YouTube.

Módulo pequeno e isolado. Só faz uma coisa: buscar candidatos no YouTube via
yt-dlp (sem API key), ordenar por views e filtrar por duração. Retorna metadados
(NÃO baixa nada aqui — download é no anime_fetch).

A língua NÃO importa: a IA traduz depois. Por isso a busca varre termos em
várias línguas pra pegar os vídeos mais vistos independente do idioma.
"""
import json
import logging
import subprocess

# Termos de busca: FOCO em animes/donghuas que NÃO têm dublagem PT-BR.
# Estratégia:
# 1. Donghuas (chineses) e Aenis (coreanos) quase nunca são dublados rápido.
# 2. Isekais genéricos / animes de nicho da temporada atual.
# 3. Evitar shounens famosos (Mashle, Demon Slayer, Jujutsu, etc).
DEFAULT_QUERIES = [
    # Donghuas (Animes Chineses) - mina de ouro sem dublagem PT
    "donghua recap full story explained",
    "chinese anime recap full story",
    "cultivation anime recap explained",
    "manhua anime recap story",
    # Manhwas animados (Coreanos)
    "manhwa anime recap full story",
    "korean anime recap explained",
    # Isekais / Fantasia de nicho (temporada atual)
    "underrated isekai anime recap full story",
    "new fantasy anime recap explained",
    "reincarnation anime recap full story",
    "overpowered mc anime recap story",
    "magic academy anime recap (not mashle)",
    # Termos em JP/KR para pegar direto da fonte
    "最新アニメ ストーリー解説",             # JP: anime mais recente explained
    "애니 스토리 요약",                     # KR: resumo da história
    "중국 애니 요약",                       # KR: resumo de anime chinês
]

# Palavras no TÍTULO que denunciam conteúdo ERRADO ou MAINSTREAM DEMAIS:
# compilações de esquete, humor, gameplay, otome/visual novel, AMV, etc.
# Se o título bater em qualquer uma, o candidato é DESCARTADO.
TITLE_BLOCKLIST = [
    # compilação / coletânea de trechos soltos (não conta uma história)
    "総集編", "総編集", "まとめ", "詰め合わせ", "compilation", "compilado",
    "compilação", "best moments", "funny",
    # jogos / visual novel / otome (prints de jogo, não anime)
    "otome", "visual novel", "ゲーム",
    "実況", "walkthrough",
    # música / AMV (edição sem história narrativa) — usar match de borda pra não bloquear substrings
    "mmd", "music video", "ost ", " ost", "lyrics", "soundtrack",
    "ending song", "opening song", "ending theme", "opening theme",
    # reação / vlog (pessoa falando, não animação)
    "reaction", "reação", "react", "vlog",
    # mundo real / não-anime
    "news", "podcast", "interview", "entrevista",
    "real life", "live action",
    # trailer / prévia
    "trailer", "teaser", "pv ", "preview",
    # conteúdo adulto
    "yaoi", "yuri", "hentai", "ecchi", "phonk",
    # animação ocidental / não-anime (o produto é anime, não desenho ocidental)
    "disney", "pixar", "dreamworks", "blue sky", "illumination",
    "lion king", "toy story", "frozen", "encanto", "moana",
    "shrek", "how to train your dragon", "kung fu panda",
    "ice age", "cars ", "finding nemo", "finding dory",
    "the incredibles", "inside out", "coco", "soul ",
    "marvel ", "spider-man", "batman animated", "superman animated",
    "cartoon network", "nickelodeon", "adult swim",
    "sonic the hedgehog", "super mario", "mario bros",
    "mortal kombat", "mario kart", "pokemon live",
    "mr beast", "pewdiepie", "markiplier",
    # jogos / gameplay (o produto é anime, não game)
    "half life", "minecraft", "roblox", "fortnite", "genshin impact",
    "valorant", "csgo", "counter-strike", "apex legends", "league of legends",
    "overwatch", "world of warcraft", "call of duty", "pubg", "fall guys",
    "among us", "fall guys", "subway surfers", "temple run",
    "brawl stars", "clash of clans", "clash royale", "mobile game",
    # conteúdo médico / científico / real (o produto é anime)
    "tus organos", "your organs", "your body", "inside your body",
    "how your body works", "anatomy", "human body", " biology",
    "medical", "medicina", "pregnancy", "childbirth", "cirurgia",
    "science", "experimento", "how things work",
    # mitologia / história real (não é anime)
    "orpheus", "mythology", "myth ", "greek gods", "greek mythology",
    "god of war", "ragnarok", "zeus", "hercules", "olimpus",
    "norse mythology", "valhalla", "shiva", "odin",
    # conteúdo TED/educativo real (não anime)
    "ted-ed", "ted ed", "tedtalk", "kurzgesagt", "veritasium",
    "smartereveryday", "minute physics", "asapSCIENCE",
    # motion graphics / cinemagraph / tutorial
    "motion graphic",
    # conteúdo rejeitado pela IA (não é recap/resumo narrativo de anime)
    "how to create", "how to make", "how i create",
    "short film", "animated short", "cómic",
    # MAINSTREAM (já têm dublagem PT-BR, não queremos)
    "mashle", "demon slayer", "kimetsu", "jujutsu", "naruto", "boruto",
    "one piece", "dragon ball", "bleach", "my hero academia", "boku no hero",
    "attack on titan", "shingeki", "spy x family", "chainsaw man",
    "solo leveling", "kaiju no 8", "frieren", "one punch", "hunter x hunter",
    "death note", "fullmetal", "sword art online", "tokyo ghoul",
]


# IDs dos vídeos que a dona mandou como EXEMPLO/REFERÊNCIA da taxonomia (ver
# [[project-shorts-tipos-fonte]]). São o ALVO a IMITAR, NÃO fontes pra processar.
# Sem isto, o discover acha o próprio exemplo no YT (casa com as queries) e o
# processa como se fosse conteúdo novo — que foi exatamente o bug reportado.
REFERENCE_EXAMPLE_IDS = {
    "eS4WzES83KA",  # tipo 1: curiosidades com narrador
    "DClrA8tR6rY",  # tipo 2: cena de anime já dublada em PT
    "4R0DcroW8qg",  # tipo 3: resumo/recap vertical (alvo principal)
}


def _title_ok(title):
    """True se o título NÃO bate em nenhuma palavra da blocklist (case-insensitive)."""
    t = title.lower()
    return not any(bad.lower() in t for bad in TITLE_BLOCKLIST)


def _search_one(query, limit):
    """Roda yt-dlp numa query e retorna [dicts] com metadados (flat, sem baixar)."""
    cmd = [
        "yt-dlp", f"ytsearch{limit}:{query}",
        "--flat-playlist", "--no-warnings",
        "--print", "%(view_count)s\x1f%(duration)s\x1f%(title)s\x1f%(id)s",
    ]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    except (subprocess.TimeoutExpired, Exception) as e:
        logging.error(f"[discover] busca falhou ({query!r}): {e}")
        return []

    results = []
    for line in out.stdout.strip().splitlines():
        parts = line.split("\x1f")
        if len(parts) != 4:
            continue
        views, dur, title, vid = parts
        try:
            views = int(views) if views not in ("NA", "None", "") else 0
            dur = float(dur) if dur not in ("NA", "None", "") else 0.0
        except ValueError:
            continue
        results.append({"views": views, "duration": dur,
                        "title": title.strip(), "id": vid.strip(),
                        "url": f"https://www.youtube.com/watch?v={vid.strip()}",
                        "query": query})
    return results


def _search_one_short(query, limit):
    """Busca vídeos curtos no YouTube.

    Removemos o filtro estrito da aba Shorts (sp=EgIYAw) porque estava causando
    erros no yt-dlp e limitando muito os resultados. Agora confiamos na duração
    e na checagem de aspect ratio posterior."""
    cmd = [
        "yt-dlp", f"ytsearch{limit}:{query} short",
        "--flat-playlist", "--no-warnings",
        "--print", "%(view_count)s\x1f%(duration)s\x1f%(title)s\x1f%(id)s",
    ]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    except (subprocess.TimeoutExpired, Exception) as e:
        logging.error(f"[discover_shorts] busca falhou ({query!r}): {e}")
        return []

    results = []
    for line in out.stdout.strip().splitlines():
        parts = line.split("\x1f")
        if len(parts) != 4:
            continue
        views, dur, title, vid = parts
        try:
            views = int(views) if views not in ("NA", "None", "") else 0
            dur = float(dur) if dur not in ("NA", "None", "") else 0.0
        except ValueError:
            continue
        results.append({"views": views, "duration": dur,
                        "title": title.strip(), "id": vid.strip(),
                        "url": f"https://www.youtube.com/watch?v={vid.strip()}",
                        "query": query})
    return results


# Termos pro SHORT (9:16). Buscamos vídeos CURTOS de anime que já são verticais.
# FOCO: recap/resumo de anime em formato SHORT vertical (o produto-alvo da dona).
# Termos em várias línguas pq a fonte pode ser de qualquer idioma (re-narramos em PT).
# No V2 usamos a aba do YT garantida de shorts (/hashtag/shorts), mas como yt-dlp não permite flat-playlist na aba shorts de forma simples
# Vamos pescar videos com duraçao ESTRITA < 60s
SHORT_QUERIES = [
    # Inglês — foco em RESUMO NARRATIVO (curiosidades, backstory, lore)
    "anime curious fact short",
    "anime backstory explained short",
    "anime lore short explained",
    "anime character story short",
    "anime facts you didn t know",
    "anime trivia short",
    "anime story explained in 60 seconds",
    "anime history explained short",
    "anime villain origin story",
    "anime hero origin explained",
    "anime power explained short",
    "anime mythology explained",
    # Coreano
    "애니 에피소드 요약",
    "애니 Lore 설명",
    "애니 한줄 요약",
    "애니 이야기 요약",
    "anime mythology lore shorts",
    # Japonês
    "アニメ 豆知識",
    "アニメ 説明 短い",
    "anime episode summary short",
    # Espanhol
    "anime dato curioso corto",
    "anime mitologia explicada cortos",
    "anime explicacion corta episodio",
    # Português
    "anime resumo episodio curto",
    "anime historia resumida",
    "curiosidades anime",
]

# Palavra "shorts" no TÍTULO é um bom sinal de vídeo vertical — usada pra dar boost.
_VERTICAL_TITLE_HINTS = ["#shorts", "shorts", "short", "쇼츠", "切り抜き"]


def _aspect_ratio_remote(url, timeout=30):
    """Descobre a proporção (largura/altura) de um vídeo do YT SEM baixá-lo.

    Usa yt-dlp só de metadados (--print). Retorna float (w/h) ou None se falhar.
    Vertical (9:16) tem ratio ~0.56; 16:9 tem ~1.78. É o passo que torna a busca
    INTELIGENTE: descarta 16:9 antes de gastar banda baixando. Ver
    [[feedback-shorts-fonte-vertical]] e [[project-shorts-tipos-fonte]]."""
    cmd = [
        "yt-dlp", url, "--skip-download", "--no-warnings", "--no-playlist",
        "--print", "%(aspect_ratio)s\x1f%(width)s\x1f%(height)s",
    ]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except (subprocess.TimeoutExpired, Exception) as e:
        logging.warning(f"[discover_shorts] probe orientação falhou ({url}): {e}")
        return None
    line = out.stdout.strip().splitlines()
    if not line:
        return None
    parts = line[0].split("\x1f")
    # 1) aspect_ratio direto do yt-dlp
    try:
        ar = float(parts[0])
        if ar > 0:
            return ar
    except (ValueError, IndexError):
        pass
    # 2) fallback: calcula de width/height
    try:
        w, h = float(parts[1]), float(parts[2])
        if w > 0 and h > 0:
            return w / h
    except (ValueError, IndexError):
        pass
    return None


def _rank_pool(queries, per_query, min_dur, max_dur, top, tag):
    """Busca em várias queries, filtra por duração + blocklist de título,
    dedup e ordena por views. Núcleo comum de discover() e discover_shorts()."""
    seen = set()
    pool = []
    for q in queries:
        for r in _search_one(q, per_query):
            if r["id"] in seen:
                continue
            if r["id"] in REFERENCE_EXAMPLE_IDS:
                logging.info(f"[{tag}] descartado (é vídeo-exemplo, não fonte): {r['title'][:50]}")
                continue
            if not (min_dur <= r["duration"] <= max_dur):
                continue
            if not _title_ok(r["title"]):
                logging.info(f"[{tag}] descartado (título): {r['title'][:60]}")
                continue
            seen.add(r["id"])
            pool.append(r)
    pool.sort(key=lambda r: r["views"], reverse=True)
    return pool[:top]


def discover(queries=None, per_query=10, min_dur=180, max_dur=14400, top=10):
    """Busca e ranqueia recaps de anime LONGOS (produto DEITADO 16:9).

    min_dur=180 (3min) descarta shorts/trailers; max_dur=4h descarta lives.
    Retorna [dicts] ordenados por views (desc), sem duplicatas.
    """
    return _rank_pool(queries or DEFAULT_QUERIES, per_query, min_dur, max_dur, top, "discover")


def _rank_pool_short(queries, per_query, top):
    """Busca com ytsearch e filtra candidatos curtos (15-60s).

    A verificação de verticalidade REAL é feita pelo ffprobe pós-download.
    ytsearch é confiável; a duração 15-60s filtra a maioria dos não-shorts."""
    seen = set()
    pool = []
    for q in queries:
        for r in _search_one_short(q, per_query):
            if r["id"] in seen:
                continue
            if r["id"] in REFERENCE_EXAMPLE_IDS:
                logging.info(f"[discover_shorts] descartado (é vídeo-exemplo): {r['title'][:50]}")
                continue
            if not (15 <= r["duration"] <= 90):
                continue
            if not _title_ok(r["title"]):
                logging.info(f"[discover_shorts] descartado (título): {r['title'][:60]}")
                continue
            seen.add(r["id"])
            pool.append(r)
    pool.sort(key=lambda r: r["views"], reverse=True)
    return pool[:top]


def discover_shorts(queries=None, per_query=5, top=15,
                    ratio_max=0.9, check_orientation=False):
    """Busca e ranqueia SHORTS de anime VERTICAIS (produto SHORT 9:16).

    Usa a aba Shorts do YouTube (sp=EgIYAw) que filtra vídeos curtos.
    Se check_orientation=True (padrão), confirma a orientação REMOTAMENTE via yt-dlp
    (sem baixar) e DESCARTA os 16:9 — short vertical é obrigatório.

    ratio_max: teto de w/h pra considerar vertical (0.9; 9:16 real ~0.56).
    Retorna [dicts] ordenados por views (desc), sem duplicatas.
    """
    pool = _rank_pool_short(queries or SHORT_QUERIES, per_query, max(top, 10))

    if not check_orientation:
        return pool[:top]

    # Probe de orientação: só manter candidatos COMprovadamente verticais (ar < 0.9).
    # Não descartar candidatos sem ar definido (ar=None) — a pipeline detecta depois.
    verticais = []
    for r in pool:
        if len(verticais) >= top:
            break
        ar = _aspect_ratio_remote(r["url"], timeout=30)
        if ar is None:
            # yt-dlp não conseguiu determinar — assumir que pode ser vertical e incluir
            logging.info(f"[discover_shorts] ar indefinido (incluindo): {r['title'][:50]}")
            r["aspect_ratio"] = None
            verticais.append(r)
            continue
        if ar < ratio_max:
            logging.info(f"[discover_shorts] VERTICAL (ar={ar:.2f}): {r['title'][:50]}")
            r["aspect_ratio"] = ar
            verticais.append(r)
        else:
            logging.info(f"[discover_shorts] DESCARTADO horizontal (ar={ar:.2f}): {r['title'][:50]}")

    return verticais[:top]


def discover_canal(url, maximo=150, top=None, min_views=0):
    """Descobre shorts de um canal específico via aba Shorts.

    Usa aba_shorts.listar() (API InnerTube) como primário;
    fallback para yt-dlp se falhar.

    Args:
        url: URL do canal (@handle/shorts ou /channel/UC.../shorts)
        maximo: quantos shorts listar (default 150)
        top: quantos retornar após ordenar (default: todos)
        min_views: piso de views (filtro)

    Returns: [{"id", "title", "url", "views", "duration", ...}]
    """
    import hashlib
    import time
    from pathlib import Path

    cache_dir = Path(__file__).parent.parent / "workspace" / "cache" / "discover_canal"
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Cache por hash da URL (24h)
    url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
    cache_file = cache_dir / f"{url_hash}.json"

    # Tenta cache (válido por 24h)
    if cache_file.exists():
        idade = time.time() - cache_file.stat().st_mtime
        if idade < 86400:  # 24h
            try:
                cached = json.loads(cache_file.read_text(encoding="utf-8"))
                logging.info(f"[discover_canal] {len(cached)} Shorts em {url} (lista guardada)")
                resultado = [c for c in cached if c.get("views", 0) >= min_views]
                return resultado[:top] if top else resultado
            except (OSError, ValueError, KeyError):
                pass

    # Busca nova via aba_shorts
    try:
        import aba_shorts
        lista = aba_shorts.listar(url, maximo=maximo)
        candidatos = [
            {
                "id": vid,
                "title": titulo,
                "url": f"https://www.youtube.com/shorts/{vid}",
                "views": views,
                "duration": 0.0,  # aba_shorts não retorna duração
                "parte": 0,
                "parceiro": url,
            }
            for vid, titulo, views in lista
        ]

        # Guarda no cache
        try:
            cache_file.write_text(json.dumps(candidatos, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass

        logging.info(f"[discover_canal] {len(candidatos)} Shorts em {url} ({len(lista)} resumos sem parte)")

        # Filtra e retorna
        resultado = [c for c in candidatos if c.get("views", 0) >= min_views]
        return sorted(resultado, key=lambda x: x.get("views", 0), reverse=True)[:top] if top else resultado

    except Exception as e:
        logging.warning(f"[discover_canal] API do site falhou em {url} ({e}) — uso o yt-dlp")
        # Fallback: yt-dlp
        return _rank_pool_short([url], per_query=maximo, top=top or maximo)


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    res = discover(per_query=6, top=10)
    print(json.dumps(res, ensure_ascii=False, indent=2))
    print(f"\n{len(res)} candidatos.", file=sys.stderr)
