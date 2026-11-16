#!/usr/bin/env python3
"""Lista os PROTEGIDOS agrupados por CATEGORIA (anime/jogo/filme/artista/funk...)."""
import os, re
import importlib
from pathlib import Path.util

spec = importlib.util.spec_from_file_location("cc", str(Path(__file__).resolve().parent / "classificar_copyright.py"))
cc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cc)

# categoria por padrao no nome (ordem importa)
CATS = [
    ("Jogo - Pokémon", [r"pok[eé]mon|hgss|omega ruby|sun & moon|sword"]),
    ("Jogo - Mario/Nintendo", [r"\bmario\b|yoshi|mario kart"]),
    ("Jogo - Kirby", [r"kirby|dedede|meta knight|gourmet race|morpho"]),
    ("Jogo - Sonic", [r"\bsonic\b|metal sonic|green hill|metallic madness|stardust speedway"]),
    ("Jogo - Zelda", [r"zelda|lost woods|wind waker|ocarina"]),
    ("Jogo - Undertale/Deltarune", [r"undertale|deltarune|megalovania|bonetrousle|sans|flowey|rude buster|mad mew"]),
    ("Jogo - Rockstar (GTA/RDR/Bully/Midnight Club)", [r"\bgta\b|grand theft|red dead|\brdr\b|bully|midnight club|real big"]),
    ("Jogo - Resident Evil", [r"resident evil|master reset.*resident"]),
    ("Jogo - outros (FNAF/Mega Man/SF/etc)", [r"\bfnaf\b|security breach|mega ?man|megaman|street fighter|blazblue|ginga force|castle crashers|celeste|plants vs|club penguin|touchgrind|skeleton boomerang|vlad to the bone"]),
    ("Anime - JoJo", [r"jojo|bizarre|giorno|narancia|stardust crusader|dio\b|josuke|nella cerniera|bruno"]),
    ("Anime - Naruto", [r"naruto|konohamaru|hinata vs neji|raising fighting"]),
    ("Anime - Dragon Ball", [r"dragon ?ball"]),
    ("Anime - HxH", [r"\bhxh\b|hunter x|meruem"]),
    ("Anime - Re:Zero", [r"re:?zero|rezero"]),
    ("Anime - outros (Higurashi/Evangelion/Your Name)", [r"higurashi|evangelion|cruel angel|your name|kimi no na|radwimps|taku iwasaki|karakuri"]),
    ("Filme/TV - Pixar/Disney/DreamWorks", [r"toy story|despicable me|ratatouille|\bup ost\b|up with end|we_re in the club|steven universe|spongebob|ren and stimpy"]),
    ("Filme/TV - outros", [r"walking dead|last of us|titanic|baby \(netflix\)|netflix|chespirito|winky dink|pai de fam[ií]lia|family guy"]),
    ("Música comercial - rap/hip-hop", [r"snoop dog|post malone|method man|drop it like|tokyo drift|teriyaki|hot action cop|hdbeendope|dustystaytrue|goblins from mars|ivan b|cxdy|k-rino|raptile|scott gaddy|pia mia"]),
    ("Música comercial - BR (funk/MPB)", [r"marcelo d2|seu jorge|sikeira|siqueira|cpf cancelado|funk d[ao]|funk das|fnaf funk|winx|automotivo|velozes|furioso|atlxs|passo bem solto"]),
    ("Música comercial - rock/pop/outros", [r"b\.j\.?thomas|raindrops keep|chris rae|chris rea|the doors|riders on the storm|what so not|slumberjack|standing here.*realize|not the king|ice tea|brothers record|coda|herb al|spanish flea|japanese goblin|doom|final countdown"]),
]


def categorize(name):
    low = name.lower()
    for catname, pats in CATS:
        for p in pats:
            if re.search(p, low):
                return catname
    return "Outros protegidos (rever)"


files = sorted(os.listdir(cc.TRILHAS))
files = [f for f in files if f.lower().endswith((".mp3",".wav",".m4a",".opus",".flac"))]
prot = [f for f in files if cc.classify(f)[0] == "PROTEGIDO"]

groups = {}
for f in prot:
    groups.setdefault(categorize(f), []).append(f)

total = 0
for cat in sorted(groups, key=lambda k: -len(groups[k])):
    lst = groups[cat]
    total += len(lst)
    print(f"\n## {cat} ({len(lst)})")
    for f in sorted(lst):
        print(f"  - {f}")
print(f"\n=== TOTAL PROTEGIDO: {total} ===")
