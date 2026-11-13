from PIL import Image
import numpy as np
from pathlib import Path
C=Path(r'D:\hipercool-videos\config\capas_referencia'); R=Path(r'D:\hipercool-materiais\capas_poses_ref\recebidas')
O=Path(r'D:\hipercool-materiais\capas_poses_ref\b'); O.mkdir(exist_ok=True)
src={'sentada_ao_lado':C/'05_sentada_ao_lado_100_namorados.png','sentada_nas_costas':C/'07_sentada_nas_costas_comprado.png',
'pernas_em_volta_cabeca':C/'08_pernas_em_volta_cabeca_unico_homem.png','de_quatro_por_cima_2':C/'09_de_quatro_por_cima_pare_de_frescura.png',
'de_quatro_bom_dia':C/'10_de_quatro_bom_dia_lindinho.png','colo_de_frente_2':C/'11_colo_de_frente_agora_sou_sua.png',
'ele_atras_dela_deusa':C/'12_ele_atras_dela_mundo_salvo.png','harem_3_waifus':C/'13_harem_3_waifus.png',
'harem_biquini':C/'14_harem_biquini_colegio.png','mao_no_peito_ciume':C/'21_mao_minha_t3ta.png',
'chute_perna_segurada':R/'e57270d3_2.png','ele_atras_agarrando':R/'e57270d3_3.png','ele_nas_costas_dela':R/'e57270d3_5.png'}
for n,p in src.items():
    if not p.exists():
        print('FALTA',p); continue
    im=Image.open(p).convert('RGB'); a=np.asarray(im).astype(int); h,w,_=a.shape
    lum=a.mean(2); top=lum[:int(h*0.6)]
    cols=np.where((top>45).mean(0)>0.5)[0]; x0,x1=cols.min(),cols.max()
    rows=np.where((lum[:,x0:x1]>45).mean(1)>0.5)[0]; y0=rows.min()
    y1=min(h,y0+int((x1-x0)*9/16))
    c=im.crop((x0+4,y0+4,x1-4,y1-4)); c.save(O/f'{n}.png'); print(n,c.size)
