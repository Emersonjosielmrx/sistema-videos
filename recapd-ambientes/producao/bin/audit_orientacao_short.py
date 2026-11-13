import sys
from pathlib import Path
from anime_probe import video_dimensions

d = Path('D:/recapd-ambientes/producao/workspace/anime')
shorts = list(d.glob('*/final_anime_short.mp4'))

print(f"Analisando os {len(shorts)} shorts gerados...")
verticais_nativos = 0
reframe_adaptado = 0
erros = 0

for v in shorts:
    work_dir = v.parent
    # Tenta achar qual foi o video original (fonte) dentro da pasta
    original = next((f for f in work_dir.glob('*.mp4') if f.name != 'final_anime_deitado.mp4' and f.name != 'final_anime_short.mp4'), None)
    
    if original:
        try:
            w, h = video_dimensions(str(original))
            razao = w / h
            # Se a largura é maior que a altura, ele é 16:9 (deitado)
            if razao > 1.0:
                print(f"[FALSO SHORT / REFRAME] {work_dir.name[:35]}... -> Original era {w}x{h}")
                reframe_adaptado += 1
            else:
                # Vertical de verdade
                verticais_nativos += 1
        except Exception as e:
            erros += 1
            pass

print(f"\nTotal: {verticais_nativos} nativos, {reframe_adaptado} reframes (falsos), {erros} erros_leitura.")
