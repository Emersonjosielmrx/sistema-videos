# Capas A/B/C do próximo longo: G1_iPga6nLg (sem-obra-2be7a8_cap1_20261101, "prisioneiro humilhado pelas
# cavaleiras desperta um poder oculto"). Regras da dona 01/11 em D:\video-fila\engenharia_reversa\CAPAS_REFERENCIA.md:
# protagonista fiel; mulheres DA HISTÓRIA (rosto tirado do vídeo) + Maria; peito BEM grande; sempre colorida;
# A = fiel à original; B = molde Porão (bumbum em 1º plano, borrado depois); C = batalha + humilhação + níveis.
# Refs: 1ª capa do parceiro, 2ª Maria, 3ª a cavaleira de cabelo roxo, 4ª Margarita (quadros do vídeo).
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, r"D:\hipercool-materiais\capas_exemplo_01nov")
import gerar  # noqa: E402

AQUI = Path(__file__).parent
VID = "parceiro_G1_iPga6nLg"
ROSTOS = [AQUI / "quadros" / "ref_roxa.jpg", AQUI / "quadros" / "ref_margarita.jpg"]
HEROI = ("Keep the SAME main character EXACTLY as drawn in the FIRST reference image (messy black hair, blue eyes, "
         "torn beige prisoner shirt open on a muscular chest, iron shackle with a broken chain on his wrist) so "
         "fans recognize him.")
CORPO = ("gorgeous voluptuous hourglass body with VERY LARGE, full, round breasts (clearly bigger than usual, deep "
         "cleavage, but natural anime proportions, not grotesque), wide hips, thick thighs")
MULHERES = ("The women are characters FROM THE STORY: the PURPLE-HAIRED KNIGHT - SAME FACE as the THIRD reference "
            "image (long violet hair with a side braid, lilac eyes, confident smirk), wearing ONLY a skimpy "
            "dark-navy-and-gold bikini armor with a short open cape; MARGARITA - SAME FACE as the FOURTH reference "
            "image (long orange hair with bangs, glowing yellow eyes), wearing ONLY a tiny silver-and-blue bikini "
            "armor with knight gauntlets and thigh-high armored boots; plus MARIA from the SECOND reference image "
            "(same face, long wavy dark-brown hair, golden-brown eyes, tanned skin) in a tiny emerald-green bikini. "
            "Each has a " + CORPO + ". All are grown-up adult women in their late twenties, blushing, everything "
            "private covered, no nudity.")
FIM = ("Colors BRIGHT, SUNNY, VIVID and HIGHLY SATURATED, glossy clean manhwa art like popular manhwa recap "
       "thumbnails - never dark or gloomy. Remove ALL text, letters, numbers, logos, arrows and watermarks. {vazio}")
CAPAS = {
    "A": ("Recreate and IMPROVE the FIRST reference image (a YouTube manhwa thumbnail) as a brand-new 16:9 anime "
          "thumbnail with the SAME composition: the prisoner in the center-bottom, blushing with a nosebleed, the "
          "purple-haired knight on the LEFT with her arm around his neck pulling him, Margarita on the RIGHT "
          "pressing her chest against him, sunny castle courtyard with blue-roofed towers behind. " + HEROI + " "
          + MULHERES + " Maria peeks in from the right edge hugging his arm. "
          + FIM.format(vazio="Keep the top-left and top-right corners less busy for speech labels.")),
    "B": ("A brand-new 16:9 anime thumbnail in the style of the most clicked Brazilian manhwa recap channels (very "
          "playful, comedic). " + HEROI + " Scene in a sunny castle courtyard: the prisoner sits on the stone floor "
          "leaning back on his hands, wrists still shackled, blushing and sweating in comic panic; MARGARITA "
          "crawls toward him on her hands and knees in the FOREGROUND, seen from behind at a three-quarter "
          "angle (her curvy hips and thighs in the bikini-armor bottom closest to the camera), turning her head "
          "back over her shoulder to wink at the viewer with a teasing confident smile; the PURPLE-HAIRED KNIGHT "
          "stands beside him holding the end of his broken chain with a smug grin; MARIA kneels at his other "
          "side poking his cheek. Funny romantic comedy mood, nothing explicit. " + MULHERES + " "
          + FIM.format(vazio="Leave the top-left and top-right corners less busy for speech labels.")),
    "C": ("A brand-new 16:9 anime thumbnail focused on a SATISFYING POWER-UP and HUMILIATION. " + HEROI + " Scene in "
          "a sunny castle arena: on the RIGHT the prisoner stands calm and smug, broken chains falling from his "
          "wrists, crackling blue lightning aura and a glowing blue lightning greatsword on his shoulder, a giant "
          "defeated beast collapsed behind him; on the LEFT the arrogant female knights who humiliated him are on "
          "their knees on the ground in shock: MARGARITA with her bikini armor cracked (still covering everything) "
          "and her broken sword, sweating, mouth open in disbelief. " + MULHERES + " The purple-haired knight and "
          "Maria cling to the hero's arms admiring him with heart eyes. No blood. "
          + FIM.format(vazio="Keep the top corners less busy for labels.")),
}

if __name__ == "__main__":
    gerar.ORIG = Path(r"D:\recapd-ambientes\producao\workspace\cache\capa_ia_anime")
    gerar.OUT = AQUI / "brutas"
    gerar.OUT.mkdir(exist_ok=True)
    nomes = sys.argv[1:] or list(CAPAS)
    with ThreadPoolExecutor(len(nomes)) as ex:
        for r in ex.map(lambda n: gerar.um(VID, n, CAPAS[n], ROSTOS), nomes):
            print(r, flush=True)
