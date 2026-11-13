#!/usr/bin/env python3
"""Classifica trilhas por risco de copyright a partir do NOME do arquivo + achados de audio.

Saida: 3 listas (PROTEGIDO / LIVRE / INCERTO) impressas e contagem.
Heuristica conservadora: na duvida -> INCERTO (revisar por audio).
"""
import os, re, sys

TRILHAS = r"D:\hipercool-materiais\assets\trilhas"

# achados confirmados por audio/fingerprint nesta sessao (sobrepoem heuristica)
CONFIRMADO_PROTEGIDO = {
    "sad_emotional.mp3": "Naruto OST - Sadness and Sorrow (Toshio Masuda)",
    "tense_dramatic.mp3": "Higurashi OST",
    "jungle_survival_theme.mp3": "The Last of Us main theme (G. Santaolalla)",
    "neutral_chill.mp3": "Naruto OST - Hinata vs Neji",
    "Overdrive.mp3": "Taku Iwasaki (OST anime)",
    "Angst.mp3": "Myuu (artista) - possivel monetizado",
    "Married Life.mp3": "Up / Michael Giacchino (OST filme)",
    # fingerprint AcoustID (confiavel) + julgamento por nome
    "hxh_returned_theme.mp3": "FP: ATLXS - Passo Bem Solto (funk/phonk comercial)",
    "MÚSICA QUE O PIUZINHO USA NOS VÍDEOS! (128 kbps).mp3": "FP: Raptile - Fight Back",
    "Third Eye(MP3_320K).mp3": "FP: Scott Gaddy - Third Eye",
    "Sad Emotional Piano Music - Gaming Background Music (HD).mp3": "FP: Pia Mia - Touch",
    "Coda- Tires On Fire.mp3": "nome: banda comercial",
    "Cxdy _ Hollow Bells(MP3_320K).mp3": "Cxdy - produtor trap comercial",
    "DOOM OST_ E1M1-At Doom_s Gate HELL YEAH!!!!!.mp3": "DOOM OST (id Software)",
    "Ivan B - Make It Ourselves (ft. Hendersin) (Prod. Tido Vegas).mp3": "Ivan B (rapper)",
    "Josuke theme but it_s only the good part.mp3": "JoJo P4 'Great Days' (Warner JP)",
    "Karakuri Spirits (MEIKAI ARRANGE).mp3": "arranjo OST jogo/doujin",
    "Not The King. 👑 - Ice Tea (320 kbps).mp3": "lançamento comercial",
    "Sleeplessness - The Brothers Record (320 kbps).mp3": "The Brothers Record (artista lofi)",
    "Sudden Changes Sans Song [OverSave-Tale].mp3": "Undertale (Toby Fox) remix",
    "sudden change sans theme (remix by Kaeny).mp3": "Undertale (Toby Fox) remix",
    "Track 15 - Vlad To The Bone (Final Boss Phase 2) - Skeleton Boomerang_ Vampire Hunter Mode.mp3": "OST jogo Skeleton Boomerang",
    "Spanish Flea (Herb Albert) - Comedy Background.mp3": "Herb Alpert - Spanish Flea (1965)",
}
CONFIRMADO_LIVRE = {
    "calm_chill.mp3": "Bensound - Acoustic Breeze (royalty-free c/ atribuicao)",
    "funny_lighthearted.mp3": "YouTube Audio Library",
    "romantic_sexy.mp3": "YouTube Audio Library",
    "Dog_Park.mp3": "YouTube Audio Library",
    "Monks.mp3": "mmodule (royalty-free)",
    "The Lobotomy.mp3": "Maebi (royalty-free)",
    "Magic.mp3": "Otis McDonald (YouTube Audio Library)",
    "Drive.mp3": "Moonlight Zoo (royalty-free)",
    # fingerprint + nome confiavel
    "musica piano tranquila.mp3": "FP: Kevin MacLeod - Five Card Shuffle",
    "Lo-fi Music no copiryght.mp3": "FP: Artificial.Music (canal no-copyright)",
    "Icelandic Arpeggios - DivKid.mp3": "DivKid - YouTube Audio Library",
    "Mac Taboel - Mistaken by Accident.mp3": "YouTube Audio Library",
    "Y2mate.mx - Dramedy - Sneaky and Mischievous (128 kbps).mp3": "Kevin MacLeod (YT Audio Lib)",
    "MUSICA QUE O MASTER RESET USA NOS VIDEO(arts of silence) (128 kbps).mp3": "Arts of Silence (royalty-free)",
    "Ambient Hum Pitched.mp3": "efeito ambiente, sem composicao",
    "Ring High Pitch.mp3": "efeito telefone, sem composicao",
    "EFEITOS SONOROS DE IMPACTO PARA EDIÇÃO - FREE FIRE EDITS (128 kbps).mp3": "pacote SFX impacto",
    "Trance Music for Racing Game.mp3": "trance banco generico",
    "FUNDO MUSICAL _ SUSPENSE _ TERROR _ HORROR THEMES _ MÚSICAS DE TERROR _ SOUNDTRACK 65 (128 kbps).mp3": "trilha banco terror",
}
# composicao em dominio publico mas GRAVACAO pode ter direito conexo - conferir caso use
DOMINIO_PUBLICO = {
    "Grieg - In The Hall Of The Mountain King (128 kbps).mp3": "Grieg 1875 (comp. DP; gravação a conferir)",
    "Satie - Gymnopedie no1 (128 kbps).mp3": "Satie 1888 (comp. DP; gravação a conferir)",
    "_Amazing Grace_ first⧸earliest⧸oldest⧸original recording - 1922 by Original Sacred Harp Choir.mp3": "1922 - dominio publico",
}

# franquias/artistas comerciais ou OSTs protegidas (sinais no nome)
PROT_PATTERNS = [
    r"pok[eé]mon", r"\bmario\b", r"kirby", r"\bsonic\b", r"undertale", r"deltarune",
    r"zelda", r"\bgta\b", r"grand theft", r"red dead", r"\brdr2?\b", r"naruto",
    r"jojo|bizarre|giorno|narancia|stardust|dio\b", r"dragon ?ball", r"\bhxh\b|hunter x",
    r"re:?zero|rezero", r"meruem", r"minecraft|c418", r"crash bandicoot|twinsanity",
    r"mega ?man", r"megaman", r"resident evil", r"\bfnaf\b|security breach",
    r"plants vs", r"club penguin", r"toy story", r"despicable me", r"ratatouille",
    r"\bup ost\b|up with end|we_re in the club", r"walking dead", r"last of us",
    r"castle crashers", r"celeste", r"steven universe", r"spongebob", r"ren and stimpy",
    r"snoop dog|post malone|bob marley|mick jagger|teriyaki|tokyo drift|method man",
    r"marcelo d2|seu jorge|sikeira|siqueira", r"the doors|riders on the storm",
    r"bully", r"midnight club", r"touchgrind", r"nfs|need for speed|underground",
    r"blazblue", r"ginga force", r"street fighter", r"mario kart", r"yoshi",
    r"super street fighter", r"metal sonic", r"dedede", r"meta knight", r"gourmet race",
    r"honeycomb highway", r"baby \(netflix\)|netflix", r"chespirito|winky dink",
    r"pai de fam[ií]lia|family guy", r"titanic", r"animal crossing|isabelle",
    r"hot action cop", r"what so not|slumberjack", r"dustystaytrue", r"hdbeendope",
    r"goblins from mars", r"chris rae|chris rea", r"b\.j\.?thomas|raindrops keep",
    r"standing here.*realize", r"automotivo|funk d[ao]|funk das|fnaf funk|winx",
    r"cpf cancelado", r"velozes|furioso", r"japanese goblin|we are japanese",
]

# sinais de LIVRE no nome
LIVRE_PATTERNS = [
    r"no copyright|non copyright|sem direitos autorais|copyright free|copyright-free",
    r"\bncs\b|ncs release", r"neffex", r"\bkevin\b|macleod|kevin macleod",
    r"patrik|patrikios", r"anno domini", r"ofshane", r"cheel", r"vyen",
    r"dj freedem", r"french fuse", r"asher fulero", r"jimena contreras", r"godmode",
    r"unicorn heads", r"silent partner", r"tracktribe", r"wayne jones", r"quincas moreira",
    r"bobby richards", r"emmit fenn", r"nana kwabena", r"jimmy fontanez", r"esther abrami",
    r"andrew langdon", r"brian bolger", r"tony hymas", r"mini vandals", r"bluejacket",
    r"uso livre|uso live|free for profit|free download|royalty", r"teknoaxe",
    r"djquads|dj quads|ryan little|lukrembo|biscoit", r"media right",
    r"infraction", r"kitsune", r"y2mate.*no copyright", r"omicron prime.*sem direitos",
]


def classify(name):
    if name in CONFIRMADO_PROTEGIDO:
        return "PROTEGIDO", "AUDIO/FP: " + CONFIRMADO_PROTEGIDO[name]
    if name in CONFIRMADO_LIVRE:
        return "LIVRE", "AUDIO/FP: " + CONFIRMADO_LIVRE[name]
    if name in DOMINIO_PUBLICO:
        return "DOMINIO_PUBLICO", DOMINIO_PUBLICO[name]
    low = name.lower()
    for p in LIVRE_PATTERNS:
        if re.search(p, low):
            return "LIVRE", f"nome: {p}"
    for p in PROT_PATTERNS:
        if re.search(p, low):
            return "PROTEGIDO", f"nome: {p}"
    return "INCERTO", "nome generico - revisar por audio"


def main():
    files = sorted(os.listdir(TRILHAS))
    files = [f for f in files if f.lower().endswith((".mp3", ".wav", ".m4a", ".opus", ".flac"))]
    buckets = {"PROTEGIDO": [], "DOMINIO_PUBLICO": [], "INCERTO": [], "LIVRE": []}
    for f in files:
        cat, motivo = classify(f)
        buckets[cat].append((f, motivo))
    for cat in ("PROTEGIDO", "DOMINIO_PUBLICO", "INCERTO", "LIVRE"):
        print(f"\n===== {cat} ({len(buckets[cat])}) =====")
        for f, m in buckets[cat]:
            print(f"  [{m}] {f}")
    print(f"\nTOTAL: {len(files)} | PROT={len(buckets['PROTEGIDO'])} "
          f"DP={len(buckets['DOMINIO_PUBLICO'])} INCERTO={len(buckets['INCERTO'])} "
          f"LIVRE={len(buckets['LIVRE'])}")


if __name__ == "__main__":
    main()
