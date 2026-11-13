import re

with open("D:/recapd-ambientes/producao/bin/anime_discover.py", "r", encoding="utf-8") as f:
    codigo = f.read()

# Substituir o short queries para buscar coisas garantidamente curtas (shorts de anime recaps / facts)
old_short_queries = """SHORT_QUERIES = [
    "anime story #shorts",           # Sem "recap", pra achar shorts nativos de história
    "anime facts #shorts",
    "anime lore #shorts",
    "curiosidades anime #shorts",    # português
    "resumo anime #shorts",          # mantém resumo
    "historia anime #shorts",        # espanhol/pt
    "アニメ 解説 shorts",             # japonês
    "애니 요약 쇼츠",                 # coreano
]"""

new_short_queries = """# No V2 usamos a aba do YT garantida de shorts (/hashtag/shorts), mas como yt-dlp não permite flat-playlist na aba shorts de forma simples
# Vamos pescar videos com duraçao ESTRITA < 60s
SHORT_QUERIES = [
    "anime story short recap",           
    "anime short facts",
    "anime short lore",
    "curiosidades anime curto",
    "anime daily trivia",
    "anime resenha rapida",
    "アニメ 解説 1分",             # japonês 1 minuto
    "애니 요약 1분",               # coreano 1 minuto
]"""

codigo = codigo.replace(old_short_queries, new_short_queries)

# Atualizar o discover_shorts para max_dur=65 pra não baixar vídeos de 3 minutos como Shorts!
codigo = codigo.replace(
    "def discover_shorts(queries=None, per_query=40, min_dur=8, max_dur=180, top=10,",
    "def discover_shorts(queries=None, per_query=40, min_dur=8, max_dur=65, top=10,"
)

with open("D:/recapd-ambientes/producao/bin/anime_discover.py", "w", encoding="utf-8") as f:
    f.write(codigo)
