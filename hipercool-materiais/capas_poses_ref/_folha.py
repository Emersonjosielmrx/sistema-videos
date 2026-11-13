from PIL import Image, ImageDraw
from pathlib import Path
import sys
fs=[]
for p in sys.argv[2:]:
    fs+=sorted(x for x in Path(p).iterdir() if x.suffix.lower() in ('.png','.jpg','.jpeg','.webp'))
W,H=360,220; cols=5; rows=(len(fs)+cols-1)//cols
g=Image.new('RGB',(W*cols,(H+18)*rows),'white'); d=ImageDraw.Draw(g)
for i,f in enumerate(fs):
    im=Image.open(f).convert('RGB'); im.thumbnail((W,H))
    x,y=(i%cols)*W,(i//cols)*(H+18); g.paste(im,(x,y+18)); d.text((x+2,y+2),f.parent.name[:10]+'/'+f.name[:40],fill='black')
g.save(sys.argv[1]); print(len(fs))
