# COMUM — fonte única: D:\hipercool-materiais\comum\sfx_categorizer.py. Mudou esta cópia? python D:\hipercool-materiais\bin\recursos.py subir sfx_categorizer.py --de <projeto>
"""sfx_categorizer.py — Categoriza SFX/memes por mood baseado no nome do arquivo.

Gera um JSON com mapeamento nome → categoria pra uso no effects_engine.
"""
import os
import json
import re
from pathlib import Path

SFX_DIR = Path(__file__).resolve().parent.parent / "workspace" / "assets" / "sfx_memes"
OUTPUT = Path(__file__).resolve().parent.parent / "workspace" / "assets" / "sfx_memes_categorized.json"

# Palavras-chave por categoria
CATEGORIES = {
    "comedia": [
        "meme", "haha", "risada", "engraçad", "piada", "peido", "fart", "bruh",
        "chaves", "faustão", "ratinho", "zoio", "cartoon", "boing", "slip",
        "bonk", "goofy", "banana", "pepino", "burro", "idiota", "palhaç",
        "thug life", "amogus", "impostor", "roblox", "yeet", "monke", "macaco",
        "sapo", "pinguim", "dolphin", "esquilo", "frog", "nerd", "beta",
        "sarcasm", "irra", "cowboy", "fortinaiti", "discord", "minecraft eat",
        "resposta errada", "wrong answer", "fail", "ba dum", "tadaah",
        "children yay", "crowd", "olé", "que fofa", "dori dori",
    ],
    "impacto": [
        "soco", "punch", "boom", "explosion", "impacto", "impact", "bass hit",
        "slam", "crash", "smash", "hit", "golpe", "strike", "tiro", "shot",
        "rifle", "metralhadora", "espada", "sword", "knife", "faca", "chicote",
        "whip", "bone crack", "metal pipe", "anvil", "lego break", "vidro",
        "quebrando", "copo", "shatter", "tatakae", "ora ora", "star platinum",
        "fatality", "finish him", "get over here", "wasted", "eren scream",
        "titan", "killer queen", "vine boom", "cinematic boom",
    ],
    "suspense": [
        "suspense", "riser", "horror", "danger", "alarm", "tension",
        "dramatic", "inception", "flashback", "conspiracy", "slenderman",
        "creepy", "cave ambience", "hells kitchen", "waterphone",
        "long suspense", "dark", "sinistro", "demon", "diabo",
        "emergencia", "enemy spotted", "rewind", "glitch",
    ],
    "tristeza": [
        "sad", "triste", "chorand", "lágrima", "boowomp", "spongebob sad",
        "chorando", "cry", "emotional", "melancol", "despedida",
        "morte", "morreu", "didi", "funeral",
    ],
    "romance": [
        "beijo", "kiss", "amor", "love", "heart", "fofa", "fofo",
        "angel", "sparkle", "magic", "romantic", "carinho",
        "som de beijo", "aleluia",
    ],
    "transicao": [
        "whoosh", "woosh", "swoosh", "slide", "click", "pop", "snap",
        "page turn", "paper", "shutter", "camera", "flash", "wind",
        "air-woosh", "transition", "warp", "teleport", "poof",
        "sonido de desaparecer", "throw", "falling",
    ],
    "sistema": [
        "minecraft", "level up", "item pickup", "potion", "xp",
        "windows", "iphone", "notification", "discord", "ps2",
        "gta", "sonic", "coin", "moeda", "cash register",
        "caixa registradora", "buzzer", "bip",
    ],
}


def categorize_file(filename):
    """Categoriza um arquivo pelo nome."""
    name_lower = filename.lower()
    scores = {}
    for cat, keywords in CATEGORIES.items():
        score = sum(1 for kw in keywords if kw in name_lower)
        if score > 0:
            scores[cat] = score
    if scores:
        return max(scores, key=scores.get)
    return "neutro"


def main():
    if not SFX_DIR.exists():
        print(f"Pasta não encontrada: {SFX_DIR}")
        return

    files = [f for f in os.listdir(SFX_DIR) if f.endswith(('.mp3', '.wav', '.mp4'))]
    categorized = {}
    stats = {}

    for f in sorted(files):
        cat = categorize_file(f)
        categorized[f] = cat
        stats[cat] = stats.get(cat, 0) + 1

    # Salvar JSON
    output_data = {
        "total": len(files),
        "categories": stats,
        "files": categorized,
    }
    OUTPUT.write_text(json.dumps(output_data, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Categorizado: {len(files)} arquivos")
    for cat, count in sorted(stats.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")


if __name__ == "__main__":
    main()
