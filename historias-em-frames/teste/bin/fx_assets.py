# -*- coding: utf-8 -*-
"""fx_assets.py — BANCOS DE DADOS de efeitos + EffectsManager (rotação anti-repetição).
W/H/FPS, MOVEMENTS_*, TRANSITIONS, COLOR/IMPACT/VIRAL/VIGNETTE_FILTERS. Sem ffmpeg. Base (não importa fx_*).

Parte do motor de efeitos — mapa completo na fachada effects_engine.py.
Split mecânico verbatim do _PRE_SPLIT_effects_engine.py.bak (2026-07-04).
"""
import random
import subprocess
import os
import re
from pathlib import Path



# ══════════════════════════════════════════════════════════════════════════
# PERFIS DE QUALIDADE (controlável via env QUALITY_PROFILE=draft|standard|high|ultra)
# ══════════════════════════════════════════════════════════════════════════
QUALITY_PROFILES = {
    "draft":    {"crf": 28, "preset": "ultrafast", "audio_bitrate": "96k"},
    "standard": {"crf": 23, "preset": "fast", "audio_bitrate": "192k"},
    "high":     {"crf": 20, "preset": "medium", "audio_bitrate": "256k"},
    "ultra":    {"crf": 18, "preset": "slow", "audio_bitrate": "320k"},
}
CURRENT_PROFILE = os.environ.get("QUALITY_PROFILE", "standard")
QP = QUALITY_PROFILES.get(CURRENT_PROFILE, QUALITY_PROFILES["standard"])

# ══════════════════════════════════════════════════════════════════════════
# SEÇÃO 1: BANCO DE MOVIMENTOS (zoompan ffmpeg) — adaptado pra 1080x1920 vertical
# ══════════════════════════════════════════════════════════════════════════

# Formato: 720x1280 (renderização + rápida). Upscale pra 1080x1920 no final.
# 720p tem 44% menos pixels que 1080p → zoompan/overlays correm 2× mais rápido.
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
# 2024-2025: zoom mais agressivo (1.3→1.5 em 2-3s vs antigo 1.15 em 4s)
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
    # ZOOM DELAY — suspense (parado no início, zoom repentino depois)
    {"filter": f"zoompan=z='if(lte(on,80),1.0,min(1.0+(on-80)*0.0015,1.35))':x='iw/2-(iw/zoom/2)':y='ih/3-(ih/zoom/2)':d={{frames}}:s={W}x{H}:fps={FPS}", "name": "🎯 Zoom Delay Rosto A"},
    {"filter": f"zoompan=z='if(lte(on,100),1.0,min(1.0+(on-100)*0.002,1.4))':x='iw/2-(iw/zoom/2)':y='ih/3-(ih/zoom/2)':d={{frames}}:s={W}x{H}:fps={FPS}", "name": "🎯 Zoom Delay Rosto B"},
    {"filter": f"zoompan=z='if(lte(on,60),1.0,min(1.0+(on-60)*0.0018,1.42))':x='iw/2-(iw/zoom/2)':y='ih/3-(ih/zoom/2)':d={{frames}}:s={W}x{H}:fps={FPS}", "name": "🎯 Zoom Delay Dramático"},
    # EASE IN/OUT — aceleração/desaceleração suave
    {"filter": f"zoompan=z='1.0+0.4*pow((on/{{frames}}),2)':x='iw/2-(iw/zoom/2)':y='ih/3-(ih/zoom/2)':d={{frames}}:s={W}x{H}:fps={FPS}", "name": "🎯 Zoom Ease In Rosto"},
    {"filter": f"zoompan=z='1.0+0.4*(1-pow(1-(on/{{frames}}),2))':x='iw/2-(iw/zoom/2)':y='ih/3-(ih/zoom/2)':d={{frames}}:s={W}x{H}:fps={FPS}", "name": "🎯 Zoom Ease Out Rosto"},
    {"filter": f"zoompan=z='1.0+0.35*(-cos(on/{{frames}}*PI)+1)/2':x='iw/2-(iw/zoom/2)':y='ih/3-(ih/zoom/2)':d={{frames}}:s={W}x{H}:fps={FPS}", "name": "🎯 Zoom Smooth Rosto"},
    # ZOOM FACIAL lento (terço superior = rosto em manhwa vertical)
    {"filter": f"zoompan=z='min(zoom+0.001,1.4)':x='iw/2-(iw/zoom/2)':y='ih/3-(ih/zoom/2)':d={{frames}}:s={W}x{H}:fps={FPS}", "name": "🎯 Zoom Facial Médio"},
    {"filter": f"zoompan=z='min(zoom+0.0006,1.3)':x='iw/2-(iw/zoom/2)':y='ih/3-(ih/zoom/2)':d={{frames}}:s={W}x{H}:fps={FPS}", "name": "🎯 Zoom Facial Lento"},
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

# Filtros de IMPACTO (portados do n8n V5.1 Tier 4) — aplicados em painéis de ação
IMPACT_FILTERS = [
    {"filter": "eq=contrast=1.3:brightness=-0.05:saturation=0.6", "name": "Impacto Dramático"},
    {"filter": "eq=contrast=1.4:saturation=0.5:brightness=-0.08", "name": "Impacto Pesado"},
    {"filter": "noise=alls=12:allf=t,eq=contrast=1.15:brightness=-0.03", "name": "Impacto Grão"},
    {"filter": "eq=contrast=1.25:gamma=0.85:saturation=0.75", "name": "Impacto Dark"},
]

# Filtros VIRAL por mood (n8n V5.1 — color grading emocional)
VIRAL_FILTERS = {
    "tense_dramatic": "eq=contrast=1.2:saturation=0.75:brightness=-0.04",
    "sad_emotional": "eq=brightness=-0.03:saturation=0.7:contrast=1.08",
    "romantic_sexy": "eq=brightness=0.04:saturation=1.15:contrast=1.02,colorbalance=rs=0.05:bs=-0.03",
    "funny_lighthearted": "eq=brightness=0.05:saturation=1.2:contrast=1.05",
    "calm_chill": "eq=brightness=0.02:contrast=1.03:saturation=1.05",
    "neutral_chill": "eq=contrast=1.04:saturation=1.0",
}

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
    """Gerencia a seleção de efeitos sem repetição consecutiva.
    Inclui memória de direção (n8n V5.1) pra não repetir mesmo sentido."""

    def __init__(self):
        self._indices = {}
        self._shuffled = {}
        self._last_direction = None  # "down", "up", "left", "right", "zoom_in", "zoom_out"

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

    def pick_movement(self, panel_height, panel_width, prefer_speed=None):
        """Escolhe movimento apropriado baseado nas dimensões do painel.
        Evita repetir mesma direção consecutivamente (memória visual n8n V5.1).
        prefer_speed (T7): se dado (ultra_slow|slow|medium|fast), tenta um movimento desse
        ritmo (guiado pela emoção da narração). Se não houver, cai no normal — sem regressão."""
        ratio = panel_height / panel_width if panel_width > 0 else 1
        cat = "movement_v" if ratio > 2.5 else ("movement_h" if ratio < 0.8 else "movement_z")

        # T7: preferência de ritmo pela emoção (CONTEXT_MOTION). Procura no pool da categoria
        # um movimento com o 'speed' pedido; se não achar, segue o fluxo normal.
        if prefer_speed:
            pool = self._get_pool(cat) or []
            cands = [m for m in pool if isinstance(m, dict) and m.get("speed") == prefer_speed]
            if cands:
                mov = random.choice(cands)
                self._last_direction = None
                return mov

        if ratio > 2.5:
            mov = self.next("movement_v")
        elif ratio < 0.8:
            mov = self.next("movement_h")
        else:
            mov = self.next("movement_z")

        if mov and isinstance(mov, dict):
            name = mov.get("name", "")
            direction = None
            if "⬇" in name or "Pan Glacial" in name or "Pan Lento" in name or "Pan Médio" in name or "Pan Rápido" in name:
                direction = "down"
            elif "⬆" in name or "Rev" in name:
                direction = "up"
            elif "➡" in name or "Dir" in name:
                direction = "right"
            elif "⬅" in name or "Esq" in name:
                direction = "left"
            elif "Zoom In" in name or "Push" in name or "Delay" in name or "Ease In" in name:
                direction = "zoom_in"
            elif "Zoom Out" in name or "Ease Out" in name:
                direction = "zoom_out"

            if direction and direction == self._last_direction:
                # Pegar outro pra não repetir direção
                alt = self.next("movement_v" if ratio > 2.5 else ("movement_h" if ratio < 0.8 else "movement_z"))
                if alt:
                    mov = alt
            self._last_direction = direction

        return mov

    def pick_transition(self):
        """Retorna nome da próxima transição."""
        return self.next("transition")

    def pick_color(self):
        """Retorna filtro de cor."""
        return self.next("color")

    def pick_vignette(self):
        """DESATIVADO — vinheta esconde texto dos balões."""
        return None
