# Capas dos 8 vídeos (A/B/C = YouTube; D/E/F/G = testes de conceito, não postados).
# Roda: python gerar_todos.py [id ...]  -> Flow, só A/B/C (com a capa do parceiro de referência).
# gerar_google.py usa os mesmos prompts no modelo do Google (sem referência).
#
# 01/11 dona, 3ª rodada (reprovou de novo):
#  - "biquíni comum" não serve: cada mulher usa um BIQUÍNI-FANTASIA do tema, como os da mascote (biquíni de bruxa com
#    chapéu, biquíni de estudante, biquíni de ferreira...). Nunca peça de roupa de verdade (camisa, saia, armadura...).
#  - seios ainda pequenos.
#  - todas na mesma pose (em pé ao lado dele) não pode: cada mulher numa pose diferente do molde hipercool/Porão (de
#    quatro, no colo, deitada, abraçando por trás, por cima dele...), e a pose muda de uma capa pra outra.
#  - prompt que gerou imagem reprovada não roda de novo (proibido(), lê _prompts.jsonl x pasta reprovadas).
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

AQUI = Path(__file__).parent
OUT = AQUI / "brutas"
OUT.mkdir(exist_ok=True)
MAQ = "pc1,desktop,x200ma,acer"

# 01/11 dona (5ª vez): "continuam com seios pequenos todas" - J-cup/"bigger than her head" no fim do prompt não
# bastou; agora comparação com objeto + o corpo no começo da descrição de CADA mulher (veste())
# (o exagero "bola de basquete" fez o Flow recuar: vestiu as mulheres e diminuiu tudo). O tamanho agora vem da
# TERCEIRA referência (CORPO_REF, mulher bem peituda de capa do hipercool) e o texto volta ao que dava biquíni.
CORPO = ("ENORMOUS breasts (huge J-cup bust, heavy, round and bouncy, deep cleavage spilling out of the tiny top) - the "
         "SAME body proportions as the woman in the THIRD reference; tiny waist, very wide hips, thick thighs - "
         "ecchi manhwa proportions like the most popular harem manhwa thumbnails")
CORPO_REF = AQUI / "poses" / "de_quatro_costas_cama.png"

ROUPA = ("WARDROBE RULE (most important, check every woman): each woman wears ONLY her themed COSTUME-BIKINI described "
         "below - a micro string bikini that IS the costume, plus the small themed accessories listed (hat, tie, collar, "
         "gloves, cape strip, props). NO shirts, NO jackets, NO robes, NO dresses, NO skirts, NO pants, NO full armor, "
         "NO coats: bare belly, bare shoulders, bare legs. If any woman is wearing normal clothes the image is WRONG.")

SEGURO = ("All women are grown-up adults in their late twenties, very sensual and flirty, blushing; everything private "
          "covered by the bikini, no nudity, nothing explicit.")

FIM = ("Colors BRIGHT, SUNNY, VIVID and HIGHLY SATURATED, glossy clean manhwa art like popular manhwa recap "
       "thumbnails - never dark or gloomy. Remove ALL text, letters, numbers, logos, arrows and watermarks. "
       "Leave the top-left and top-right corners less busy for speech labels.")

# 01/11 dona (4ª rodada, "nenhuma dessas poses foi feita" + prints do hipercool): a capa que funciona é CLOSE, com UMA
# mulher ENORME ocupando a maior parte da imagem numa pose com ele (de quatro por cima dele, sentada no colo de frente,
# de quatro de costas olhando pra trás...). Cena aberta com todos em pé em volta dele = errado.
# As poses vêm das capas do hipercool (config\capas_referencia, recortadas em poses\); no Flow a imagem da pose vai
# como SEGUNDA referência; no Google (sem referência) vai só a descrição.
POSES_DIR = AQUI / "poses"
POSES = {
    "de_quatro_por_cima": "SHE tripped and fell on top of him - he lies flat on his back on the floor with a shocked "
                          "blushing face and steam from his ears; she landed on all fours over him, her face above his, "
                          "one hand on his chest, her huge round hips raised high filling the right side of the frame "
                          "closest to the camera, she looks down at him with a mischievous oops-smile",
    "de_quatro_olhando_tras": "SHE dropped something and bends down to pick it up - she is on her hands and knees in "
                              "the FOREGROUND facing the viewer, leaning toward the camera so her huge chest hangs "
                              "forward between her arms, hips raised high behind her, looking back over her shoulder "
                              "with a playful smile; he stands behind her bright red and covering his eyes but peeking "
                              "through his fingers",
    "de_quatro_costas_cama": "SHE is searching for something under the bed - on her hands and knees seen from BEHIND, "
                             "her huge round hips and thick thighs fill the right half of the frame closest to the "
                             "camera, she looks back over her shoulder at him with an innocent smile; he sits on the bed "
                             "beside her, face bright red, looking away with steam puffs from his head",
    "colo_de_frente": "SHE jumped to hug him and won't let go - he sits on a chair/bed, she sits straddling his lap "
                      "facing him with her legs wrapped around his waist, arms tight around his neck, her huge chest "
                      "pressed flat against him, their faces centimeters apart; he leans back with a panicked blushing "
                      "face, she has a happy teasing grin",
    "sentada_nele": "SHE sat on him to stop him from leaving - he lies on his back on the floor, shocked and blushing "
                    "with sweat drops; she sits right on his stomach facing the camera, knees up on both sides of him, "
                    "her huge chest front and center, cheerful teasing smile, one finger on her cheek going hmm?",
    "harem_cama": "They ALL pounced on him at once - he sits in the middle of a big bed looking overwhelmed with a "
                  "nosebleed and spiral eyes; one woman hugs him from behind pressing her huge chest on the back of his "
                  "head, another lies across his lap clinging, another kneels beside him pulling his arm into her chest",
}
ORDEM_POSES = list(POSES)
LETRA_POSE = {"A": 0, "B": 1, "C": 2, "D": 3, "E": None, "F": 4, "G": 5}  # E = harém na cama


def pose_de(obra, letra):
    """Pose da capa: E sempre harém; nas outras gira pela obra, pra cada obra ter poses diferentes nas letras."""
    if LETRA_POSE[letra] is None:
        return "harem_cama"
    i = list(OBRAS).index(obra)
    poses = [p for p in ORDEM_POSES if p != "harem_cama"]
    return poses[(LETRA_POSE[letra] + i) % len(poses)]


def veste(q, f):
    """01/11: o Flow lia "biquíni de estudante" como UNIFORME (colete + saia). Agora a peça vem descrita como duas
    peças de biquíni, e o tema só como estampa/acessório."""
    return (f"{q}, with very large breasts like the woman in the THIRD reference, wearing ONLY a tiny triangle bikini "
            f"top and a tiny string bikini bottom - {f} - the theme is ONLY the "
            f"fabric pattern and small accessories; her belly, waist, hips and thighs are completely bare (NO skirt, NO "
            f"vest, NO shirt, NO shorts)")


def mulheres_com_pose(lista, letra, pose):
    """A mulher principal (gira pela letra) faz a pose GRANDE; as outras ficam menores atrás, também sensuais."""
    principal = lista[list("ABCDEFG").index(letra) % len(lista)]
    outras = [m for m in lista if m is not principal]
    txt = (f"COMPOSITION (most important): close-up framing like the hit harem manhwa thumbnails - the MAIN WOMAN is "
           f"HUGE in the frame (fills about 60% of the image), only the hero and her in the front. POSE: {POSES[pose]}. "
           f"THE MAIN WOMAN: {veste(*principal)}.")
    if pose != "harem_cama":
        txt += (" Smaller in the background (not standing in a line, flirty poses): " +
                "; ".join(veste(q, f) for q, f in outras) + ".")
    else:
        txt += " The other women on the bed: " + "; ".join(veste(q, f) for q, f in outras) + "."
    return txt + f" Every woman has {CORPO}."


def maria(fantasia):
    return ("MARIA the mascot girl (long wavy dark-brown hair to her waist, golden-brown eyes, tanned caramel skin, "
            "beauty mark under her left eye, cheerful smile)", fantasia)


def montar(obra, letra):
    o = OBRAS[obra]
    pose = pose_de(obra, letra)
    abre = ("A brand-new 16:9 anime thumbnail. Use the FIRST reference only for the hero's face, hair and outfit and the "
            "story elements; copy the exact POSE, camera angle and close framing of the SECOND reference (redraw it "
            "with our characters and costumes - do NOT copy its clothes, text or background). From the THIRD "
            "reference copy ONLY the woman's body proportions (very large breasts, wide hips), nothing else.")
    cena = f"Story elements in the background: {o['cenas'][letra]}"
    return " ".join([abre, mulheres_com_pose(o["mulheres"], letra, pose), o["heroi"], cena, ROUPA, SEGURO, FIM])


OBRAS = {
    "ssMbrCz0fhE": {
        "heroi": ("Keep the SAME main character as the FIRST reference: messy dark-brown hair, brown eyes, leather "
                  "blacksmith apron over a white shirt, muscular arms."),
        "mulheres": [
            ("the RED-HAIRED ACADEMY GIRL (red hair in a bun, red eyes)",
             "ACADEMY-STUDENT BIKINI: red school-plaid micro string bikini, a tiny loose necktie, white thigh-high socks"),
            ("the BLONDE NOBLE GIRL (long blonde hair)",
             "NOBLE-LADY BIKINI: gold micro string bikini with lace trim, a small tiara, long white lace gloves, pearl necklace"),
            maria("BLACKSMITH BIKINI: brown leather micro string bikini, a tiny leather apron strip at the hips, welding "
                  "goggles on her head, fingerless leather gloves"),
        ],
        "cenas": {
            "A": "the blacksmith hero forging a glowing rainbow-fire sword on an anvil, sparks flying, rival students in the background pointing in shock. Sunny academy forge.",
            "B": "playful comedic: the hero sitting on a wooden bench in the forge, blushing in panic, steam from his ears. Sunny forge.",
            "C": "POWER-UP and HUMILIATION: the hero raises a legendary glowing rainbow greatsword; rival male blacksmiths kneel on the LEFT, their swords shattered, sweating in shock. Forge with fire and sparks.",
            "D": "BEFORE vs AFTER split: LEFT dark - the hero as a weak boy with a rusty hammer at a ruined forge; RIGHT golden-bright - the hero muscular with a legendary rainbow sword and the women around him.",
            "E": "PURE HAREM: the hero sits on a big anvil-throne in a grand forge, the women all over him. Rainbow fire sparks.",
            "F": "FUNNY: the hero proudly shows a sword but the women only stare at his muscles, he sweats confused. Sunny forge.",
            "G": "MYSTERY: extreme close-up of the hero's face, one eye glowing with rainbow fire, half-smile, the women in the lower part of the frame.",
        },
    },
    "vMyOmvaaFIk": {
        "heroi": ("Keep the SAME main character as the FIRST reference: spiky dark hair, purple jacket over a white "
                  "shirt, confident smirk, golden SSS lightning aura."),
        "mulheres": [
            ("the BLONDE STUDENT (short blonde hair, blue eyes)",
             "STUDENT BIKINI: navy micro string bikini with a big red bow tie, a white sailor collar, knee socks"),
            ("the BRUNETTE STUDENT (long brown hair, glasses)",
             "CLASS-PRESIDENT BIKINI: white micro string bikini with a red armband, a necktie, black thigh-high stockings"),
            maria("ACADEMY GOLD-RANK BIKINI: purple-and-gold micro string bikini with a tiny golden badge, a school tie"),
        ],
        "cenas": {
            "A": "the hero stepping out of a golden energy portal with SSS lightning aura on the LEFT; on the RIGHT male students cowering and sweating. Sunny school courtyard with a clock tower.",
            "B": "playful comedic: the hero leaning against the school gate, arms crossed, smug but blushing. Sunny courtyard.",
            "C": "POWER-UP and HUMILIATION: the hero with a golden SSS aura and an energy blast behind him; rival male students kneel defeated, uniforms torn. School arena.",
            "D": "BEFORE vs AFTER split: LEFT dark - the hero alone, rank F, laughed at; RIGHT bright - the hero with SSS aura and the women around him.",
            "E": "PURE HAREM: the hero sits on the teacher's desk in a sunny classroom, the women all over him.",
            "F": "FUNNY: the hero's ranking test machine explodes, he scratches his head embarrassed, the women react. Classroom.",
            "G": "MYSTERY: extreme close-up of the hero's face, golden SSS glow in his eyes, the women in the lower part of the frame.",
        },
    },
    "XNKCOSdfMrU": {
        "heroi": ("Keep the SAME main character as the FIRST reference: dark messy hair, blue hoodie, calm expression, "
                  "glowing magic supply crates floating around him."),
        "mulheres": [
            ("the EX-GIRLFRIEND (long black hair, desperate teary eyes)",
             "SURVIVOR BIKINI: torn black micro string bikini, dirt smudges, a bandage on her thigh, fingerless gloves"),
            ("the PINK-HAIRED SURVIVOR (short pink hair, tough look)",
             "MILITARY BIKINI: camo-pattern micro string bikini, a bandolier across her chest, combat boots, dog tags"),
            maria("SOLDIER BIKINI: olive-green micro string bikini, a military cap, dog tags, combat boots"),
        ],
        "cenas": {
            "A": "split composition - LEFT dark blue with zombies chasing; RIGHT warm and bright with the hero above a stocked convenience store holding glowing supply crates.",
            "B": "playful comedic: the hero sits on stacked supply crates in his fortified shelter, smug and blushing. Shelter full of food.",
            "C": "POWER-UP and HUMILIATION: LEFT a ruined city with zombies and desperate male survivors pressing on a glowing barrier; RIGHT his bright safe shelter with food, the hero smug.",
            "D": "BEFORE vs AFTER split: LEFT - the ex-girlfriend laughing at him before the apocalypse on a sunny beach; RIGHT - the hero rich in his shelter, she outside crying.",
            "E": "PURE HAREM: the hero on a throne of supply crates inside a cozy shelter, the women all over him.",
            "F": "FUNNY: the hero eats a fancy meal pretending not to see the ex-girlfriend begging at the window; zombies photobomb.",
            "G": "MYSTERY: extreme close-up of the hero's calm face behind shelter glass, glowing crates reflected in his eyes, the women in the lower part of the frame.",
        },
    },
    "ZIGA4roGbmQ": {
        "heroi": ("Keep the SAME main character as the FIRST reference: brown hair, muscular shirtless torso covered in "
                  "battle scars, confident smirk."),
        "mulheres": [
            ("the WHITE-HAIRED BULLY GIRL (long straight white hair, red eyes, arrogant turned flustered)",
             "DELINQUENT-STUDENT BIKINI: white micro string bikini with a loose school tie, an open sailor collar, knee socks"),
            ("the PINK-HAIRED CLASSMATE (twintails, cheerful)",
             "CHEERLEADER BIKINI: pink-and-white micro string bikini with pom-poms and ribbons in her hair"),
            maria("GYM-CLASS BIKINI: navy sporty micro string bikini with a name tag, a sweatband, knee socks"),
        ],
        "cenas": {
            "A": "face-off - the scarred hero on the LEFT smirking, the white-haired girl on the RIGHT shocked. School window background.",
            "B": "playful comedic: the hero leans against a school locker, arms crossed, blushing. School hallway.",
            "C": "POWER-UP and HUMILIATION: the hero stands in a school gym with an assassin aura, male bullies lying defeated around him.",
            "D": "BEFORE vs AFTER split: LEFT - the hero bullied by big male students; RIGHT - the hero shirtless with scars, the bullies on the floor, the women around him.",
            "E": "PURE HAREM: the hero sits on a school desk, the women all over him. Sunny classroom.",
            "F": "FUNNY: the bully girl's punch is stopped by one of his fingers, he is completely unfazed. School courtyard.",
            "G": "MYSTERY: extreme close-up of the hero's scarred face, one eye glowing red, half-smile, the women in the lower part of the frame.",
        },
    },
    "KkJZkt3TpwI": {
        "heroi": ("Keep the SAME main character as the FIRST reference: white/silver hair, bright blue eyes, round "
                  "glasses, long black hooded cloak, casting blue-black void orbs."),
        "mulheres": [
            ("the ELF MAGE (long golden hair, pointed ears, green eyes)",
             "ELF-MAGE BIKINI: white-and-gold micro string bikini with gold body chains, a leaf circlet, a small magic staff"),
            ("the DARK PRIESTESS (long purple hair, red eyes)",
             "DARK-PRIESTESS BIKINI: black micro string bikini with glowing purple runes, a small veil, long black gloves"),
            maria("WITCH BIKINI: dark-purple micro string bikini, a big pointy witch hat, a tiny short cape, striped "
                  "thigh-high stockings, holding a broom"),
        ],
        "cenas": {
            "A": "the white-haired orphan mage in the center casting blue-black void orbs, magical forest with floating blue particles.",
            "B": "playful comedic: the hero sits on a mossy rock in a moonlit magic forest clearing, blushing in panic.",
            "C": "POWER-UP and HUMILIATION: the hero floats with a massive void-magic explosion behind him; rival male mages on the ground, staffs broken, cowering.",
            "D": "BEFORE vs AFTER split: LEFT - the hero as a ragged orphan boy begging in the rain; RIGHT - the hero as a powerful mage with the women around him.",
            "E": "PURE HAREM: the hero on a glowing throne of vines in a moonlit clearing, the women all over him.",
            "F": "FUNNY: the hero's void portal sucks up the witch hat and the staff, he covers his eyes in panic. Magic forest.",
            "G": "MYSTERY: extreme close-up of the hero's face, glasses reflecting void orbs, the women in the lower part of the frame.",
        },
    },
    "4wufdzeZKgs": {
        "heroi": ("Keep the SAME main character as the FIRST reference: black hair, sharp eyes, long black coat with "
                  "purple aura, cold assassin expression."),
        "mulheres": [
            ("the WHITE-HAIRED GODDESS (long white hair, glowing skin)",
             "GODDESS BIKINI: white-and-gold micro string bikini, a glowing halo, gold arm cuffs, a thin floating shawl"),
            ("the PINK-HAIRED CLASSMATE",
             "SCHOOL BIKINI: plaid micro string bikini with a sailor collar and a necktie"),
            ("the BLUE-HAIRED CLASSMATE",
             "ADVENTURER BIKINI: brown leather micro string bikini with a dagger belt and a tiny short cape"),
            maria("NINJA-ASSASSIN BIKINI: black micro string bikini, a red scarf around her neck, a kunai garter on her "
                  "thigh, arm wraps"),
        ],
        "cenas": {
            "A": "the assassin hero on the RIGHT with purple aura facing the goddess and classmates on the LEFT. Isekai portal background.",
            "B": "playful comedic: the hero sits on a dark throne, blushing in panic. Fantasy throne room.",
            "C": "POWER-UP and HUMILIATION: the hero with dual shadow daggers and a purple aura explosion; the male classmates who bullied him kneel terrified. Isekai battlefield.",
            "D": "BEFORE vs AFTER split: LEFT - the hero pushed to the ground by male classmates; RIGHT - the hero as a dark assassin lord with the women around him.",
            "E": "PURE HAREM: the hero on a dark throne with purple light, the women all over him.",
            "F": "FUNNY: the goddess tries to hug him but he dodges with assassin reflexes and she falls, the others laugh. Isekai castle.",
            "G": "MYSTERY: extreme close-up of the hero's face, one eye glowing purple, cold half-smile, the women in the lower part of the frame.",
        },
    },
    "PFbuZNbc6cA": {
        "heroi": ("Keep the SAME main character as the FIRST reference: auburn/reddish-brown hair, very muscular, "
                  "primitive fur clothing, confident modern expression."),
        "mulheres": [
            ("the LEOPARD CAT-GIRL (orange-blonde hair in twin buns, leopard ears and tail)",
             "TRIBAL-LEOPARD BIKINI: leopard-fur micro string bikini with a bone necklace and a feather in her hair"),
            ("the TIGER CAT-GIRL (blonde hair with bangs, tiger ears and tail)",
             "TIGER-HUNTRESS BIKINI: tiger-stripe fur micro string bikini with a fang necklace, holding a spear"),
            maria("CAVEGIRL BIKINI: brown fur micro string bikini, a bone hair clip, a wooden club over her shoulder"),
        ],
        "cenas": {
            "A": "the muscular hero sitting on a fur-covered log in a lush sunny jungle with colorful flowers.",
            "B": "playful comedic: the hero sits on a stone throne in a jungle clearing, blushing.",
            "C": "POWER-UP and HUMILIATION: LEFT primitive huts and scared male tribesmen kneeling; RIGHT his modern fortress, the hero holding a forged iron weapon.",
            "D": "BEFORE vs AFTER split: LEFT - a dark cave with the hero alone and starving; RIGHT - the hero on a fur throne in a modern village with the women around him.",
            "E": "PURE HAREM: the hero lies on a pile of furs by a waterfall, the women all over him.",
            "F": "FUNNY: the hero shows a lighter's flame and the cat-girls jump back hissing with their fur puffed up. Jungle.",
            "G": "MYSTERY: extreme close-up of the hero's face, his eye reflecting a modern fortress, the women in the lower part of the frame.",
        },
    },
    "KbLvZJy0B3Q": {
        "heroi": ("Keep the SAME main character as the FIRST reference: white/silver hair, very muscular, leather "
                  "collar around his neck, tanned skin, bare chest."),
        "mulheres": [
            ("the PURPLE CAT-GIRL (long purple-grey hair, cat ears and tail, violet eyes)",
             "BEASTKIN BIKINI: purple micro bikini made of bandage wraps, a bell collar"),
            ("the WOLF GIRL (silver hair, wolf ears and tail, blue eyes)",
             "WOLF-WARRIOR BIKINI: blue fur micro string bikini with a fang necklace and fur arm cuffs"),
            maria("BEAST-TAMER BIKINI: red leather micro string bikini, a whip on her hip, a cat-ear headband"),
        ],
        "cenas": {
            "A": "the muscular hero embraced by the purple cat-girl, romantic fantasy background with floating petals.",
            "B": "playful comedic: the hero sits on a stone floor in a softly lit fantasy dungeon, blushing.",
            "C": "POWER-UP and HUMILIATION: the hero breaks free from chains with a glowing aura, defeated male beast-tamers on the ground. Fantasy arena.",
            "D": "BEFORE vs AFTER split: LEFT - the hero chained as a slave in a dark dungeon; RIGHT - the hero free and powerful with the women around him.",
            "E": "PURE HAREM: the hero lies on luxurious furs in a candle-lit fantasy chamber, the women all over him.",
            "F": "FUNNY: the cat-girl offers him a collar with a heart tag, he recoils in panic. Fantasy room.",
            "G": "MYSTERY: extreme close-up of the hero's face, one eye glowing with beast power, collar cracking, the women in the lower part of the frame.",
        },
    },
}

TODOS = {vid: {l: montar(vid, l) for l in "ABCDEFG"} for vid in OBRAS}

# 01/11 dona: cada obra numa subpasta (dentro de brutas/ e de brutas_google/), arquivo = só a letra (A.png...);
# reprovadas dela em <obra>\reprovadas\
NOMES = {
    "ssMbrCz0fhE": "Ferreiro Genio",
    "vMyOmvaaFIk": "Unico Rank SSS",
    "XNKCOSdfMrU": "Ex-Namorada Apocalipse",
    "ZIGA4roGbmQ": "Assassino na Escola",
    "KkJZkt3TpwI": "Orfao Magia Rara",
    "4wufdzeZKgs": "Assassino e a Deusa",
    "PFbuZNbc6cA": "Idade da Pedra",
    "KbLvZJy0B3Q": "Garota Gato",
}


def pasta(raiz, vid):
    p = raiz / f"{NOMES[vid]} ({vid})"
    p.mkdir(parents=True, exist_ok=True)
    return p


def registrar(raiz, vid, letra, gerador, prompt):
    """Prompt de cada imagem fica gravado em <raiz>\\_prompts.jsonl."""
    import time
    with open(raiz / "_prompts.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({"obra": vid, "letra": letra, "gerador": gerador, "quando": time.strftime("%Y-%m-%d %H:%M"),
                            "prompt": prompt}, ensure_ascii=False) + "\n")


def proibido(raiz, vid, letra, prompt):
    """Dona 01/11: prompt que gerou imagem reprovada não se usa mais. Reprovada = a letra está em <obra>\\reprovadas e
    não na pasta da obra; o prompt registrado pra ela é o mesmo de agora."""
    p = pasta(raiz, vid)
    if (p / f"{letra}.png").exists() or not any((p / "reprovadas").glob(f"{letra}*.png")):
        return False
    try:
        linhas = (raiz / "_prompts.jsonl").read_text(encoding="utf-8").splitlines()
    except OSError:
        return False
    return any(json.loads(x).get("obra") == vid and json.loads(x).get("letra") == letra and
               json.loads(x).get("prompt") == prompt for x in linhas if x.strip())


def um(vid, letra, prompt):
    """Uma capa no Flow. Ref = só a capa do parceiro (a Maria vai descrita no prompt, com a fantasia da obra)."""
    p = pasta(OUT, vid)
    saida = p / f"{letra}.png"
    if saida.exists():
        return f"{NOMES[vid]} {letra} já existe"
    if proibido(OUT, vid, letra, prompt):
        return f"{NOMES[vid]} {letra}: prompt já reprovado, não gero de novo"
    logs = OUT / "_logs"
    logs.mkdir(exist_ok=True)
    try:
        r = subprocess.run([r"D:\veo\venv\Scripts\python.exe", r"D:\flow-imagens\gera_imagem.py", prompt,
                            str(saida), "--ref", str(AQUI / f"parceiro_{vid}.jpg"),
                            str(POSES_DIR / f"{pose_de(vid, letra)}.png"), str(CORPO_REF), "--formato", "16:9",
                            "--quantidade", "1", "--maquinas", MAQ, "--max-contas", "6"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1800,
                           creationflags=0x08000000)
        (logs / f"{vid}_{letra}.log").write_text(r.stdout[-4000:] + "\n---\n" + r.stderr[-4000:], encoding="utf-8")
    except subprocess.TimeoutExpired:
        return f"{NOMES[vid]} {letra}: TIMEOUT 30 min"
    if saida.exists():
        registrar(OUT, vid, letra, "flow", prompt)
    return f"{NOMES[vid]} {letra}: {'OK' if saida.exists() else 'FALHOU rc=' + str(r.returncode)}"


if __name__ == "__main__":
    ids = [a for a in sys.argv[1:] if not a.startswith("-")] or list(TODOS)
    letras = next((a[2:] for a in sys.argv[1:] if a.startswith("--") and a[2:].isalpha()), "ABC")
    # 01/11 dona: no Flow só A/B/C (precisam do protagonista da capa original como referência)
    tarefas = [(v, l, TODOS[v][l]) for v in ids for l in letras]
    with ThreadPoolExecutor(2) as ex:
        for r in ex.map(lambda t: um(*t), tarefas):
            print(r, flush=True)
