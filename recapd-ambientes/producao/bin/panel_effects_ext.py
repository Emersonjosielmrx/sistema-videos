"""panel_effects_ext.py — LOTE EXTRA de efeitos de painel (2026-07-04).

Separado do panel_effects.py de propósito (evita conflito de edição). O panel_effects.py
faz `PANEL_FX.update(EXTRA_FX)` / `CUTOUT_FX.update(EXTRA_CUTOUT)` no fim do arquivo.

Fontes:
  - panel_fx_auto.EXTRA_FX_AUTO = 58 builders SINGLE-INPUT auto-convertidos do
    COMANDOS_PROTOTIPOS.sh (fonte de verdade regerada 2026-07-04). Usam o ffmpeg EXATO
    dos protótipos aprovados. 33 são zoompan puro (seguros); 25 usam blend/geq (validar).
  - _MANUAL = variações minhas de zoompan (não estão no catálogo, mas dão variedade).

⚠️ Os 58 auto ainda não foram todos ffmpeg-testados. Se algum tiver erro de sintaxe, o
build_effect_clip retorna False → cai no Ken Burns (não quebra). Rodar o teste de build
em lote (bin/smoketest ou o script de lote) quando não houver render competindo.
"""

# Variações extras (não estão no catálogo dos 126 — bônus de variedade, zoompan puro)
_MANUAL = {
    "punchin":     "scale=2160:3840,setsar=1,zoompan=z='min(1+0.03*on,1.6)':x='iw/2-(iw/zoom/2)':y='ih*0.32-(ih/zoom/2)':d={FR}:s={W}x{H}:fps={FPS}",
    "slowpull":    "scale=2160:3840,setsar=1,zoompan=z='1.5-0.32*on/{FR}':x='iw/2-(iw/zoom/2)':y='ih*0.35-(ih/zoom/2)':d={FR}:s={W}x{H}:fps={FPS}",
    "driftLR":     "scale=1584:2816,setsar=1,zoompan=z=1.28:x='(iw-iw/zoom)*(0.5+0.4*sin(on/40))':y='ih*0.35-(ih/zoom/2)':d={FR}:s={W}x{H}:fps={FPS}",
    "riseup":      "scale=1584:2816,setsar=1,zoompan=z='1.2+0.1*on/{FR}':x='iw/2-(iw/zoom/2)':y='(ih-ih/zoom)*(1-0.5*on/{FR})':d={FR}:s={W}x{H}:fps={FPS}",
    "tensionhold": "scale=1584:2816,setsar=1,zoompan=z='1.1+0.03*sin(on/8)':x='iw/2-(iw/zoom/2)':y='ih*0.4-(ih/zoom/2)':d={FR}:s={W}x{H}:fps={FPS}",
}

try:
    from panel_fx_auto import EXTRA_FX_AUTO, CUTOUT_TPL_AUTO, FX2_TPL_AUTO
except Exception:
    EXTRA_FX_AUTO = {}
    CUTOUT_TPL_AUTO = {}
    FX2_TPL_AUTO = {}
try:
    from panel_fx_auto import ADVFX_AUTO
except Exception:
    ADVFX_AUTO = {}

# Transições/multi-painel (2-input com o PRÓXIMO painel = IMG2). Templates crus do .sh.
EXTRA_FX2 = dict(FX2_TPL_AUTO)
# Avançados (depth/atmosfera/multi-personagem): {nome: {tpl, inputs:[...], cmd}}.
EXTRA_ADVFX = dict(ADVFX_AUTO)

# auto (fonte de verdade) tem prioridade sobre o manual se colidir o nome
EXTRA_FX = {**_MANUAL, **EXTRA_FX_AUTO}

# Recorte: minhas variações (tuplas) + os templates 2-input do .sh (strings, fonte de verdade).
# build_cutout_clip aceita OS DOIS formatos (tupla = estrutura fixa; string = template cru [0:v]/[1:v]).
_MANUAL_CUTOUT = {
    "charfloat":     (0.80, "(main_w-overlay_w)/2", "(main_h-overlay_h)/2 + 28*sin(1.2*t)", 18, 0.0008),
    "charsway":      (0.80, "(main_w-overlay_w)/2 + 40*sin(1.1*t)", "(main_h-overlay_h)/2 + 12*sin(2.2*t)", 20, 0.0011),
    "charzoomdrift": (0.82, "(main_w-overlay_w)/2 + 30*sin(0.7*t)", "(main_h-overlay_h)/2 + 30*cos(0.5*t)", 20, 0.0013),
}
EXTRA_CUTOUT = {**_MANUAL_CUTOUT, **CUTOUT_TPL_AUTO}
