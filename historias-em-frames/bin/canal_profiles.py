import sys
import os
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hp_common import PROJECT_DIR, log

PROFILES_JSON_PATH = PROJECT_DIR / "workspace" / "canal_profiles.json"

DEFAULT_PROFILES = {
    "default": {
        "nome": "Inovare Stories",
        "watermark": "@InovareStories",
        "watermark_pos": "bottom_right",
        "cores": {"primaria": "#FF6B35", "secundaria": "#1A1A2E", "texto": "#FFFFFF"},
        "fonte": "Impact",
        "generos_preferidos": ["superacao", "terror", "misterio", "drama"],
        "frequencia_post": "daily",
        "intro_style": "fade_title",
        "outro_cta": "Se inscreva e ative o sininho!",
    },
    "terror_br": {
        "nome": "Terror BR Stories",
        "watermark": "@TerrorBRStories",
        "watermark_pos": "bottom_right",
        "cores": {"primaria": "#8B0000", "secundaria": "#0D0D0D", "texto": "#CCCCCC"},
        "fonte": "Impact",
        "generos_preferidos": ["terror", "misterio"],
        "frequencia_post": "3x_week",
        "intro_style": "glitch_dark",
        "outro_cta": "Curte se sentiu medo...",
    },
    "motivacao_diaria": {
        "nome": "Motivação Diária",
        "watermark": "@MotivacaoDiaria",
        "watermark_pos": "top_right",
        "cores": {"primaria": "#FFD700", "secundaria": "#1B1B2F", "texto": "#FFFFFF"},
        "fonte": "Arial Bold",
        "generos_preferidos": ["motivacional", "superacao", "religioso"],
        "frequencia_post": "daily",
        "intro_style": "sunrise_glow",
        "outro_cta": "Marca alguém que precisa ouvir isso!",
    },
}

def load_profiles():
    if PROFILES_JSON_PATH.exists():
        try:
            with open(PROFILES_JSON_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            log.warning(f"Erro ao ler {PROFILES_JSON_PATH}: {e}, usando defaults.")
    return DEFAULT_PROFILES.copy()

def get_profile(name=None):
    if name is None:
        name = os.environ.get("CANAL_PROFILE", "default")

    profiles = load_profiles()
    if name in profiles:
        return profiles[name]

    log.warning(f"Perfil '{name}' não encontrado, usando 'default'.")
    return profiles.get("default", DEFAULT_PROFILES["default"])

def save_profile(name, profile_data):
    profiles = load_profiles()
    profiles[name] = profile_data

    PROFILES_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(PROFILES_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(profiles, f, indent=4, ensure_ascii=False)

    log.info(f"Perfil '{name}' salvo com sucesso.")

def get_watermark_filter(profile=None):
    p = get_profile(profile)
    text = p.get("watermark", "")
    if not text:
        return ""

    pos = p.get("watermark_pos", "bottom_right")
    # Tenta usar valor real ou fallback simplificado
    font = p.get("fonte", "Arial")
    cor_texto = p.get("cores", {}).get("texto", "#FFFFFF")

    if pos == "bottom_right":
        x_y = "x=w-tw-20:y=h-th-20"
    elif pos == "bottom_left":
        x_y = "x=20:y=h-th-20"
    elif pos == "top_right":
        x_y = "x=w-tw-20:y=20"
    elif pos == "top_left":
        x_y = "x=20:y=20"
    else:
        x_y = "x=w-tw-20:y=h-th-20"

    return f"drawtext=text='{text}':fontcolor={cor_texto}:fontsize=24:fontfile='{font}':{x_y}:alpha=0.6"

def get_intro_config(profile=None):
    p = get_profile(profile)
    return {
        "style": p.get("intro_style", "fade_title"),
        "primary_color": p.get("cores", {}).get("primaria", "#FFFFFF"),
        "secondary_color": p.get("cores", {}).get("secundaria", "#000000"),
        "channel_name": p.get("nome", "")
    }

def get_outro_config(profile=None):
    p = get_profile(profile)
    return {
        "cta_text": p.get("outro_cta", ""),
        "cta_color": p.get("cores", {}).get("texto", "#FFFFFF"),
        "bg_color": p.get("cores", {}).get("secundaria", "#000000")
    }

def list_profiles():
    profiles = load_profiles()
    return list(profiles.keys())
