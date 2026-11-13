# Capas-exemplo 01/11 (dona): capa ORIGINAL do parceiro melhorada — mesmos personagens, colorida (nunca escura),
# mulheres sensuais (Maria, a mascote, + outra que combine). 8 pedidos em paralelo no Flow, todas as máquinas.
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

BASE = Path(r"D:\hipercool-materiais\capas_exemplo_01nov")
ORIG = BASE / "originais"
OUT = BASE / "brutas"
OUT.mkdir(exist_ok=True)
MARIA = r"D:\hipercool-materiais\mascote_waifu_v2\andando_16x9\14_biquini_dama_1.png"
MAQ = "pc1,desktop,x200ma,acer"

COMUM = (
    "Recreate and IMPROVE the FIRST reference image (a YouTube manhwa thumbnail) as a brand-new 16:9 anime thumbnail. "
    "Keep the SAME main character EXACTLY as drawn in it (same face, hair, eyes, outfit, props) so fans recognize the "
    "story, large in the frame, and keep the same story elements. Colors: BRIGHT, SUNNY, VIVID and HIGHLY SATURATED, "
    "daylight, clean sharp manhwa art, glossy lighting - never dark, gloomy, desaturated or night. "
    "Add MARIA: the woman from the SECOND reference image - same face, long wavy dark-brown hair, golden-brown eyes, "
    "tanned skin, curvy grown-up adult body in her late twenties - {maria}. {extra} "
    "The women are gorgeous, curvy, blushing, flirty, clearly adults, nothing private exposed, no nudity. "
    "One single scene (no panels unless stated). Remove ALL text, letters, numbers, logos and watermarks. {vazio}")

PEDIDOS = {
    "pjOoN03xa0k": ("Leave the top-left and bottom areas a bit less busy for big labels.", [
        ("a", "wearing a red-and-gold pirate bikini with a short open captain coat, clinging to his left arm and "
              "smiling at the viewer",
         "Also add a gorgeous blonde noblewoman in a low-cut off-shoulder royal-blue gown with a high leg slit, "
         "leaning on his right shoulder. Keep the old wooden galleon and steampunk airships on the left and the "
         "modern battleship and warplanes on the right, bright blue sky and turquoise sea."),
        ("b", "wearing a red-and-gold pirate bikini, hugging him tightly from behind with her chin on his shoulder",
         "Also add a gorgeous blonde noblewoman in lace lingerie-style corset and sheer robe sitting sideways on the "
         "railing beside him, hand on his chest, jealous of Maria. Galleon left, battleship right, sunny blue sea."),
    ]),
    "VgQUQTmYLeQ": ("Leave the bottom area less busy for big labels.", [
        ("a", "wearing a tiny plaid farm-girl bikini top, denim micro shorts and a straw hat, holding a basket of "
              "vegetables and leaning on his arm",
         "KEEP the before/after SPLIT layout of the original: left half = the poor patched greenhouse in an "
         "apocalypse desert but painted in vivid orange and gold sunset colors (not muddy); right half = the same "
         "silver-haired farmer in overalls and yellow gloves at a lush green farm with red barn. Do NOT include the "
         "small chibi child; instead add a gorgeous redhead woman in a tied-up crop top and short shorts on the "
         "right half admiring him."),
        ("b", "wearing a tiny plaid bikini and a straw hat, hugging his arm and pressing close, blushing",
         "One single scene at the lush green farm with red barn and glowing holographic farm level panel (no text "
         "in it). A gorgeous redhead woman in a cropped tank top and denim micro shorts hugs him from the other "
         "side. Do NOT include the small chibi child. Bright summer day."),
    ]),
    "ssMbrCz0fhE": ("Leave the top-left corner less busy for a big label.", [
        ("a", "wearing only a short leather blacksmith apron over a red bikini, standing behind him with hands on "
              "his shoulders, heart eyes",
         "Keep the glowing rainbow-fire sword on the anvil, the bright sunny forge with big windows and the shocked "
         "blond man. Restyle the shocked redhead woman as a gorgeous curvy adult in an unbuttoned white shirt tied "
         "under the chest showing cleavage and a tight short skirt, pointing at the sword amazed."),
        ("b", "wearing a red bikini with a tiny leather apron, pressed against his arm, biting her lip",
         "The redhead woman (gorgeous curvy adult, low-cut tied white shirt, short skirt) clings to his other arm, "
         "both women competing for him (comedic), while he hammers the glowing rainbow-fire sword. Blond man shocked "
         "in the background. Bright sunny forge."),
    ]),
    "bSwsF_ISmrM": ("Leave the top area less busy for big labels.", [
        ("a", "wearing a yellow-and-black bee-striped bikini with tiny wings hair clip, sitting on the wheelbarrow of "
              "tomatoes winking",
         "Keep the farmer (brown hair, straw hat, white t-shirt, hoe on shoulder), the bunnies, the cat, the bees, "
         "the tomatoes and carrots and the green dungeon garden with pond. Make the bee monster-girl a gorgeous "
         "curvy ADULT bee-woman with a fluffy collar and striped bodysuit, flirting with him."),
        ("b", "wearing a yellow-and-black bee-striped bikini, hugging his arm and leaning on him",
         "A gorgeous curvy adult elf woman in a green leaf bikini holding a basket of tomatoes hugs him from the "
         "other side. Keep the bunnies with straw hat, the cat, the bees and the lush green dungeon farm with pond, "
         "farmer with straw hat and hoe."),
    ]),
}


def um(vid, letra, prompt, refs=()):
    saida = OUT / f"{vid}_{letra}.png"
    if saida.exists():
        return f"{saida.name} já existe"
    r = subprocess.run([r"D:\veo\venv\Scripts\python.exe", r"D:\flow-imagens\gera_imagem.py", prompt, str(saida),
                        "--ref", str(ORIG / f"{vid}.jpg"), MARIA, *map(str, refs), "--formato", "16:9", "--quantidade", "1",
                        "--maquinas", MAQ, "--max-contas", "6"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=2400,
                       creationflags=0x08000000)
    (OUT / f"{vid}_{letra}.log").write_text(r.stdout[-4000:] + "\n---\n" + r.stderr[-4000:], encoding="utf-8")
    feitos = sorted(OUT.glob(f"{vid}_{letra}*.png"))
    return f"{vid}_{letra}: {'OK ' + feitos[0].name if feitos else 'FALHOU rc=' + str(r.returncode)}"


def main():
    so = sys.argv[1:]
    jobs = []
    for vid, (vazio, vs) in PEDIDOS.items():
        for letra, maria, extra in vs:
            if so and f"{vid}_{letra}" not in so:
                continue
            jobs.append((vid, letra, COMUM.format(maria=maria, extra=extra, vazio=vazio)))
    with ThreadPoolExecutor(len(jobs)) as ex:
        for res in ex.map(lambda j: um(*j), jobs):
            print(res, flush=True)


if __name__ == "__main__":
    main()
