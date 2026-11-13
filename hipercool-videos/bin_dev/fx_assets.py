# -*- coding: utf-8 -*-
"""fx_assets.py — BANCOS DE DADOS de efeitos + rotação (EffectsManager).

Parte do motor de efeitos (ver mapa completo em effects_engine.py).
Aqui só moram DADOS + a classe que os rotaciona — nenhuma chamada a ffmpeg.

  W, H, FPS               resolução de render (720p) e taxa de quadros.
  MOVEMENTS_VERTICAL/ZOOM/HORIZONTAL   filtros zoompan (Ken Burns) por formato.
  TRANSITIONS             nomes de transição xfade do ffmpeg.
  TRANSITION_DURATION     duração da transição (s).
  COLOR_FILTERS / VIGNETTE_FILTERS     ajustes sutis de cor/vinheta.
  EffectsManager          escolhe o próximo efeito SEM repetir consecutivo
                          (embaralha e rotaciona por categoria).

Não importa nenhum outro fx_* (é a base). Mexa aqui pra adicionar movimento
de câmera, transição nova, ou mudar a resolução de render.
"""
import random
import subprocess
import os
import re
from pathlib import Path


# Formato de renderização: 720p (44% menos pixels que 1080p -> 2× mais rápido).
# Upscale pra 1080x1920 acontece no fim do pipeline (ver fx_clips.upscale_to_fullhd).
W, H = 720, 1280
FPS = 30


# Movimentos de PAN vertical (pra strips altos de manhwa)
MOVEMENTS_VERTICAL = [
    # Ultra lento (pra painéis longos com texto)
    {"filter": f"zoompan=z=1.25:d={{frames}}:x='iw/2-(iw/zoom/2)':y='if(lte(on,{FPS}),0,min(ih-ih/zoom,(on-{FPS})*3))':s={W}x{H}:fps={FPS}", "name": "⬇️ Pan Glacial", "speed": "ultra_slow"},
    {"filter": f"zoompan=z=1.3:d={{frames}}:x='iw/2-(iw/zoom/2)':y='if(lte(on,{FPS}),0,min(ih-ih/zoom,(on-{FPS})*3.5))':s={W}x{H}:fps={FPS}", "name": "⬇️ Pan Ultra Lento", "speed": "ultra_slow"},
    {"filter": f"zoompan=z=1.25:d={{frames}}:x='iw/2-(iw/zoom/2)':y='if(lte(on,{FPS}),ih-ih/zoom,max(0,(ih-ih/zoom)-(on-{FPS})*3))':s={W}x{H}:fps={FPS}", "name": "⬆️ Pan Reverso Glacial", "speed": "ultra_slow"},
    {"filter": f"zoompan=z=1.3:d={{frames}}:x='iw/2-(iw/zoom/2)':y='if(lte(on,{FPS}),ih-ih/zoom,max(0,(ih-ih/zoom)-(on-{FPS})*3.5))':s={W}x{H}:fps={FPS}", "name": "⬆️ Pan Reverso Ultra Lento", "speed": "ultra_slow"},
    # Lento
    {"filter": f"zoompan=z=1.4:d={{frames}}:x='iw/2-(iw/zoom/2)':y='if(lte(on,{FPS}),0,min(ih-ih/zoom,(on-{FPS})*5))':s={W}x{H}:fps={FPS}", "name": "⬇️ Pan Lento A", "speed": "slow"},
    {"filter": f"zoompan=z=1.45:d={{frames}}:x='iw/2-(iw/zoom/2)':y='if(lte(on,{FPS}),0,min(ih-ih/zoom,(on-{FPS})*5.5))':s={W}x{H}:fps={FPS}", "name": "⬇️ Pan Lento B", "speed": "slow"},
    {"filter": f"zoompan=z=1.4:d={{frames}}:x='iw/2-(iw/zoom/2)':y='if(lte(on,{FPS}),ih-ih/zoom,max(0,(ih-ih/zoom)-(on-{FPS})*5))':s={W}x{H}:fps={FPS}", "name": "⬆️ Pan Rev Lento A", "speed": "slow"},
    {"filter": f"zoompan=z=1.45:d={{frames}}:x='iw/2-(iw/zoom/2)':y='if(lte(on,{FPS}),ih-ih/zoom,max(0,(ih-ih/zoom)-(on-{FPS})*5.5))':s={W}x{H}:fps={FPS}", "name": "⬆️ Pan Rev Lento B", "speed": "slow"},
    # Médio
    {"filter": f"zoompan=z=1.5:d={{frames}}:x='iw/2-(iw/zoom/2)':y='if(lte(on,{FPS}),0,min(ih-ih/zoom,(on-{FPS})*6.5))':s={W}x{H}:fps={FPS}", "name": "⬇️ Pan Médio A", "speed": "medium"},
    {"filter": f"zoompan=z=1.48:d={{frames}}:x='iw/2-(iw/zoom/2)':y='if(lte(on,{FPS}),0,min(ih-ih/zoom,(on-{FPS})*7))':s={W}x{H}:fps={FPS}", "name": "⬇️ Pan Médio B", "speed": "medium"},
    {"filter": f"zoompan=z=1.5:d={{frames}}:x='iw/2-(iw/zoom/2)':y='if(lte(on,{FPS}),ih-ih/zoom,max(0,(ih-ih/zoom)-(on-{FPS})*6.5))':s={W}x{H}:fps={FPS}", "name": "⬆️ Pan Rev Médio A", "speed": "medium"},
    {"filter": f"zoompan=z=1.55:d={{frames}}:x='iw/2-(iw/zoom/2)':y='if(lte(on,{FPS}),ih-ih/zoom,max(0,(ih-ih/zoom)-(on-{FPS})*7.5))':s={W}x{H}:fps={FPS}", "name": "⬆️ Pan Rev Médio B", "speed": "medium"},
    # Rápido
    {"filter": f"zoompan=z=1.3:d={{frames}}:x='iw/2-(iw/zoom/2)':y='if(lte(on,{FPS}),0,min(ih-ih/zoom,(on-{FPS})*9))':s={W}x{H}:fps={FPS}", "name": "⬇️ Pan Rápido", "speed": "fast"},
    {"filter": f"zoompan=z=1.3:d={{frames}}:x='iw/2-(iw/zoom/2)':y='if(lte(on,{FPS}),ih-ih/zoom,max(0,(ih-ih/zoom)-(on-{FPS})*9))':s={W}x{H}:fps={FPS}", "name": "⬆️ Pan Rev Rápido", "speed": "fast"},
]


# Movimentos de ZOOM (pra painéis curtos ou quadrados)
# 2024-2025: zoom mais agressivo (1.3->1.5 em 2-3s vs antigo 1.15 em 4s)
MOVEMENTS_ZOOM = [
    {"filter": f"zoompan=z='min(zoom+0.002,1.35)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={{frames}}:s={W}x{H}:fps={FPS}", "name": "🔍 Zoom In Agressivo"},
    {"filter": f"zoompan=z='if(eq(on,1),1.35,max(zoom-0.002,1.0))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={{frames}}:s={W}x{H}:fps={FPS}", "name": "🔍 Zoom Out Agressivo"},
    {"filter": f"zoompan=z='min(zoom+0.0015,1.3)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={{frames}}:s={W}x{H}:fps={FPS}", "name": "🔍 Zoom In Médio"},
    {"filter": f"zoompan=z='min(zoom+0.002,1.30)':x='iw/2-(iw/zoom/2)':y='0':d={{frames}}:s={W}x{H}:fps={FPS}", "name": "🔍 Zoom In Topo Rápido"},
    {"filter": f"zoompan=z='min(zoom+0.002,1.30)':x='iw/2-(iw/zoom/2)':y='ih-ih/zoom':d={{frames}}:s={W}x{H}:fps={FPS}", "name": "🔍 Zoom In Base Rápido"},
    {"filter": f"zoompan=z='min(zoom+0.0018,1.25)':x='0':y='ih/2-(ih/zoom/2)':d={{frames}}:s={W}x{H}:fps={FPS}", "name": "🔍 Zoom In Esquerda"},
    {"filter": f"zoompan=z='min(zoom+0.0018,1.25)':x='iw-iw/zoom':y='ih/2-(ih/zoom/2)':d={{frames}}:s={W}x{H}:fps={FPS}", "name": "🔍 Zoom In Direita"},
    # RESPIRAÇÃO — zoom sinusoidal (amplitude maior = mais dramático)
    {"filter": f"zoompan=z='1+0.06*sin(on*PI/{{frames}})':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={{frames}}:s={W}x{H}:fps={FPS}", "name": "🫁 Respiração Centro"},
    {"filter": f"zoompan=z='1+0.07*sin(on*PI/{{frames}})':x='iw/2-(iw/zoom/2)':y='0':d={{frames}}:s={W}x{H}:fps={FPS}", "name": "🫁 Respiração Topo"},
    {"filter": f"zoompan=z='1+0.06*sin(on*PI/{{frames}})':x='iw/2-(iw/zoom/2)':y='ih-ih/zoom':d={{frames}}:s={W}x{H}:fps={FPS}", "name": "🫁 Respiração Base"},
    # SPEED RAMP — zoom lento no início, acelera no final (snap effect)
    {"filter": f"zoompan=z='1+0.25*(on/{{frames}})*(on/{{frames}})':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={{frames}}:s={W}x{H}:fps={FPS}", "name": "🚀 Speed Ramp Centro"},
    {"filter": f"zoompan=z='1+0.20*(on/{{frames}})*(on/{{frames}})':x='iw/2-(iw/zoom/2)':y='0':d={{frames}}:s={W}x{H}:fps={FPS}", "name": "🚀 Speed Ramp Topo"},
    # HEARTBEAT — duplo pulso (emoção/tensão romântica)
    {"filter": f"zoompan=z='1.04+0.05*abs(sin(on*PI/{{frames}}*6))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={{frames}}:s={W}x{H}:fps={FPS}", "name": "💓 Heartbeat"},
    # PUSH emocional lento (tensão crescente)
    {"filter": f"zoompan=z='min(zoom+0.0009,1.18)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={{frames}}:s={W}x{H}:fps={FPS}", "name": "🎯 Push Emocional"},
]


# Movimentos HORIZONTAIS (pra painéis largos)
MOVEMENTS_HORIZONTAL = [
    {"filter": f"zoompan=z=1.2:d={{frames}}:x='if(lte(on,{FPS}),0,min(iw-iw/zoom,(on-{FPS})*4))':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={FPS}", "name": "➡️ Pan Horizontal Dir"},
    {"filter": f"zoompan=z=1.2:d={{frames}}:x='if(lte(on,{FPS}),iw-iw/zoom,max(0,(iw-iw/zoom)-(on-{FPS})*4))':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={FPS}", "name": "⬅️ Pan Horizontal Esq"},
]


# ══════════════════════════════════════════════════════════════════════════
# SEÇÃO 2: TRANSIÇÕES (xfade do ffmpeg)
# ══════════════════════════════════════════════════════════════════════════
TRANSITIONS = [
    # Suaves (momentos calmos)
    "fade", "fadeblack", "fadewhite", "dissolve",
    "smoothleft", "smoothright", "smoothup", "smoothdown",
    # Geométricas
    "wipeleft", "wiperight", "wipeup", "wipedown",
    "slideleft", "slideright", "slideup", "slidedown",
    "circlecrop", "circleopen", "circleclose",
    # Diagonais
    "diagtl", "diagtr", "diagbl", "diagbr",
    # Artísticas
    "pixelize", "radial", "horzopen", "horzclose", "vertopen", "vertclose",
    # Cover/Reveal
    "coverleft", "coverright", "coverup", "coverdown",
    "revealleft", "revealright", "revealup", "revealdown",
    # Estilo manhwa
    "squeezeh", "squeezev", "zoomin", "pagetear", # Novo efeito "rasgar página"
    "hlslice", "hrslice", "vuslice", "vdslice",
    # Rápidas/impacto
    "fadefast", "fadeslow", "distance", "punch", "snap", "rewind",
]


TRANSITION_DURATION = 0.3  # segundos (era 0.5, causava tela preta visível)


# ══════════════════════════════════════════════════════════════════════════
# SEÇÃO 3: FILTROS VISUAIS (cor, atmosfera)
# ══════════════════════════════════════════════════════════════════════════
# Filtros sutis que não atrapalham a leitura
COLOR_FILTERS = [
    # Apenas ajustes sutis de brilho/contraste/saturação — NADA de colorbalance,
    # curves ou rgbashift que alterem as cores originais dos painéis.
    {"filter": "eq=brightness=0.03:contrast=1.05:saturation=1.1", "name": "Vivid Leve"},
    {"filter": "eq=brightness=-0.02:contrast=1.08:saturation=0.9", "name": "Cinematic"},
    {"filter": "eq=brightness=0.01:contrast=1.03:saturation=1.2", "name": "Saturado"},
    {"filter": "eq=brightness=-0.03:contrast=1.1:saturation=0.8", "name": "Noir Leve"},
    {"filter": "eq=brightness=0.02:contrast=1.02:saturation=1.0", "name": "Natural+"},
    {"filter": "eq=brightness=-0.01:contrast=1.15:saturation=0.85", "name": "Alto Contraste"},
    {"filter": "eq=brightness=0.04:contrast=0.95:saturation=1.05", "name": "Soft Light"},
    {"filter": "eq=contrast=1.2:saturation=0.7:brightness=-0.02", "name": "Tensão Dessaturada"},
    {"filter": "eq=saturation=1.25:contrast=1.06:gamma=1.05", "name": "Vívido Pop"},
    {"filter": "noise=alls=8:allf=t,eq=contrast=1.06", "name": "Filme Grão Leve"},
]


# Efeitos de vinheta (bordas escuras)
VIGNETTE_FILTERS = [
    "vignette=PI/5",
    "vignette=PI/4",
    "vignette=PI/6:a=1.3",
    "vignette=PI/5:a=1.5",
    "vignette=PI/4.5",
    "vignette=PI/3.5:a=1.6",     # mais fechada (dramática)
    "vignette=PI/5,eq=contrast=1.04",  # vinheta + leve contraste
]


# ══════════════════════════════════════════════════════════════════════════
# SEÇÃO 4: GERENCIADOR DE EFEITOS (rotaciona pra não repetir)
# ══════════════════════════════════════════════════════════════════════════
class EffectsManager:
    """Gerencia a seleção de efeitos sem repetição consecutiva."""

    def __init__(self):
        self._indices = {}
        self._shuffled = {}

    def _get_pool(self, category):
        pools = {
            "movement_v": MOVEMENTS_VERTICAL,
            "movement_z": MOVEMENTS_ZOOM,
            "movement_h": MOVEMENTS_HORIZONTAL,
            "transition": TRANSITIONS,
            "color": COLOR_FILTERS,
            "vignette": VIGNETTE_FILTERS,
        }
        return pools.get(category, [])

    def next(self, category):
        """Retorna próximo efeito da categoria (rotação com shuffle)."""
        pool = self._get_pool(category)
        if not pool:
            return None

        if category not in self._shuffled:
            self._shuffled[category] = list(range(len(pool)))
            random.shuffle(self._shuffled[category])
            self._indices[category] = 0

        idx = self._indices[category]
        if idx >= len(self._shuffled[category]):
            # Re-shuffle
            random.shuffle(self._shuffled[category])
            self._indices[category] = 0
            idx = 0

        pick = pool[self._shuffled[category][idx]]
        self._indices[category] = idx + 1
        return pick

    def pick_movement(self, panel_height, panel_width):
        """Escolhe movimento apropriado baseado nas dimensões do painel."""
        ratio = panel_height / panel_width if panel_width > 0 else 1

        if ratio > 2.5:
            # Painel muito alto -> pan vertical
            return self.next("movement_v")
        elif ratio < 0.8:
            # Painel largo -> pan horizontal
            return self.next("movement_h")
        else:
            # Painel quadrado/médio -> zoom
            return self.next("movement_z")

    def pick_transition(self):
        """Retorna nome da próxima transição."""
        return self.next("transition")

    # clima da cena atual (fx_detect.detect_mood_from_text); o pipeline seta antes de montar cada clip
    clima = None

    def pick_color(self):
        """Filtro de cor que combina com o clima da cena (só eq sutil); sem clima -> rotação normal."""
        nomes = CORES_POR_CLIMA.get(self.clima)
        if nomes:
            return random.choice([c for c in COLOR_FILTERS if c["name"] in nomes])
        return self.next("color")

    def pick_vignette(self):
        """Filtro de vinheta: 50% em cena tensa/triste, 20% no resto (pra não escurecer balões)."""
        if random.random() < (0.5 if self.clima in ("tense_dramatic", "sad_emotional") else 0.2):
            return self.next("vignette")
        return None


CORES_POR_CLIMA = {
    "tense_dramatic": {"Tensão Dessaturada", "Alto Contraste", "Noir Leve"},
    "sad_emotional": {"Cinematic", "Noir Leve"},
    "romantic_sexy": {"Soft Light", "Vivid Leve"},
    "funny_lighthearted": {"Vívido Pop", "Saturado"},
    "calm_chill": {"Natural+", "Soft Light"},
}

