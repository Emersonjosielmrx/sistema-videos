# Prova (01/11): capa com modelo anime Illustrious + ControlNet OpenPose no Space grátis r3gm/DiffuseCraft.
# A pose vem da capa do hipercool (só o esqueleto), o tamanho do corpo vem das tags (o Flow/Google travam o seio).
#   python poc_illustrious.py <pose.png> <saida.png> "<tags extras>" [modelo]
import json
import shutil
import sys
from pathlib import Path

from gradio_client import Client, handle_file

API = json.loads((Path(__file__).parent / "_diffusecraft_api.json").read_text(encoding="utf-8"))
MODELO = "John6666/wai-nsfw-illustrious-sdxl-v140-sdxl"
POS = ("masterpiece, best quality, amazing quality, very aesthetic, absurdres, manhwa style, vibrant colors, "
       "bright sunny lighting, 1girl, 1boy, mature female, huge breasts, cleavage, narrow waist, wide hips, "
       "thick thighs, micro bikini, blush, smile, looking at viewer, 1boy blushing, embarrassed boy, {extra}")
NEG = ("nsfw, nude, nipples, areola, pussy, penis, sex, explicit, topless, bottomless, loli, child, "
       "small breasts, flat chest, clothes, shirt, skirt, dress, jacket, text, watermark, logo, signature, "
       "lowres, bad anatomy, bad hands, extra fingers, missing fingers, worst quality, low quality, blurry, monochrome")


def main(pose, saida, extra="", modelo=MODELO):
    c = Client("r3gm/DiffuseCraft", verbose=False)
    print(c.predict(modelo, "None", "openpose ControlNet", "Automatic", api_name="/load_new_model"))
    params = API["named_endpoints"]["/sd_gen_generate_pipeline"]["parameters"]
    v = [p.get("parameter_default") for p in params]
    v[0], v[1] = POS.format(extra=extra), NEG
    v[3], v[4] = 28, 6.0                     # passos, cfg
    v[21], v[22] = "Euler a", "Automatic"
    v[24], v[25] = 1344, 768                 # 16:9
    v[26], v[27], v[28] = modelo, "None", "openpose ControlNet"
    v[29] = handle_file(pose)                # imagem de controle
    v[30] = "Openpose"                       # pré-processador: tira só o esqueleto da imagem
    v[31], v[32] = 512, 1024                 # resolução do pré-processador / imagem
    r = c.predict(*v, api_name="/sd_gen_generate_pipeline")
    print(str(r)[:800])
    imgs = []

    def achar(x):
        if isinstance(x, str) and Path(x).suffix.lower() in (".png", ".jpg", ".webp") and Path(x).exists():
            imgs.append(x)
        elif isinstance(x, (list, tuple)):
            for y in x:
                achar(y)
        elif isinstance(x, dict):
            for y in x.values():
                achar(y)
    achar(r)
    if imgs:
        shutil.copy(imgs[0], saida)
        print("OK", saida)
    else:
        print("sem imagem")


if __name__ == "__main__":
    main(*sys.argv[1:])
