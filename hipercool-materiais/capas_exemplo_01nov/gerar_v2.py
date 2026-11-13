# v2 das 3 capas do SNhb31ZuuFA (Release That Witch) — regras da dona 01/11 em
# D:\video-fila\engenharia_reversa\CAPAS_REFERENCIA.md: mulheres DA HISTÓRIA (bruxas) + Maria, pouca roupa, nunca uma só;
# A = fiel à original; B = a mais sensual (trono no navio); C = batalha + humilhação do inimigo + sensualidade.
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import gerar

REF = r"D:\recapd-ambientes\producao\workspace\cache\capa_ia_anime\parceiro_SNhb31ZuuFA.jpg"
HEROI = ("Keep the SAME main character EXACTLY as drawn in the FIRST reference image (long dark-brown hair with a side "
         "braid, red-tinted eyes, black military coat with gold trim, black gloves) so fans recognize him.")
BRUXAS = ("The women are characters FROM THE STORY (Release That Witch): ANNA, the fire witch - long straight bright "
          "blonde hair, clear blue eyes, flames dancing in her palm, wearing ONLY a tiny black-and-gold string bikini "
          "and a pointed witch hat (bare belly, bare thighs, no dress, no skirt); NIGHTINGALE, the assassin witch - "
          "wavy platinum-blonde hair, grey-blue eyes, wearing ONLY a skimpy black leather bikini-armor with thin "
          "straps and thigh-high boots (bare belly, bare thighs, no pants), a dagger strapped to her thigh; plus "
          "MARIA from the SECOND reference image (same face, long wavy dark-brown hair, golden-brown eyes, tanned skin) "
          "in a tiny red-and-gold pirate bikini. All three are gorgeous, curvy, voluptuous grown-up adult women in "
          "their late twenties, blushing, everything private covered, no nudity.")
FIM = ("Colors BRIGHT, SUNNY, VIVID and HIGHLY SATURATED, glossy clean manhwa art - never dark or gloomy. Remove ALL "
       "text, letters, numbers, logos and watermarks. {vazio}")
CAPAS = {
    "v2_A": ("Recreate and IMPROVE the FIRST reference image (a YouTube manhwa thumbnail) as a brand-new 16:9 anime "
             "thumbnail with the SAME composition: the hero large in the center making the same commanding hand "
             "gesture, the old wooden galleon and the steampunk airships on the LEFT, the modern red-hulled "
             "battleship and the warplanes on the RIGHT, bright blue sky and turquoise sea. " + HEROI + " " + BRUXAS +
             " Anna and Nightingale press against him on each side, Maria clings to his arm at the front. "
             + FIM.format(vazio="Keep the bottom-left and bottom-right corners less busy for big labels.")),
    "v2_B": ("Recreate the FIRST reference image (a YouTube manhwa thumbnail) as a brand-new 16:9 anime thumbnail, "
             "VERY SEDUCTIVE harem style like the most clicked manhwa recap channels. " + HEROI + " Scene: he sits on "
             "a golden captain's throne on the wooden ship deck, sweating and blushing in comic panic; ANNA sits "
             "sideways on his lap with her arms around his neck; NIGHTINGALE kneels on the deck floor hugging his "
             "leg and looking up at him; MARIA hugs him from behind pressing against his back. " + BRUXAS +
             " Background: turquoise sea with the wooden galleon, the steampunk airships, the modern battleship and "
             "the warplanes. " + FIM.format(vazio="Faces in the upper half; the bottom band less busy for a phrase.")),
    "v2_C": ("Recreate the FIRST reference image (a YouTube manhwa thumbnail) as a brand-new 16:9 anime thumbnail "
             "focused on a SATISFYING NAVAL BATTLE and HUMILIATION. " + HEROI + " Scene: on the RIGHT the hero stands "
             "calm and smug on the bow of his huge modern red-hulled battleship, its big cannons firing, warplanes "
             "flying over; on the LEFT the arrogant ENEMY DUKE - middle-aged noble with short grey beard, heavy "
             "silver-and-gold armor and red cape - kneels on the deck of his small burning wooden galleon, sails "
             "torn, screaming in shock and despair with his knights panicking. " + BRUXAS + " Anna hurls a big "
             "fireball at the enemy galleon, Nightingale and Maria hug the hero's arms, laughing at the enemy. "
             "No blood. " + FIM.format(vazio="Keep the top corners less busy for labels.")),
}

if __name__ == "__main__":
    gerar.ORIG = Path(REF).parent

    def um(nome):
        return gerar.um("parceiro_SNhb31ZuuFA", nome, CAPAS[nome])
    import sys
    nomes = sys.argv[1:] or list(CAPAS)
    with ThreadPoolExecutor(len(nomes)) as ex:
        for r in ex.map(um, nomes):
            print(r, flush=True)
