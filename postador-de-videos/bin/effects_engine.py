#!/usr/bin/env python3
"""effects_engine.py — Motor de efeitos visuais portado do n8n (4500 linhas JS → Python).

Porta os melhores efeitos do node Code "aplica efeitos" da fábrica de animes.
Inclui: filtros visuais, transições, movimentos (zoom/pan), trilha sonora.

ARQUITETURA:
  Seção 1: Movimentos (zoompan) — 14 vertical + 22 zoom + 2 horizontal
  Seção 2: Transições (xfade no concat entre clips)
  Seção 3: Filtros visuais (cor, viral por mood, impacto, vinheta)
  Seção 4: EffectsManager (rotação anti-repetição)
  Seção 4B: Transições baked-in (get_transition_and_sfx + apply_effects_to_cmd)
  Seção 4C: SFX contextual por keyword (pick_sfx_for_text)
  Seção 5: Build clips (build_clip, build_clip_with_shake, build_flash_clip, build_meme_clip)
  Seção 6: Concat + trilha dinâmica + legendas + upscale
  Seção 7: Áudio profissional (enhance_narration_audio)

REFERÊNCIA: bin/_reference_n8n_effects_FULL.js (256KB extraído do n8n workflow)
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


# ══════════════════════════════════════════════════════════════════════════
# SEÇÃO 4B: DETECÇÃO DE IMPACTO (pra decidir shake/sfx)
# ══════════════════════════════════════════════════════════════════════════

IMPACT_KEYWORDS = [
    "soco", "punch", "chute", "kick", "explosão", "explosion", "impacto",
    "impact", "quebr", "smash", "crash", "bate", "hit", "golpe", "strike",
    "pow", "bang", "slam", "ataque", "attack", "destr", "sangue", "blood",
    "grito", "scream", "tiro", "shot", "cai", "fall", "queda", "drop",
    "esmaga", "crush", "rasga", "rip", "corta", "cut", "faca", "knife",
    "espada", "sword", "luta", "fight", "morre", "kill", "rage", "fúria",
    "voando", "arremess", "jogou", "empurr", "choque", "colidiu", "batida",
    "pancada", "murro", "porrada", "nocaute", "ko", "desmaiou", "capotou",
]


def is_impact_panel(description: str) -> bool:
    """Detecta se o painel tem contexto de ação/impacto. Haiku primeiro, keyword fallback."""
    if not description:
        return False
    try:
        import haiku_helpers
        c = haiku_helpers.classify_action(description)
        if c is not None:
            return c == "impact"
    except Exception:
        pass
    desc_lower = description.lower()
    return any(kw in desc_lower for kw in IMPACT_KEYWORDS)


# ══════════════════════════════════════════════════════════════════════════
# SEÇÃO 4C: SFX BANK (efeitos sonoros pra transições)
# ══════════════════════════════════════════════════════════════════════════

SFX_DIR = Path(__file__).parent.parent / "workspace" / "assets" / "sfx"
SFX_MEMES_DIR = Path(__file__).parent.parent / "workspace" / "assets" / "sfx_memes"
SFX_FOLEY_DIR = Path(__file__).parent.parent / "workspace" / "assets" / "sfx_foley"
# Pasta de SFX PRIORITÁRIOS (genéricos/atmosféricos — riser, drone, ambiência).
# Igual às trilhas prioritárias: o usuário arrasta pra cá os efeitos que quer ouvir
# mais. SFX ESPECÍFICOS (soco, porta, espada) NÃO entram aqui — eles são acionados
# direto por palavra-chave no FOLEY_DIRECT_MAP, sem sorteio.
SFX_PRIORIDADE_DIR = Path(__file__).parent.parent / "workspace" / "assets" / "sfx_prioridade"
# sfx_extras: 748 sons baixados, ficam na subpasta sonoros/. Antes NÃO eram usados.
SFX_EXTRAS_DIR = Path(__file__).parent.parent / "workspace" / "assets" / "sfx_extras" / "sonoros"
ALL_SFX_DIRS = [SFX_DIR, SFX_MEMES_DIR, SFX_FOLEY_DIR, SFX_EXTRAS_DIR]

# Duração de SFX em segundos, com cache (ffprobe é caro p/ chamar por clip).
_sfx_dur_cache = {}
def sfx_duration(path):
    """Retorna a duração (s) de um arquivo de áudio. Cacheada. 0.0 se falhar."""
    if not path:
        return 0.0
    key = str(path)
    if key in _sfx_dur_cache:
        return _sfx_dur_cache[key]
    dur = 0.0
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", key],
            capture_output=True, text=True, timeout=15)
        dur = float(out.stdout.strip() or 0.0)
    except Exception:
        dur = 0.0
    _sfx_dur_cache[key] = dur
    return dur

# ── Banco de SFX por MOOD (lê os *_categorized.json) ─────────────────────────
# Os JSONs mapeiam cada arquivo a uma categoria de clima (impacto/comedia/triste/
# suspense/romance/ambiente/transicao/sistema/neutro). Antes esse trabalho de
# categorização ficava IGNORADO — agora o pick_sfx_by_mood() usa pra escolher um
# som que combine com a cena em vez de sortear no escuro.
_SFX_MOOD_BANK = None  # cache: {categoria: [Path, ...]}

# tradução mood do vídeo (detect_mood_from_text) → categoria dos JSONs de SFX
MOOD_TO_SFX_CAT = {
    "tense_dramatic": "suspense", "sad_emotional": "tristeza",
    "romantic_sexy": "romance", "funny_lighthearted": "comedia",
    "calm_chill": "ambiente", "neutral_chill": "neutro", "action": "impacto",
}


def _load_sfx_mood_bank():
    """Lê os *_categorized.json e indexa os arquivos por categoria de clima.
    Resolve o caminho real de cada som (sfx_extras/sonoros, sfx_memes). Cacheado."""
    global _SFX_MOOD_BANK
    if _SFX_MOOD_BANK is not None:
        return _SFX_MOOD_BANK
    import json as _json
    bank = {}
    sources = [
        (SFX_DIR.parent / "sfx_extras_categorized.json", SFX_EXTRAS_DIR),
        (SFX_DIR.parent / "sfx_memes_categorized.json", SFX_MEMES_DIR),
    ]
    for json_path, base_dir in sources:
        if not json_path.exists():
            continue
        try:
            data = _json.loads(json_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        for fname, cat in (data.get("files") or {}).items():
            f = base_dir / fname
            if f.exists():
                bank.setdefault(cat, []).append(f)
    _SFX_MOOD_BANK = bank
    return bank


def pick_sfx_by_mood(mood):
    """Sorteia um SFX cuja categoria combina com o mood do vídeo (via JSONs).
    Aplica anti-repetição. Retorna Path (str) ou None se não houver candidato."""
    global _last_sfx_used
    bank = _load_sfx_mood_bank()
    cat = MOOD_TO_SFX_CAT.get(mood)
    pool = bank.get(cat, []) if cat else []
    candidates = [f for f in pool if str(f) != _last_sfx_used] or pool
    if not candidates:
        return None
    chosen = random.choice(candidates)
    _last_sfx_used = str(chosen)
    return str(chosen)

# Categorias de SFX por contexto
SFX_IMPACT = [
    "impact.wav", "bass_hit.wav", "snap.wav",
    "new_impact_1.wav", "new_impact_2.wav",
    "whoosh_heavy.wav", "punch.wav", "thud.wav",
    "reverse_impact.wav", "deep_boom.wav",
]
SFX_TRANSITION = [
    "woosh.wav", "page_turn.wav", "riser.wav",
    "new_transition_1.wav", "new_transition_2.wav",
    "slide.wav", "swoosh_light.wav", "magic_sparkle.wav",
    "cinema_whoosh.wav", "paper_slide.wav", "subtle_click.wav",
    "dramatic_riser.wav", "tension_string.wav",
] + [f"whoosh_cinematic_{i:02d}.wav" for i in range(1, 26)]  # pack 25 (curadoria aprovada)
SFX_PAGE_TEAR = [
    "page_tear_1.wav", "page_tear_2.wav",
]

_last_sfx_used = None  # Anti-repetição: nunca repetir o mesmo SFX consecutivo

# TAREFA 18 (curadoria aprovada 2026-07-01): SFX disparados por CONTEXTO da narração.
# vraa = grito de transformação/virada épica; reprovação = erro/fracasso/"deu ruim".
# 7 e 5 variações → anti-repetição alterna (regra fixa #9). Ficam em SFX_DIR.
VRAA_POOL = [f"vraa_grito_{i:02d}.wav" for i in range(1, 8)]
VRAA_KEYWORDS = ["transform", "se transformou", "evoluiu", "despertou o poder",
                 "aura cresceu", "ficou mais forte", "virou outr", "subiu de nível",
                 "subiu de nivel", "level up", "vraa", "vrááá", "poder explod",
                 "liberou o poder", "modo besta", "se revelou"]
REPROV_POOL = [f"reprovacao_{i:02d}.wav" for i in range(1, 6)]
REPROV_KEYWORDS = ["deu ruim", "deu errado", "errou", "errado", "fracassou", "fracasso",
                   "reprovado", "reprovou", "não deu certo", "nao deu certo", "falhou",
                   "vacilou", "se ferrou", "deu merda", "foi mal", "que vergonha"]


def _pick_from_pool(pool_names, base_dir):
    """Escolhe um arquivo do pool (por nome), com anti-repetição consecutiva global.
    Reusa _last_sfx_used (mesma trava do pick_sfx). Retorna Path str válido ou None."""
    global _last_sfx_used
    cands = [base_dir / n for n in pool_names]
    cands = [p for p in cands if _valid_audio(p)]
    if not cands:
        return None
    filtered = [p for p in cands if str(p) != _last_sfx_used] or cands
    chosen = random.choice(filtered)
    _last_sfx_used = str(chosen)
    return str(chosen)


def pick_sfx(sfx_category=None):
    """Escolhe um SFX aleatório de uma categoria específica (IMPACT, TRANSITION, PAGE_TEAR).
    Garante que nunca repete o mesmo SFX consecutivamente."""
    global _last_sfx_used
    pool = SFX_TRANSITION # Default
    if sfx_category == "impact":
        pool = SFX_IMPACT
    elif sfx_category == "page_tear":
        pool = SFX_PAGE_TEAR

    # Tenta escolher um SFX do pool específico (diferente do último usado)
    sfx_file = None
    if pool:
        candidates = [SFX_DIR / f for f in pool if (SFX_DIR / f).exists()]
        # Filtrar o último usado pra não repetir
        if _last_sfx_used and len(candidates) > 1:
            candidates = [c for c in candidates if str(c) != _last_sfx_used] or candidates
        if candidates:
            sfx_file = random.choice(candidates)

    # Fallback: qualquer SFX disponível de TODAS as pastas.
    # SFX dentro de sfx_prioridade/ entram com PESO 3 (3× mais chance) — é o
    # controle manual do usuário: arrastar um efeito atmosférico pra essa pasta
    # faz ele tocar mais. Efeitos específicos (soco/porta) não passam por aqui.
    if not sfx_file:
        available = []
        for sfx_dir in ALL_SFX_DIRS:
            if sfx_dir.exists():
                available.extend([f for f in sfx_dir.glob("*.wav") if str(f) != _last_sfx_used])
                available.extend([f for f in sfx_dir.glob("*.mp3") if str(f) != _last_sfx_used])
        # Prioritários entram 3× (peso) se a pasta existir.
        if SFX_PRIORIDADE_DIR.exists():
            prio = [f for f in SFX_PRIORIDADE_DIR.glob("*.wav") if str(f) != _last_sfx_used]
            prio += [f for f in SFX_PRIORIDADE_DIR.glob("*.mp3") if str(f) != _last_sfx_used]
            available.extend(prio * 3)
        if not available:
            for sfx_dir in ALL_SFX_DIRS:
                if sfx_dir.exists():
                    available.extend(sfx_dir.glob("*.wav"))
                    available.extend(sfx_dir.glob("*.mp3"))
        if available:
            sfx_file = random.choice(available)

    if sfx_file:
        _last_sfx_used = str(sfx_file)

    return str(sfx_file) if sfx_file else None


# SFX contextual por keyword na narração (portado do n8n SOUND_EFFECTS_MAP)
SFX_CONTEXTUAL_MAP = {
    # AÇÃO E COMBATE
    "soco": {"category": "impact", "volume": 0.6, "keywords": ["soco", "murro", "pancada", "socou", "esmurrou"]},
    "tapa": {"category": "impact", "volume": 0.6, "keywords": ["tapa", "tapão", "esbofeteou", "estapeou"]},
    "explosão": {"category": "impact", "volume": 0.8, "keywords": ["explosão", "explodiu", "bomba", "detonou", "explode"]},
    "chute": {"category": "impact", "volume": 0.6, "keywords": ["chute", "chutou", "pontapé"]},
    "espada": {"category": "impact", "volume": 0.7, "keywords": ["espada", "lâmina", "cortou", "fatiou", "katana"]},
    # IMPACTO E QUEDAS
    "queda": {"category": "impact", "volume": 0.6, "keywords": ["caiu", "cair", "queda", "tropeçou", "desabou", "escorregou"]},
    "quebrou": {"category": "impact", "volume": 0.6, "keywords": ["quebrou", "vidro", "estilhaçou", "partiu", "rachou"]},
    "bateu": {"category": "impact", "volume": 0.6, "keywords": ["bateu", "colidiu", "impacto", "trombou"]},
    # EMOÇÕES E REAÇÕES
    "grito": {"category": "impact", "volume": 0.6, "keywords": ["grito", "gritou", "berrou", "urrou", "berro"]},
    "surpresa": {"category": "transition", "volume": 0.5, "keywords": ["surpresa", "surpreso", "chocado", "não acredito", "impossível"]},
    "risada": {"category": "transition", "volume": 0.5, "keywords": ["risada", "riso", "riu", "gargalhada", "haha"]},
    # SUSPENSE E DRAMA
    "suspense": {"category": "transition", "volume": 0.5, "keywords": ["suspense", "tensão", "perigo", "ameaça", "sombrio"]},
    "revelação": {"category": "transition", "volume": 0.6, "keywords": ["revelação", "segredo", "descobriu", "verdade", "revelou"]},
    "morte": {"category": "impact", "volume": 0.7, "keywords": ["morte", "morreu", "matar", "matou", "assassin"]},
    # MOVIMENTO
    "correr": {"category": "transition", "volume": 0.4, "keywords": ["correr", "correndo", "fugir", "escapar", "rápido", "velocidade"]},
    "pular": {"category": "transition", "volume": 0.5, "keywords": ["pular", "pulou", "salto", "saltou", "voou"]},
    # AMBIENTE
    "porta": {"category": "transition", "volume": 0.4, "keywords": ["porta", "bateu a porta", "abriu a porta", "fechou", "portão"]},
    "coração": {"category": "transition", "volume": 0.4, "keywords": ["coração", "batendo", "palpitou", "acelerou", "coração disparou"]},
    "trovão": {"category": "impact", "volume": 0.7, "keywords": ["trovão", "raio", "relâmpago", "tempestade"]},
    "água": {"category": "transition", "volume": 0.4, "keywords": ["água", "chuva", "mergulho", "afogando", "rio"]},
    "vento": {"category": "transition", "volume": 0.3, "keywords": ["vento", "ventania", "tempestade", "soprou"]},
    # === T8: GATILHOS NOVOS (categorias do n8n que faltavam → SÓ pools que temos) ===
    # MAGIA / SOBRENATURAL (→ magic_sparkle/sparkle vivem em SFX_TRANSITION)
    "magia": {"category": "transition", "volume": 0.5, "keywords": ["magia", "mágic", "feitiço", "feitic", "encanto", "conjur", "poder mágico", "sobrenatural", "místic", "mistic"]},
    "teleporte": {"category": "transition", "volume": 0.5, "keywords": ["teleport", "desapareceu", "sumiu", "surgiu do nada", "materializ", "portal abriu"]},
    "transformação": {"category": "transition", "volume": 0.6, "keywords": ["transform", "se transformou", "metamorf", "evoluiu", "virou outr"]},
    # GAME / POWER (→ impact pra força, transition pra brilho)
    "powerup": {"category": "transition", "volume": 0.6, "keywords": ["upou", "subiu de nível", "subiu de nivel", "level up", "power up", "powerup", "ficou mais forte", "despertou o poder", "aura cresceu"]},
    "derrota": {"category": "impact", "volume": 0.6, "keywords": ["foi derrotado", "perdeu a luta", "caiu derrotado", "game over", "wasted", "fim de jogo"]},
    "vitória": {"category": "transition", "volume": 0.6, "keywords": ["venceu", "vitória", "vitoria", "ganhou", "triunf", "conquistou", "campeão", "campeao"]},
    # NOTIFICAÇÃO / DISPOSITIVO (→ subtle_click/snap em transition)
    "notificação": {"category": "transition", "volume": 0.4, "keywords": ["notificação", "notificac", "mensagem chegou", "celular tocou", "alerta", "ping", "tocou o telefone"]},
}

# Mapa direto keyword → foley específico (prioridade sobre SFX genérico)
FOLEY_DIRECT_MAP = {
    "porta": "door_close.wav", "abriu a porta": "door_close.wav", "fechou a porta": "door_close.wav",
    "passos": "footsteps.wav", "andando": "footsteps.wav", "caminh": "footsteps.wav",
    "beijo": "kiss_smooch.wav", "beijou": "kiss_smooch.wav", "beijar": "kiss_smooch.wav",
    "coração": "heartbeat.wav", "batendo forte": "heartbeat.wav", "palpitou": "heartbeat.wav",
    "chuva": "rain_loop.wav", "chov": "rain_loop.wav",
    "trovão": "thunder.wav", "raio": "thunder.wav", "relâmpago": "thunder.wav",
    "vento": "wind_blow.wav", "ventania": "wind_blow.wav",
    "espada": "sword_slash.wav", "katana": "sword_slash.wav", "lâmina": "sword_hit.wav",
    "tiro": "gunshot.wav", "atirou": "gunshot.wav", "pistola": "gunshot_echo.wav",
    "vidro": "glass_break.wav", "estilhaçou": "glass_break.wav",
    "caiu": "body_fall.wav", "desabou": "body_fall.wav", "corpo caiu": "body_fall.wav",
    "explosão": "explosion_big.wav", "explodiu": "explosion_big.wav",
    "comendo": "eating_crunch.wav", "mordeu": "eating_crunch.wav", "mastig": "eating_crunch.wav",
    "bebendo": "drinking_gulp.wav", "engoliu": "drinking_gulp.wav", "gole": "drinking_gulp.wav",
    "telefone": "phone_ring.wav", "celular": "phone_ring.wav", "ligou": "phone_ring.wav",
    "corrente": "chain_rattle.wav", "pres": "chain_rattle.wav",
    "metal": "metal_clang.wav", "ferro": "metal_clang.wav",
    "mar": "ocean_waves.wav", "praia": "ocean_waves.wav", "ondas": "ocean_waves.wav",
    "pássaro": "birds_morning.wav", "manhã": "birds_morning.wav",
    "aplausos": "crowd_cheer.wav", "plateia": "crowd_cheer.wav", "torcida": "crowd_cheer.wav",
    "espanto": "crowd_gasp.wav", "todos ficaram": "crowd_gasp.wav",
    "sinistro": "creepy_ambience.wav", "arrepio": "creepy_ambience.wav",
    "escrevendo": "pen_writing.wav", "anotou": "pen_writing.wav",
    "tensão": "tension_drone.wav",
    # Foley extras
    "soco": "punch_hit.wav", "socou": "punch_hit.wav", "murro": "punch_hit.wav",
    "notificação": "notification.wav", "mensagem": "notification.wav", "alerta": "notification.wav",
    # Foley adicionais (arquivos confirmados em sfx_foley/)
    "explosão pequena": "explosion_small.wav", "estouro": "explosion_small.wav",
    "rápido": "fast_whoosh.wav", "disparou": "fast_whoosh.wav", "veloz": "fast_whoosh.wav",
    "devagar": "slow_whoosh.wav", "lentamente": "slow_whoosh.wav",
    "espada cortou": "sword_hit.wav", "golpe de espada": "sword_hit.wav",
    "comeu": "eating_crunch.wav", "mordida": "eating_crunch.wav",
}


# Efeitos da pasta sfx_memes acionados DIRETO por palavra-chave (estilo "humor
# brasileiro"). keyword (na narração) → nome EXATO do arquivo em sfx_memes/.
# Diferente do FOLEY_DIRECT_MAP (sons realistas), estes são cômicos/expressivos.
# Só mapeei os de nome claro; os 600+ restantes seguem disponíveis pelo sorteio
# por mood/categoria (pick_sfx). Adicione mais pares aqui conforme quiser.
MEME_SFX_DIRECT_MAP = {
    "chicote": "37- Chicote.mp3", "chibatada": "37- Chicote.mp3",
    "buzina": "30- Buzina.mp3", "buzinou": "30- Buzina.mp3",
    "tapa": "Som de Tapa Na Cara Audio TAPAS e Murros EFEITO SONORO (128 kbps).mp3",
    "bofetada": "Som de Tapa Na Cara Audio TAPAS e Murros EFEITO SONORO (128 kbps).mp3",
    "beijo": "Som de Beijo - Efeitos Sonoros Nerzinho.mp3",
    "moeda": "Efeitos Sonoros - Moeda caindo.mp3", "moedas": "Efeitos Sonoros - Moeda caindo.mp3",
    "dinheiro": "26- Dinheiro 2.mp3", "grana": "26- Dinheiro 2.mp3",
    "freio": "SE EU LARGAR O FREIO.mp3", "freada": "SE EU LARGAR O FREIO.mp3",
    "errou": "25- Errou.mp3", "errado": "25- Errou.mp3",
    "suspense": "9- Suspense 2.mp3",
    "risada": "Bixo Piruleta Risada - Efeitos sonoros Nerzinho.mp3", "gargalhada": "Bixo Piruleta Risada - Efeitos sonoros Nerzinho.mp3",
    "grito": "Grito - Efeitos sonoros Nerzinho.mp3", "gritou": "Grito - Efeitos sonoros Nerzinho.mp3",
    "campainha": "Campainha Ding Dong - Efeitos sonoros Nerzinho.mp3", "ding dong": "Campainha Ding Dong - Efeitos sonoros Nerzinho.mp3",
    "ding-dong": "Campainha Ding Dong - Efeitos sonoros Nerzinho.mp3", "interfone": "Campainha Ding Dong - Efeitos sonoros Nerzinho.mp3",
    "campainha toca": "Campainha Ding Dong - Efeitos sonoros Nerzinho.mp3",
    # Fallbacks pra foleys QUEBRADOS (door_open/footsteps/punch_hit = XML 111B):
    "passos": "Minecraft som de passos - Efeitos sonoros Nerzinho.mp3",
    "step step": "Minecraft som de passos - Efeitos sonoros Nerzinho.mp3",
    "passo a passo": "Minecraft som de passos - Efeitos sonoros Nerzinho.mp3",
    "abriu a porta": "Minecraft Porta abrindo - Efeitos sonoros Nerzinho.mp3",
    "porta se abre": "Minecraft Porta abrindo - Efeitos sonoros Nerzinho.mp3",
    "porta abrindo": "Minecraft Porta abrindo - Efeitos sonoros Nerzinho.mp3",
    "bate na porta": "Batendo na Porta - Efeitos sonoros Nerzinho.mp3",
    "batida na porta": "Batendo na Porta - Efeitos sonoros Nerzinho.mp3",
    "batem na porta": "Batendo na Porta - Efeitos sonoros Nerzinho.mp3",
    "soco": "Som de Tapa Na Cara Audio TAPAS e Murros EFEITO SONORO (128 kbps).mp3",
    "murro": "Som de Tapa Na Cara Audio TAPAS e Murros EFEITO SONORO (128 kbps).mp3",
    "socou": "Som de Tapa Na Cara Audio TAPAS e Murros EFEITO SONORO (128 kbps).mp3",
    "carro": "Carro Buzinando - Efeitos sonoros Nerzinho.mp3",
    "teclado": "Digitando teclado - Efeitos sonoros Nerzinho.mp3", "digitando": "Digitando teclado - Efeitos sonoros Nerzinho.mp3", "digitou": "Digitando teclado - Efeitos sonoros Nerzinho.mp3",
    "trovão": "Trovão - Efeitos Sonoros Nerzinho.mp3", "trovao": "Trovão - Efeitos Sonoros Nerzinho.mp3",
    "vidro": "Vidro Quebrando -  Efeito Sonoro.mp3", "vidro quebrou": "Vidro Quebrando -  Efeito Sonoro.mp3", "quebrou o vidro": "Vidro Quebrando -  Efeito Sonoro.mp3",
    "tiro": "Tiro - Efeitos Sonoros Nerzinho.mp3", "atirou": "Tiro - Efeitos Sonoros Nerzinho.mp3", "disparo": "Tiro - Efeitos Sonoros Nerzinho.mp3",
    "máquina de escrever": "Maquina de Escrever - Efeitos sonoros Nerzinho.mp3", "datilograf": "Maquina de Escrever - Efeitos sonoros Nerzinho.mp3",
    "whatsapp": "Assobio do whatsapp _ zap zap_ toque whatsapp_ whistle (donwload) ----(MP3_320K).mp3", "zap": "Assobio do whatsapp _ zap zap_ toque whatsapp_ whistle (donwload) ----(MP3_320K).mp3",
}


def _valid_audio(path):
    """True se o arquivo de áudio é válido (não um XML de erro de ~111B).
    Vários foleys baixados falharam e ficaram como '<?xml...' disfarçado de wav."""
    try:
        p = Path(path)
        if not p.exists() or p.stat().st_size < 1000:
            return False
        with open(p, "rb") as fh:
            head = fh.read(4)
        # wav=RIFF, mp3=ID3 ou 0xFFFx, ogg=OggS. XML de erro começa com '<'
        return head[:1] != b"<"
    except Exception:
        return False


# ── Toggle GAP do foley (env HIPER_FOLEY_GAP) ────────────────────────────────
# LIGADO (1): o foley contextual (campainha/porta/passos...) PAUSA a voz —
#   atrasa a fala, o som toca limpo nesse início, depois a voz continua. Igual
#   à "pausa" das transições, não atropela a fala.
# DESLIGADO (0): o foley toca JUNTO com a voz desde t=0 (de fundo).
FOLEY_GAP_MODE = os.environ.get("HIPER_FOLEY_GAP", "0").strip().lower() in ("1", "true", "yes", "on")
FOLEY_GAP_S = 0.7  # atraso aplicado à voz no modo gap


def prepare_foley_gap_audio(voice_audio, foley_file, out_audio, vol=0.9):
    """Modo GAP: gera um novo wav onde a VOZ é atrasada FOLEY_GAP_S e o foley
    toca limpo nesse início (volume cheio), depois entra a fala. O clip fica
    ~FOLEY_GAP_S mais longo (build_clip deriva a duração do áudio). Retorna o
    caminho do áudio gerado, ou o áudio original se falhar."""
    if not _valid_audio(foley_file) or not Path(voice_audio).exists():
        return str(voice_audio)
    delay_ms = int(FOLEY_GAP_S * 1000)
    norm = "loudnorm=I=-16:TP=-1.5," if os.environ.get("SFX_LOUDNORM", "1") != "0" else ""
    fc = (
        f"[0:a]adelay={delay_ms}|{delay_ms},apad=pad_dur=0.1[v];"
        f"[1:a]{norm}volume={vol}[f];"
        f"[f][v]amix=inputs=2:duration=longest:dropout_transition=0:normalize=0[a]"
    )
    cmd = [
        "ffmpeg", "-y", "-i", str(voice_audio), "-i", str(foley_file),
        "-filter_complex", fc, "-map", "[a]",
        "-c:a", "pcm_s16le", "-ar", "44100", "-ac", "2", str(out_audio),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=60)
        return str(out_audio) if Path(out_audio).exists() else str(voice_audio)
    except Exception:
        return str(voice_audio)



def _kw_match(blob, kw):
    """Casa keyword com limite de palavra (evita 'mar' casar 'marcam',
    'rápido' casar dentro de outra). Keywords multi-palavra ou com pontuação
    usam substring; tokens simples usam fronteira de palavra."""
    if " " in kw or "-" in kw:
        return kw in blob
    return re.search(r'(?<![0-9a-zà-ú])' + re.escape(kw) + r'(?![0-9a-zà-ú])', blob) is not None


# Onomatopeias das DESCRIÇÕES → SFX (prioridade MÁXIMA: é o som literal do que
# acontece na cena). Ex.: "DING DONG" sempre vence "rápido"/"acaba" genéricos.
ONOMATOPEIA_SFX = [
    (["ding dong", "ding-dong"], ("memes", "Campainha Ding Dong - Efeitos sonoros Nerzinho.mp3", 0.55)),
    (["step step", "step"], ("memes", "Minecraft som de passos - Efeitos sonoros Nerzinho.mp3", 0.45)),
    (["clack", "clack clack"], ("foley", "door_close.wav", 0.5)),
    (["smooch", "chu~", "chu "], ("foley", "kiss_smooch.wav", 0.5)),
    (["knock", "toc toc", "tum tum"], ("memes", "Batendo na Porta - Efeitos sonoros Nerzinho.mp3", 0.5)),
    (["crash", "smash", "estilha"], ("memes", "Vidro Quebrando -  Efeito Sonoro.mp3", 0.55)),
    (["bang", "pow"], ("memes", "Tiro - Efeitos Sonoros Nerzinho.mp3", 0.5)),
]


def pick_sfx_for_text(text):
    """Escolhe SFX baseado no conteúdo do texto da narração + descrição.
    Prioridade: onomatopeia > foley direto > MEME direto > keyword contextual.
    Retorna (sfx_path, volume) ou (None, None) se não encontrar match."""
    if not text:
        return None, None
    text_lower = text.lower()

    # 0. Onomatopeia literal da descrição (prioridade máxima)
    for kws, (kind, fname, vol) in ONOMATOPEIA_SFX:
        if any(_kw_match(text_lower, k) for k in kws):
            base = SFX_MEMES_DIR if kind == "memes" else SFX_FOLEY_DIR
            p = base / fname
            if _valid_audio(p):
                return str(p), vol
            break

    # 1. Foley direto (alta prioridade — sons específicos e realistas)
    for keyword, foley_file in FOLEY_DIRECT_MAP.items():
        if _kw_match(text_lower, keyword):
            foley_path = SFX_FOLEY_DIR / foley_file
            if _valid_audio(foley_path):
                return str(foley_path), 0.6
            # arquivo quebrado/ausente → não dá break, tenta próximas camadas
            break

    # 1b. MEME direto (efeitos da pasta sfx_memes acionados por palavra-chave).
    #     São os 600+ efeitos "engraçados/brasileiros" (chicote, buzina, tapa,
    #     risada...). Volume um pouco mais baixo (0.5) por serem mais chamativos.
    for keyword, meme_file in MEME_SFX_DIRECT_MAP.items():
        if _kw_match(text_lower, keyword):
            meme_path = SFX_MEMES_DIR / meme_file
            if _valid_audio(meme_path):
                return str(meme_path), 0.5
            break

    # 1c. TAREFA 18: vraa (transformação/virada) e reprovação (erro/fracasso) por CONTEXTO.
    #     Disparo por keyword (não sorteio genérico). Depois do foley/meme direto, antes do
    #     contextual — são sons de DESTAQUE, ganham do genérico quando o contexto casa.
    for kw in VRAA_KEYWORDS:
        if _kw_match(text_lower, kw):
            p = _pick_from_pool(VRAA_POOL, SFX_DIR)
            if p:
                return p, 0.7
            break
    for kw in REPROV_KEYWORDS:
        if _kw_match(text_lower, kw):
            p = _pick_from_pool(REPROV_POOL, SFX_DIR)
            if p:
                return p, 0.6
            break

    # 2. Keyword contextual (SFX genérico por categoria)
    for key, config in SFX_CONTEXTUAL_MAP.items():
        for keyword in config["keywords"]:
            if _kw_match(text_lower, keyword):
                sfx = pick_sfx(config["category"])
                return sfx, config["volume"]

    # 3. SEM fallback por mood. Decisão do usuário (28/jun): efeito sonoro só
    #    entra quando a narração tem CONTEXTO pra ele (keyword) — tiro só quando
    #    "atirou", tapa só quando "tapa", etc. Sem keyword, NÃO sobrepõe efeito:
    #    o clip mantém o som de transição LIMPO (whoosh/riser) do
    #    get_transition_and_sfx. Isso evita a "salada" de memes-fala e SFX
    #    especiais (Wilhelm Scream, "11 - Arma 2", falas) tocando aleatoriamente
    #    como fundo. (Antes: pick_sfx_by_mood sorteava da categoria 'neutro' que
    #    é 336 memes-fala não-curados → atropelava as vozes.)
    return None, None


def enhance_narration_audio(wav_in, wav_out=None):
    """Pós-processamento de áudio profissional na narração TTS.

    Aplica (portado do n8n V5.1 GLOBAL_CONFIG.audio):
    - Loudness normalization (LUFS -16, true peak -1.5)
    - Compression leve (threshold -18dB, ratio 3:1)
    - Noise reduction sutil (afftdn)
    - De-esser (highshelf eq sutil)

    Se wav_out não fornecido, sobrescreve o arquivo original.
    """
    if wav_out is None:
        wav_out = wav_in
    tmp_out = Path(str(wav_in) + "_enhanced.wav")

    af_chain = ",".join([
        "afftdn=nf=-20",
        "acompressor=threshold=-18dB:ratio=3:attack=5:release=50",
        "equalizer=f=7000:t=h:w=2000:g=-2",
        "loudnorm=I=-16:TP=-1.5:LRA=11"
    ])

    cmd = [
        "ffmpeg", "-y", "-i", str(wav_in),
        "-af", af_chain,
        "-ar", "44100", "-ac", "1",
        str(tmp_out),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=15)
        if tmp_out.exists() and tmp_out.stat().st_size > 100:
            tmp_out.replace(wav_out)
            return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        if tmp_out.exists():
            tmp_out.unlink(missing_ok=True)
    return False

# Tensão keywords (shake + glitch em momentos tensos, não só impacto)
TENSION_KEYWORDS = [
    "tensão", "tenso", "nervos", "medo", "assust", "choque", "revela",
    "segredo", "surpres", "descobre", "traição", "mentir", "ameaça",
    "confronto", "encurralad", "perigo", "desespero", "pânico", "furioso",
    "raiva", "ciúme", "obsess", "stalker", "persegu", "escuro", "sombr",
    "suspeito", "olhar frio", "silêncio pesado", "calafrio", "arrepio",
    "tremendo", "lágrima", "choqu", "apavorad", "terror", "sinistro",
    "ameaçador", "intimidar", "pressionad", "acuad", "encosta na parede",
]


def is_tension_panel(description: str) -> bool:
    """Detecta se o painel tem tensão dramática. Haiku primeiro, keyword fallback."""
    if not description:
        return False
    try:
        import haiku_helpers
        c = haiku_helpers.classify_action(description)
        if c is not None:
            return c == "tension"
    except Exception:
        pass
    desc_lower = description.lower()
    return any(kw in desc_lower for kw in TENSION_KEYWORDS)


# Sensual/+18 keywords. "cena intensa"/"intensa" é o marcador deixado pela
# sanitização da visão quando o painel tinha conteúdo adulto explícito.
SENSUAL_KEYWORDS = [
    "cena intensa", "intensa", "beijo", "beij", "abraç", "carícia", "caric",
    "toque", "toca", "sedut", "seduz", "sensual", "provocan", "provoca",
    "desejo", "tesão", "paixão", "íntim", "intim", "corpo", "pele",
    "quente", "ofegant", "suspiro", "gemid", "cama", "lençol", "nu ",
    "deitad", "abraçad", "colo", "peito", "coxa", "cintura", "vermelh",
    "nervos", "tímid", "noona", "amante", "romance", "romântic",
]


def is_sensual_panel(description: str = "", text: str = "") -> bool:
    """Detecta momentos sensuais/+18 (pra aplicar voz sensual no TTS).

    Olha tanto a descrição visual (sanitizada → 'cena intensa') quanto o texto
    da narração, que costuma ter as pistas românticas/provocantes.
    """
    blob = f"{description} {text}".lower()
    if not blob.strip():
        return False
    return any(kw in blob for kw in SENSUAL_KEYWORDS)


def build_glitch_filter(duration=0.08):
    """Gera filtro de glitch RGB split (deslocamento de canais R/G/B).

    Efeito moderno usado em transições de tensão/revelação.
    Duração curtíssima (0.08s = 2-3 frames) pra não enjoar.
    """
    # RGB split: desloca o canal R pra direita e B pra esquerda
    return (
        f"rgbashift=rh=-4:bh=4:rv=2:bv=-2,"
        f"noise=alls=30:allf=t+u,"
        f"eq=contrast=1.3:brightness=-0.05"
    )


def build_letterbox_filter():
    """Adiciona barras cinematográficas (letterbox 2.39:1 dentro de 9:16).

    Usado em momentos dramáticos pra dar clima de cinema.
    """
    # Barras pretas top/bottom (120px cada = ~12.5% do frame)
    bar_h = 120
    return f"drawbox=x=0:y=0:w={W}:h={bar_h}:color=black:t=fill,drawbox=x=0:y={H-bar_h}:w={W}:h={bar_h}:color=black:t=fill"


def build_rewind_filter():
    """Gera um efeito de rebobinar retrô com scanlines, chromatic aberration e ruído."""
    return (
        "rgbashift=rh=-8:bh=8:rv=4:bv=-4,"
        "noise=alls=40:allf=t+u,"
        "eq=contrast=1.35:brightness=-0.08"
    )


def _build_pagetear_filter():
    """Simula o efeito de rasgar página: wipe diagonal rápido com distorção.

    Combina um scale acelerado + deslocamento horizontal que simula
    a página sendo arrancada para o lado com um leve twist.
    """
    # Wipe lateral acelerado com distorção horizontal (simula rasgar)
    return (
        f"scale={W}:{H}:force_original_aspect_ratio=decrease,"
        f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,"
        f"avgblur=sizeX=30:sizeY=1"
    )


def get_transition_and_sfx(panel_idx, descriptions):
    """Determina o tipo de transição e o SFX para um painel específico.

    Transições FREQUENTES e VARIADAS (estilo Shorts) — quase todo corte tem efeito:
    - impacto → flash vermelho / branco / zoom punch / whip + SFX de impacto
    - tensão  → glitch / blur-in / fade preto / rasgar página / rebobinar + SFX de transição
    - normal  → variedade (fade/blur/pixel/whip/flash) + uns cortes secos + SFX de transição
    """
    if panel_idx == 0:
        return None, None

    desc = descriptions[panel_idx] if panel_idx < len(descriptions) else ""
    impact = is_impact_panel(desc)
    tension = is_tension_panel(desc)

    transition_type = None
    sfx_category = "transition" # default
    sfx_file = None

    if impact:
        transition_type = random.choice(["flashred", "flash", "flashgold", "zoomin", "whip", "glitch", "punch", "snap", "speedblur", "zoomout"])
        sfx_category = "impact"
    elif tension:
        r_val = random.random()
        if r_val < 0.20:
            transition_type = "pagetear"
            sfx_category = "page_tear"
        elif r_val < 0.40:
            transition_type = "rewind"
            _rz = "rezero_respawn.wav" if (SFX_DIR / "rezero_respawn.wav").exists() and random.random() < 0.5 else "rezero_rewind.wav"
            sfx_file = str(SFX_DIR / _rz)
        elif r_val < 0.55:
            transition_type = "speedblur"
            sfx_category = "impact"
        else:
            transition_type = random.choice(["glitch", "blurin", "fade", "flashblue", "zoomin", "snap"])
            sfx_category = "transition"
    else:
        # variedade pros cortes normais; ~1/10 ficam corte seco pra dar respiro
        if random.random() < 0.10: # 10% de chance de corte seco
            transition_type = None # Corte seco
            sfx_category = None # Sem SFX para corte seco
        else:
            transition_type = random.choice([
                "fade", "dissolve", "wipeleft", "wiperight", "wipeup", "wipedown",
                "slideleft", "slideright", "slideup", "slidedown",
                "smoothleft", "smoothright", "smoothup", "smoothdown",
                "pixelize", "zoomin", "squeezeh", "squeezev",
                "circleopen", "circleclose", "circlecrop",
                "diagtl", "diagtr", "diagbl", "diagbr",
                "fadefast", "fadeslow", "snap", "distance",
                "horzopen", "horzclose", "vertopen", "vertclose",
                "radial",
            ])
            sfx_category = "transition"

    if sfx_file is None:
        sfx_file = pick_sfx(sfx_category)

    return transition_type, sfx_file


def apply_effects_to_cmd(cmd, transition_type, sfx_file, duration):
    """
    Modifica em tempo de execução a lista de argumentos 'cmd' do FFmpeg
    para aplicar a transição (fade/flash/glitch) e mixagem de SFX em uma única passada.
    """
    if not transition_type and not sfx_file:
        return cmd

    # 1. Encontrar os índices importantes no cmd original
    try:
        fc_idx = cmd.index("-filter_complex")
        filter_complex = cmd[fc_idx + 1]
    except ValueError:
        return cmd

    # 2. Contar inputs existentes e localizar o input de áudio principal
    input_indices = [i for i, x in enumerate(cmd) if x == "-i"]
    num_inputs = len(input_indices)

    orig_audio_map = None
    try:
        map_indices = [i for i, x in enumerate(cmd) if x == "-map"]
        for idx in map_indices:
            val = cmd[idx + 1]
            if val.endswith(":a"):
                orig_audio_map = val
                break
    except Exception:
        pass

    if not orig_audio_map:
        orig_audio_map = f"{num_inputs - 1}:a"

    orig_video_map = None
    try:
        map_indices = [i for i, x in enumerate(cmd) if x == "-map"]
        for idx in map_indices:
            val = cmd[idx + 1]
            if val.startswith("[") and val.endswith("]"):
                orig_video_map = val
                break
    except Exception:
        pass

    if not orig_video_map:
        orig_video_map = "[v]"

    # 3. Se houver SFX, adicionar o novo input
    if sfx_file:
        sfx_idx = num_inputs
        cmd.insert(fc_idx, "-i")
        cmd.insert(fc_idx + 1, str(sfx_file))
        fc_idx += 2

        sfx_vol = "1.2" if transition_type == "flash" or "impact" in str(sfx_file) else "0.8"
        # Duração de reprodução do SFX no mix:
        #  - teto pela duração do clip (amix usa duration=first → nunca estende vídeo)
        #  - teto absoluto SFX_PLAY_MAX (default 1.5s) pra um SFX longo (ex:
        #    fast_whoosh 9s) não arrastar por cima da fala. A abertura re:zero é
        #    tratada à parte em build_intro_clip e NÃO passa por aqui.
        try:
            play_max = max(0.3, float(os.environ.get("SFX_PLAY_MAX", "1.5")))
        except ValueError:
            play_max = 1.5
        sfx_dur = sfx_duration(sfx_file)
        play = min(sfx_dur, duration, play_max) if sfx_dur > 0 else 1.0
        play = max(0.20, play)
        # loudnorm nivela cada SFX a um volume parelho e audível — resolve os
        # arquivos quase mudos (new_transition_1 -77dB, swoosh_light -68dB) que
        # sumiam no mix. Aplicado ANTES do volume/trim. SFX_LOUDNORM=0 desliga.
        norm = ("loudnorm=I=-16:TP=-1.5,"
                if os.environ.get("SFX_LOUDNORM", "1") != "0" else "")
        audio_mix_filter = (
            f";[{sfx_idx}:a]{norm}volume={sfx_vol},atrim=0:{play:.2f},apad=whole_dur={play:.2f}[sfx_temp];"
            f"[{orig_audio_map}][sfx_temp]amix=inputs=2:duration=first:dropout_transition=0.3[aout]"
        )
        filter_complex += audio_mix_filter
        new_audio_map = "[aout]"
    else:
        new_audio_map = orig_audio_map

    # 4. Adicionar a transição de vídeo
    v_in = orig_video_map
    v_out = orig_video_map
    video_filters = []

    # Transições simples (fade auto-janelado — só afeta os primeiros frames)
    SIMPLE_TRANS = {
        "flash":     "fade=t=in:st=0:d=0.25:color=white",
        "flashred":  "fade=t=in:st=0:d=0.28:color=0xCC1111",
        "flashgold": "fade=t=in:st=0:d=0.30:color=0xE8B500",
        "flashblue": "fade=t=in:st=0:d=0.30:color=0x2244CC",
        "fade":      "fade=t=in:st=0:d=0.40:color=black",
    }
    # Transições "split": efeito só nos primeiros segundos, depois corte limpo.
    # (duração, filtro aplicado no trecho inicial). Dimensões PARES p/ libx264.
    _zw = (int(W * 1.25) // 2) * 2
    _zh = (int(H * 1.25) // 2) * 2
    _zw2 = (int(W * 1.45) // 2) * 2
    _zh2 = (int(H * 1.45) // 2) * 2
    SPLIT_TRANS = {
        "glitch":  ("0.10", build_glitch_filter()),
        "blurin":  ("0.18", "gblur=sigma=26"),
        "pixelin": ("0.16", f"scale={W//12}:{H//12}:flags=neighbor,scale={W}:{H}:flags=neighbor"),
        "zoomin":  ("0.18", f"scale={_zw}:{_zh},crop={W}:{H}:({_zw}-{W})/2:({_zh}-{H})/2"),
        "whip":    ("0.12", "avgblur=sizeX=60:sizeY=1"),
        "pagetear": ("0.15", _build_pagetear_filter()),
        "rewind":   ("0.25", build_rewind_filter()),
        "punch":    ("0.14", f"scale={_zw2}:{_zh2},crop={W}:{H}:({_zw2}-{W})/2:({_zh2}-{H})/2"),
        "snap":     ("0.16", f"scale={_zw2}:{_zh2},crop={W}:{H}:({_zw2}-{W})/2:({_zh2}-{H})/2,eq=contrast=1.15:brightness=0.04"),
        "speedblur": ("0.14", "avgblur=sizeX=1:sizeY=40"),
        "zoomout":   ("0.20", f"scale={_zw2}:{_zh2},crop={W}:{H}:({_zw2}-{W})/2:({_zh2}-{H})/2,gblur=sigma=8"),
        "flashpink": ("0.16", "fade=t=in:st=0:d=0.16:color=0xFF66AA"),
    }

    if transition_type in SIMPLE_TRANS:
        v_out = "[vfinal_trans]"
        video_filters.append(SIMPLE_TRANS[transition_type])
    elif transition_type in SPLIT_TRANS:
        v_out = "[vfinal_trans]"
        d, eff = SPLIT_TRANS[transition_type]
        filter_complex += (
            f";{v_in}split[tA][tB];"
            f"[tA]trim=0:{d},setpts=PTS-STARTPTS,{eff}[tAo];"
            f"[tB]trim={d},setpts=PTS-STARTPTS[tBo];"
            f"[tAo][tBo]concat=n=2:v=1:a=0{v_out}"
        )
        v_in = ""

    if video_filters and v_in:
        filter_complex += f";{v_in}{','.join(video_filters)}{v_out}"

    # Atualizar o filter_complex no cmd
    cmd[fc_idx + 1] = filter_complex

    # 5. Atualizar os mapeamentos de áudio/vídeo no cmd
    map_indices = [i for i, x in enumerate(cmd) if x == "-map"]
    for idx in map_indices:
        val = cmd[idx + 1]
        if val == orig_video_map:
            cmd[idx + 1] = v_out
        elif val == orig_audio_map:
            cmd[idx + 1] = new_audio_map

    return cmd


# ══════════════════════════════════════════════════════════════════════════
# SEÇÃO 4E: INTRO HOOK + OUTRO CTA (branding)
# ══════════════════════════════════════════════════════════════════════════

def _text_block_png(out_png, lines_styles, y_center_frac=0.5):
    """Renderiza um bloco de linhas (cada uma com (texto, fontsize, cor)) centralizado.

    lines_styles: lista de (texto, fontsize, (r,g,b)). Retorna o PNG 1080x1920.
    """
    from PIL import Image, ImageDraw
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    rendered = []
    total_h = 0
    for text, fs, color in lines_styles:
        font = _load_font(fs)
        lines = _wrap_lines(text, font, draw, max_w=int(W * 0.88))
        lh = int(fs * 1.2)
        for ln in lines:
            rendered.append((ln, font, color, lh))
            total_h += lh
    y = int(H * y_center_frac) - total_h // 2
    for ln, font, color, lh in rendered:
        bbox = draw.textbbox((0, 0), ln, font=font, stroke_width=8)
        x = (W - (bbox[2] - bbox[0])) // 2 - bbox[0]
        draw.text((x, y), ln, font=font, fill=(*color, 255),
                  stroke_width=8, stroke_fill=(0, 0, 0, 235))
        y += lh
    img.save(out_png)
    return out_png


def build_intro_clip(titulo, first_panel, out_path, duration=1.8, sfx_file=None):
    """Gera um clip de abertura: 1º painel borrado/escuro + título + zoom lento.
    Se o SFX de abertura for mais longo que `duration` (ex: re:zero 2.72s), a
    intro ESTICA pra caber o SFX inteiro — ele é a assinatura sonora e deve
    tocar completo antes da narração começar."""
    from PIL import Image, ImageFilter, ImageEnhance
    sfx_dur = sfx_duration(sfx_file) if sfx_file else 0.0
    if sfx_dur > duration:
        duration = sfx_dur + 0.3  # respiro curto após o SFX terminar
    tmp = Path(str(out_path) + "_introbg.jpg")
    try:
        img = Image.open(first_panel).convert("RGB")
        sw, sh = W / img.width, H / img.height
        sc = max(sw, sh)
        img = img.resize((int(img.width * sc), int(img.height * sc)), Image.LANCZOS)
        left = (img.width - W) // 2; top = (img.height - H) // 2
        img = img.crop((left, top, left + W, top + H))
        img = img.filter(ImageFilter.GaussianBlur(22))
        img = ImageEnhance.Brightness(img).enhance(0.4)
        img.save(tmp, quality=85)
    except Exception:
        Image.new("RGB", (W, H), (10, 12, 24)).save(tmp)
    txt_png = Path(str(out_path) + "_introtxt.png")
    _text_block_png(txt_png, [(titulo, 96, (255, 255, 255))], y_center_frac=0.46)

    frames = int(duration * FPS)
    zoom = f"zoompan=z='min(zoom+0.0015,1.12)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps={FPS}"
    audio_in = ["-i", str(sfx_file)] if sfx_file and Path(sfx_file).exists() else \
               ["-f", "lavfi", "-t", f"{duration:.2f}", "-i", "anullsrc=r=44100:cl=mono"]
    # Abertura estilo "Return by Death" (re:zero): a tela fica PRETA no primeiro
    # instante — só o som tocando no escuro (mistério) — e a imagem só REVELA
    # depois. black_hold = tempo preto antes do fade; reveal = duração do fade-in.
    # Ajustável por env INTRO_BLACK_HOLD / INTRO_REVEAL.
    try:
        black_hold = max(0.0, float(os.environ.get("INTRO_BLACK_HOLD", "0.8")))
    except ValueError:
        black_hold = 0.8
    try:
        reveal = max(0.2, float(os.environ.get("INTRO_REVEAL", "1.0")))
    except ValueError:
        reveal = 1.0
    # nunca passar da metade do clip (precisa sobrar imagem visível antes do fim)
    black_hold = min(black_hold, duration * 0.45)
    # o título também só aparece junto da imagem (não some o suspense)
    fc = (f"[0:v]{zoom},format=yuv420p[bg];"
          f"[bg][1:v]overlay=0:0:format=auto,"
          f"fade=t=in:st={black_hold:.2f}:d={reveal:.2f}:color=black,"
          f"fade=t=out:st={duration-0.2:.2f}:d=0.2[v];"
          f"[2:a]apad=whole_dur={duration:.2f},atrim=0:{duration:.2f}[a]")
    cmd = ["ffmpeg", "-y",
           "-loop", "1", "-t", f"{duration:.2f}", "-i", str(tmp),
           "-i", str(txt_png), *audio_in,
           "-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-t", f"{duration:.2f}",
           "-c:v", "libx264", "-preset", QP["preset"], "-crf", str(QP["crf"]), "-g", "30",
           "-c:a", "aac", "-b:a", QP["audio_bitrate"], "-ar", "44100", "-ac", "2", "-pix_fmt", "yuv420p", str(out_path)]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=90)
        ok = True
    except Exception:
        ok = False
    for f in (tmp, txt_png):
        try: f.unlink()
        except Exception: pass
    return ok


def build_outro_clip(out_path, duration=2.4, sfx_file=None,
                     linha1="INSCREVA-SE", linha2="e ative o sino",
                     linha3="PRÓXIMO CAPÍTULO EM BREVE"):
    """Gera um clip de fechamento: fundo escuro + CTA inscreva-se."""
    txt_png = Path(str(out_path) + "_outrotxt.png")
    _text_block_png(txt_png, [
        (linha1, 110, (255, 70, 70)),
        (linha3, 64, (255, 255, 255)),
    ], y_center_frac=0.5)
    frames = int(duration * FPS)
    pulse = f"zoompan=z='1+0.03*sin(on/{frames}*3.14159*4)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps={FPS}"
    audio_in = ["-i", str(sfx_file)] if sfx_file and Path(sfx_file).exists() else \
               ["-f", "lavfi", "-t", f"{duration:.2f}", "-i", "anullsrc=r=44100:cl=mono"]
    fc = (f"color=c=0x0a0e1a:s={W}x{H}:d={duration:.2f}:r={FPS}[bg0];"
          f"[bg0]{pulse}[bg];"
          f"[bg][0:v]overlay=0:0,fade=t=in:st=0:d=0.2:color=black[v];"
          f"[1:a]apad=whole_dur={duration:.2f},atrim=0:{duration:.2f}[a]")
    cmd = ["ffmpeg", "-y", "-loop", "1", "-t", f"{duration:.2f}", "-i", str(txt_png),
           *audio_in,
           "-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-t", f"{duration:.2f}",
           "-c:v", "libx264", "-preset", QP["preset"], "-crf", str(QP["crf"]), "-g", "30",
           "-c:a", "aac", "-b:a", QP["audio_bitrate"], "-ar", "44100", "-ac", "2", "-pix_fmt", "yuv420p", str(out_path)]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=90)
        ok = True
    except Exception:
        ok = False
    try: txt_png.unlink()
    except Exception: pass
    return ok


# ══════════════════════════════════════════════════════════════════════════
# SEÇÃO 4F: OVERLAYS ATMOSFÉRICOS (chuva/neve/faíscas/pétalas) por mood
# ══════════════════════════════════════════════════════════════════════════

OVERLAYS_DIR = Path(__file__).parent.parent / "workspace" / "assets" / "overlays"

# mood → overlay (partícula atmosférica que combina com o clima da cena).
# Igual à trilha, o overlay é escolhido pelo MOOD detectado — não há "prioridade"
# entre eles, mas cada clima tem a partícula que faz sentido:
#   rain (chuva)      → tristeza / drama melancólico
#   petals (pétalas)  → romance / fofura
#   sparks (faíscas)  → tensão / suspense
#   snow (neve)       → calmo / contemplativo
#   speedlines        → AÇÃO / IMPACTO (linhas de velocidade estilo mangá)
# Vários moods podem apontar pro mesmo arquivo (ex.: ação e impacto → speedlines).
MOOD_OVERLAY = {
    "sad_emotional": "rain",
    "romantic_sexy": "petals",
    "tense_dramatic": "sparks",
    "calm_chill": "snow",
    "neutral_chill": "snow",
    # ação / impacto → linhas de velocidade
    "action": "speedlines",
    "impact": "speedlines",
    "funny_lighthearted": "petals",
}


def overlay_for_mood(mood, chance=0.3):
    """Escolhe um overlay atmosférico pelo mood (com `chance` de NÃO aplicar nenhum).

    - Retorna o caminho do .mp4 do overlay que combina com o clima, ou None.
    - `chance` = probabilidade de aplicar (0.3 = 30% dos clips ganham overlay).
      Mantido baixo de propósito: overlay em todo clip cansa a vista.
    - Se o mood não tiver overlay mapeado (ou o arquivo não existir), retorna None.
    """
    if mood not in MOOD_OVERLAY:
        return None
    if random.random() > chance:
        return None
    overlay_name = MOOD_OVERLAY[mood]
    overlay_file = OVERLAYS_DIR / f"{overlay_name}.mp4"
    return str(overlay_file) if overlay_file.exists() else None


def _append_overlay(filter_complex, overlay_video, input_idx=2, opacity=0.3):
    """Anexa overlay atmosférico ao filter_complex usando overlay com opacidade.
    Usa colorkey pra remover fundo preto do overlay (mais seguro que blend=screen).
    """
    if not overlay_video or not Path(overlay_video).exists():
        return filter_complex, []
    if not filter_complex.endswith("[v]"):
        return filter_complex, []
    base = filter_complex[:-3] + "[vbase]"
    base += (
        f";[{input_idx}:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
        f"crop={W}:{H},setsar=1,colorkey=black:0.3:0.2,"
        f"format=yuva420p,colorchannelmixer=aa={opacity}[ovl];"
        f"[vbase][ovl]overlay=0:0:format=auto,format=yuv420p[v]"
    )
    return base, ["-stream_loop", "-1", "-i", str(overlay_video)]


# ══════════════════════════════════════════════════════════════════════════
# SEÇÃO 5: FUNÇÕES DE MONTAGEM (ffmpeg commands)
# ══════════════════════════════════════════════════════════════════════════

def build_clip(img_path, audio_path, out_path, panel_idx, effects_mgr, duration=None,
               transition_type=None, sfx_file=None, overlay_video=None, mood=None,
               narr_text=None):
    """Cria clip de um painel com efeitos visuais completos.

    Aplica: background blur + movimento (pan/zoom) + filtro de cor + vinheta.
    O background blur usa uma versão borrada e escurecida da própria imagem
    como fundo, em vez de bordas pretas — muito mais profissional.
    """
    from PIL import Image
    img = Image.open(img_path)
    pw, ph = img.size

    if duration is None:
        # Obter duração do áudio
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                 "-of", "csv=p=0", str(audio_path)],
                capture_output=True, text=True, timeout=10,
            )
            duration = float(result.stdout.strip())
        except Exception:
            duration = 4.0
    duration = max(duration, 1.5)
    frames = int(duration * FPS)

    # Escolher movimento baseado nas dimensões
    # T7: se CONTEXT_MOTION=1 e há texto, o ritmo é guiado pela emoção da narração.
    _prefer_speed = None
    if narr_text and os.environ.get("CONTEXT_MOTION", "0") == "1":
        try:
            import contextual_motion as _cmot
            _pref = _cmot.motion_pref(narr_text)
            if _pref:
                _prefer_speed = _pref.get("speed")
        except Exception:
            _prefer_speed = None
    movement = effects_mgr.pick_movement(ph, pw, prefer_speed=_prefer_speed)
    movement_filter = movement["filter"].format(frames=frames) if isinstance(movement, dict) else movement.format(frames=frames)

    # Escolher cor — se mood fornecido, usar filtro viral por emoção
    if mood and mood in VIRAL_FILTERS:
        color_filter = VIRAL_FILTERS[mood]
    else:
        color = effects_mgr.pick_color()
        color_filter = color["filter"] if isinstance(color, dict) else color

    # T5: correção adaptativa (CONTENT_ADAPT=1). Mede a imagem e ANEXA um eq de correção
    # (clareia painel escuro, sobe contraste lavado) ao grading já escolhido — não substitui.
    if os.environ.get("CONTENT_ADAPT", "0") == "1":
        try:
            import content_analyzer as _ca
            _eq, _ = _ca.adaptive_eq(img_path)
            if _eq:
                color_filter = f"{color_filter},{_eq}"
        except Exception:
            pass

    # Vinheta (opcional)
    vignette = effects_mgr.pick_vignette()
    vignette_filter = vignette if isinstance(vignette, str) else (vignette["filter"] if isinstance(vignette, dict) else None)

    # Ratio da imagem vs canvas
    img_ratio = ph / pw
    canvas_ratio = H / W  # 1920/1080 = 1.78

    if img_ratio > 2.0:
        # Painel ALTO — pan vertical na imagem inteira
        prescale = f"scale=1080:-1"
        filters = [prescale, movement_filter, color_filter]
        if vignette_filter:
            filters.append(vignette_filter)
        filters.append(f"fade=t=out:st={duration-0.3:.2f}:d=0.3")
        filters.append("format=yuv420p")
        filter_chain = ",".join(filters)
        filter_complex = f"[0:v]{filter_chain}[v]"
    elif img_ratio > 1.2:
        # Painel médio/alto — zoompan direto
        filters = [movement_filter, color_filter]
        if vignette_filter:
            filters.append(vignette_filter)
        filters.append(f"fade=t=out:st={duration-0.3:.2f}:d=0.3")
        filters.append("format=yuv420p")
        filter_chain = ",".join(filters)
        filter_complex = f"[0:v]{filter_chain}[v]"
    else:
        # Painel LARGO (ratio < 1.2) — background blur profissional
        # Em vez de bordas pretas, usa a própria imagem borrada como fundo (n8n V5.1)
        filter_complex = (
            f"[0:v]split=2[bg][fg];"
            f"[bg]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
            f"boxblur=18:8,eq=brightness=-0.3[bg_blur];"
            f"[fg]scale={W}:{H}:force_original_aspect_ratio=decrease[fg_scaled];"
            f"[bg_blur][fg_scaled]overlay=(W-w)/2:(H-h)/2,"
            f"{color_filter}"
        )
        if vignette_filter:
            filter_complex += f",{vignette_filter}"
        filter_complex += f",fade=t=out:st={duration-0.3:.2f}:d=0.3,format=yuv420p[v]"

    # Overlay atmosférico (chuva/neve/faíscas/pétalas) entra como input 2
    filter_complex, overlay_input = _append_overlay(filter_complex, overlay_video)

    # Clip base (movimento + cor + vinheta + overlay). Transição/SFX embutidos na
    # MESMA chamada (single-pass) via apply_effects_to_cmd — sem re-encode extra.
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-t", f"{duration:.2f}", "-i", str(img_path),
        "-i", str(audio_path),
        *overlay_input,
        "-filter_complex", filter_complex,
        "-map", "[v]", "-map", "1:a",
        "-c:v", "libx264", "-preset", QP["preset"], "-crf", str(QP["crf"]), "-g", "30",
        "-c:a", "aac", "-b:a", QP["audio_bitrate"], "-ar", "44100", "-ac", "2",
        "-pix_fmt", "yuv420p", "-t", f"{duration:.2f}",
        str(out_path),
    ]

    try:
        cmd = apply_effects_to_cmd(cmd, transition_type, sfx_file, duration)
        subprocess.run(cmd, check=True, capture_output=True, timeout=180)
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        # Fallback: escala simples com padding escuro
        minimal = f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=0x0a0f1c,{color_filter},format=yuv420p"
        cmd_simple = [
            "ffmpeg", "-y",
            "-loop", "1", "-t", f"{duration:.2f}", "-i", str(img_path),
            "-i", str(audio_path),
            "-filter_complex", f"[0:v]{minimal}[v]",
            "-map", "[v]", "-map", "1:a",
            "-c:v", "libx264", "-preset", QP["preset"], "-crf", str(QP["crf"]), "-g", "30",
            "-c:a", "aac", "-b:a", QP["audio_bitrate"], "-ar", "44100", "-ac", "2",
            "-pix_fmt", "yuv420p", "-t", f"{duration:.2f}",
            str(out_path),
        ]
        try:
            cmd_simple = apply_effects_to_cmd(cmd_simple, transition_type, sfx_file, duration)
            subprocess.run(cmd_simple, check=True, capture_output=True, timeout=60)
            return True
        except Exception:
            return False


def build_clip_with_shake(img_path, audio_path, out_path, panel_idx, effects_mgr,
                          duration=None, shake_intensity=10, shake_freq=12,
                          transition_type=None, sfx_file=None, overlay_video=None, mood=None):
    """Cria clip com camera shake — pra painéis de impacto/ação.

    O shake é aplicado via crop com offset sinusoidal nos eixos X e Y.
    O efeito diminui ao longo do clip (decay), simulando tremor de impacto.

    Args:
        shake_intensity: amplitude do tremor em pixels (default 10)
        shake_freq: frequência das oscilações (default 12 Hz)
    """
    from PIL import Image
    img = Image.open(img_path)
    pw, ph = img.size

    if duration is None:
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                 "-of", "csv=p=0", str(audio_path)],
                capture_output=True, text=True, timeout=10,
            )
            duration = float(result.stdout.strip())
        except Exception:
            duration = 4.0
    duration = max(duration, 1.5)
    frames = int(duration * FPS)

    # Escolher movimento, cor, vinheta (como build_clip normal)
    movement = effects_mgr.pick_movement(ph, pw)
    movement_filter = movement["filter"].format(frames=frames) if isinstance(movement, dict) else movement.format(frames=frames)
    if mood and mood in VIRAL_FILTERS:
        color_filter = VIRAL_FILTERS[mood]
    else:
        color = effects_mgr.pick_color()
        color_filter = color["filter"] if isinstance(color, dict) else color
    vignette = effects_mgr.pick_vignette()
    vignette_filter = vignette if isinstance(vignette, str) else (
        vignette["filter"] if isinstance(vignette, dict) else None)

    # Camera shake: crop com margem extra, offset sinusoidal com decay
    # Precisamos gerar um frame maior e depois croppar com tremor
    margin = shake_intensity + 2  # margem extra pra não cortar fora
    shake_w = W + margin * 2
    shake_h = H + margin * 2

    # Decay: o shake diminui ao longo do tempo (forte no início, sumindo)
    # decay = max(0, 1 - on/(frames*0.6))  → shake dura 60% do clip
    shake_x = f"{margin}+{shake_intensity}*sin(t*{shake_freq})*max(0,1-t/({duration*0.6:.2f}))"
    shake_y = f"{margin}+{shake_intensity}*cos(t*{shake_freq}*1.3)*max(0,1-t/({duration*0.6:.2f}))"
    shake_crop = f"crop={W}:{H}:{shake_x}:{shake_y}"

    img_ratio = ph / pw

    if img_ratio > 2.0:
        prescale = "scale=1080:-1"
        # Ajustar zoompan pra gerar frame maior (shake_w x shake_h)
        shake_movement = movement_filter.replace(f"s={W}x{H}", f"s={shake_w}x{shake_h}")
        filters = [prescale, shake_movement, shake_crop, color_filter]
    elif img_ratio > 1.2:
        shake_movement = movement_filter.replace(f"s={W}x{H}", f"s={shake_w}x{shake_h}")
        filters = [shake_movement, shake_crop, color_filter]
    else:
        # Painel largo — scale+pad maior, depois crop com shake
        fg_filter = (
            f"scale={shake_w}:{shake_h}:force_original_aspect_ratio=decrease,"
            f"pad={shake_w}:{shake_h}:(ow-iw)/2:(oh-ih)/2:color=0x0a0f1c"
        )
        filters = [fg_filter, shake_crop, color_filter]

    if vignette_filter:
        filters.append(vignette_filter)
    filters.append("format=yuv420p")
    filter_chain = ",".join(filters)
    filter_complex = f"[0:v]{filter_chain}[v]"
    filter_complex, overlay_input = _append_overlay(filter_complex, overlay_video)

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-t", f"{duration:.2f}", "-i", str(img_path),
        "-i", str(audio_path),
        *overlay_input,
        "-filter_complex", filter_complex,
        "-map", "[v]", "-map", "1:a",
        "-c:v", "libx264", "-preset", QP["preset"], "-crf", str(QP["crf"]), "-g", "30",
        "-c:a", "aac", "-b:a", QP["audio_bitrate"], "-ar", "44100", "-ac", "2",
        "-pix_fmt", "yuv420p", "-t", f"{duration:.2f}",
        str(out_path),
    ]

    try:
        cmd = apply_effects_to_cmd(cmd, transition_type, sfx_file, duration)
        subprocess.run(cmd, check=True, capture_output=True, timeout=180)
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        # Fallback: build_clip sem shake (mantém transição/SFX + overlay)
        return build_clip(img_path, audio_path, out_path, panel_idx, effects_mgr,
                          duration, transition_type, sfx_file, overlay_video)


def build_flash_clip(img_path, out_path, clip_idx, effects_mgr, duration=0.8,
                     transition_type=None, sfx_file=None):
    """Cria clip rápido (sem áudio) com flash branco no final.

    Pra painéis sem narração — passam rápido e dão ritmo ao vídeo.
    """
    from PIL import Image
    img = Image.open(img_path)
    pw, ph = img.size
    img_ratio = ph / pw
    frames = int(duration * FPS)

    # Zoom rápido (mais agressivo que o normal pra dar sensação de velocidade)
    zoom_filter = f"zoompan=z='min(zoom+0.002,1.15)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps={FPS}"

    # Flash branco no final (últimos 5 frames = fade to white)
    flash = f"fade=t=out:st={max(0, duration-0.15):.2f}:d=0.15:color=white"

    if img_ratio > 2.0:
        prescale = "scale=1080:-1"
        filter_chain = f"{prescale},{zoom_filter},{flash},format=yuv420p"
    elif img_ratio > 1.2:
        filter_chain = f"{zoom_filter},{flash},format=yuv420p"
    else:
        filter_chain = (
            f"scale={W}:{H}:force_original_aspect_ratio=decrease,"
            f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=0x0a0f1c,"
            f"{flash},format=yuv420p"
        )

    # Gerar áudio: usar micro-SFX se disponível, senão tom mínimo (não silêncio puro)
    # Silêncio puro (anullsrc) corrompe stream de áudio no concat
    sfx_for_flash = pick_sfx("transition") if SFX_DIR.exists() else None
    if sfx_for_flash and Path(sfx_for_flash).exists():
        audio_input = ["-i", str(sfx_for_flash)]
        audio_filter = f"[1:a]volume=0.3,atrim=0:{duration:.2f},apad=whole_dur={duration:.2f}[a]"
        audio_map = "[a]"
    else:
        # Tom inaudível (1Hz, volume quase zero) — mantém stream válido sem silêncio
        audio_input = ["-f", "lavfi", "-t", f"{duration:.2f}", "-i", f"sine=frequency=1:sample_rate=44100:duration={duration:.2f}"]
        audio_filter = "[1:a]volume=0.001[a]"
        audio_map = "[a]"

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-t", f"{duration:.2f}", "-i", str(img_path),
        *audio_input,
        "-filter_complex", f"[0:v]{filter_chain}[v];{audio_filter}",
        "-map", "[v]", "-map", audio_map,
        "-c:v", "libx264", "-preset", QP["preset"], "-crf", str(QP["crf"]), "-g", "30",
        "-c:a", "aac", "-b:a", QP["audio_bitrate"], "-ar", "44100", "-ac", "2",
        "-pix_fmt", "yuv420p", "-t", f"{duration:.2f}",
        str(out_path),
    ]
    try:
        cmd = apply_effects_to_cmd(cmd, transition_type, sfx_file, duration)
        subprocess.run(cmd, check=True, capture_output=True, timeout=30)
        return True
    except Exception:
        return False


# --- Meme System (inserção inteligente de memes entre clips) ---
MEMES_VIDEO_DIR = Path(__file__).parent.parent / "workspace" / "assets" / "memes_img" / "memes"
_meme_counter = 0          # clips desde o último meme
_memes_inseridos = 0       # total de memes no vídeo (pra teto global)
# Cadência DINÂMICA (não fixa): o meme só pode entrar depois de MEME_GAP_MIN
# clips, é forçado depois de MEME_GAP_MAX, e entre os dois a chance depende do
# mood (cena cômica/leve puxa mais meme; neutra puxa menos). Assim fica "mais
# quando precisa, menos quando não" — com piso e teto pra não encher nem sumir.
MEME_GAP_MIN = 4           # nunca 2 memes a menos de 4 clips de distância (teto de proximidade)
MEME_GAP_MAX = 12          # se passou disso sem meme, força um (piso)
MEME_MOOD_CHANCE = {       # chance por clip, na janela [min,max], conforme o clima
    "funny_lighthearted": 0.55,
    "romantic_sexy": 0.22,
    "calm_chill": 0.18,
    "neutral_chill": 0.25,
    "action": 0.30,
}


def should_insert_meme(clip_idx, mood):
    """Cadência DINÂMICA de meme. NUNCA em cena triste/tensa.
    - antes de MEME_GAP_MIN clips desde o último: nunca (evita encher)
    - depois de MEME_GAP_MAX sem meme: força (evita sumir)
    - no meio: chance proporcional ao mood (mais em comédia, menos em neutro)"""
    global _meme_counter
    if mood in ("tense_dramatic", "sad_emotional"):
        return False
    _meme_counter += 1
    if _meme_counter < MEME_GAP_MIN:
        return False
    if _meme_counter >= MEME_GAP_MAX:
        _meme_counter = 0
        return True
    chance = MEME_MOOD_CHANCE.get(mood, 0.25)
    if random.random() < chance:
        _meme_counter = 0
        return True
    return False


def build_meme_clip(out_path, mood="neutral_chill", duration=None):
    """Constrói clip de meme. Se o meme tem áudio nativo, usa direto. Se é
    imagem/sem áudio, adiciona um SFX que COMBINA com o clima da cena (via
    pick_sfx_by_mood) em vez de um whoosh genérico — evita som que não tem
    nada a ver com o que está acontecendo.

    duration DINÂMICA por mood (None = auto): comédia segura mais tempo na tela
    (3.2s), cenas neutras/leves passam rápido (2.2s)."""
    global _memes_inseridos
    if duration is None:
        duration = {"funny_lighthearted": 3.2, "action": 2.6,
                    "romantic_sexy": 2.4}.get(mood, 2.2)
    if not MEMES_VIDEO_DIR.exists():
        return False
    memes = list(MEMES_VIDEO_DIR.glob("*.mp4"))
    if not memes:
        return False

    meme_video = random.choice(memes)
    _memes_inseridos += 1

    # Detectar se meme tem áudio
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "quiet", "-select_streams", "a", "-show_entries", "stream=codec_type", "-of", "csv=p=0", str(meme_video)],
            capture_output=True, text=True, timeout=5)
        has_audio = "audio" in r.stdout
    except Exception:
        has_audio = False

    if has_audio:
        # Meme com áudio nativo — usar direto. Áudio FORÇADO a `duration` (apad+atrim):
        # sem isso, áudio nativo mais curto + `-shortest` encurtava o CLIP e o desalinho
        # ACUMULAVA no concat → fala saía no quadro errado (drift progressivo). Sem -shortest.
        cmd = [
            "ffmpeg", "-y", "-i", str(meme_video),
            "-t", f"{duration:.2f}",
            "-vf", f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:black",
            "-af", f"apad,atrim=0:{duration:.3f},asetpts=PTS-STARTPTS",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
            "-c:a", "aac", "-b:a", QP["audio_bitrate"], "-ar", "44100", "-ac", "2", "-pix_fmt", "yuv420p",
            str(out_path),
        ]
    else:
        # Meme sem áudio (imagem) — SFX que COMBINA com o mood da cena
        sfx = pick_sfx_by_mood(mood) or pick_sfx("transition")
        if sfx and Path(sfx).exists():
            cmd = [
                "ffmpeg", "-y",
                "-i", str(meme_video),
                "-i", str(sfx),
                "-t", f"{duration:.2f}",
                "-filter_complex",
                f"[0:v]scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:black,"
                f"tpad=stop_mode=clone:stop_duration={duration},trim=0:{duration:.3f},setpts=PTS-STARTPTS[v];"
                f"[1:a]volume=0.8,apad,atrim=0:{duration:.3f},asetpts=PTS-STARTPTS[a]",
                "-map", "[v]", "-map", "[a]",
                "-t", f"{duration:.2f}",
                "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
                "-c:a", "aac", "-b:a", QP["audio_bitrate"], "-ar", "44100", "-ac", "2", "-pix_fmt", "yuv420p",
                str(out_path),
            ]
        else:
            # Sem SFX disponível — gerar silêncio. Vídeo estendido a `duration` (tpad clone) +
            # silêncio do mesmo tamanho; sem -shortest (que encurtava e acumulava drift).
            cmd = [
                "ffmpeg", "-y", "-i", str(meme_video),
                "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=mono:d={duration}",
                "-vf", f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:black,"
                       f"tpad=stop_mode=clone:stop_duration={duration},trim=0:{duration:.3f},setpts=PTS-STARTPTS",
                "-map", "0:v", "-map", "1:a",
                "-t", f"{duration:.2f}",
                "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
                "-c:a", "aac", "-b:a", QP["audio_bitrate"], "-ar", "44100", "-ac", "2", "-pix_fmt", "yuv420p",
                str(out_path),
            ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=30)
        return Path(out_path).exists() and Path(out_path).stat().st_size > 1000
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False


# ── Vídeos de transição entre cenas (os 19 mp4 de overlays/transitions) ───────
TRANSITIONS_VIDEO_DIR = OVERLAYS_DIR / "transitions"
_transition_counter = 0
TRANSITION_VIDEO_FREQUENCY = 5  # insere um vídeo de transição a cada N clips


def should_insert_transition(clip_idx):
    """Decide se entra um vídeo de transição (a cada TRANSITION_VIDEO_FREQUENCY clips).
    Diferente do meme (que é cômico e só em cena leve), a transição é neutra e
    serve só de "respiro" visual entre cenas — pode entrar em qualquer mood."""
    global _transition_counter
    _transition_counter += 1
    if _transition_counter >= TRANSITION_VIDEO_FREQUENCY:
        _transition_counter = 0
        return True
    return False


def build_transition_clip(out_path, duration=1.0):
    """Monta um clip curto a partir de um dos 19 vídeos de transição.

    Re-encoda pros MESMOS parâmetros dos clips normais (resolução, fps, codec,
    áudio aac) — é isso que permite entrar no concat simples `-c copy` SEM
    quebrar a sincronia de áudio (o erro histórico foi mexer no xfade; aqui não
    tocamos nele, a transição é só mais um clip curtinho na fila).
    O áudio do vídeo de transição é descartado e trocado por silêncio (são
    efeitos visuais; o som fica por conta dos SFX/trilha do pipeline)."""
    if not TRANSITIONS_VIDEO_DIR.exists():
        return False
    vids = list(TRANSITIONS_VIDEO_DIR.glob("*.mp4"))
    if not vids:
        return False
    tv = random.choice(vids)
    cmd = [
        "ffmpeg", "-y", "-i", str(tv),
        "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=mono:d={duration}",
        "-vf", f"scale={W}:{H}:force_original_aspect_ratio=decrease,"
               f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:black,fps={FPS},setsar=1,"
               f"tpad=stop_mode=clone:stop_duration={duration},trim=0:{duration:.3f},setpts=PTS-STARTPTS",
        "-map", "0:v", "-map", "1:a",
        "-t", f"{duration:.2f}",
        "-c:v", "libx264", "-preset", QP["preset"], "-crf", str(QP["crf"]),
        "-c:a", "aac", "-b:a", QP["audio_bitrate"], "-ar", "44100", "-ac", "2", "-pix_fmt", "yuv420p",
        str(out_path),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=30)
        return Path(out_path).exists() and Path(out_path).stat().st_size > 1000
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False


def detect_mood_from_text(text):
    """Detecta mood dominante de um texto. Tenta Haiku primeiro (entende contexto/
    ironia); se indisponível/falhar, cai no scoring por keywords (300+ palavras)."""
    try:
        import haiku_helpers
        m = haiku_helpers.detect_mood(text)
        if m:
            # 'action' do Haiku mapeia pro mood mais próximo do pipeline
            return "tense_dramatic" if m == "action" else m
    except Exception:
        pass
    text_lower = text.lower()
    scores = {"tense_dramatic": 0, "sad_emotional": 0, "romantic_sexy": 0,
              "funny_lighthearted": 0, "calm_chill": 0, "neutral_chill": 0}
    keywords = {
        "tense_dramatic": [
            "luta","batalha","medo","terror","perigo","tensão","morte","sangue","raiva",
            "ódio","fúria","matar","ameaça","violência","soco","golpe","destruir","arma",
            "tiro","guerra","vingança","traição","assassin","inimigo","demônio","monstro",
            "ataque","defesa","poder","explosão","grito","confronto","desafio","rival",
            "espada","faca","veneno","armadilha","emboscada","sequestro","refém","ameaçar",
            "fugi","perseguição","caçar","prender","capturar","invasão","destruição",
            "apocalipse","inferno","pesadelo","agonia","desesper","pavor","horror",
            "amaldiçoar","maldição","sombr","escuridão","trevas","caos","cruel",
            "tortura","ferido","machucado","cicatriz","queimad","envenenad","sufocad",
        ],
        "sad_emotional": [
            "chora","lágrima","triste","dor","sofr","morreu","saudade","solidão",
            "abandonad","separação","perdeu","luto","despedida","adeus","nunca mais",
            "sozinho","vazio","depressão","angústia","melancol","nostalgia","arrependimento",
            "culpa","perdão","desculpa","sinto muito","coitad","injusto","cruel destino",
            "sacrifício","partida","funeral","túmulo","memória","lembrança","chorand",
            "desabou","quebrou por dentro","coração partido","não aguento","demais pra mim",
        ],
        "romantic_sexy": [
            "amor","beijo","abraço","coração","paixão","seduz","carinho","te amo",
            "namorad","crush","romântic","lindo","linda","bonit","olhos","sorriso",
            "toque","mão","sussurro","intimidade","desejo","quero você","atraente",
            "encantad","apaixonad","ciúme","declaração","anel","casamento","encontro",
            "jantar","vinho","rosa","flor","perfume","corpo","pele","lábios","cabelo",
            "dançar","noite","lua","estrela","juntos","nós dois","sempre","pra sempre",
        ],
        "funny_lighthearted": [
            "rir","risada","engraçad","piada","haha","kkkk","zueira","brincadeir",
            "idiota","meme","eita","oxe","caramba","uai","mano","nossa","vergonha",
            "constrang","trapalhada","confusão","ridícul","bizarro","absurd","maluco",
            "doido","palhaçada","zoar","trollar","pegadinha","gafe","bobagem","besteira",
            "ué","hein","wtf","loucura","surreal","impossível","inacreditável","sério isso",
            "tô rindo","morri","não tanko","perdi tudo","genial","mitou","lendário",
            "lacrou","arrasar","poderosa","empoderad","rainha","diva","slayou",
            "mandou bem","arrasou","top","incrível","magnífico","show","brilhou",
        ],
        "calm_chill": [
            "calmo","paz","tranquil","sereno","silêncio","café","escola","casa","normal",
            "rotina","trabalho","escritório","mesa","cadeira","livro","estudo","aula",
            "professor","aluno","biblioteca","conversa","papo","bate-papo","diálogo",
            "explicar","entender","pensar","refletir","meditar","plano","estratégia",
            "preparar","treinar","praticar","cozinhar","comida","almoço","jantar",
            "amigo","colega","companheiro","parceiro","equipe","sorrindo","satisfeito",
            "aliviado","bonito dia","sol","céu","nuvem","brisa","natureza","árvore",
            "rio","lago","montanha","jardim","parque","caminhada","passeio","relaxar",
        ],
    }
    import re as _re
    for mood, words in keywords.items():
        for w in words:
            if len(w) <= 4:
                if _re.search(r'\b' + _re.escape(w), text_lower):
                    scores[mood] += 1
            else:
                if w in text_lower:
                    scores[mood] += 1
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "neutral_chill"


# ── Transições xfade REAIS entre clips (1 passada, áudio em sync) ────────────
_XFADE_SUPPORTED = None


def _xfade_supported():
    """Descobre quais transições xfade existem NESTE build do ffmpeg (cacheado)."""
    global _XFADE_SUPPORTED
    if _XFADE_SUPPORTED is not None:
        return _XFADE_SUPPORTED
    supported = set()
    try:
        r = subprocess.run(["ffmpeg", "-hide_banner", "-h", "filter=xfade"],
                           capture_output=True, text=True, timeout=15)
        txt = (r.stdout or "") + (r.stderr or "")
        for line in txt.splitlines():
            m = re.match(r"\s+([a-z]+)\s+\d+\s+\.", line)  # "  fade  0  ..FV..."
            if m:
                supported.add(m.group(1))
    except Exception:
        pass
    if not supported:  # fallback mínimo garantido (presente desde ffmpeg 4.3)
        supported = {"fade", "fadeblack", "fadewhite", "dissolve", "wipeleft",
                     "wiperight", "wipeup", "wipedown", "slideleft", "slideright",
                     "slideup", "slidedown", "smoothleft", "smoothright", "smoothup",
                     "smoothdown", "circleopen", "circleclose", "diagtl", "diagtr",
                     "diagbl", "diagbr", "pixelize", "radial", "distance",
                     "hlslice", "hrslice", "vuslice", "vdslice"}
    _XFADE_SUPPORTED = supported
    return supported


def _probe_dur(path):
    try:
        r = subprocess.run(["ffprobe", "-v", "quiet", "-show_entries",
                            "format=duration", "-of", "csv=p=0", str(path)],
                           capture_output=True, text=True, timeout=15)
        return float(r.stdout.strip())
    except Exception:
        return 3.0


def _pick_xfade(desc, supported, last):
    """Escolhe transição xfade + duração pelo mood do painel (varia, não repete)."""
    impact = is_impact_panel(desc) if desc else False
    tension = is_tension_panel(desc) if desc else False
    if impact:                       # corte de ação: rápido, direcional, com "vento"
        pool = ["coverleft", "coverright", "coverup", "hrwind", "vuwind",
                "hrslice", "vuslice", "zoomin", "squeezev", "slideleft",
                "slideright", "wipeleft", "diagtr"]
        d = 0.22
    elif tension:                    # tensão: desfaz/rasga em tiras / revela
        pool = ["dissolve", "hlslice", "vdslice", "hlwind", "vdwind", "pixelize",
                "radial", "distance", "fadeblack", "revealdown", "diagbl"]
        d = 0.35
    else:                            # normal/calmo: suave + reveals elegantes
        pool = ["fade", "dissolve", "smoothleft", "smoothright", "smoothup",
                "smoothdown", "circleopen", "circleclose", "revealleft",
                "revealright", "revealup", "coverdown", "wipeleft", "wiperight",
                "slideup", "slidedown", "diagtl", "diagbr", "horzopen", "vertopen",
                "pixelize"]
        d = 0.42
    pool = [t for t in pool if t in supported]
    if not pool:
        pool = [t for t in ("fade", "dissolve") if t in supported] or ["fade"]
    choices = [t for t in pool if t != last] or pool
    return random.choice(choices), d


def _choose_xfade_batches(n, is_speech, max_batch):
    """Divide [0,n) em lotes de no máximo max_batch clips. Prefere cortar os
    lotes numa fronteira de CORTE SECO (k onde NÃO há xfade: respiro/meme),
    porque ali não se perde transição ao emendar os lotes via concat. Se não
    houver corte seco dentro da janela, corta no limite mesmo."""
    batches = []
    s = 0
    while s < n:
        hard_cap = min(s + max_batch, n)
        if hard_cap >= n:
            batches.append((s, n)); break
        # procura, de trás pra frente dentro da janela, uma fronteira de corte
        # seco (k tal que a transição k-1→k seria seca). soft = fala→fala.
        cut = hard_cap
        for k in range(hard_cap, s + 3, -1):
            soft = is_speech[k] and is_speech[k - 1]
            if not soft:
                cut = k; break
        batches.append((s, cut))
        s = cut
    return batches


# Posições reais (start, total) do ÚLTIMO segmento renderizado — usadas pra
# sincronizar legenda com o vídeo (o xfade comprime o tempo de forma NÃO-linear,
# só nas fronteiras fala→fala; um fator linear erra e a legenda "desanda" ~30s).
_LAST_SEG_STARTS = []
_LAST_SEG_TOTAL = 0.0
# Posições absolutas (s) de início de cada clip no vídeo final concatenado.
# A legenda usa isto pra casar exatamente com o vídeo (corrige o "desanda ~30s").
_CLIP_ABS_STARTS = []


def _render_xfade_segment(clips, durs, is_speech, gaps, descriptions,
                          supported, out_path):
    """Renderiza UM segmento (lista de clips) numa única passada de
    filter_complex: xfade+acrossfade nas fronteiras fala→fala, corte seco nas
    demais. Aplica o gap (respiro) no fim de cada clip de fala. Retorna True/False.
    Mantém o segmento pequeno o bastante pra não estourar memória.
    Efeito colateral: grava em _LAST_SEG_STARTS/_LAST_SEG_TOTAL as posições reais
    de início de cada clip no segmento e a duração total dele."""
    global _LAST_SEG_STARTS, _LAST_SEG_TOTAL
    m = len(clips)
    if m == 0:
        _LAST_SEG_STARTS, _LAST_SEG_TOTAL = [], 0.0
        return False
    if m == 1:
        gi0 = (gaps[0] if gaps else 0.0) or 0.0
        _LAST_SEG_STARTS = [0.0]
        _LAST_SEG_TOTAL = durs[0] + gi0
        # 1 clip só: aplica o gap (se houver) e re-encoda, ou copia.
        gi = gaps[0] if gaps else 0.0
        if gi and gi > 0:
            tgt1 = durs[0] + gi
            fc = (f"[0:v]format=yuv420p,fps={FPS},scale={W}:{H},setsar=1,"
                  f"tpad=stop_mode=clone:stop_duration={gi:.3f},settb=AVTB,setpts=PTS-STARTPTS[v];"
                  f"[0:a]aresample=44100,aformat=sample_fmts=fltp:channel_layouts=stereo,"
                  f"apad=whole_dur={tgt1:.4f},atrim=0:{tgt1:.4f},asetpts=PTS-STARTPTS[a]")
            cmd = ["ffmpeg", "-y", "-i", clips[0], "-filter_complex", fc,
                   "-map", "[v]", "-map", "[a]",
                   "-c:v", "libx264", "-preset", QP["preset"], "-crf", str(QP["crf"]),
                   "-c:a", "aac", "-b:a", QP["audio_bitrate"], "-ar", "44100", "-ac", "2",
                   "-movflags", "+faststart", "-pix_fmt", "yuv420p", out_path]
        else:
            import shutil
            shutil.copy2(clips[0], out_path)
            return True
        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=300)
            return Path(out_path).exists()
        except Exception:
            return False

    durs_eff = [durs[i] + (gaps[i] if i < len(gaps) else 0.0) for i in range(m)]
    cmd = ["ffmpeg", "-y"]
    for c in clips:
        cmd += ["-i", c]

    vparts, aparts = [], []
    for i in range(m):
        gi = gaps[i] if i < len(gaps) else 0.0
        vtail = (f",tpad=stop_mode=clone:stop_duration={gi:.3f}" if gi > 0 else "")
        vparts.append(f"[{i}:v]format=yuv420p,fps={FPS},scale={W}:{H},setsar=1{vtail},"
                      f"settb=AVTB,setpts=PTS-STARTPTS[v{i}]")
        # SYNC FIX: força o áudio a ter EXATAMENTE durs_eff[i] segundos (pad até
        # esse total, depois corta). Sem isso, o áudio real diverge ~4-17ms do
        # que a matemática do xfade/offset assume (que usa durs_eff do probe), e
        # esse drift ACUMULA a cada acrossfade → falas de personagem saem
        # dessincronizadas depois de ~30s (vários clips curtos somados). A
        # narração não erra porque é contínua/longa.
        tgt = durs_eff[i]
        aparts.append(f"[{i}:a]aresample=44100,"
                      f"aformat=sample_fmts=fltp:channel_layouts=stereo,"
                      f"apad=whole_dur={tgt:.4f},atrim=0:{tgt:.4f},"
                      f"asetpts=PTS-STARTPTS[a{i}]")

    chain = []
    last_trans = None
    acc = durs_eff[0]
    starts = [0.0]  # posição real de início de cada clip no segmento
    v_cur, a_cur = "v0", "a0"
    for k in range(1, m):
        v_out, a_out = f"vx{k}", f"ax{k}"
        soft = is_speech[k] and is_speech[k - 1]
        if soft:
            desc = descriptions[k] if k < len(descriptions) else ""
            trans, d = _pick_xfade(desc, supported, last_trans)
            last_trans = trans
            d = max(0.10, min(d, durs_eff[k] * 0.5, acc * 0.5))
            offset = max(0.0, acc - d)
            chain.append(f"[{v_cur}][v{k}]xfade=transition={trans}:"
                         f"duration={d:.3f}:offset={offset:.3f}[{v_out}]")
            chain.append(f"[{a_cur}][a{k}]acrossfade=d={d:.3f}[{a_out}]")
            starts.append(acc - d)  # o clip k começa onde o xfade inicia
            acc = acc + durs_eff[k] - d
        else:
            chain.append(f"[{v_cur}][v{k}]concat=n=2:v=1:a=0[{v_out}]")
            chain.append(f"[{a_cur}][a{k}]concat=n=2:v=0:a=1[{a_out}]")
            last_trans = None
            starts.append(acc)  # corte seco: começa exatamente no fim do anterior
            acc = acc + durs_eff[k]
        v_cur, a_cur = v_out, a_out

    _LAST_SEG_STARTS = starts
    _LAST_SEG_TOTAL = acc

    filter_complex = ";".join(vparts + aparts + chain)
    cmd += ["-filter_complex", filter_complex,
            "-map", f"[{v_cur}]", "-map", f"[{a_cur}]",
            "-c:v", "libx264", "-preset", QP["preset"], "-crf", str(QP["crf"]),
            "-c:a", "aac", "-b:a", QP["audio_bitrate"], "-ar", "44100", "-ac", "2",
            "-movflags", "+faststart", "-pix_fmt", "yuv420p", out_path]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=900)
        return Path(out_path).exists() and Path(out_path).stat().st_size > 1000
    except subprocess.CalledProcessError as e:
        try:
            err = e.stderr.decode("utf-8", "ignore") if e.stderr else ""
            with open("xfade_debug_full.txt", "w", encoding="utf-8") as _dbg:
                _dbg.write("=== CMD ===\n" + " ".join(cmd))
                _dbg.write("\n\n=== FILTER_COMPLEX ===\n" + filter_complex)
                _dbg.write("\n\n=== STDERR ===\n" + err)
            print("[xfade seg] falhou. Fim do stderr:\n", err[-500:], flush=True)
        except Exception:
            pass
        return False
    except subprocess.TimeoutExpired:
        print("[xfade seg] timeout.", flush=True)
        return False


def _concat_segments(seg_paths, out_path):
    """Junta os segmentos já renderizados via concat demuxer (-c copy). Como
    todos saíram do mesmo encoder (mesmo codec/fps/sar/taxa), o copy é seguro e
    barato. Reencoda como fallback se o copy falhar."""
    seg_paths = [str(p) for p in seg_paths]
    if len(seg_paths) == 1:
        import shutil
        shutil.copy2(seg_paths[0], str(out_path))
        return True
    list_file = Path(seg_paths[0]).parent / "_xfseg_list.txt"
    with open(list_file, "w", encoding="utf-8") as f:
        for p in seg_paths:
            f.write(f"file '{p}'\n")
    base = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file)]
    try:
        subprocess.run(base + ["-c", "copy", "-movflags", "+faststart", str(out_path)],
                       check=True, capture_output=True, timeout=180)
        return Path(out_path).exists()
    except Exception:
        try:
            subprocess.run(base + ["-c:v", "libx264", "-preset", QP["preset"],
                           "-crf", str(QP["crf"]), "-c:a", "aac",
                           "-b:a", QP["audio_bitrate"], "-ar", "44100", "-ac", "2",
                           "-movflags", "+faststart", "-pix_fmt", "yuv420p", str(out_path)],
                           check=True, capture_output=True, timeout=600)
            return Path(out_path).exists()
        except Exception:
            return False
    finally:
        try: list_file.unlink()
        except Exception: pass


def concat_with_xfade(clips, out_path, descriptions=None, clip_texts=None, clip_sfx_dur=None):
    """Concatena clips com transições xfade REAIS entre eles, numa ÚNICA passada
    de filter_complex: vídeo via xfade + áudio via acrossfade (mesma duração por
    fronteira) → o áudio encolhe em lockstep com o vídeo, sem o bug de corrupção
    do xfade pair-by-pair. A transição varia pelo mood de cada painel.

    `clip_texts` (alinhado com `clips`) marca quais clips são FALA (texto != "").
    Clips de "respiro" (meme/transição/intro/outro) vêm com texto vazio.
    - Fronteira FALA→FALA: xfade (vídeo) + acrossfade (áudio) suave.
    - Fronteira que toca um respiro: CORTE SECO (concat, sem overlap) — assim a
      fala termina inteira e o meme toca inteiro, sem o áudio se atropelar.

    Em qualquer falha cai no concat simples (-c copy) pra nunca perder o vídeo.
    """
    clips = [str(c) for c in clips]
    n = len(clips)
    if n < 2:
        if clips:
            import shutil
            shutil.copy2(clips[0], str(out_path))
        return bool(clips)

    supported = _xfade_supported()
    durs = [_probe_dur(c) for c in clips]
    descriptions = descriptions or []
    # is_speech[i]: True se o clip tem fala (texto não-vazio). Sem a lista, assume
    # tudo fala (comportamento antigo). Respiros (meme/transição) têm texto "".
    if clip_texts:
        is_speech = [bool((clip_texts[i] if i < len(clip_texts) else "").strip())
                     for i in range(n)]
    else:
        is_speech = [True] * n

    # GAP (respiro) entre clips de fala — HÍBRIDO fixo+dinâmico:
    #   - MÍNIMO fixo: env CLIP_GAP_S (default 0.5s) — a cadência que o usuário
    #     aprovou; garante que o vídeo nunca fique acelerado.
    #   - DINÂMICO: se o PRÓXIMO clip carrega um SFX mais longo que o mínimo, o
    #     respiro cresce pra caber o som (gap = duração do SFX), dando espaço
    #     sonoro a ele em vez de atropelá-lo.
    #   - MÁXIMO fixo: env CLIP_GAP_MAX (default 1.2s) — teto pra um SFX muito
    #     longo não esticar o vídeo com pausa morta.
    #   - CLIP_GAP_DYNAMIC=0 desliga o crescimento (usa só o mínimo fixo).
    # Cada clip de fala ganha no FIM um congela-último-frame + silêncio do tamanho
    # do seu gap — vídeo e áudio crescem igual, sem desync. Memes/transições não.
    try:
        gap_base = max(0.0, float(os.environ.get("CLIP_GAP_S", "0.5")))
    except ValueError:
        gap_base = 0.5
    try:
        gap_cap = max(gap_base, float(os.environ.get("CLIP_GAP_MAX", "1.2")))
    except ValueError:
        gap_cap = 1.2
    # TOGGLE de SFX (env SFX_MODE):
    #   "gap" (default) = o respiro entre falas CRESCE pra o SFX tocar no silêncio,
    #                     sem atropelar a narração. (= gap dinâmico ligado)
    #   "junto" = o SFX sai POR CIMA da fala (gap fica só na base fixa, não cresce).
    # CLIP_GAP_DYNAMIC continua funcionando como override de baixo nível.
    sfx_mode = os.environ.get("SFX_MODE", "gap").strip().lower()
    if sfx_mode == "junto":
        gap_dyn = False
    elif sfx_mode == "gap":
        gap_dyn = True
    else:
        gap_dyn = os.environ.get("CLIP_GAP_DYNAMIC", "1") != "0"
    sfx_durs = clip_sfx_dur or [0.0] * n

    gaps = [0.0] * n
    for i in range(n):
        if not is_speech[i]:
            continue
        g = gap_base
        if gap_dyn and i + 1 < n:
            sfx_next = sfx_durs[i + 1] if i + 1 < len(sfx_durs) else 0.0
            if sfx_next > gap_base:
                g = min(sfx_next, gap_cap)
        gaps[i] = g
    # Log dos gaps dinâmicos que cresceram além da base (pra dar visibilidade ao
    # respiro que abre espaço pra um SFX longo no clip seguinte).
    _grown = [(i, round(gaps[i], 2)) for i in range(n) if gaps[i] > gap_base + 0.001]
    if _grown:
        print(f"  [gap dinâmico] base={gap_base:.2f}s teto={gap_cap:.2f}s · "
              f"respiros esticados p/ SFX longo: {_grown}", flush=True)

    # ── Render em LOTES pra não estourar memória ───────────────────────────
    # Um filter_complex com TODOS os clips de uma vez estoura a RAM (ffmpeg
    # -12 "Cannot allocate memory") por volta de ~25+ clips. Solução: processar
    # em lotes de XFADE_BATCH clips, cortando os lotes em fronteiras de CORTE
    # SECO (onde não há xfade a perder) e juntando os lotes com concat demuxer.
    try:
        max_batch = max(4, int(os.environ.get("XFADE_BATCH", "8")))
    except ValueError:
        max_batch = 8

    if n <= max_batch:
        ok = _render_xfade_segment(clips, durs, is_speech, gaps, descriptions,
                                   supported, str(out_path))
        if ok and Path(out_path).exists() and Path(out_path).stat().st_size > 1000:
            # offsets absolutos = os do único segmento
            global _CLIP_ABS_STARTS
            _CLIP_ABS_STARTS = list(_LAST_SEG_STARTS)
            return True
        return concat_with_transitions(clips, out_path, descriptions=descriptions)

    batches = _choose_xfade_batches(n, is_speech, max_batch)
    print(f"  [xfade lotes] {n} clips → {len(batches)} lotes {batches}", flush=True)
    tmp_dir = Path(clips[0]).parent
    seg_paths = []
    abs_starts = []      # posição absoluta de início de cada clip no vídeo final
    seg_base = 0.0       # deslocamento acumulado dos lotes anteriores
    for bi, (s, e) in enumerate(batches):
        seg_out = tmp_dir / f"_xfseg_{bi:02d}.mp4"
        ok = _render_xfade_segment(
            clips[s:e], durs[s:e], is_speech[s:e], gaps[s:e],
            descriptions[s:e] if descriptions else [],
            supported, str(seg_out))
        if not ok or not seg_out.exists():
            print(f"  [xfade lotes] lote {bi} falhou — fallback concat geral.", flush=True)
            return concat_with_transitions(clips, out_path, descriptions=descriptions)
        # acumula as posições reais deste lote, deslocadas pelo total dos anteriores.
        # lotes são unidos por corte seco (concat demuxer), então somam direto.
        for st in _LAST_SEG_STARTS:
            abs_starts.append(seg_base + st)
        # DESYNC FIX: avança seg_base pela duração REAL do segmento renderizado
        # (ffprobe), não pelo total MATEMÁTICO (_LAST_SEG_TOTAL/acc). O encoder
        # arredonda a duração final por causa de fps/keyframes, então o acc teórico
        # diverge alguns centésimos por lote — e como os lotes são concatenados pelos
        # arquivos reais, esse erro escalona A CADA lote e desloca a legenda dos
        # lotes seguintes (o "some/desanda a partir do meio"). Medir o real corrige.
        seg_real = _probe_dur(seg_out)
        seg_base += seg_real if seg_real and seg_real > 0 else _LAST_SEG_TOTAL
        seg_paths.append(seg_out)

    ok = _concat_segments(seg_paths, out_path)
    for p in seg_paths:
        try: p.unlink()
        except Exception: pass
    if ok and Path(out_path).exists() and Path(out_path).stat().st_size > 1000:
        _CLIP_ABS_STARTS = abs_starts
        return True
    return concat_with_transitions(clips, out_path, descriptions=descriptions)


def concat_with_transitions(clips, out_path, transition_dur=TRANSITION_DURATION,
                            descriptions=None):
    """Concatena clips com concat simples (-c copy).

    O xfade pair-by-pair corrompia o áudio depois de ~20 pares em vídeos longos.
    Transições visuais já estão embutidas em cada clip (fade-out + apply_effects_to_cmd),
    então concat simples mantém sincronia perfeita.
    """
    if len(clips) < 2:
        if clips:
            import shutil
            shutil.copy2(str(clips[0]), str(out_path))
        return bool(clips)

    tmp_dir = Path(clips[0]).parent
    list_file = tmp_dir / "_concat_final.txt"
    with open(list_file, "w") as f:
        for c in clips:
            f.write(f"file '{c}'\n")

    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(list_file), "-c", "copy",
        "-movflags", "+faststart", str(out_path),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=120)
    except subprocess.CalledProcessError:
        cmd_reenc = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file),
            "-c:v", "libx264", "-preset", QP["preset"], "-crf", str(QP["crf"]),
            "-c:a", "aac", "-b:a", QP["audio_bitrate"], "-ar", "44100", "-ac", "2",
            "-movflags", "+faststart", "-pix_fmt", "yuv420p",
            str(out_path),
        ]
        subprocess.run(cmd_reenc, check=True, capture_output=True, timeout=300)

    try:
        list_file.unlink()
    except Exception:
        pass

    return Path(out_path).exists() and Path(out_path).stat().st_size > 1000


# Resolução final de entrega (1080x1920 Full HD vertical)


# Resolução final de entrega (1080x1920 Full HD vertical)
W_FINAL, H_FINAL = 1080, 1920


def upscale_to_fullhd(video_in, video_out):
    """Upscala o vídeo de 720x1280 → 1080x1920 (lanczos, 1 passada rápida).

    Clips são renderizados em 720p pra velocidade. Upscale só no final,
    uma única vez, com qualidade boa (lanczos + CRF 20).
    """
    cmd = [
        "ffmpeg", "-y", "-i", str(video_in),
        "-vf", f"scale={W_FINAL}:{H_FINAL}:flags=lanczos",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-g", "30",
        "-c:a", "copy",
        "-movflags", "+faststart", "-pix_fmt", "yuv420p",
        str(video_out),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=600)
        return Path(video_out).exists() and Path(video_out).stat().st_size > 0
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False
# SEÇÃO 5B: LEGENDAS QUEIMADAS (estilo Shorts) — Ponto F
# Este ffmpeg não tem libass/drawtext, então renderizamos cada legenda como PNG
# transparente com PIL e sobrepomos via filtro overlay (sem dependências novas).
# ══════════════════════════════════════════════════════════════════════════

# Fontes bold disponíveis no macOS (heavy → bom pra Shorts)
_FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Impact.ttf",
    "/System/Library/Fonts/Supplemental/Arial Black.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Helvetica Bold.ttf",
    "/System/Library/Fonts/Impact.ttf",
    "/Library/Fonts/Impact.ttf",
    "/Library/Fonts/Arial Black.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "/Library/Fonts/Helvetica Bold.ttf",
]

# Fallback de fontes populares em Linux/Windows, se necessário
# (ex: para ambiente Docker ou CI/CD headless)
_FONT_CANDIDATES_FALLBACK = [
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", # Linux
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",        # Linux
    "C:/Windows/Fonts/impact.ttf",                                  # Windows
    "C:/Windows/Fonts/arialbd.ttf",                                 # Windows
]


def _load_font(size):
    from PIL import ImageFont
    for fp in _FONT_CANDIDATES + _FONT_CANDIDATES_FALLBACK:
        if Path(fp).exists():
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _wrap_lines(text, font, draw, max_w):
    """Quebra o texto em linhas que cabem em max_w pixels."""
    words = (text or "").strip().replace("\n", " ").split()
    lines, cur = [], ""
    for w in words:
        test = f"{cur} {w}".strip()
        bbox = draw.textbbox((0, 0), test, font=font, stroke_width=8)
        if cur and (bbox[2] - bbox[0]) > max_w:
            lines.append(cur)
            cur = w
        else:
            cur = test
    if cur:
        lines.append(cur)
    return lines[:3]  # no máx 3 linhas


def detect_context(text):
    """T6: detecta o TOM da frase p/ estilo de legenda (porte do SubtitleProcessor do n8n).
    Retorna 'shout'|'whisper'|'thought'|'emphasis'|'normal'. Ordem: emphasis(!!)>shout(!)>
    whisper(...)>thought(*) — !! checado antes de ! pra não virar shout."""
    t = (text or "")
    low = t.lower()
    if "!!" in t or re.search(r"import|crític|critic|vital", low):
        return "emphasis"
    if "!" in t or re.search(r"grito|berro|alto\b", low):
        return "shout"
    if "..." in t or re.search(r"sussurr|baixo|murmur", low):
        return "whisper"
    if "*" in t or re.search(r"pensa|imagin|reflet", low):
        return "thought"
    return "normal"


# Estilo por contexto (NOSSO formato PNG, não ASS). (mult_fontsize, cor_RGB|None=branco).
_SUB_CONTEXT_STYLE = {
    "normal":   (1.00, None),
    "shout":    (1.22, None),              # maior, outline forte (tratado no render)
    "whisper":  (0.82, (190, 190, 200)),   # menor, cinza
    "thought":  (0.90, (200, 200, 235)),   # leve azulado (pensamento)
    "emphasis": (1.10, (255, 214, 60)),    # amarelo
}


def _render_caption_png(text, out_png, fontsize=65, highlight_idx=None,
                        highlight_color=(255, 214, 60)):
    """Renderiza uma legenda como PNG transparente (recortado na região do texto).

    Branco com contorno preto grosso, embaixo-centro. Retorna (png, x, y) com a
    posição do recorte no canvas 1080x1920, pra overlay leve (pouca memória).

    highlight_idx: índice da palavra (na contagem global do texto) a destacar em
    amarelo (estilo karaokê). None = sem destaque (legenda estática).
    """
    from PIL import Image, ImageDraw
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # T6: estilo por contexto (SUB_CONTEXT=1). Ajusta fontsize/cor base pelo tom da frase.
    _ctx_color = None
    _ctx_stroke_boost = 0
    if os.environ.get("SUB_CONTEXT", "0") == "1":
        _ctx = detect_context(text)
        _mult, _col = _SUB_CONTEXT_STYLE.get(_ctx, (1.0, None))
        fontsize = int(fontsize * _mult)
        _ctx_color = _col
        if _ctx == "shout":
            _ctx_stroke_boost = 3
    font = _load_font(fontsize)
    lines = _wrap_lines(text, font, draw, max_w=int(W * 0.86))
    if not lines:
        return None

    line_h = int(fontsize * 1.18)
    total_h = line_h * len(lines)
    # Base: ~85-88% da altura (área de leitura de Shorts, evita balões)
    y0 = int(H * 0.85) - total_h
    stroke = 8 + _ctx_stroke_boost
    _base_fill = (*_ctx_color, 255) if _ctx_color else (255, 255, 255, 255)
    word_counter = 0  # índice global da palavra (pra casar com highlight_idx)
    space_w = draw.textlength(" ", font=font)
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font, stroke_width=stroke)
        lw = bbox[2] - bbox[0]
        x = (W - lw) // 2 - bbox[0]
        y = y0 + i * line_h
        if highlight_idx is None:
            draw.text((x, y), line, font=font, fill=_base_fill,
                      stroke_width=stroke, stroke_fill=(0, 0, 0, 235))
        else:
            # desenha palavra a palavra pra colorir a ativa
            cx = x
            for word in line.split():
                color = (*highlight_color, 255) if word_counter == highlight_idx \
                    else _base_fill
                draw.text((cx, y), word, font=font, fill=color,
                          stroke_width=stroke, stroke_fill=(0, 0, 0, 235))
                cx += draw.textlength(word, font=font) + space_w
                word_counter += 1

    # Recorta só a região do texto (com folga) → PNG pequeno, overlay barato
    bbox = img.getbbox()
    if not bbox:
        return None
    pad = 6
    cx0 = max(0, bbox[0] - pad); cy0 = max(0, bbox[1] - pad)
    cx1 = min(W, bbox[2] + pad); cy1 = min(H, bbox[3] + pad)
    img.crop((cx0, cy0, cx1, cy1)).save(out_png)
    return (out_png, cx0, cy0)


def render_subtitles(entries, tmp_dir, offsets=None):
    """Gera PNGs das legendas com timing cumulativo.

    entries: lista de (texto, duracao_segundos) na ORDEM dos clips.
    offsets: se fornecido, lista de timestamps absolutos de início para cada entry.
             Usado quando as legendas são filtradas (ex: só narrador) e os tempos
             não são mais sequenciais.
    Retorna lista de dicts {png, start, end} (só pros painéis com texto).
    """
    tmp_dir = Path(tmp_dir)
    subs = []
    t = 0.0
    for i, (text, dur) in enumerate(entries):
        dur = max(0.4, float(dur or 0))
        if offsets:
            start = offsets[i]
            end = start + dur
        else:
            start, end = t, t + dur
            t = end
        if not (text or "").strip():
            continue
        png = tmp_dir / f"_cap_{i:03d}.png"
        res = _render_caption_png(text, png)
        if res:
            _, x, y = res
            subs.append({"png": str(png), "x": x, "y": y, "start": start, "end": end})
    return subs


def render_subtitles_progressive(entries, tmp_dir, offsets=None, word_times=None):
    """Legendas KARAOKÊ OTIMIZADO: a palavra ativa fica amarela, sincronizada por tempo.

    word_times (MELHORIA WordBoundary): lista alinhada às entries; cada item é a lista de
    [start_s,end_s,word] REAL do edge-tts (sidecar .words.json). Quando presente p/ a entry,
    usa o timing REAL de cada palavra (mata o drift do karaokê); senão, estimativa por len().

    OTIMIZAÇÃO: Em vez de 1 PNG por palavra (que gerava centenas de overlays e timeout),
    gera 1 PNG a cada CHUNK de 3 palavras. Dentro de cada chunk, a palavra destacada
    muda — mas o total de PNGs fica ~3x menor que o original.

    Sem timestamps do TTS, estima o timing dividindo a duração do clip igualmente
    entre as palavras. Reusa o mesmo wrap/layout da legenda estática.

    offsets: se fornecido, lista de timestamps absolutos de início para cada entry.
    """
    tmp_dir = Path(tmp_dir)
    subs = []
    t = 0.0
    CHUNK_SIZE = 5  # Palavras por PNG (aumentado de 3 pra 5 pra gerar menos PNGs)

    for i, (text, dur) in enumerate(entries):
        dur = max(0.4, float(dur or 0))
        if offsets:
            start = offsets[i]
        else:
            start = t
            t += dur
        words = (text or "").strip().split()
        if not words:
            continue
        n = len(words)
        # MELHORIA WordBoundary: usa timing REAL de cada palavra se veio o sidecar da entry.
        wt_real = None
        if word_times and i < len(word_times) and word_times[i] and len(word_times[i]) == n:
            wt_real = word_times[i]  # [[start,end,word],...] relativo ao clip
        # Distribuição proporcional ao comprimento de cada palavra (fallback quando sem real)
        weights = [max(2, len(w)) for w in words]
        total_weight = sum(weights)
        word_durs = [dur * (wt / total_weight) for wt in weights]

        # Gerar PNGs em chunks: cada chunk destaca 1 palavra diferente
        # mas só cria 1 PNG por chunk (a palavra central do chunk fica amarela)
        for w_idx in range(0, n, CHUNK_SIZE):
            chunk_end = min(w_idx + CHUNK_SIZE, n)
            # Pra cada palavra do chunk, gerar um PNG com ela destacada
            for highlight in range(w_idx, chunk_end):
                png = tmp_dir / f"_capk_{i:03d}_{highlight:03d}.png"
                res = _render_caption_png(text, png, highlight_idx=highlight)
                if not res:
                    continue
                _, x, y = res
                if wt_real:
                    # timing REAL do edge-tts (relativo ao clip) + offset absoluto do clip
                    w_start = start + wt_real[highlight][0]
                    w_end = start + wt_real[highlight][1]
                else:
                    w_start = start + sum(word_durs[:highlight])
                    w_end = start + sum(word_durs[:highlight + 1])
                subs.append({"png": str(png), "x": x, "y": y,
                             "start": w_start, "end": w_end})

        # LIMITE DE SEGURANÇA: se já ultrapassou 300 PNGs, para de gerar karaokê
        # e volta pra estático pro restante (evita timeout no ffmpeg)
        if len(subs) > 300:
            # Restante em modo estático (1 PNG por entry)
            for j in range(i + 1, len(entries)):
                txt_j, dur_j = entries[j]
                dur_j = max(0.4, float(dur_j or 0))
                if offsets:
                    start_j = offsets[j]
                else:
                    start_j = t
                    t += dur_j
                if not (txt_j or "").strip():
                    continue
                png = tmp_dir / f"_capk_{j:03d}_static.png"
                res = _render_caption_png(txt_j, png)
                if res:
                    _, x, y = res
                    subs.append({"png": str(png), "x": x, "y": y,
                                 "start": start_j, "end": start_j + dur_j})
            break

    return subs


def render_name_tag(name, out_png, fontsize=58):
    """Renderiza o nome do personagem (tag) acima da legenda, em destaque.

    Retorna (png, x, y) recortado. Cor de destaque amarela com contorno preto.
    """
    from PIL import Image, ImageDraw
    name = (name or "").strip().upper()
    if not name:
        return None
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = _load_font(fontsize)
    bbox = draw.textbbox((0, 0), name, font=font, stroke_width=6)
    # Canto superior-esquerdo (abaixo do watermark central, longe da legenda)
    x = 60 - bbox[0]
    y = int(H * 0.12)
    draw.text((x, y), name, font=font, fill=(255, 214, 60, 255),
              stroke_width=6, stroke_fill=(0, 0, 0, 235))
    crop = img.getbbox()
    if not crop:
        return None
    img.crop(crop).save(out_png)
    return (out_png, crop[0], crop[1])


def render_watermark(text, tmp_dir, total_dur, fontsize=40):
    """Gera um watermark (handle do canal) fixo no topo, semitransparente.

    Retorna um spec de overlay {png,x,y,start,end} pro burn_subtitles.
    """
    from PIL import Image, ImageDraw
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = _load_font(fontsize)
    bbox = draw.textbbox((0, 0), text, font=font, stroke_width=4)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (W - tw) // 2 - bbox[0]
    y = int(H * 0.045)
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 200),
              stroke_width=4, stroke_fill=(0, 0, 0, 160))
    crop = img.getbbox()
    if not crop:
        return None
    out = Path(tmp_dir) / "_watermark.png"
    img.crop(crop).save(out)
    return {"png": str(out), "x": crop[0], "y": crop[1], "start": 0.0, "end": total_dur}


def censurar_video(video_in, windows, video_out, radius=45):
    """Censura com 3 níveis por janela de tempo (painéis +18).

    windows: lista de tuplas. Aceita 2 formatos:
      - (start, end)          → censura FORTE (retrocompat)
      - (start, end, nivel)   → 'forte' / 'leve' / 'intacto'
    nivel='forte': UM método só — tarja preta central (default) OU blur pesado.
                   Escolha por CENSURA_FORTE_MODO: 'tarja' (default) | 'blur'.
                   NUNCA os dois juntos.
    nivel='leve':  UM método só — shift de cor sutil (engana detector sem destruir cena).
    Uma passada só (re-encode do vídeo; áudio copiado).
    """
    parsed = []
    for w in windows:
        if len(w) == 3:
            s, e, niv = float(w[0]), float(w[1]), w[2]
        else:
            s, e, niv = float(w[0]), float(w[1]), "forte"
        if e > s and niv != "intacto":
            parsed.append((s, e, niv))
    if not parsed:
        import shutil as _shu
        _shu.copy2(str(video_in), str(video_out))
        return True
    fortes = [(s, e) for s, e, n in parsed if n == "forte"]
    leves = [(s, e) for s, e, n in parsed if n == "leve"]
    modo_forte = os.environ.get("CENSURA_FORTE_MODO", "tarja").strip().lower()
    filters = []
    if fortes:
        en_f = "+".join(f"between(t,{s:.2f},{e:.2f})" for s, e in fortes)
        if modo_forte == "blur":
            # MÉTODO ÚNICO: blur pesado na tela toda (sem tarja).
            filters.append(
                f"boxblur=luma_radius=28:luma_power=3:chroma_radius=28:chroma_power=3:enable='{en_f}'")
        else:
            # MÉTODO ÚNICO (default): tarja preta central sólida (sem blur junto).
            filters.append(
                f"drawbox=x=iw*0.10:y=ih*0.10:w=iw*0.80:h=ih*0.78:color=black:t=fill:enable='{en_f}'")
    if leves:
        # MÉTODO ÚNICO: grade de cor sutil (dessatura + leve brilho/contraste), sem blur/tarja.
        en_l = "+".join(f"between(t,{s:.2f},{e:.2f})" for s, e in leves)
        filters.append(f"hue=s=0.78:enable='{en_l}'")
        filters.append(f"eq=brightness=0.02:contrast=1.05:enable='{en_l}'")
    vf = ",".join(filters)
    cmd = [
        "ffmpeg", "-y", "-i", str(video_in),
        "-vf", vf,
        "-c:v", "libx264", "-preset", QP["preset"], "-crf", str(QP["crf"]), "-g", "30",
        "-c:a", "copy", "-movflags", "+faststart", "-pix_fmt", "yuv420p",
        str(video_out),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=1200)
        return Path(video_out).exists() and Path(video_out).stat().st_size > 0
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False


def render_subtitles_short(entries, tmp_dir, offsets=None, words_per_card=None, word_times=None):
    """Legenda DINÂMICA estilo Shorts/TikTok: 1-2 palavras na tela por vez.

    Em vez de mostrar a frase inteira (render_subtitles_progressive), mostra só
    um grupo de `words_per_card` palavras de cada vez, trocando rápido — deixa o
    vídeo mais dinâmico/moderno. Cada grupo vira 1 PNG curtinho centralizado.

    words_per_card: nº de palavras por card (default lê env SUB_WORDS_PER_CARD, senão 2).
    offsets: timestamps absolutos de início de cada entry (sincronia pós-xfade).
    word_times (WordBoundary): lista alinhada às entries; cada item é [[start,end,word],...]
      REAL do edge-tts (relativo ao clip). Quando presente e casa nº de palavras, usa o
      timing REAL de cada palavra (mata o drift legenda×balão); senão, estimativa por len().
    """
    import os as _os
    if words_per_card is None:
        try:
            words_per_card = max(1, int(_os.environ.get("SUB_WORDS_PER_CARD", "2")))
        except ValueError:
            words_per_card = 2
    tmp_dir = Path(tmp_dir)
    subs = []
    t = 0.0
    for i, (text, dur) in enumerate(entries):
        dur = max(0.4, float(dur or 0))
        start = offsets[i] if offsets else t
        if not offsets:
            t += dur
        words = (text or "").strip().split()
        if not words:
            continue
        # tempo de cada palavra proporcional ao tamanho (palavra longa dura mais)
        weights = [max(2, len(w)) for w in words]
        total_w = sum(weights)
        word_durs = [dur * (wt / total_w) for wt in weights]
        # WordBoundary: timing REAL de cada palavra (relativo ao clip) se veio o sidecar
        # e o nº de palavras casa. Mata o drift legenda×balão.
        wt_real = None
        if word_times and i < len(word_times) and word_times[i] and len(word_times[i]) == len(words):
            wt_real = word_times[i]
        # agrupa em cards de N palavras; cada palavra do card ACENDE amarelo no seu tempo
        for g in range(0, len(words), words_per_card):
            grp = words[g:g + words_per_card]
            card_text = " ".join(grp)
            for local_idx in range(len(grp)):
                png = tmp_dir / f"_capshort_{i:03d}_{g:03d}_{local_idx}.png"
                # highlight_idx é relativo ao card_text (que começa na palavra g)
                res = _render_caption_png(card_text, png, highlight_idx=local_idx)
                if not res:
                    continue
                _, x, y = res
                gi = g + local_idx
                if wt_real:
                    w_start = start + wt_real[gi][0]
                    w_end = start + wt_real[gi][1]
                else:
                    w_start = start + sum(word_durs[:gi])
                    w_end = start + sum(word_durs[:gi + 1])
                subs.append({"png": str(png), "x": x, "y": y, "start": w_start, "end": w_end})
    return subs


def burn_subtitles(video_in, subs, video_out, max_overlays_per_pass=30):
    """Sobrepõe os PNGs de legenda no vídeo em MÚLTIPLAS PASSADAS.

    O FFmpeg não suporta mais de ~100 overlays PNG numa única filter_complex
    (a cadeia de overlay fica enorme e o parser do FFmpeg estoura).

    SOLUÇÃO: divide os overlays em lotes de max_overlays_per_pass (default 30)
    e aplica em passadas sequenciais. Cada passada recebe o output da anterior.
    """
    if not subs:
        return False

    # Defesa: este burner é só de PNG. Ignora entradas sem "png" (ex: overlays webm
    # do karaokê HyperFrames, que são queimados em outro caminho) — evita KeyError 'png'.
    subs = [s for s in subs if isinstance(s, dict) and s.get("png")]
    if not subs:
        return False

    MAX_PER_PASS = max(max_overlays_per_pass, 100)  # Aumentado de 30 pra 100 (reduz passadas)
    batches = [subs[i:i + MAX_PER_PASS] for i in range(0, len(subs), MAX_PER_PASS)]
    temp_dir = Path(str(video_out)).parent
    temp_input = str(video_in)
    temp_outputs = []

    for batch_idx, batch in enumerate(batches):
        if batch_idx == len(batches) - 1:
            # Último batch → output final
            current_out = str(video_out)
        else:
            # Batch intermediário → arquivo temporário
            current_out = str(temp_dir / f"_subs_batch_{batch_idx:02d}.mp4")
            temp_outputs.append(current_out)

        inputs = ["-i", temp_input]
        for s in batch:
            inputs += ["-i", s["png"]]

        parts = []
        cur = "[0:v]"
        for idx, s in enumerate(batch, start=1):
            out = f"[v{idx}]"
            parts.append(
                f"{cur}[{idx}:v]overlay={s.get('x', 0)}:{s.get('y', 0)}:"
                f"enable='between(t,{s['start']:.2f},{s['end']:.2f})'{out}"
            )
            cur = out

        filter_complex = ";".join(parts)
        cmd = [
            "ffmpeg", "-y", *inputs,
            "-filter_complex", filter_complex,
            "-map", cur, "-map", "0:a?",
            "-c:v", "libx264", "-preset", QP["preset"], "-crf", str(QP["crf"]), "-g", "30",
            "-c:a", "copy",
            "-movflags", "+faststart", "-pix_fmt", "yuv420p",
            current_out,
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=1800)
            if not (Path(current_out).exists() and Path(current_out).stat().st_size > 0):
                return False
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False

        # Próxima passada usa o output atual como input
        temp_input = current_out

    # Cleanup: remover arquivos temporários
    for t in temp_outputs:
        try:
            Path(t).unlink()
        except Exception:
            pass

    return Path(video_out).exists() and Path(video_out).stat().st_size > 0


# Ganho da trilha por mood: romântica/calma/triste mais BAIXA; ação/tensão mais alta.
MOOD_MUSIC_GAIN = {
    "romantic_sexy": 0.55, "calm_chill": 0.60, "sad_emotional": 0.60,
    "neutral_chill": 0.72, "funny_lighthearted": 0.80,
    "tense_dramatic": 0.95, "action": 1.0,
}


def _mood_gain(mood):
    return MOOD_MUSIC_GAIN.get((mood or "").strip().lower(), 0.72)


# ── Nível-alvo da trilha (LUFS). Mais negativo = mais baixa/discreta. ──────────
# O usuário pediu trilha "naturalmente baixa, mas NIVELADA" entre faixas (uma de
# game e uma romântica calma têm masterização nativa diferente; o loudnorm iguala
# as duas pro MESMO volume percebido). -28 LUFS = bem atrás da narração.
MUSIC_TARGET_LUFS = -28.0


def add_background_music(video_path, music_path, out_path,
                         music_volume=0.10, fade_in=3, fade_out=3,
                         music_lufs=MUSIC_TARGET_LUFS, extra_gain=1.0,
                         duck=True):
    """Mixa UMA trilha de fundo no vídeo, com loudness nivelada e ducking.

    Conceito (o que cada parte resolve):
    - `loudnorm=I=music_lufs` → mede a loudness real da faixa e a traz pro alvo.
      É isto que NIVELA faixas com masterização diferente (game alta vs romântica
      baixa saem no mesmo volume percebido). Aplicado UMA vez só por faixa.
    - `volume=extra_gain` → ajuste fino POR MOOD aplicado DEPOIS do loudnorm
      (romântica/calma um pouco mais baixa, ação um pouco mais alta). Como vem
      depois do loudnorm, a hierarquia por mood não é desfeita.
    - Ducking BIDIRECIONAL: a música abaixa quando há narração
      (`sidechaincompress`) E sobe nos trechos sem diálogo. O lado "sobe no
      silêncio" vem de um ganho base maior + o sidechain só puxa pra baixo na voz.

    Parâmetros:
    - music_lufs=None  → PULA o loudnorm (usar quando a faixa JÁ foi normalizada
      antes, pra não medir/achatar duas vezes).
    - duck=False       → mixa sem ducking (trilha constante).
    """
    if not music_path or not Path(music_path).exists():
        # Sem trilha disponível: copia o vídeo como está (não é erro fatal).
        subprocess.run(["cp", str(video_path), str(out_path)], check=True)
        return True

    # Duração do vídeo (pra loopar a trilha e posicionar o fade-out).
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "csv=p=0", str(video_path)],
            capture_output=True, text=True, timeout=10,
        )
        video_dur = float(result.stdout.strip())
    except Exception:
        video_dur = 60.0

    # 1) loudnorm (nivela) — só se music_lufs definido.
    norm = f"loudnorm=I={music_lufs}:TP=-2:LRA=11," if music_lufs is not None else ""

    # 2) Monta a faixa de música: loop infinito → corta no tamanho do vídeo →
    #    nivela (loudnorm) → ganho por mood (extra_gain) → fade in/out nas pontas.
    music_chain = (
        f"[1:a]aloop=loop=-1:size=3e+07,atrim=0:{video_dur},"
        f"{norm}volume={extra_gain:.3f},"
        f"afade=t=in:st=0:d={fade_in},"
        f"afade=t=out:st={video_dur - fade_out}:d={fade_out}[music];"
    )

    if duck:
        # 3) Ducking: a narração (stream 0) comprime a música quando há voz.
        #    threshold baixo + ratio alto = a música "deita" sob a fala e volta a
        #    subir sozinha nos silêncios (release longo = subida suave).
        music_filter = (
            music_chain +
            f"[music][0:a]sidechaincompress=threshold=0.05:ratio=12:attack=20:release=350[music_ducked];"
            f"[0:a][music_ducked]amix=inputs=2:duration=first:dropout_transition=2[aout]"
        )
    else:
        music_filter = (
            music_chain +
            f"[0:a][music]amix=inputs=2:duration=first:dropout_transition=2[aout]"
        )

    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-i", str(music_path),
        "-filter_complex", music_filter,
        "-map", "0:v", "-map", "[aout]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", QP["audio_bitrate"], "-ar", "44100", "-ac", "2",
        "-shortest",
        str(out_path),
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=180)
        return True
    except Exception as e:
        # Qualquer falha no mix → entrega o vídeo sem trilha (nunca perde o vídeo).
        subprocess.run(["cp", str(video_path), str(out_path)], check=True)
        return True


def build_clip_animated(img_path, audio_path, out_path, panel_idx, effects_mgr, duration=None,
                        transition_type=None, sfx_file=None):
    """Cria clip animado de um painel manga — simula movimento sutil dos personagens.

    Técnicas aplicadas via FFmpeg:
    1. Breathing effect — zoom sinusoidal sutil (1.0→1.02) simulando respiração
    2. Parallax/Ken Burns com leve rotação — drift x/y + rotação (-0.5° a 0.5°)
    3. Hair/cloth flutter — deslocamento horizontal variável (mais no topo, menos na base)

    Para painéis altos (manhwa strips): pan vertical com breathing sobreposto.
    Para painéis médios/quadrados: background blur + animação no foreground.

    Fallback: se falhar/timeout, chama build_clip normal.
    """
    from PIL import Image
    img = Image.open(img_path)
    pw, ph = img.size

    if duration is None:
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                 "-of", "csv=p=0", str(audio_path)],
                capture_output=True, text=True, timeout=10,
            )
            duration = float(result.stdout.strip())
        except Exception:
            duration = 4.0
    duration = max(duration, 1.5)
    frames = int(duration * FPS)

    # Escolher cor e vinheta
    color = effects_mgr.pick_color()
    color_filter = color["filter"] if isinstance(color, dict) else color
    vignette = effects_mgr.pick_vignette()
    vignette_filter = vignette if isinstance(vignette, str) else (
        vignette["filter"] if isinstance(vignette, dict) else None)

    # Ratio da imagem vs canvas
    img_ratio = ph / pw

    # Animated zoompan: breathing + drift (sinusoidal)
    # Breathing cycle ~3s, drift cycle ~4s
    # z oscila entre 1.0 e 1.02 (sutil)
    # x drift: ±2 pixels sinusoidal
    # y drift: ±1 pixel sinusoidal (mais lento)
    animated_zoom_filter = (
        f"zoompan="
        f"z='1+0.02*sin(2*PI*on/({FPS}*3))':"
        f"x='iw/2-(iw/zoom/2)+2*sin(2*PI*on/({FPS}*4))':"
        f"y='ih/2-(ih/zoom/2)+1*sin(2*PI*on/({FPS}*5))':"
        f"d={frames}:s={W}x{H}:fps={FPS}"
    )

    # Para painéis altos: pan vertical com breathing sobreposto
    animated_tall_filter = (
        f"zoompan="
        f"z='1.25+0.02*sin(2*PI*on/({FPS}*3))':"
        f"x='iw/2-(iw/zoom/2)+2*sin(2*PI*on/({FPS}*4))':"
        f"y='if(lte(on,{FPS}),0,min(ih-ih/zoom,(on-{FPS})*3))+1*sin(2*PI*on/({FPS}*5))':"
        f"d={frames}:s={W}x{H}:fps={FPS}"
    )

    if img_ratio > 2.0:
        # Painel ALTO — pan vertical animado
        prescale = "scale=1080:-1"
        filters = [prescale, animated_tall_filter, color_filter]
        if vignette_filter:
            filters.append(vignette_filter)
        filters.append("format=yuv420p")
        filter_chain = ",".join(filters)
        filter_complex = f"[0:v]{filter_chain}[v]"
        extra_inputs = []
    else:
        # Painel médio/quadrado — background blur + foreground animado
        bg_path = Path(str(out_path) + "_bg.jpg")
        from PIL import ImageFilter, ImageEnhance

        # Cover-crop pro background
        scale_w = W / pw
        scale_h = H / ph
        scale = max(scale_w, scale_h)
        new_w = int(pw * scale)
        new_h = int(ph * scale)
        bg = img.resize((new_w, new_h), Image.LANCZOS)
        left = (new_w - W) // 2
        top = (new_h - H) // 2
        bg = bg.crop((left, top, left + W, top + H))
        bg = bg.filter(ImageFilter.GaussianBlur(radius=40))
        bg = ImageEnhance.Brightness(bg).enhance(0.35)
        bg.save(str(bg_path), quality=70)

        # Foreground com animação: scale to fit + color + animated zoompan
        # Para o foreground, usamos zoompan no input original pra criar animação
        # depois overlay no background
        fg_filter = (
            f"scale={W}:{H}:force_original_aspect_ratio=decrease,"
            f"{color_filter}"
        )
        if vignette_filter:
            fg_filter += f",{vignette_filter}"

        # O zoompan é aplicado na imagem foreground antes do overlay
        # Precisamos redimensionar pro tamanho que cabe no canvas
        fit_w = min(W, int(pw * (H / ph))) if img_ratio > (H / W) else W
        fit_h = min(H, int(ph * (W / pw))) if img_ratio <= (H / W) else H

        fg_animated_filter = (
            f"zoompan="
            f"z='1+0.02*sin(2*PI*on/({FPS}*3))':"
            f"x='iw/2-(iw/zoom/2)+2*sin(2*PI*on/({FPS}*4))':"
            f"y='ih/2-(ih/zoom/2)+1*sin(2*PI*on/({FPS}*5))':"
            f"d={frames}:s={fit_w}x{fit_h}:fps={FPS}"
        )

        filter_complex = (
            f"[0:v]scale={W}:{H}[bg];"
            f"[1:v]{fg_animated_filter},{color_filter}"
            f"{',' + vignette_filter if vignette_filter else ''}[fg];"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]"
        )
        extra_inputs = ["-r", str(FPS), "-loop", "1", "-t", f"{duration:.2f}", "-i", str(bg_path)]

    if extra_inputs:
        cmd = [
            "ffmpeg", "-y",
            *extra_inputs,
            "-r", str(FPS), "-loop", "1", "-t", f"{duration:.2f}", "-i", str(img_path),
            "-i", str(audio_path),
            "-filter_complex", filter_complex,
            "-map", "[v]", "-map", "2:a",
            "-r", str(FPS),
            "-c:v", "libx264", "-preset", QP["preset"], "-crf", str(QP["crf"]), "-g", "30",
            "-c:a", "aac", "-b:a", QP["audio_bitrate"], "-ar", "44100", "-ac", "2",
            "-pix_fmt", "yuv420p", "-t", f"{duration:.2f}",
            str(out_path),
        ]
    else:
        cmd = [
            "ffmpeg", "-y",
            "-r", str(FPS), "-loop", "1", "-t", f"{duration:.2f}", "-i", str(img_path),
            "-i", str(audio_path),
            "-filter_complex", filter_complex,
            "-map", "[v]", "-map", "1:a",
            "-r", str(FPS),
            "-c:v", "libx264", "-preset", QP["preset"], "-crf", str(QP["crf"]), "-g", "30",
            "-c:a", "aac", "-b:a", QP["audio_bitrate"], "-ar", "44100", "-ac", "2",
            "-pix_fmt", "yuv420p", "-t", f"{duration:.2f}",
            str(out_path),
        ]

    try:
        cmd = apply_effects_to_cmd(cmd, transition_type, sfx_file, duration)
        subprocess.run(cmd, check=True, capture_output=True, timeout=180)
        if extra_inputs:
            bg_path.unlink(missing_ok=True)
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        if extra_inputs:
            bg_path.unlink(missing_ok=True)
        # Fallback: tentar build_clip normal
        return build_clip(img_path, audio_path, out_path, panel_idx, effects_mgr, duration, transition_type, sfx_file)


# Subpasta cuja simples PRESENÇA do arquivo marca a trilha como prioritária.
# O usuário controla a prioridade no Explorer: arrastar o .mp3 pra dentro de
# `trilhas/prioritarias/` aumenta a chance dele tocar; tirar de lá volta ao normal.
# Não precisa editar JSON nenhum — a pasta é a fonte da verdade da prioridade.
PRIORITARIAS_SUBDIR = "prioritarias"


def _is_prioritaria(file_name, trilhas_dir):
    """True se existe uma cópia do arquivo dentro de trilhas/prioritarias/."""
    if not file_name:
        return False
    return (Path(trilhas_dir) / PRIORITARIAS_SUBDIR / file_name).exists()


def _resolve_track(file_name, trilhas_dir):
    """Acha o .mp3 da trilha, olhando PRIMEIRO em prioritarias/ e depois na raiz.

    Assim o usuário pode mover o arquivo livremente entre as duas pastas sem
    quebrar a reprodução — onde estiver, o código encontra.
    Retorna um Path existente, ou None se não achar em lugar nenhum.
    """
    if not file_name:
        return None
    prio = Path(trilhas_dir) / PRIORITARIAS_SUBDIR / file_name
    if prio.exists():
        return prio
    raiz = Path(trilhas_dir) / file_name
    return raiz if raiz.exists() else None


def _get_track_info(track_data, trilhas_dir=None):
    """Sorteia UMA trilha da lista do mood, com peso (weighted random).

    Uma trilha ganha peso 3 (3× mais chance) se QUALQUER destes for verdade:
    - tem "priority": true ou "favorite": true no moods.json, OU
    - o arquivo dela está dentro da pasta trilhas/prioritarias/ (controle manual
      do usuário pelo Explorer — ver _is_prioritaria).
    Trilhas comuns têm peso 1.
    """
    if isinstance(track_data, list):
        if not track_data:
            return {}
        weighted = []
        for t in track_data:
            in_folder = _is_prioritaria(t.get("file"), trilhas_dir) if trilhas_dir else False
            weight = 3 if (t.get("priority") or t.get("favorite") or in_folder) else 1
            weighted.extend([t] * weight)
        return random.choice(weighted)
    return track_data


def add_dynamic_music(video_path, locucoes, out_path, trilhas_dir,
                      music_volume=0.08, block_size=8):
    """Adiciona trilha dinâmica que muda conforme o clima do manhwa.

    Divide as locuções em blocos, detecta o mood de cada bloco,
    e monta uma trilha composta com crossfade entre músicas diferentes.
    """
    import json as _json

    trilhas_dir = Path(trilhas_dir)
    moods_file = trilhas_dir / "moods.json"

    # PREVIEW: força UMA trilha em todo o vídeo (config externa, sem editar código).
    try:
        import preview_config as _pv
        _ft = _pv.force_trilha()
    except Exception:
        _ft = None
    if _ft:
        _forced = _resolve_track(_ft, trilhas_dir) or (trilhas_dir / _ft)
        if Path(_forced).exists():
            import sys as _sys
            print(f"  [PREVIEW] trilha forçada: {Path(_forced).name}", file=_sys.stderr, flush=True)
            return add_background_music(video_path, _forced, out_path, music_volume,
                                        extra_gain=0.0, duck=True)
        else:
            import sys as _sys
            print(f"  [PREVIEW] trilha '{_ft}' não encontrada, seguindo normal", file=_sys.stderr, flush=True)

    if not moods_file.exists():
        # Fallback: trilha única
        default_track = trilhas_dir / "neutral_chill.mp3"
        if not default_track.exists():
            default_track = trilhas_dir.parent / "trilha.mp3"
        return add_background_music(video_path, default_track, out_path, music_volume)

    moods_data = _json.loads(moods_file.read_text())
    tracks = moods_data.get("tracks", {})

    # Obter duração do vídeo
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "csv=p=0", str(video_path)],
            capture_output=True, text=True, timeout=10,
        )
        video_dur = float(result.stdout.strip())
    except Exception:
        video_dur = 60.0

    # Detectar mood por bloco de painéis
    n_panels = len(locucoes)
    blocks = []
    for i in range(0, n_panels, block_size):
        block_text = " ".join(
            loc.get("text", "") for loc in locucoes[i:i+block_size]
        )
        mood = detect_mood_from_text(block_text)
        blocks.append(mood)

    if not blocks:
        blocks = ["neutral_chill"]

    # Se todos os blocos têm o mesmo mood, usar trilha única
    unique_moods = list(dict.fromkeys(blocks))  # preservar ordem

    if len(unique_moods) == 1:
        track_key = unique_moods[0]
        track_info = _get_track_info(tracks.get(track_key, {}), trilhas_dir)
        # Resolve olhando prioritarias/ primeiro; cai em neutral_chill se sumir.
        track_file = _resolve_track(track_info.get("file", "neutral_chill.mp3"), trilhas_dir) \
            or _resolve_track("neutral_chill.mp3", trilhas_dir)
        # Lyria fallback pra mood unico
        if not track_file and os.environ.get("LYRIA_MOOD_FALLBACK", "0") == "1":
            try:
                import omniroute_music
                generated = omniroute_music.generate_mood_track(track_key)
                if generated:
                    track_file = generated
            except Exception:
                pass
        if not track_file:
            track_file = trilhas_dir / "neutral_chill.mp3"
        # mood único: nivela uma vez aqui, com ganho do mood e ducking bidirecional.
        return add_background_music(video_path, track_file, out_path, music_volume,
                                    extra_gain=_mood_gain(track_key), duck=True)

    # Trilha composta: concatenar as trilhas por bloco com crossfade
    # Duração de cada bloco = video_dur / len(blocks)
    block_dur = video_dur / len(blocks)
    # crossfade entre blocos: clamp pra nunca exceder o bloco (blocos curtos).
    crossfade = max(0.5, min(2.0, block_dur * 0.4))

    # LOG DETALHADO da trilha dinâmica
    import sys
    print(f"  [TRILHA] Vídeo: {video_dur:.1f}s | Blocos: {len(blocks)} | Duração/bloco: {block_dur:.1f}s", file=sys.stderr, flush=True)
    print(f"  [TRILHA] Moods detectados: {blocks}", file=sys.stderr, flush=True)
    print(f"  [TRILHA] Moods únicos: {unique_moods}", file=sys.stderr, flush=True)

    # Montar trilha composta concatenando trechos de cada música
    tmp_dir = Path(str(video_path)).parent
    composed_music = tmp_dir / "_composed_music.mp3"

    # Extrair trecho de cada trilha
    segments = []
    for i, mood in enumerate(blocks):
        track_key = mood
        track_data = tracks.get(track_key, tracks.get("neutral_chill", {}))
        track_info = _get_track_info(track_data, trilhas_dir)
        # Resolve olhando prioritarias/ primeiro; cai em neutral_chill se sumir.
        track_file = _resolve_track(track_info.get("file", "neutral_chill.mp3"), trilhas_dir) \
            or _resolve_track("neutral_chill.mp3", trilhas_dir)
        # Lyria fallback: gerar trilha por mood se não tem local
        if not track_file and os.environ.get("LYRIA_MOOD_FALLBACK", "0") == "1":
            try:
                import omniroute_music
                generated = omniroute_music.generate_mood_track(mood)
                if generated:
                    track_file = generated
            except Exception:
                pass
        if not track_file:
            continue
        print(f"  [TRILHA] Bloco {i+1}/{len(blocks)}: mood={mood} → {track_file.name}", file=sys.stderr, flush=True)

        seg_path = tmp_dir / f"_music_seg_{i:02d}.mp3"
        # É TROCA de mood? (primeiro bloco conta como "entrada" também.)
        is_change = (i == 0) or (blocks[i] != blocks[i - 1])

        # Ganho por mood (hierarquia): romântica/calma mais baixa, ação mais alta.
        mood_gain = _mood_gain(mood)

        # Bump SÓ na troca: nos primeiros ~1.5s do bloco que estreia um mood novo,
        # a trilha sobe um pouco pra você perceber que a música mudou. Blocos que
        # repetem o mesmo mood do bloco anterior NÃO recebem bump.
        bump = "volume=1.6:enable='between(t,0,1.5)'," if is_change else ""

        # Nivelamento: loudnorm UMA vez aqui (por faixa) → mesmo volume percebido
        # entre faixas de masterização diferente. O composto final NÃO re-normaliza
        # (add_background_music recebe music_lufs=None), pra não medir duas vezes.
        # SEM afade aqui: o acrossfade entre segmentos faz a sobreposição (um sobe
        # enquanto o outro desce), então NÃO há buraco de silêncio na troca.
        # Cada segmento tem block_dur + crossfade de material pra haver overlap.
        start_offset = (i * 10) % max(1, int(track_info.get("duration_seconds", 60)) - int(block_dur))
        cmd = [
            "ffmpeg", "-y", "-ss", str(start_offset),
            "-i", str(track_file), "-t", f"{block_dur + crossfade:.1f}",
            "-af", (
                f"loudnorm=I={MUSIC_TARGET_LUFS}:TP=-2:LRA=11,"
                f"volume={mood_gain:.3f},"
                f"{bump}"
                f"aresample=44100"
            ),
            "-c:a", "libmp3lame", "-b:a", "128k",
            str(seg_path),
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=30)
            segments.append(seg_path)
        except Exception:
            pass

    if not segments:
        # Fallback
        track_file = trilhas_dir / "neutral_chill.mp3"
        return add_background_music(video_path, track_file, out_path, music_volume)

    # Concatenar segmentos com ACROSSFADE (sobreposição) — sem buraco de silêncio.
    # acrossfade junta 2 entradas por vez; encadeamos N segmentos numa só passada.
    if len(segments) == 1:
        subprocess.run(["cp", str(segments[0]), str(composed_music)], check=True)
    else:
        inputs = []
        for s in segments:
            inputs += ["-i", str(s)]
        # Encadeia: [0][1]acrossfade->[x1]; [x1][2]acrossfade->[x2]; ...
        parts = []
        prev = "[0:a]"
        for k in range(1, len(segments)):
            out_lbl = f"[x{k}]" if k < len(segments) - 1 else "[mout]"
            parts.append(
                f"{prev}[{k}:a]acrossfade=d={crossfade:.1f}:c1=tri:c2=tri{out_lbl}"
            )
            prev = out_lbl
        fc = ";".join(parts)
        cmd = ["ffmpeg", "-y", *inputs, "-filter_complex", fc,
               "-map", "[mout]", "-c:a", "libmp3lame", "-b:a", "160k",
               str(composed_music)]
        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=120)
        except Exception:
            # Fallback: concat seco (volta ao comportamento antigo, mas não perde a trilha)
            seg_list = tmp_dir / "_music_segments.txt"
            with open(seg_list, "w") as f:
                for s in segments:
                    f.write(f"file '{s}'\n")
            try:
                subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0",
                                "-i", str(seg_list), "-c", "copy", str(composed_music)],
                               check=True, capture_output=True, timeout=60)
            except Exception:
                subprocess.run(["cp", str(segments[0]), str(composed_music)], check=True)

    # Ponto O: stinger (riser) nos pontos de TROCA de clima
    change_times = [i * block_dur for i in range(1, len(blocks)) if blocks[i] != blocks[i - 1]]
    riser = SFX_DIR / "riser.wav"
    if change_times and riser.exists():
        stung = tmp_dir / "_music_stung.mp3"
        inputs = ["-i", str(composed_music)]
        parts = []
        for k, t in enumerate(change_times):
            inputs += ["-i", str(riser)]
            ms = int(t * 1000)
            parts.append(f"[{k+1}:a]adelay={ms}|{ms},volume=0.5[s{k}]")
        mix_in = "".join(f"[s{k}]" for k in range(len(change_times)))
        fc = ";".join(parts) + (f";[0:a]{mix_in}amix=inputs={len(change_times)+1}:"
                                f"duration=first:dropout_transition=0[mout]")
        try:
            subprocess.run(["ffmpeg", "-y", *inputs, "-filter_complex", fc,
                            "-map", "[mout]", "-c:a", "libmp3lame", "-b:a", "160k", str(stung)],
                           check=True, capture_output=True, timeout=60)
            if stung.exists() and stung.stat().st_size > 0:
                stung.replace(composed_music)
        except Exception:
            pass

    # Mix final: o composto JÁ foi nivelado por segmento (loudnorm) e já tem o
    # ganho por mood. Por isso music_lufs=None (não re-normalizar) e extra_gain=1.0
    # (não aplicar ganho de novo). O ducking bidirecional acontece aqui.
    result = add_background_music(video_path, composed_music, out_path,
                                  music_volume, music_lufs=None,
                                  extra_gain=1.0, duck=True)

    # Cleanup
    for s in segments:
        try:
            s.unlink()
        except Exception:
            pass
    for f in [tmp_dir / "_music_segments.txt", composed_music]:
        try:
            f.unlink()
        except Exception:
            pass

    return result

