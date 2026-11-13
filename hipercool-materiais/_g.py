from PIL import Image
from pathlib import Path
r=Path(r"D:\hipercool-videos\config\capas_referencia")
o=Path(r"D:\hipercool-materiais\capas_proximo_G1_iPga6nLg\proximos\poses"); o.mkdir(exist_ok=True)
cortes={"de_quatro_por_cima":("09_de_quatro_por_cima_pare_de_frescura.png",None),
 "de_quatro_olhando_tras":("10_de_quatro_bom_dia_lindinho.png",None),
 "de_quatro_costas_cama":("06_pernas_no_pescoco_e_de_quatro_waifu.png","dir"),
 "colo_de_frente":("11_colo_de_frente_agora_sou_sua.png",None),
 "sentada_nele":("07_sentada_nas_costas_comprado.png",None),
 "harem_cama":("13_harem_3_waifus.png",None)}
ims=[]
for nome,(f,lado) in cortes.items():
    im=Image.open(r/f).convert("RGB"); w,h=im.size
    if lado=="dir": im=im.crop((w//2+4,0,w,h)); w,h=im.size
    im=im.crop((0,0,w,int(h*0.80)))
    im.save(o/f"{nome}.png"); ims.append(im)
W,H=480,270
sh=Image.new("RGB",(W*3,H*2))
for i,im in enumerate(ims):
    im=im.copy(); im.thumbnail((W,H)); sh.paste(im,((i%3)*W,(i//3)*H))
sh.save(r"D:\hipercool-materiais\_folha_ref.jpg",quality=85)
