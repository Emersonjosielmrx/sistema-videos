"""capa_longo_v2.py — prompts das capas A/B/C (e D-G de teste) do LONGO de parceiro, nas regras da dona de 01/11/2026
(D:\\video-fila\\engenharia_reversa\\CAPAS_REFERENCIA.md; testes em D:\\hipercool-materiais\\capas_proximo_G1_iPga6nLg).

O que ela pediu (e reprovou várias vezes até chegar aqui):
- protagonista FIEL à capa do parceiro (Flow com a capa dele de 1ª referência);
- mulheres DA HISTÓRIA + a Maria, cada uma num BIQUÍNI-FANTASIA do tema (bruxa com chapéu, estudante com gravata,
  militar com cinto de balas...) - nunca roupa (o Flow lia "biquíni de estudante" como uniforme: veste());
- seios bem grandes (texto exagerado faz o Flow recuar e vestir; o tamanho vem da 3ª referência CORPO_REF);
- POSE do hipercool: UMA mulher ENORME em close numa pose com ele (de quatro por cima dele, colo de frente...), as
  outras menores atrás; a pose vem da 2ª referência (capas do hipercool recortadas em POSES_DIR) e é descrita como
  SITUAÇÃO inocente ("tropeçou e caiu por cima dele"), nunca como posição sexual (dica da dona);
- A fiel à composição do parceiro, B a mais sensual (cômica), C batalha + humilhação; cada letra numa pose diferente.

Usado por capa_ia_anime.capa_melhorada (A) e capas_ab (B/C) quando formato 16:9. Desliga: CAPA_LONGO_V2=0.
A ficha da obra (protagonista, mulheres, fantasias, cenas) sai da visão sobre a capa do parceiro + título.
"""
import hashlib
import json
import os
import re
from pathlib import Path

POSES_DIR = Path(r"D:\hipercool-materiais\capas_poses_ref")
# 02/11 03h: o Flow passou a RECUSAR o upload da de_quatro_costas_cama.png ("upload recusado [3]", todas as contas,
# desde 02:58) e toda capa caía. Corpo agora vem de uma capa que o próprio Flow gerou (Morando B: biquíni, seios grandes).
CORPO_REF = POSES_DIR / "corpo_ref.jpg"

CORPO = ("ENORMOUS breasts (huge J-cup bust, heavy, round and bouncy, deep cleavage spilling out of the tiny top) - the "
         "SAME body proportions as the woman in the THIRD reference; tiny waist, very wide hips, thick thighs - "
         "ecchi manhwa proportions like the most popular harem manhwa thumbnails")
ROUPA = ("WARDROBE RULE (most important, check every woman): each woman wears ONLY her themed COSTUME-BIKINI described "
         "below - a micro string bikini that IS the costume, plus the small themed accessories listed (hat, tie, collar, "
         "gloves, cape strip, props). NO shirts, NO jackets, NO robes, NO dresses, NO skirts, NO pants, NO full armor, "
         # 03/11 (PFbu tribal, 15 h sem capa): saíam tanga, saia de couro, cropped e túnica de onça
         "NO coats, NO loincloths, NO wraps, NO crop tops, NO tunics, NO fur trims: the top is a tiny TRIANGLE bikini "
         "top and the bottom a tiny STRING bikini bottom tied at the hips, nothing hanging over it: bare belly, bare "
         "shoulders, bare legs. If any woman is wearing normal clothes the image is WRONG.")
# 09/11 (teste cLF1: armadura/ombreira/veste vieram junto) e FX1y (reprovada por "Luck +99999" numa tela de status):
# sem luvas/capa liberadas, ombreira/armadura/espartilho proibidos por nome e nada de janela de status de jogo.
# Desliga junto com o tema só cor: CAPA_TEMA_SO_COR=0.
if os.environ.get("CAPA_TEMA_SO_COR", "1") == "1":
    ROUPA = (ROUPA.replace("(hat, tie, collar, gloves, cape strip, props)", "(at most one small prop held in a hand)")
             + " NO shoulder pads, NO pauldrons, NO armor pieces, NO gauntlets, NO long gloves, NO capes, NO corsets, "
               "NO leotards, NO bodysuits - only bare skin around the two tiny bikini pieces."
               # 10/11 (Monster Cores A, d-wzjHX3nFM): 3 de 5 de MAIÔ inteiro (one-piece) — tolerada por "vestidas"
               " NO one-piece swimsuits, NO monokinis, NO cut-out swimsuits: ALWAYS TWO SEPARATE PIECES with the bare"
               " belly and navel fully visible between the top and the bottom.")
# 02/11 13h: a A do KJ5F (história de orfanato/babá) saiu com uma menina com cara de criança -> nenhuma criança na
# imagem nem na ficha.
SEGURO = ("All women are grown-up adults in their late twenties, very sensual and flirty, blushing; everything private "
          "covered by the bikini, no nudity, nothing explicit. NO children and no young-looking or petite characters "
          "anywhere in the image.")
FIM = ("Colors BRIGHT, SUNNY, VIVID and HIGHLY SATURATED, glossy clean manhwa art like popular manhwa recap "
       "thumbnails - never dark or gloomy. Remove ALL text, letters, numbers, logos, arrows and watermarks. "
       # 05/11 (5FDt B reprovada por "letras": rótulos minúsculos de potes na prateleira do bunker)
       "No writing anywhere in the scene either: jars, cans, boxes, bottles, signs, screens and posters are plain "
       "and unlabeled. "
       + ("NO floating game status windows, stat panels, HUD or UI boxes (they always carry text). "
          if os.environ.get("CAPA_TEMA_SO_COR", "1") == "1" else "") +
       "Leave the top-left and top-right corners less busy for speech labels."
       # 11/11 (Slave Mage A refeita: loira e morena de SHORT + cropped mesmo com a regra no começo): o Flow pesa mais o
       # FIM do prompt -> a regra da roupa repetida por último. Mesma chave CAPA_TEMA_SO_COR.
       + (" FINAL CHECK: every woman wears exactly TWO tiny pieces - a triangle bikini top and a string bikini bottom - "
          "with the bare belly, navel, hips and whole thighs visible; NO shorts, NO hot pants, NO skirts, NO crop tops, "
          "NO swimsuits, NO armor, NO clothing of any kind on any woman."
          if os.environ.get("CAPA_TEMA_SO_COR", "1") == "1" else ""))

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
LETRA_POSE = {"A": 0, "B": 1, "C": 2, "D": 3, "E": None, "F": 4, "G": 0}  # E = harém na cama


# 01/11 20h dona: capa B = pose COPIADA de uma capa do hipercool (2ª referência) SEM descrever a pose no texto (ideia
# dela; aprovada a "ele_nas_costas_dela" na Ferreiro: D:\hipercool-materiais\capas_poses_ref\b\aprovadas) + as outras
# mulheres menores ao fundo ("está sem as outras mulheres"). Só poses aprovadas por ela entram aqui.
POSES_B_DIR = POSES_DIR / "b"
# 01/11 22h30 dona aprovou também as de teste\ e teste_pose\: a referência é a PRÓPRIA capa aprovada (já de biquíni e
# com as outras mulheres — o Flow veste menos que com a capa do hipercool de roupa). ok_* = capa nossa aprovada.
POSES_B_OK = ["ele_nas_costas_dela", "ok_de_quatro_por_cima", "ok_colo_montada", "ok_inclinada_costas"]
# 01/11 dona: "essa cara que ela está fazendo temos que adicionar em uma das mulheres em todas as capas" (hipercool
# rosto_4: capas_poses_ref\cara_lingua_rosto_4.png)
# 01/11 23h dona: "as de hoje de manhã estão melhores porque tinham os elementos da original (barcos, navios...)" —
# toda letra mantém os OBJETOS DA HISTÓRIA da capa do parceiro no fundo (a capa_melhorada da manhã fazia isso).
# 02/11 04h: "keep the SAME ... of the FIRST reference" fez o Flow redesenhar a capa original INTEIRA, com as mulheres
# VESTIDAS dela (Ferreiro/Engenheiro saíram de empregada, armadura, colete; a Morando escapou porque a original já era
# de pouca roupa). Da 1ª referência só os OBJETOS e o cenário — nunca as pessoas nem as roupas.
# 02/11 05h40: os exemplos ("ships, airships, monsters") viraram dirigíveis e dragões em TODA obra (a hJaA é frio e
# geladeira e saiu com dirigíveis). Só o que a 1ª referência mostra de verdade, sem exemplos.
ELEMENTOS = ("STORY ELEMENTS (fans recognize the story by them): in the BACKGROUND show the objects and scenery that "
             "the FIRST reference really shows (whatever they are in that image). Do NOT add objects that are not in it. "
             "Take ONLY those objects and the scenery from it: NOT its women, NOT their clothes, NOT its composition.")
CARA = ("ONE of the women (not the main one) makes a playful teasing face at the viewer: mouth wide open with her "
        "tongue sticking far out, flushed red cheeks, a few sweat drops, half-closed eyes looking straight at the "
        "viewer, one hand tugging a bikini strap off her shoulder.")


# 01/11 23h dona: "as poses estão corretas, mas a capa B seria justamente a MISTURA das B com as E (harém)" — a pose
# de uma mulher (as dela de poses\B, as do hipercool B_serve e as nossas aprovadas ok_*) + as outras mulheres
# agarradas nele como no harém, do jeito das A/B/C da tarde (mulher principal grande + corpo da 3ª ref pros seios).
POSES_B_POOL = POSES_DIR / "b_pool"


def _pool_b():
    return sorted(p.stem for p in POSES_B_POOL.glob("*.png")) or POSES_B_OK


def _quem(q):
    """02/11 05h (teste X1/X2, Ferreiro): com o PAPEL da capa original ("the noble knight companion", "the rival
    artisan" de empregada) o Flow reconhece a personagem na 1ª referência e copia a ROUPA dela (saíam de armadura e
    uniforme de empregada). Com a mesma montagem e as mulheres descritas só pela aparência (como na tarde de 01/11)
    saíram todas de biquíni-fantasia. Fica só a aparência (cabelo, olhos, orelhas)."""
    import re
    m = re.search(r"\(([^)]+)\)", q or "")
    return f"a gorgeous woman ({m.group(1)})" if m else "a gorgeous woman"


_ACESS_ROUPA = (r"apron|pauldron|bracer|wristguard|gauntlet|headband|armor|vest|collar|sleeve|glove|dress|skirt|robe|"
                r"uniform|plate|shorts|jacket|coat|tunic|corset|leggings")


def _fantasia(f):
    """02/11 05h30 (teste V1/V2 do Ferreiro): o NOME do tema ("KNIGHT-BIKINI", "MAID-BIKINI") igual à roupa da
    personagem na capa original fazia o Flow desenhar a roupa original (armadura, uniforme de empregada). Sem o nome
    do tema e sem os acessórios que viram roupa (avental, ombreira, braçadeira, tiara) saíram de biquíni."""
    import re
    # 03/11 (PFbu, tribal): "fur micro bikini" virava pele/vestido de pele e a checagem "vestidas" reprovava todas
    # (a obra ficou 15 h sem nenhuma capa) -> pele vira estampa de onça, tecido fino
    f = re.sub(r"\b(furry|fur|pelt|hide|animal-skin)\b", "leopard-print", f or "", flags=re.I)
    partes = [p.strip() for p in re.sub(r"^[A-Z][A-Z \-]*BIKINI\s*(for the mascot girl)?\s*:\s*", "", f or "").split(",")]
    if os.environ.get("CAPA_TEMA_SO_COR", "1") == "1":  # 09/11 teste: FX1y saiu toda de biquíni (antes túnica/tanga)
        return _so_cor(partes)
    return ", ".join([partes[0]] + [p for p in partes[1:] if p and not re.search(_ACESS_ROUPA, p, re.I)])


# 09/11 (problema nº 1 da PASSAGEM_CAPAS): estampa com NOME de roupa ("school-plaid", "camouflage", "nurse") e
# acessório USADO no corpo (auréola+asas = túnica de anjo; colar de osso = tanga tribal; gravata+meia = uniforme)
# puxavam a roupa inteira do papel (dee293 B 08/11: anjo de túnica, tribal de tanga). Tema = SÓ cor/estampa neutra
# + no máximo 1 objeto NA MÃO. Chave: CAPA_TEMA_SO_COR=1 liga.
_ESTAMPA = [
    (r"school[- ]?plaid|plaid|tartan|checkered", "red-and-navy small check print"),
    (r"camo(uflage)?|military", "olive and dark-green spotted print"),
    (r"nurse|medical", "white with small red cross dots"),
    (r"maid", "black with white polka dots"),
    (r"police|cop", "navy blue with tiny gold stars"),
    (r"leopard[- ]?print|tribal|fur|pelt", "leopard-spot print"),
    (r"leather", "glossy brown"),
    (r"lace( trim)?", "with a thin satin trim"),
    # 09/11 reteste cLF1: "skull/cross/celestial pattern" ainda virava necromante de saia e sacerdotisa de túnica
    (r"(with\s+)?(a\s+)?(skull|bone|cross|holy|celestial|moon|rune|arcane|crest|emblem)s?\s+(pattern|print|motifs?)",
     "with a tiny dot print"),
]
_NA_MAO = r"\b(staff|wand|sword|dagger|katana|bow|spear|hammer|book|orb|fan|scythe|whip|harp|lantern)\b"


def _so_cor(partes):
    import re
    base = partes[0] if partes else ""
    for padrao, troca in _ESTAMPA:
        base = re.sub(padrao, troca, base, flags=re.I)
    base = re.sub(r"\b(micro\s+)?(string\s+)?bikini\b", "", base, flags=re.I).strip(" ,-")
    prop = next((p for p in partes[1:] if re.search(_NA_MAO, p, re.I)), "")
    s = f"{base} micro string bikini (just a printed fabric color, NOT a uniform or costume outfit)"
    prop = re.sub(r"^(holding|carrying|with)\s+|\s+in (her|one) hands?$", "", prop, flags=re.I)
    return s + (f", holding {prop} in one hand" if prop else "")


def _sem_acess(f):
    import re
    partes = [p.strip() for p in (f or "").split(",")]
    return ", ".join([partes[0]] + [p for p in partes[1:] if p and not re.search(_ACESS_ROUPA, p, re.I)])


def _sem_papel(q):
    """'the RED-HAIRED WITCH GIRL (long red hair...)' -> 'a gorgeous red-haired woman (long red hair...)'."""
    import re
    m = re.match(r"\s*the\s+([A-Z][A-Z\-]*)\s[^(]*(\(.*\))?", q or "")
    if not m:
        return q
    return f"a gorgeous {m.group(1).lower()} woman" + (f" {m.group(2)}" if m.group(2) else "")


def _lista(ficha):
    """Ficha v3 (02/11 06h, jeito da X2 = mulheres escritas como na tarde de 01/11) vai como está; as fichas antigas
    (papel e tema da roupa da capa original) passam pelos filtros acima."""
    if ficha.get("v") == 3:
        # 02/11 10h: com o papel real da obra (cavaleira, empregada) os acessórios "pauldron/apron/armor" voltaram e
        # vestiram RRrh, LAei, 4wuf -> tira também aqui. 02/11 12h: mesmo assim o NOME do papel ("ACADEMY GIRL",
        # "GODDESS", "WITCH-BIKINI") vestiu RA4H (uniforme), 4wuf (túnica), SNhb A (manto), LAei -> sai o nome do papel
        # (quem e fantasia); o papel fica só nos acessórios pequenos (chapéu de bruxa, auréola, gravata).
        return ([(_sem_papel(m["quem"]), _fantasia(m["fantasia"])) for m in ficha["mulheres"]]
                + [(MARIA, _fantasia(ficha["maria"]))])
    return ([(_quem(m["quem"]), _fantasia(m["fantasia"])) for m in ficha["mulheres"]]
            + [(MARIA, _fantasia(ficha["maria"]))])


def _desc_b(pose):
    """02/11: a pose também em TEXTO (como na tarde de 01/11, que dava certo); b_pool\\_descricoes.json é gerado pelo
    capas_poses_ref\\descrever_b_pool.py (visão). Sem descrição = só a imagem."""
    try:
        return json.loads((POSES_B_POOL / "_descricoes.json").read_text("utf-8")).get(pose, "")
    except (OSError, ValueError):
        return ""


def pose_b(semente):
    pool = _pool_b()
    i = int(hashlib.md5(str(semente).encode()).hexdigest(), 16) % len(pool)
    return pool[i]


def _roupa_b(q, f):
    return (f"{q}, wearing ONLY a tiny triangle bikini top and a tiny string bikini bottom - {f} - the theme is ONLY "
            f"the fabric pattern and small accessories; belly, waist, hips and thighs bare (NO skirt, NO shirt)")


def montar_b(ficha, semente):
    """Capa B = pose da 2ª referência (copiada, sem descrever) MISTURADA com harém: as outras mulheres agarradas nele;
    corpo/seios da 3ª referência (mesmo jeito das A/B/C da tarde de 01/11)."""
    lista = _lista(ficha)
    principal, outras = lista[0], lista[1:]
    lugar = (ficha["cenas"].get("B") or ficha["cenas"].get("A", "")).split(":", 1)[-1]
    # 02/11 01h: as 2 primeiras B mix (Ferreiro) saíram com as mulheres de colete/armadura/avental — a roupa da capa
    # original vazava. A regra do biquíni vem PRIMEIRO e nenhuma referência dá roupa às mulheres.
    return (
        f"A brand-new 16:9 anime thumbnail. {ROUPA} The women's clothes come from NO reference image (the references "
        "show them dressed - ignore that): only the costume-bikinis written here. "
        "Use the FIRST reference ONLY for the hero's face, hair and outfit and the story elements. Copy the "
        "exact POSE, body positions, camera angle and close framing of the man and the woman in the SECOND reference "
        "(do NOT copy its clothes, text or background). From the THIRD reference copy ONLY the woman's body "
        "proportions (very large breasts, wide hips), nothing else. "
        # 02/11 04h: a composição da tarde (a que dava certo): mulher principal ENORME, perto da câmera, só ela e ele
        # na frente — sem isso a B virava um grupo em pé
        f"The man is the hero: {ficha['heroi']} COMPOSITION (most important): close-up framing like the hit harem "
        "manhwa thumbnails - the hero and THE MAIN WOMAN in the front, she is HUGE in the frame (fills about 60% of "
        "the image), in the exact pose of the SECOND reference with him. "
        + (f"POSE: {_desc_b(pose_b(semente))} " if _desc_b(pose_b(semente)) else "") +
        f"THE MAIN WOMAN: {veste(*principal)}. "
        "HAREM MIX: right behind them, a bit smaller, the other women cling to him jealously - hugging his arm, "
        "draped over his back, leaning on his shoulder - never standing in a line, never far away: "
        f"{'; '.join(veste(q, f) for q, f in outras)}. "
        f"Every woman has {CORPO}. {CARA} {ELEMENTOS} Scene: {lugar} Again: every woman in a tiny costume-bikini, "
        f"bare belly and bare legs. {SEGURO} {FIM}")


# 02/11 14h dona: "foi usada uma pose de B na C" (u7tN), "é uma pose de C na B" (RRrh), "essa pose (SNhb B, chute) na
# verdade seria a pose de batalha do C nova". A C tirava a pose da lista sensual (POSES) e a batalha ia só no fundo;
# e o b_pool tinha 2 poses de luta. Elas foram pro c_pool (capas_poses_ref\c_pool): a C usa só pose de batalha.
POSES_C_POOL = POSES_DIR / "c_pool"


def _pool_c():
    return sorted(p.stem for p in POSES_C_POOL.glob("*.png"))


def pose_c(semente):
    pool = _pool_c()
    return pool[int(hashlib.md5(str(semente).encode()).hexdigest(), 16) % len(pool)] if pool else None


def _desc_c(pose):
    try:
        return json.loads((POSES_C_POOL / "_descricoes.json").read_text("utf-8-sig")).get(pose, "")
    except (OSError, ValueError):
        return ""


BATALHA_C = ("It is an ACTION FIGHT scene from the story: the hero and the women fight TOGETHER against the story's "
             "enemies (shown in the background), speed lines, sparks and impact effects, the hero BIG and central; the "
             "women fight in their costume-bikinis (no armor, no battle clothes).")


def pose_de(semente, letra):
    """E sempre harém; as outras giram pela obra, pra cada obra ter poses diferentes nas letras."""
    if LETRA_POSE[letra] is None:
        return "harem_cama"
    poses = [p for p in POSES if p != "harem_cama"]
    i = int(hashlib.md5(str(semente).encode()).hexdigest(), 16) % len(poses)
    return poses[(LETRA_POSE[letra] + i) % len(poses)]


def refs_extras(semente, letra):
    """2ª e 3ª referências do Flow (depois da capa do parceiro): a pose e o corpo. B: só a pose aprovada."""
    if letra == "B":
        p = POSES_B_POOL / f"{pose_b(semente)}.png"
        return [p if p.exists() else POSES_B_DIR / f"{pose_b(semente)}.png", CORPO_REF]
    if letra == "C" and pose_c(semente):
        return [POSES_C_POOL / f"{pose_c(semente)}.png", CORPO_REF]
    return [POSES_DIR / f"{pose_de(semente, letra)}.png", CORPO_REF]


# 02/11 21h dona (X90, "O poder secreto do bebê"): "é um caso onde não tem mulheres e é só um bebê, aí não dá pra
# colocar mulheres; a C (bebê + poder + inimigos) está correta e a B (harém) errada; esses têm que seguir outra
# estratégia". Herói criança/bebê = capa SÓ do herói e da história: nenhuma mulher, nada sensual, nada de romance.
_CRIANCA = re.compile(r"\b(baby|babies|infant|toddler|newborn|child|kid|little boy|little girl)\b", re.I)


def sem_mulheres(ficha):
    return bool(ficha) and bool(_CRIANCA.search(ficha.get("heroi", "")))


SO_HEROI = {
    "A": "the SAME scene as the FIRST reference (same hero, same place, same story objects and power effects), "
         "redrawn brighter and more dramatic",
    "B": "a funny showing-off scene: the little hero casually shows his secret power (glowing aura, energy weapons, "
         "status window) while shocked grown-up MEN around him drop their jaws",
    "C": "an EPIC BATTLE: the hero BIG and central unleashing his power, enemies and monsters blasted away around "
         "him, speed lines, sparks and impact effects",
}


def montar_so_heroi(ficha, letra):
    return (f"A 16:9 recap YouTube thumbnail: {SO_HEROI[letra]}. The hero is the SAME character as in the FIRST "
            f"reference: copy his face, hair, eyes and outfit exactly ({ficha.get('heroi', '')}). NO WOMEN AT ALL in "
            "the image, no romance, nothing sensual, no bikinis; only the hero, his powers, story objects and (if any) "
            # 02/11 22h15 (X90 B do Google): dois balões de fala vazios no alto
            "grown-up men or monsters as side characters. No speech bubbles, no empty balloons, no captions. Story "
            "elements in the background: "
            f"{ficha['cenas'].get(letra) or ficha['cenas'].get('A', '')} {FIM}")


# 03/11 dona: "o sistema de pegar os personagens já começou a funcionar, aí você pode inserir eles nas capas".
# Banco de fotos das mulheres tiradas do próprio vídeo (capas_referencias\<vid>\, banco_mulheres.py + nomear.py):
# o rosto/cabelo/cor das mulheres vem dessas fotos; o corpo continua do corpo_ref e a roupa é o biquíni-fantasia.
# Só entra mulher marcada adulta=true e mulher=true (menor de idade nunca vai pra capa).
BANCO = Path(r"D:\hipercool-materiais\capas_referencias")


def banco(semente, maximo=3):
    """[(foto_do_rosto, descrição)] do ELENCO da obra tirado do próprio vídeo: até `maximo` mulheres adultas
    DIFERENTES (a principal primeiro) + o protagonista ("HERO|...") + 1 personagem de fundo ("BG|...").
    03/11 dona: "agora tem muito mais fotos de personagens; dá pra incluir as mulheres com rosto das da obra e
    personagens de fundo que estão na história?" [] se a obra não tem banco."""
    saida = _banco_mulheres(semente, maximo + 1)
    mulheres, sobra = saida[:maximo], saida[maximo:]
    h = heroi_banco(semente)
    if h:
        mulheres.append((h[0], "HERO|" + h[1]))
    fundo = _fundo_banco(semente) or [(f, d) for f, d in sobra]
    if fundo:
        mulheres.append((fundo[0][0], "BG|" + fundo[0][1]))
    return [(_so_rosto_foto(f), d) for f, d in mulheres]


def _so_rosto_foto(f):
    """05/11 madrugada: com a foto inteira o Flow copiava a ROUPA do vídeo (Leonora de uniforme, Mi-kyung de xadrez,
    Selena de capuz -> B reprovada por 'vestidas') e a LEGENDA queimada embaixo ('fumaça preta' -> 'letras').
    Manda só o terço de cima (rosto e cabelo): corta os 35% de baixo."""
    try:
        from PIL import Image
        f = Path(f)
        dst = f.parent / "_so_rosto" / f.name
        if not dst.exists() or dst.stat().st_mtime < f.stat().st_mtime:
            dst.parent.mkdir(exist_ok=True)
            im = Image.open(f).convert("RGB")
            im.crop((0, 0, im.width, int(im.height * 0.65))).save(dst, quality=92)
        return dst
    except Exception:  # noqa: BLE001
        return f


def _fundo_banco(semente):
    """2º homem do vídeo em diante (aliado, rival, vilão) — personagem de fundo da história."""
    m = re.search(r"(?:v=|youtu\.be/|parceiro_|^)([\w-]{11})", str(semente))
    if not m:
        return []
    try:
        ind = json.loads((BANCO / m.group(1) / "homens.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    todos = sorted(ind.get("homens", []), key=lambda h: (not h.get("principal"), -h.get("aparicoes", 0)))
    hs = todos[1:]
    # 04/11 (KwdN: h01..h03 todos "Kim Ojin"; 5FDt: 2x "Siang Ho"): o mesmo herói partido em grupos não é fundo
    def _k(n):
        return re.sub(r"[^a-z0-9]", "", re.sub(r"\(.*?\)", "", n or "").split("/")[0].lower())
    heroi = _k(todos[0].get("nome")) if todos else ""
    saida = []
    for h in hs:
        if h.get("adulto") is False or h.get("menor"):
            continue
        if heroi and _k(h.get("nome")) == heroi:
            continue
        fotos = sorted((BANCO / m.group(1) / "homens" / h["personagem"]).glob("rosto_*.jpg"))
        if fotos:
            saida.append((fotos[0], h.get("visual") or h.get("nome") or "a side character of the story"))
    return saida


def _banco_mulheres(semente, maximo=2):
    """[(foto_do_rosto, descrição)] das mulheres adultas da obra, a principal primeiro; [] se a obra não tem banco."""
    m = re.search(r"(?:v=|youtu\.be/|parceiro_|^)([\w-]{11})", str(semente))
    if not m:
        return []
    try:
        ind = json.loads((BANCO / m.group(1) / "indice.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    ok = [x for x in ind.get("mulheres", []) if x.get("adulta") is True and x.get("mulher") is not False
          and not x.get("repetida")]
    ok.sort(key=lambda x: (not x.get("principal"), -x.get("aparicoes", 0)))
    # 03/11 dona: "preciso de mulheres DIFERENTES" — índice antigo (sem "repetida") tinha Mia em p01..p05: o nome
    # repetido não entra 2x
    nomes, unicas = set(), []
    for x in ok:
        k = re.sub(r"[^a-z0-9]", "", re.sub(r"\(.*?\)", "", (x.get("nome") or "")).split("/")[0].lower())
        if k and k in nomes:
            continue
        nomes.add(k)
        unicas.append(x)
    saida = []
    for x in unicas[:maximo]:
        fotos = sorted((BANCO / m.group(1) / "mulheres" / x["personagem"]).glob("rosto_*.jpg"))
        if fotos:
            saida.append((fotos[0], x.get("visual") or x.get("nome") or "a woman of the story"))
    return saida


def heroi_banco(semente):
    """03/11 dona ("e do protagonista claro"): (foto_do_rosto, descrição) do protagonista tirado do vídeo
    (capas_referencias\\<vid>\\homens.json, banco_mulheres + nomear); None se a obra ainda não tem."""
    m = re.search(r"(?:v=|youtu\.be/|parceiro_|^)([\w-]{11})", str(semente))
    if not m:
        return None
    try:
        ind = json.loads((BANCO / m.group(1) / "homens.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    for h in sorted(ind.get("homens", []), key=lambda h: (not h.get("principal"), -h.get("aparicoes", 0))):
        fotos = sorted((BANCO / m.group(1) / "homens" / h["personagem"]).glob("rosto_*.jpg"))
        if fotos:
            return fotos[0], h.get("visual") or h.get("nome") or "the male protagonist"
    return None


_ORD = ["FIRST", "SECOND", "THIRD", "FOURTH", "FIFTH", "SIXTH", "SEVENTH"]


def texto_banco(lista, primeira):
    """primeira = posição (1-based) da 1ª foto do banco entre as referências."""
    if not lista:
        return ""
    mulheres, extra = [], []
    for i, (_f, d) in enumerate(lista):
        ordem = _ORD[min(primeira - 1 + i, len(_ORD) - 1)]
        if d.startswith("HERO|"):
            extra.append(f" HERO FACE: the {ordem} reference is the REAL face of the male protagonist from the story "
                         f"video ({d[5:]}) - draw the hero with exactly that face, hair and eye color.")
        elif d.startswith("BG|"):
            extra.append(f" BACKGROUND CHARACTER: the {ordem} reference is a side character from the story video "
                         f"({d[3:]}) - include him/her SMALLER in the background with exactly that face and hair, "
                         "fully dressed, never in front of the main woman or the hero.")
        else:
            # 05/11: só rosto/cabelo (a roupa do vídeo vestia as mulheres na capa)
            d_rosto = ", ".join(p.strip() for p in re.split(r"[,;]", d) if p.strip() and not re.search(
                r"\b(wear\w*|dress\w*|hood\w*|cloak|cape\w*|capelet|uniform|armou?r\w*|shirt|robe|coat|outfit|"
                r"cloth\w*|jacket|blouse|sweater|tunic|apron|skirt|vest|gown|kimono|suit|scarf|collar)\b", p, re.I)) or d
            mulheres.append(f"the {ordem} reference is a REAL face from the story video ({d_rosto}; IGNORE the "
                            "clothes in that photo)")
    txt = ""
    if mulheres:
        txt = (" STORY WOMEN FACES: " + "; ".join(mulheres) + ". Each woman in the image uses a DIFFERENT one of "
               "those faces (the main woman = the first), with EXACTLY that face, hair color, hairstyle and eye "
               "color - only the face and hair come from those photos; the body and the costume-bikini follow the "
               "rules above. Extra women beyond these photos must look like they belong to the same story.")
    return txt + "".join(extra)


def _ficha_com_banco(ficha, semente):
    """05/11 dona ("os personagens das fotos não têm nada de parecido com os das capas"): o texto descrevia cada
    mulher pela ficha (cabelo/rosto da capa do parceiro, ex. 'elfa de cabelo prateado') e a foto do vídeo só vinha no
    fim -> o Flow seguia o texto. Com banco, a aparência das primeiras mulheres passa a ser a da foto do vídeo."""
    try:
        fotos = [d for _f, d in banco(semente) if not d.startswith(("HERO|", "BG|"))]
    except Exception:  # noqa: BLE001
        return ficha
    if not fotos or not ficha.get("mulheres"):
        return ficha
    # 05/11 02h (KwdN B: a Selena veio de capuz verde, capa e armadura de folhas): a descrição da foto traz a roupa do
    # vídeo -> fica só rosto/cabelo/olhos; a roupa do vídeo é ignorada
    roupa = re.compile(r"\b(wear\w*|dress\w*|hood\w*|cloak|cape\w*|capelet|uniform|armou?r\w*|shirt|robe|coat|"
                       r"outfit|cloth\w*|jacket|blouse|sweater|tunic|apron|skirt|vest|gown|kimono|suit|scarf|collar)\b",
                       re.I)

    def _so_rosto(d):
        partes = [p.strip() for p in re.split(r"[,;]", d) if p.strip() and not roupa.search(p)]
        return ", ".join(partes) or d

    novas = []
    for i, m in enumerate(ficha["mulheres"]):
        m = dict(m)
        if i < len(fotos):
            m["quem"] = (f"a woman with EXACTLY the face, hair color, hairstyle and eye color of story-video photo "
                         f"#{i + 1} ({_so_rosto(fotos[i])}) - ONLY her face and hair come from that photo, never "
                         f"the clothes she wears in it")
        novas.append(m)
    return dict(ficha, mulheres=novas)


def prompt_letra(ficha, letra, semente):
    if sem_mulheres(ficha):
        return montar_so_heroi(ficha, letra)
    ficha = _ficha_com_banco(ficha, semente)
    return montar_b(ficha, semente) if letra == "B" else montar(ficha, letra, semente)


def nome_pose(semente, letra):
    if letra == "C" and pose_c(semente):
        return "c_" + pose_c(semente)
    return "b_" + pose_b(semente) if letra == "B" else pose_de(semente, letra)


def veste(q, f):
    return (f"{q}, with very large breasts like the woman in the THIRD reference, wearing ONLY a tiny triangle bikini "
            f"top and a tiny string bikini bottom - {f} - the theme is ONLY the fabric pattern and small accessories; "
            f"her belly, waist, hips and thighs are completely bare (NO skirt, NO vest, NO shirt, NO shorts)")


MARIA = ("MARIA the mascot girl (long wavy dark-brown hair to her waist, golden-brown eyes, tanned caramel skin, "
         "beauty mark under her left eye, cheerful smile)")


# 02/11 07h40-10h: testadas A "original + mulheres em volta" e C "batalha só com capa + corpo" (sem a 2ª referência de
# pose). A saiu aceitável só sem mulher na original (G1 copiou os vestidos; dona: "a anterior estava melhor") e a C
# vestiu todas (KbLv, cLF1, SNhb). As duas voltaram pra pose; a batalha da C vem da cena C da ficha.
def montar(ficha, letra, semente):
    """Prompt do Flow pra letra A-G a partir da ficha da obra."""
    # 02/11 10h: a montar_c (só capa + corpo) vestiu as mulheres pra batalha (vestido, armadura, macacão: KbLv, cLF1,
    # SNhb). C voltou pra pose (mantém o biquíni) com a batalha da cena C no fundo.
    pose = pose_de(semente, letra)
    lista = _lista(ficha)
    principal = lista[list("ABCDEFG").index(letra) % len(lista)]
    outras = [m for m in lista if m is not principal]
    mul = (f"COMPOSITION (most important): close-up framing like the hit harem manhwa thumbnails - the MAIN WOMAN is "
           f"HUGE in the frame (fills about 60% of the image), only the hero and her in the front. POSE: "
           f"{_desc_c(pose_c(semente)) + ' ' + BATALHA_C if letra == 'C' and pose_c(semente) else POSES[pose]}. "
           f"THE MAIN WOMAN: {veste(*principal)}.")
    mul += ((" Smaller in the background (not standing in a line, flirty poses): " if pose != "harem_cama"
             else " The other women on the bed: ") + "; ".join(veste(q, f) for q, f in outras) + ".")
    mul += f" Every woman has {CORPO}."
    abre = ("A brand-new 16:9 anime thumbnail. Use the FIRST reference only for the hero's face, hair and outfit and the "
            "story elements; copy the exact POSE, camera angle and close framing of the SECOND reference (redraw it "
            "with our characters and costumes - do NOT copy its clothes, text or background). From the THIRD "
            "reference copy ONLY the woman's body proportions (very large breasts, wide hips), nothing else. Do NOT "
            "copy the women of the FIRST reference nor their clothes or dresses: every woman is drawn NEW from the "
            "text, in a costume-bikini.")
    heroi = f"Keep the SAME main character as the FIRST reference: {ficha['heroi']}"
    cena = f"Story elements in the background: {ficha['cenas'].get(letra) or ficha['cenas'].get('A', '')}"
    if letra == "A":
        # 02/11 13h30 dona (PFbu A): "por que o personagem principal e as mulheres que já tem saíram tão diferentes?
        # essa não era a regra da A". A ficha errou o herói (castanho/olhos azuis; na capa é ruivo) e inventou o
        # cenário (cabanas, fogueira), e o "do NOT copy the women of the FIRST reference" redesenhava as mulheres.
        # A = MESMO herói e MESMAS mulheres da capa original (copiados da imagem), só a roupa vira biquíni.
        abre = abre.replace(
            "Do NOT copy the women of the FIRST reference nor their clothes or dresses: every woman is drawn NEW from "
            "the text, in a costume-bikini.",
            "The women who appear in the FIRST reference are the SAME characters here: copy their faces, hair color "
            "and style, eyes, skin, animal ears and tails EXACTLY from that image - ONLY their clothes change: their "
            "original clothes are REPLACED by the costume-bikinis written here. Their clothes in the FIRST reference "
            "(school uniforms, dresses, long gowns, veils, robes, armor, jackets) are NOT copied at all - not even "
            "partly, not even the colors of the fabric cut.")
        heroi = ("Keep the SAME main character as the FIRST reference: copy his face, hair color and style, eye color, "
                 f"age and body EXACTLY from that image (the text is only a hint; the image wins): {ficha['heroi']}")
        cena = ("Background: the SAME place, scenery, lighting mood and story objects that the FIRST reference really "
                "shows, made brighter.")
        # 02/11 14h20 dona (4wuf A): "elas estão vestidas" — copiou o uniforme escolar e o vestido da deusa. Como na
        # montar_b (que parou de vestir assim), a regra do biquíni vai PRIMEIRO.
        primeiro = (f"{ROUPA} The women's clothes come from NO reference image (the FIRST reference shows them "
                    "dressed - ignore that): only the costume-bikinis written here.")
        return " ".join([primeiro, abre, mul, CARA, heroi, ELEMENTOS.replace("NOT its women, ", ""), cena, SEGURO,
                         "Again: every woman in a tiny costume-bikini, bare belly and bare legs.", FIM])
    return " ".join([abre, mul, CARA, heroi, ELEMENTOS, cena, ROUPA, SEGURO, FIM])


FICHA = (
    "This is the YouTube thumbnail of a manhwa recap video. Story title/premise (context): {cena}\n"
    "Plan new thumbnails for this SAME story. Answer ONLY JSON:\n"
    '{{"heroi": "<the MAIN MALE character exactly as drawn here: hair color/style, eyes, outfit, weapon/props, in '
    'English, 1 sentence>",\n'
    ' "mulheres": [{{"quem": "the <HAIR COLOR>-HAIRED <THEME> GIRL (<hair color/style, eyes, ears/tail if any>)", '
    '"fantasia": "<THEME>-BIKINI: <color/pattern> micro string bikini, <2-3 small themed accessories>"}}, ...2 or 3 '
    'women of THIS story (the ones in the thumbnail first; if fewer than 2 appear, the female characters the premise '
    'implies)],\n'
    ' "maria": "<THEME>-BIKINI for the mascot girl: <color> micro string bikini, <2-3 accessories matching this '
    'story world>",\n'
    ' "cenas": {{"A": "<the SAME composition/setting of this thumbnail: what the hero does, the background, the '
    'story objects (levels, ships, weapons, monsters...)>", "B": "playful comedic: <the hero in a place of the story, '
    'blushing in panic>", "C": "POWER-UP and HUMILIATION: <the hero overpowering, MALE rivals/villains defeated and '
    'humiliated around him, story setting>"}}}}\n'
    "RULES for each fantasia: the costume is ONLY a tiny bikini whose color/pattern and accessories show the theme "
    "(witch = pointy hat + tiny cape; student = plaid pattern + necktie + sailor collar; military = camo + bandolier + "
    "dog tags; knight = silver bikini + a small sword in her hand; blacksmith = leather bikini + goggles + tiny hammer; "
    "tribal = leopard-print bikini + bone necklace; goddess = white-gold + halo; priestess = runes + veil; maid = black-and-white "
    "frilly bikini + maid headdress). "
    "Never shirts, skirts, dresses, uniforms or armor. "
    "MOST IMPORTANT (02/11): each woman keeps her LOOK from the thumbnail (hair, eyes), but her THEME must be "
    "DIFFERENT from the clothes she wears in this thumbnail - if she wears armor, she is NOT a knight; a maid dress, NOT "
    "a maid; a vest/apron, NOT a blacksmith; a military uniform, NOT a soldier. Pick another theme that fits the story "
    "world (academy student, noble lady, goddess, idol, cheerleader, witch, priestess, tribal, pirate, nurse...), each "
    "woman a different theme. Example for a blacksmith story whose thumbnail shows a red-haired girl in a leather vest "
    "and a blonde knight: 'the RED-HAIRED ACADEMY GIRL (red hair in a bun, red eyes)' with 'ACADEMY-STUDENT BIKINI: "
    "red school-plaid micro string bikini, a tiny loose necktie, white thigh-high socks' and 'the BLONDE NOBLE GIRL "
    "(long blonde hair)' with 'NOBLE-LADY BIKINI: gold micro string bikini with lace trim, a small tiara, long white "
    "lace gloves, pearl necklace'. All women are adults (never a child or teenage character). Every scene is ONE single continuous "
    "scene - never split screen, panels or before/after halves (the cover check rejects split images).")


# 02/11 08h dona: "sempre a ideia é usar personagens femininas da própria obra — na da engenheira tem várias e são
# bruxas". Só pela capa a visão inventava (SNhb sem mulher na capa virou oficial da marinha e aviadora). O roteiro
# narrado do nosso vídeo diz quem são elas.
ROTEIROS = [Path(r"D:\hipercool-materiais\animes recap\na_nuvem"), Path(r"D:\hipercool-materiais\_longos_postar"),
            Path(r"D:\recapd-ambientes\producao\workspace\anime")]
ROTEIRO_TXT = (
    "\nTHE STORY SCRIPT (narration of our video, Portuguese) - use it to know the REAL female characters of this "
    "story:\n<<<\n{roteiro}\n>>>\n"
    "WOMEN RULE (most important): the women MUST be the real main FEMALE CHARACTERS of this story from the script "
    "(heroines, love interests, companions), 2 or 3, with their real look and their real role as the THEME (if they "
    "are witches -> WITCH-BIKINI, elves -> ELF-BIKINI, etc). If several of them share the same role (e.g. several "
    "witches), ALL of them keep that role, each with a different color and accessory - never swap their role for "
    "noble lady, maid, academy girl or anything the script does not say. Only if the script has no women, invent "
    "ones that fit. NEVER pick a child or teenage character (skip kids, orphans, little sisters): only adult women. "
    "The role shows ONLY through the bikini color and ONE OR TWO small hand-held props or head items "
    "(sword, wand, staff, witch hat, cat ears, tiara) - NEVER armor, plates, pauldrons, robes, uniforms, aprons, "
    "dresses, skirts, vests or sleeves (the image AI turns those into full clothes). "
    "The 'different theme' rule below is only for a woman who appears DRESSED in this thumbnail.\n")


def _roteiro(ref):
    vid = Path(ref).stem.replace("parceiro_", "")[:11]
    for raiz in ROTEIROS:
        for p in raiz.glob(f"{glob_escape(vid)}*/roteiro.txt"):
            try:
                return p.read_text(encoding="utf-8", errors="replace")[:60000]
            except OSError:
                pass
    return ""


def glob_escape(s):
    import glob
    return glob.escape(s)


def ficha(ref, cena, perguntar, gateway, cache_dir):
    """Ficha da obra pela visão sobre a capa do parceiro + o roteiro (cache por capa). None se não saiu."""
    b = Path(ref).read_bytes()
    rot = _roteiro(ref)
    # v3 (02/11 06h) = só a capa; v4 (02/11 08h) = capa + roteiro (as mulheres da obra). Sem roteiro fica a v3.
    arq = Path(cache_dir) / f"ficha{4 if rot else 3}_{hashlib.md5(b).hexdigest()[:12]}.json"
    if arq.exists():
        try:
            return json.loads(arq.read_text(encoding="utf-8"))
        except ValueError:
            pass
    pergunta = FICHA.format(cena=cena or "(unknown)") + (ROTEIRO_TXT.format(roteiro=rot) if rot else "")
    try:
        f = perguntar(b, pergunta, gateway=gateway, max_tokens=1200) or {}
    except Exception:  # noqa: BLE001
        return None
    ok = (isinstance(f.get("heroi"), str) and isinstance(f.get("mulheres"), list) and f["mulheres"]
          and all(isinstance(m, dict) and m.get("quem") and m.get("fantasia") for m in f["mulheres"])
          and f.get("maria") and isinstance(f.get("cenas"), dict))
    if not ok:
        return None
    f["mulheres"] = f["mulheres"][:3]
    f["v"] = 3
    arq.parent.mkdir(parents=True, exist_ok=True)
    arq.write_text(json.dumps(f, ensure_ascii=False, indent=1), encoding="utf-8")
    return f
