"""anime_discover.py — descobre recaps de anime populares no YouTube.

Módulo pequeno e isolado. Só faz uma coisa: buscar candidatos no YouTube via
yt-dlp (sem API key), ordenar por views e filtrar por duração. Retorna metadados
(NÃO baixa nada aqui — download é no anime_fetch).

A língua NÃO importa: a IA traduz depois. Por isso a busca varre termos em
várias línguas pra pegar os vídeos mais vistos independente do idioma.

V2 (2026-08-02): inteligência de busca expandida — queries diversas, variação
temporal, busca por canais de recap, shuffle por rodada, per_query maior.
"""
import hashlib
import json
import logging
import random
import subprocess
import time
import ytdlp_vez  # COMUM: 1 yt-dlp por vez no PC (rajada bloqueou o IP da casa)
from datetime import datetime
from pathlib import Path

_NOW = datetime.now()
_YEAR = _NOW.year
_SEASON = ["winter", "spring", "summer", "fall"][(_NOW.month - 1) // 3]

_BASE_QUERIES = [
    # === Donghuas (Animes Chineses) - mina de ouro sem dublagem PT ===
    "donghua recap full story explained",
    "chinese anime recap full story",
    "cultivation anime recap explained",
    "manhua anime recap story",
    "donghua full episode recap",
    "chinese animation story explained",
    "soul land donghua recap",
    "battle through the heavens recap",
    "martial god asura donghua",
    "tales of demons and gods recap",
    "perfect world donghua explained",
    "swallowed star donghua recap",
    # === Manhwas animados (Coreanos) ===
    "manhwa anime recap full story",
    "korean anime recap explained",
    "webtoon anime recap full story",
    "tower of god recap explained",
    "noblesse anime recap",
    "the god of high school recap",
    # === Isekai / Fantasia ===
    "underrated isekai anime recap full story",
    "new fantasy anime recap explained",
    "reincarnation anime recap full story",
    "overpowered mc anime recap story",
    "isekai anime recap all episodes",
    "transported to another world anime recap",
    "demon lord anime recap full story",
    "summoned hero anime recap explained",
    "villainess anime recap full story",
    "otome game isekai anime recap",
    # === Ação / Aventura ===
    "action anime recap full story explained",
    "martial arts anime recap full story",
    "dungeon anime recap explained",
    "monster tamer anime recap",
    "adventurer anime recap full story",
    "strongest character anime recap",
    # === Romance / Drama ===
    "romance anime recap full story",
    "school romance anime recap explained",
    "wholesome anime recap full story",
    # === Dark / Thriller / Horror ===
    "dark fantasy anime recap full story",
    "psychological anime recap explained",
    "survival game anime recap",
    "horror anime recap full story",
    # === Sci-fi / Mecha ===
    "sci-fi anime recap full story",
    "mecha anime recap explained",
    "space anime recap full story",
    "cyberpunk anime recap",
    # === Formatos de recap ===
    "anime all episodes recap in one video",
    "anime season 1 recap full story",
    "anime complete story recap",
    "entire anime explained in one video",
    "anime full season recap explained",
    "anime recap from beginning to end",
    # === Termos em JP/KR/CN pra pegar da fonte ===
    "最新アニメ ストーリー解説",
    "アニメ 全話 あらすじ",
    "アニメ ストーリー まとめ 解説",
    "이세계 애니 스토리 요약",
    "애니 스토리 요약",
    "중국 애니 요약",
    "판타지 애니 전체 요약",
    "动漫 全集 解说",
    "国漫 剧情 解说",
]

_TEMPORAL_TEMPLATES = [
    "anime recap {year}",
    "{season} {year} anime recap full story",
    "new anime {year} recap explained",
    "best donghua {year} recap",
    "underrated anime {year} recap full story",
    "new isekai anime {year} recap",
    "donghua {year} full story explained",
    "{year} anime season recap",
]

_CHANNEL_QUERIES = [
    "AniRecap anime recap full story",
    "AniSenpai anime recap",
    "Anime Jenius recap",
    "Ani-One recap full story",
    "AniBot recap explained",
    "Aniwatch recap full story",
    "Quick Anime Recap explained",
    "Anime Recap Hub full story",
    "Manhwa Recap full story",
    "Donghua World recap",
]

def _build_queries():
    queries = list(_BASE_QUERIES)
    for tmpl in _TEMPORAL_TEMPLATES:
        queries.append(tmpl.format(year=_YEAR, season=_SEASON))
        queries.append(tmpl.format(year=_YEAR - 1, season=_SEASON))
    queries.extend(_CHANNEL_QUERIES)
    random.shuffle(queries)
    return queries

DEFAULT_QUERIES = _build_queries()

# Palavras no TÍTULO que denunciam conteúdo ERRADO ou MAINSTREAM DEMAIS:
# compilações de esquete, humor, gameplay, otome/visual novel, AMV, etc.
# Se o título bater em qualquer uma, o candidato é DESCARTADO.
# BLOCKLIST TEMPORARIAMENTE DESABILITADA (2026-08-04) pra testar fix yt-dlp deno.
# A blocklist original bloqueava 100% dos candidatos (mainstream anime + "in a nutshell").
# Restaurar depois que validar que o download funciona.
TITLE_BLOCKLIST_ORIGINAL = [
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
    "turning red", "luca", "onward", "raya",
    # filmes live-action / super-heróis
    "marvel ", "spider-man", "batman animated", "superman animated",
    "suicide squad", "deadshot", "harley quinn", "joker",
    "avengers", "iron man", "captain america", "thor",
    "black widow", "hulk", "guardians",
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
    # história real / geopolítica (não é anime)
    "oversimplified", "opium war", "three kingdoms", "world war",
    "cold war", "civil war", "revolution", "animated history",
    "history explained", "historical", "ww1", "ww2",
    # conteúdo TED/educativo real (não anime)
    "ted-ed", "ted ed", "tedtalk", "kurzgesagt", "veritasium",
    "smartereveryday", "minute physics", "asapSCIENCE",
    # motion graphics / cinemagraph / tutorial
    "motion graphic",
    # conteúdo rejeitado pela IA (não é recap/resumo narrativo de anime)
    "how to create", "how to make", "how i create",
    "short film", "animated short", "cómic",
    # creepypasta / cartoon horror (não anime)
    "cartoon cat", "cartoon dog", "siren head", "trevor henderson",
    "backrooms", "creepypasta",
    # rankings / tier lists (não contam história)
    "tier list", "top 10 best", "top 10 worst", "ranking",
    "in a nutshell", "best of anime", "worst anime",
    # cartoon ocidental disfarçado
    "adventure time", "regular show", "gravity falls", "steven universe",
    "avatar the last", "legend of korra", "curious george", "tom and jerry",
    "tom & jerry", "looney tunes", "scooby doo",
    "おさるのジョージ",  # Curious George em japonês
    # MAINSTREAM (já têm dublagem PT-BR, não queremos)
    "mashle", "demon slayer", "kimetsu", "jujutsu", "naruto", "boruto",
    "one piece", "dragon ball", "bleach", "my hero academia", "boku no hero",
    "attack on titan", "shingeki", "spy x family", "chainsaw man",
    "solo leveling", "kaiju no 8", "frieren", "one punch", "hunter x hunter",
    "death note", "fullmetal", "sword art online", "tokyo ghoul",
    # psychology / character analysis (não é recap narrativo)
    "psychology of", "character analysis", "villain explained",
    "greatest villain",
]

# Blocklist mínima: só cartoon ocidental + jogos (lixo óbvio)
TITLE_BLOCKLIST = [
    "disney", "pixar", "dreamworks", "toy story", "frozen", "moana",
    "shrek", "kung fu panda", "minecraft", "roblox", "fortnite",
    "reaction", "react", "vlog", "trailer", "teaser",
    "cartoon cat", "siren head", "curious george", "tom and jerry",
    "トムとジェリー", "tom et jerry", "tom y jerry", "tom e jerry",
    "wb kids", "looney tunes", "ルーニー・テューンズ",
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
        with ytdlp_vez.vez("anime: busca"):
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=180, encoding='utf-8', errors='replace')
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
        with ytdlp_vez.vez("anime: busca shorts"):
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=180, encoding='utf-8', errors='replace')
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
        with ytdlp_vez.vez("anime: orientação"):
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
    raw_count = 0
    for q in queries:
        hits = _search_one(q, per_query)
        raw_count += len(hits)
        for r in hits:
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
    logging.info(f"[{tag}] {len(queries)} queries, {raw_count} brutos, {len(pool)} após filtro")
    pool.sort(key=lambda r: r["views"], reverse=True)
    return pool[:top]


def discover(queries=None, per_query=15, min_dur=180, max_dur=14400, top=10):
    """Busca e ranqueia recaps de anime LONGOS (produto DEITADO 16:9).

    min_dur=180 (3min) descarta shorts/trailers; max_dur=4h descarta lives.
    Retorna [dicts] ordenados por views (desc), sem duplicatas.
    V2: queries reshuffled a cada chamada pra variar resultados do YouTube.
    """
    qs = queries or _build_queries()
    return _rank_pool(qs, per_query, min_dur, max_dur, top, "discover")


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



if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    res = discover(per_query=15, top=10)
    print(json.dumps(res, ensure_ascii=False, indent=2))
    print(f"\n{len(res)} candidatos.", file=sys.stderr)


# ── Canal PARCEIRO (16/10): o dono liberou reusar TODOS os Shorts (ex.: @kaijinre) ──────────────────────
# 21/10: a lista INTEIRA do canal (até 3 mil Shorts = dezenas de páginas) saía a cada rodada, sem a vez e sem olhar a
# pausa — era o grosso dos pedidos ao YouTube e o IP voltou a ser barrado a cada fim de pausa. Parceiro posta pouco/dia.
CANAL_CACHE = Path(__file__).resolve().parent.parent / "workspace" / "cache" / "discover_canal"
CANAL_CACHE_H = 6


def discover_canal(url, top=0):
    """Shorts de um canal parceiro, na ordem de produção: SEMPRE do mais visto pro menos visto (dona 30/10: "pegar
    sempre os mais virais primeiro"; antes os resumos sem "Part N" iam antes e as partes por número). Dado do hipercool (bin/short_resumo.py): no @kaijinre o Short sem parte fez 513 mil e a
    "Parte 2" da mesma obra 2,4 mil — o algoritmo empurra o resumo."""
    import re
    cache = CANAL_CACHE / (hashlib.md5(url.encode("utf-8")).hexdigest()[:12] + ".json")
    try:
        if time.time() - cache.stat().st_mtime < CANAL_CACHE_H * 3600:
            itens = sorted(json.loads(cache.read_text(encoding="utf-8")), key=lambda c: -(c.get("views") or 0))
            logging.info(f"[discover_canal] {len(itens)} Shorts em {url} (lista guardada)")
            return itens[:top] if top else itens
    except (OSError, ValueError):
        pass
    falta = ytdlp_vez.pausado()
    px = None
    if falta:
        # 23/10 (dona: "a produção dos recaps tem que ser máxima"): com o IP pausado o canal sem lista nova ficava SEM
        # candidato. 1) lista guardada de qualquer idade (Short antigo continua valendo; feitos/tentados são filtrados
        # depois); 2) sem lista nenhuma, consulta pequena pelo proxy (KB, não gasta a banda de emergência).
        try:
            itens = sorted(json.loads(cache.read_text(encoding="utf-8")), key=lambda c: -(c.get("views") or 0))
            if itens:
                logging.info(f"[discover_canal] IP em pausa — uso a lista guardada antiga ({len(itens)} Shorts, "
                             f"{(time.time() - cache.stat().st_mtime) / 3600:.0f} h) de {url}")
                return itens[:top] if top else itens
        except (OSError, ValueError):
            pass
        px = ytdlp_vez.proxy_url()
        if not px:
            logging.warning(f"[discover_canal] yt-dlp em pausa (YouTube barrando o IP) por mais {falta / 60:.0f} min — "
                            "sem lista agora (sem proxy)")
            return []
        logging.warning(f"[discover_canal] IP em pausa — listando {url} pelo proxy")
    # --encoding utf-8: sem ele o yt-dlp sai em cp1252 e troca o emoji do começo do título por espaço
    cmd = ["yt-dlp", "--flat-playlist", "--encoding", "utf-8", "--print",
           "%(id)s\t%(view_count)s\t%(duration)s\t%(title)s", url] + (["--proxy", px] if px else [])
    with ytdlp_vez.vez("anime: canal"):
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
    if r.returncode and ytdlp_vez.bloqueio(r.stderr):
        if px:
            ytdlp_vez.proxy_ruim(px, r.stderr)  # proxy barrado sai da roda; nunca alonga a pausa do IP de casa
        else:
            ytdlp_vez.pausar(r.stderr)
    itens = []
    for linha in (r.stdout or "").splitlines():
        p = linha.split("\t", 3)
        if len(p) < 4 or not p[0]:
            continue
        vid, views, dur, title = p
        # o título começa com emoji ("🎮 Part 2. ..."): procura o "Part N" em qualquer lugar (re.match deixava
        # a "Part 8" passar como resumo e ela foi a 1ª da fila no teste de 16/10)
        parte = re.search(r"\b(?:part|parte)\.?\s*(\d+)", title, re.I)
        try:
            d = float(dur)
        except ValueError:
            d = 0.0
        itens.append({"id": vid, "title": title.strip(), "url": f"https://www.youtube.com/shorts/{vid}",
                      "views": int(views) if views.isdigit() else 0, "duration": d,
                      "parte": int(parte.group(1)) if parte else 0, "parceiro": url})
    itens.sort(key=lambda c: -c["views"])  # 30/10 (dona): SEMPRE os mais vistos primeiro, parte ou não
    logging.info(f"[discover_canal] {len(itens)} Shorts em {url} "
                 f"({sum(1 for c in itens if not c['parte'])} resumos sem parte)")
    if itens:
        try:
            CANAL_CACHE.mkdir(parents=True, exist_ok=True)
            cache.write_text(json.dumps(itens, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass
    return itens[:top] if top else itens
