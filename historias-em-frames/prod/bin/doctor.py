# -*- coding: utf-8 -*-
"""doctor.py — Diagnóstico rápido do projeto historias-em-frames.

Verifica: Python, ffmpeg, dependências, paths, caches, assets, configuração.
Roda em <5s e mostra o que está OK vs quebrado.
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

PROJECT_DIR = Path(__file__).resolve().parent.parent
BIN_DIR = PROJECT_DIR / "bin"
# Python do venv da propria pista (sem depender de outro projeto).
_env_py = os.environ.get("HEF_PYTHON")
_local_py = PROJECT_DIR / "venv" / "Scripts" / "python.exe"
VENV_PYTHON = (Path(_env_py) if _env_py and Path(_env_py).exists()
               else _local_py if _local_py.exists()
               else Path(sys.executable))


def check(label, condition, detail=""):
    status = "OK" if condition else "FAIL"
    marker = "+" if condition else "!"
    line = f"  [{marker}] {label}"
    if detail:
        line += f" — {detail}"
    print(line)
    return condition


def run_doctor():
    print("=" * 60)
    print("DOCTOR — Historias em Frames")
    print(f"  Projeto: {PROJECT_DIR}")
    print("=" * 60)
    fails = 0

    # Python
    py_ok = VENV_PYTHON.exists()
    if not check("Python venv", py_ok, str(VENV_PYTHON)):
        fails += 1

    # ffmpeg
    ff = shutil.which("ffmpeg")
    if not check("ffmpeg", ff is not None, ff or "NAO ENCONTRADO"):
        fails += 1

    # ffprobe
    fp = shutil.which("ffprobe")
    if not check("ffprobe", fp is not None, fp or "NAO ENCONTRADO"):
        fails += 1

    # Módulos críticos
    critical_modules = [
        "story_pipeline", "story_writer", "image_generator", "edge_tts_engine",
        "effects_engine", "fx_clips", "fx_detect", "fx_subtitles", "fx_assets",
        "panel_effects", "parallax_engine", "panel_classifier", "motion_director",
        "elemental_transitions", "hp_common", "auto_validate", "viralizador",
        # 2026-10-02: diretor de cena, rasgo (divisoria), legenda ASS, audio final, memes, gateway
        "diretor_cena", "fx_divisoria", "fx_legendas_ass", "fx_audio_final",
        "memes_catalogo", "gateway_cfg",
    ]
    for mod in critical_modules:
        mod_file = BIN_DIR / f"{mod}.py"
        if not check(f"modulo {mod}", mod_file.exists()):
            fails += 1

    # Dirs
    dirs = [
        __import__("hp_common").VIDEOS_DIR,   # saida em hipercool-materiais
        PROJECT_DIR / "workspace" / "images",
        PROJECT_DIR / "workspace" / "narration_cache",
        PROJECT_DIR / "workspace" / "assets" / "trilhas",
        PROJECT_DIR / "workspace" / "assets" / "sfx",
        PROJECT_DIR / "workspace" / "tmp",
        PROJECT_DIR / "logs",
    ]
    for d in dirs:
        if not check(f"dir {d.name}", d.exists()):
            fails += 1

    # Assets trilhas
    trilhas_dir = PROJECT_DIR / "workspace" / "assets" / "trilhas"
    moods_json = trilhas_dir / "moods.json"
    n_trilhas = len(list(trilhas_dir.glob("*.mp3"))) if trilhas_dir.exists() else 0
    check("trilhas", n_trilhas > 0, f"{n_trilhas} mp3s")
    check("moods.json", moods_json.exists())

    # Assets SFX
    sfx_dir = PROJECT_DIR / "workspace" / "assets" / "sfx"
    n_sfx = len(list(sfx_dir.rglob("*.mp3"))) + len(list(sfx_dir.rglob("*.wav"))) if sfx_dir.exists() else 0
    check("SFX", n_sfx > 0, f"{n_sfx} arquivos")

    # Secrets
    secrets_dir = PROJECT_DIR / "secrets"
    check("secrets dir", secrets_dir.exists())
    gemini_keys = secrets_dir / "gemini_keys.json"
    check("gemini_keys.json", gemini_keys.exists())
    # gateway OmniRoute (roteiro, imagens, juizes): chave num lugar so
    try:
        sys.path.insert(0, str(BIN_DIR))
        import gateway_cfg
        if not check("secrets/omniroute.json (gateway)", gateway_cfg.ok(),
                     "base_url + api_key" if gateway_cfg.ok() else "FALTA — roteiro/imagens nao funcionam"):
            fails += 1
    except Exception as e:
        check("secrets/omniroute.json (gateway)", False, str(e))
        fails += 1

    # Novos recursos (legenda ASS, gatilhos de som, memes, CTA, copyright)
    assets = PROJECT_DIR / "workspace" / "assets"
    fontes = assets / "fonts"
    n_fontes = len(list(fontes.glob("*.ttf"))) if fontes.exists() else 0
    if not check("fontes da legenda ASS", n_fontes >= 3, f"{n_fontes} .ttf em assets/fonts"):
        fails += 1
    for nome, arq in (("gatilhos de som", PROJECT_DIR / "config" / "gatilhos_palavras.json"),
                      ("catalogo de memes", PROJECT_DIR / "config" / "memes_catalogo.json"),
                      ("frases de CTA", assets / "cta_frases.json"),
                      ("blocklist copyright", assets.resolve().parent / "_curadoria" / "copyright_blocklist.json")):
        check(nome, arq.exists(), "" if arq.exists() else f"NAO EXISTE: {arq}")

    # Cache stats
    narr_cache = PROJECT_DIR / "workspace" / "narration_cache"
    n_cached = len(list(narr_cache.glob("*.wav"))) if narr_cache.exists() else 0
    check("narration cache", True, f"{n_cached} audios em cache")

    # Proxies
    proxies = PROJECT_DIR / "secrets" / "proxies.txt"
    if proxies.exists():
        n_proxies = len([l for l in proxies.read_text().splitlines() if l.strip() and not l.startswith("#")])
        check("proxies.txt", n_proxies > 0, f"{n_proxies} proxies")
    else:
        check("proxies.txt", False, "NAO EXISTE")
        fails += 1

    print("=" * 60)
    if fails == 0:
        print("RESULTADO: Tudo OK")
    else:
        print(f"RESULTADO: {fails} problemas encontrados")
    print("=" * 60)
    return fails


if __name__ == "__main__":
    sys.exit(run_doctor())
