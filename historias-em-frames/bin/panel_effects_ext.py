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

# CORRECOES (QA visual em cena de 7s, 2026-10-02) — tem prioridade sobre o auto:
#  - spinin: o rotate vinha ANTES do zoompan; com imagem parada o zoompan so usa o 1o
#    quadro, entao o giro congelava torto o clip inteiro. Agora gira por quadro e o zoom
#    (que cobre os cantos pretos) desfaz junto com o giro.
#  - snapzoom/whipzoom/slowmoin: zoom sem teto (prototipo de 2.5s); em cena longa
#    terminava mostrando so um olho. Teto de 1.6x e curva presa em 1.
_CORRECOES = {
    "spinin": ("scale=1260:2240,setsar=1,fps={FPS},rotate='0.45*(1-min(t/1.0,1))':c=black,"
               "zoompan=z='1+0.75*(1-min(it/1.0,1))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
               ":d=1:s={W}x{H}:fps={FPS}"),
    "snapzoom": ("scale=2160:3840,setsar=1,zoompan=z='min(1+0.2*floor(on/15),1.6)':x='iw/2-(iw/zoom/2)'"
                 ":y='ih*0.35-(ih/zoom/2)':d={FR}:s={W}x{H}:fps={FPS}"),
    "whipzoom": ("scale=2160:3840,setsar=1,zoompan=z='min(1+0.06*on,1.6)':x='iw*0.5-(iw/zoom/2)'"
                 ":y='ih*0.3-(ih/zoom/2)':d={FR}:s={W}x{H}:fps={FPS},tblend=all_mode=average"),
    "slowmoin": ("scale=2160:3840,setsar=1,zoompan=z='1+0.5*(1-pow(1-min(on/63,1),3))':x='iw/2-(iw/zoom/2)'"
                 ":y='ih*0.32-(ih/zoom/2)':d={FR}:s={W}x{H}:fps={FPS}"),
}

# auto (fonte de verdade) tem prioridade sobre o manual se colidir o nome; correcoes por ultimo
EXTRA_FX = {**_MANUAL, **EXTRA_FX_AUTO, **_CORRECOES}

# Recorte: minhas variações (tuplas) + os templates 2-input do .sh (strings, fonte de verdade).
# build_cutout_clip aceita OS DOIS formatos (tupla = estrutura fixa; string = template cru [0:v]/[1:v]).
_MANUAL_CUTOUT = {
    # 1.04 e preso na base (ver CUTOUT_FX no panel_effects): em 0.80 centralizado o
    # personagem flutuava no meio da tela com o corpo cortado numa linha reta.
    "charfloat":     (1.04, "(main_w-overlay_w)/2", "(main_h-overlay_h) + 16 + 14*sin(1.2*t)", 18, 0.0008),
    "charsway":      (1.04, "(main_w-overlay_w)/2 + 26*sin(1.1*t)", "(main_h-overlay_h) + 16 + 8*sin(2.2*t)", 20, 0.0011),
    "charzoomdrift": (1.06, "(main_w-overlay_w)/2 + 22*sin(0.7*t)", "(main_h-overlay_h) + 18 + 12*cos(0.5*t)", 20, 0.0013),
}
EXTRA_CUTOUT = {**_MANUAL_CUTOUT, **CUTOUT_TPL_AUTO}
