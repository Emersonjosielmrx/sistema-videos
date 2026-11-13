from PIL import Image
import os
d = r"D:\ms-energy\propostas\_img"
k = 1786/924
def c(pag, box, nome):
    im = Image.open(os.path.join(d, f"pag{pag}.png"))
    b = tuple(int(v*k) for v in box)
    im.crop(b).convert("RGB").save(os.path.join(d, nome), quality=93)
c(1, (0,0,924,1090), "capa.jpg")
c(2, (115,485,290,578), "logo.jpg")
c(3, (82,1060,690,1103), "parceiros.jpg")
c(7, (122,452,770,503), "bancos.jpg")
fotos = [(113,203,425,447),(482,203,792,447),(110,497,425,735),(482,497,792,735),(113,780,425,1017),(482,780,792,1017)]
cid = ["Capitão Poço","Santa Maria do Pará","Capitão Poço","Capitão Poço","Capitão Poço","Capitão Poço"]
for i,f in enumerate(fotos): c(11, f, f"inst{i}.jpg")
prods = {"painel":(120,218,237,320),"estrutura":(120,430,237,525),"cabo_preto":(120,532,237,625),"cabo_verm":(120,635,237,728),"projeto":(120,735,252,825),"instalacao":(120,835,190,925)}
for n,b in prods.items(): c(6, b, f"prod_{n}.jpg")
# folha de conferencia
ims = [Image.open(os.path.join(d,f)) for f in sorted(os.listdir(d)) if f.endswith(".jpg")]
W=1400; y=0; folha=Image.new("RGB",(W,4000),"white"); x=0; h=0
for im in ims:
    im.thumbnail((330,330))
    if x+im.width>W: x=0; y+=h+10; h=0
    folha.paste(im,(x,y)); x+=im.width+10; h=max(h,im.height)
folha.crop((0,0,W,y+h)).save(os.path.join(d,"_folha.png"))
