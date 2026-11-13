# v3 das capas do SNhb31ZuuFA (Release That Witch) — dona 01/11 (2ª rodada):
# - rosto da personagem SEMPRE o do vídeo (bruxa da fogueira = Anna; pirata do tapa-olho), o corpo pode ser mais
#   sensual que no vídeo; peito BEM grande (hoje saía "grande normal"), sem chegar a ficar estranho;
# - B no molde Porão/hipercool: ela de quatro/por cima dele, bumbum em primeiro plano (parte borrada depois, em
#   compor_v3.py), fala dela e rótulo dele com seta.
# Refs: 1ª = capa do parceiro, 2ª = Maria, 3ª+ = rostos tirados do vídeo (quadros/ref_*.jpg).
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import gerar

REF = r"D:\recapd-ambientes\producao\workspace\cache\capa_ia_anime\parceiro_SNhb31ZuuFA.jpg"
Q = Path(__file__).parent / "quadros"
HEROI = ("Keep the SAME main character EXACTLY as drawn in the FIRST reference image (long dark-brown hair with a side "
         "braid, red-tinted eyes, black military coat with gold trim, black gloves) so fans recognize him.")
CORPO = ("gorgeous voluptuous hourglass body with VERY LARGE, full, round breasts (clearly bigger than usual, deep "
         "cleavage, but natural anime proportions, not grotesque), wide hips, thick thighs")
MULHERES = ("The women are characters FROM THE STORY: ANNA, the fire witch - SAME FACE as the THIRD reference image "
            "(keep her face, hair and eye colors from it), wearing ONLY a tiny black-and-gold string bikini and a "
            "pointed witch hat, flames in her palm; the PIRATE CAPTAIN - SAME FACE as the FOURTH reference image "
            "(long wavy dark hair, skull eyepatch over one eye, teal eye), wearing ONLY a skimpy pirate bikini, an "
            "open captain coat and a belt; plus MARIA from the SECOND reference image (same face, long wavy "
            "dark-brown hair, golden-brown eyes, tanned skin) in a tiny red-and-gold bikini. Each has a " + CORPO +
            ". All are grown-up adult women in their late twenties, blushing, everything private covered, no nudity.")
FIM = ("Colors BRIGHT, SUNNY, VIVID and HIGHLY SATURATED, glossy clean manhwa art like popular manhwa recap "
       "thumbnails - never dark or gloomy. Remove ALL text, letters, numbers, logos and watermarks. {vazio}")
CAPAS = {
    "v3_A": ("Recreate and IMPROVE the FIRST reference image (a YouTube manhwa thumbnail) as a brand-new 16:9 anime "
             "thumbnail with the SAME composition: the hero large in the center making the same commanding hand "
             "gesture, the old wooden galleon and the steampunk airships on the LEFT, the modern red-hulled "
             "battleship and the warplanes on the RIGHT, bright blue sky and turquoise sea. " + HEROI + " " + MULHERES +
             " Anna and the pirate captain press their chests against him on each side, Maria clings to his arm at "
             "the front. " + FIM.format(vazio="Keep the bottom-left and bottom-right corners less busy for labels.")),
    "v3_B": ("A brand-new 16:9 anime thumbnail in the style of the most clicked Brazilian manhwa recap channels "
             "(very seductive, comedic). " + HEROI + " Scene on the sunny wooden deck of his ship: the hero lies on "
             "his back on the deck, blushing and sweating in panic; ANNA is on all fours over him, seen from "
             "behind at a three-quarter angle, her big round butt in a tiny string bikini bottom in the FOREGROUND "
             "toward the camera, she looks back over her shoulder at the viewer with a flirty teasing smile and her "
             "very large breasts hang over his chest; MARIA kneels at his side leaning over him with her cleavage "
             "close to his face; the PIRATE CAPTAIN sits on a cannon behind them, legs crossed, licking her lip. " +
             MULHERES + " Background: turquoise sea, the wooden galleon, the steampunk airships and the battleship. "
             + FIM.format(vazio="Leave the top-left and top-right corners less busy for speech labels.")),
    "v3_C": ("Recreate the FIRST reference image (a YouTube manhwa thumbnail) as a brand-new 16:9 anime thumbnail "
             "focused on a SATISFYING NAVAL BATTLE and HUMILIATION. " + HEROI + " Scene: on the RIGHT the hero stands "
             "calm and smug on the bow of his huge modern red-hulled battleship, its big cannons firing, warplanes "
             "flying over; on the LEFT the arrogant ENEMY DUKE - middle-aged noble with short grey beard, heavy "
             "silver-and-gold armor and red cape - kneels on the deck of his small burning wooden galleon, sails "
             "torn, screaming in shock and despair with his knights panicking. " + MULHERES + " Anna hurls a big "
             "fireball at the enemy galleon, the pirate captain and Maria hug the hero's arms pressing their chests "
             "against him, laughing at the enemy. No blood. " + FIM.format(vazio="Keep the top corners less busy.")),
}
ROSTOS = [Q / "ref_anna.jpg", Q / "ref_pirata.jpg"]

if __name__ == "__main__":
    gerar.ORIG = Path(REF).parent
    faltam = [p for p in ROSTOS if not p.exists()]
    if faltam:
        sys.exit(f"faltam os rostos: {faltam}")

    def um(nome):
        return gerar.um("parceiro_SNhb31ZuuFA", nome, CAPAS[nome], ROSTOS)
    nomes = sys.argv[1:] or list(CAPAS)
    with ThreadPoolExecutor(len(nomes)) as ex:
        for r in ex.map(um, nomes):
            print(r, flush=True)
