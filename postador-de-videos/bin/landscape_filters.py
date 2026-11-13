# COMUM — fonte única: D:\hipercool-materiais\comum\landscape_filters.py. Mudou esta cópia? python D:\hipercool-materiais\bin\recursos.py subir landscape_filters.py --de <projeto>
"""landscape_filters.py — banco de fundos 16:9 pro compilado paisagem (T10, abordagem B).

Porte dos VISUAL_FILTERS do fluxo n8n "3" (eram 1280x720; aqui parametrizados por W/H, default
1920x1080). Cada filtro compõe a imagem retrato CENTRADA num quadro 16:9 com fundo desfocado/
colorido — exatamente o que NÃO cabia no vertical e agora aproveita a largura do paisagem.

Uso no landscape-compiler atrás de LS_FILTERS=1: em vez do blur fixo, escolhe um destes
(anti-repetição). pick_filter() devolve o filter_complex pronto pra W/H dados.
"""
import os
import random

# (nome, peso, template). {W}/{H} são formatados. Estrutura split bg(blur/cor)+fg(centro).
# Subconjunto curado do Tier 1 (alta legibilidade) do fluxo 3.
_FILTERS = [
    ("Blur Suave", 10,
     "[0:v]split=2[bg][fg];[bg]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=18:8[bgb];[fg]scale={W}:{H}:force_original_aspect_ratio=decrease[fgs];[bgb][fgs]overlay=(W-w)/2:(H-h)/2"),
    ("Dark Suave", 10,
     "[0:v]split=2[bg][fg];[bg]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=18:8,eq=brightness=-0.4[bgd];[fg]scale={W}:{H}:force_original_aspect_ratio=decrease[fgs];[bgd][fgs]overlay=(W-w)/2:(H-h)/2"),
    ("Depth Focus", 9,
     "[0:v]split=2[bg][fg];[bg]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=22:9[bgb];[fg]scale={W}:{H}:force_original_aspect_ratio=decrease,unsharp=5:5:0.8:5:5:0.0[fgsh];[bgb][fgsh]overlay=(W-w)/2:(H-h)/2"),
    ("Romantic Suave", 8,
     "[0:v]split=2[bg][fg];[bg]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=28:10,colorbalance=rs=0.15:gs=0.08:bs=0.15[bgp];[fg]scale={W}:{H}:force_original_aspect_ratio=decrease[fgs];[bgp][fgs]overlay=(W-w)/2:(H-h)/2"),
    ("Cold Suave", 8,
     "[0:v]split=2[bg][fg];[bg]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=18:8,colorbalance=bs=0.25:rs=-0.15[bgc];[fg]scale={W}:{H}:force_original_aspect_ratio=decrease,eq=saturation=0.85[fgs];[bgc][fgs]overlay=(W-w)/2:(H-h)/2"),
    ("Golden Suave", 8,
     "[0:v]split=2[bg][fg];[bg]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=22:8,colorbalance=rs=0.15:gs=0.08:bs=-0.15[bgg];[fg]scale={W}:{H}:force_original_aspect_ratio=decrease[fgs];[bgg][fgs]overlay=(W-w)/2:(H-h)/2"),
    ("Noir Suave", 7,
     "[0:v]split=2[bg][fg];[bg]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=18:8,hue=s=0[bgbw];[fg]scale={W}:{H}:force_original_aspect_ratio=decrease,hue=s=0,eq=contrast=1.05[fgs];[bgbw][fgs]overlay=(W-w)/2:(H-h)/2"),
    ("Sepia Suave", 7,
     "[0:v]split=2[bg][fg];[bg]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=18:8,colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131[bgsp];[fg]scale={W}:{H}:force_original_aspect_ratio=decrease[fgs];[bgsp][fgs]overlay=(W-w)/2:(H-h)/2"),
    ("Blue Suave", 8,
     "[0:v]split=2[bg][fg];[bg]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=18:8,colorbalance=bs=0.3:rs=-0.15:gs=-0.08[bgbl];[fg]scale={W}:{H}:force_original_aspect_ratio=decrease[fgs];[bgbl][fgs]overlay=(W-w)/2:(H-h)/2"),
    ("Cinematic Frame", 9,
     "[0:v]split=2[bg][fg];[bg]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=18:8[bgb];[fg]scale={W}:{H}:force_original_aspect_ratio=decrease[fgs];[bgb][fgs]overlay=(W-w)/2:(H-h)/2,vignette=PI/10"),
]

_last_name = None


def pick_filter(width=1920, height=1080):
    """Escolhe um filtro 16:9 (ponderado, anti-repetição) e retorna (nome, filter_complex).
    O resultado termina SEM label de saída — o caller decide [out]/-map. Espelha o formato
    que o landscape-compiler já usa (a string atual termina em ...overlay=...[out])."""
    global _last_name
    cands = [f for f in _FILTERS if f[0] != _last_name] or _FILTERS
    nomes = [c[0] for c in cands]
    pesos = [c[1] for c in cands]
    nome = random.choices(nomes, weights=pesos, k=1)[0]
    tpl = next(f[2] for f in cands if f[0] == nome)
    _last_name = nome
    return nome, tpl.format(W=width, H=height)


def names():
    return [f[0] for f in _FILTERS]
