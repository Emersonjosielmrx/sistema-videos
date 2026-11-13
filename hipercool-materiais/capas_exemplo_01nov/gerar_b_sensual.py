# Capa B (a SENSUAL) do the-greatest-estate-developer_cap1_20261101 — dona 01/11: "como as do hipercool e dos canais
# de referência" (Porão/Zeni/Trigger) + palavra colada estilo AmericanNickas. Ref = capa do parceiro + Maria.
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import gerar

REF = r"D:\recapd-ambientes\producao\workspace\cache\capa_ia_anime\parceiro_SNhb31ZuuFA.jpg"
BASE = ("Recreate the FIRST reference image (a YouTube manhwa thumbnail) as a brand-new 16:9 anime thumbnail, VERY "
        "SEDUCTIVE harem style like the most clicked manhwa recap channels. Keep the SAME main character EXACTLY as "
        "drawn (long dark-brown braided hair, red-tinted eyes, black military coat with gold trim, black gloves). "
        "Background: bright sunny blue sky and turquoise sea with the wooden galleon, the steampunk airships, the "
        "modern battleship and the warplanes from the reference. Colors BRIGHT, VIVID, HIGHLY SATURATED, glossy - "
        "never dark. MARIA = the woman from the SECOND reference image (same face, long wavy dark-brown hair, "
        "golden-brown eyes, tanned skin, curvy grown-up adult body in her late twenties). {cena} All women are "
        "gorgeous, curvy, voluptuous, clearly adults in their late twenties, blushing, everything private covered, "
        "no nudity. One single scene. Remove ALL text, letters, logos and watermarks. Faces in the upper half; the "
        "lower-middle area less busy for one big word.")
CENAS = {
    "harem": "Scene: he sits on a golden captain's throne on the ship deck, sweating and blushing in comic panic; "
             "MARIA in red lace lingerie with a sheer red robe sits sideways on his lap with her arms around his "
             "neck; a blonde noblewoman in a tiny white-and-gold bikini hugs him from behind pressing against his "
             "back; a silver-haired navy officer woman in a skimpy unbuttoned uniform crop top and micro skirt "
             "clings to his arm, jealous.",
    "obcecada": "Scene: close-up, MARIA in a red pirate bikini leans over him on the ship deck with one hand on his "
                "chest, her face and bare shoulders filling half the frame, flushed cheeks, heart-shaped pupils, "
                "obsessive teasing smile at the viewer, long hair falling around him; he looks shocked and sweats; "
                "a blonde woman in a white bikini hugs his arm on the other side.",
}

if __name__ == "__main__":
    def um(nome):
        gerar.ORIG = Path(REF).parent  # gerar.um lê ORIG/<vid>.jpg
        return gerar.um("parceiro_SNhb31ZuuFA", nome, BASE.format(cena=CENAS[nome]))
    with ThreadPoolExecutor(2) as ex:
        for r in ex.map(um, CENAS):
            print(r, flush=True)
