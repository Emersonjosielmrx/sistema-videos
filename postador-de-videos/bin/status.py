#!/usr/bin/env python3
"""status.py — Relatório rápido do estado do projeto hipercool-inferior.

Uso: python bin/status.py
"""
import json
from pathlib import Path
from datetime import datetime

PROJECT_DIR = Path(__file__).resolve().parent.parent
PANELS_DIR = PROJECT_DIR / "workspace" / "panels"
VIDEOS_DIR = PROJECT_DIR / "workspace" / "videos"
TRILHAS_DIR = PROJECT_DIR / "workspace" / "assets" / "trilhas"
SFX_DIR = PROJECT_DIR / "workspace" / "assets" / "sfx"
SFX_MEMES_DIR = PROJECT_DIR / "workspace" / "assets" / "sfx_memes"
SFX_FOLEY_DIR = PROJECT_DIR / "workspace" / "assets" / "sfx_foley"
MEMES_DIR = PROJECT_DIR / "workspace" / "assets" / "memes_img" / "memes"

def main():
    print(f"\n{'='*60}")
    print(f"  HIPERCOOL-INFERIOR — Status ({datetime.now().strftime('%Y-%m-%d %H:%M')})")
    print(f"{'='*60}")

    # Painéis
    print(f"\n  PAINEIS CORTADOS:")
    caps = sorted(PANELS_DIR.glob("the-meek-cat-cap*"))
    total_panels = 0
    for cap in caps:
        n = len(list(cap.glob("*.jpg")))
        total_panels += n
        print(f"    {cap.name}: {n} painéis")
    print(f"    TOTAL: {total_panels} painéis em {len(caps)} capítulos")

    # Vídeos
    print(f"\n  VIDEOS GERADOS:")
    videos = sorted(VIDEOS_DIR.glob("hipercool_*ULTIMO*.mp4"))
    for v in videos:
        size_mb = v.stat().st_size / (1024*1024)
        print(f"    {v.name} ({size_mb:.0f} MB)")
    if not videos:
        print("    Nenhum vídeo final")

    # Assets
    print(f"\n  ASSETS:")
    trilhas = list(TRILHAS_DIR.glob("*.mp3")) if TRILHAS_DIR.exists() else []
    sfx = list(SFX_DIR.glob("*.*")) if SFX_DIR.exists() else []
    sfx_memes = list(SFX_MEMES_DIR.glob("*.*")) if SFX_MEMES_DIR.exists() else []
    sfx_foley = list(SFX_FOLEY_DIR.glob("*.*")) if SFX_FOLEY_DIR.exists() else []
    memes = list(MEMES_DIR.glob("*.mp4")) if MEMES_DIR.exists() else []
    print(f"    Trilhas: {len(trilhas)}")
    print(f"    SFX: {len(sfx)} base + {len(sfx_memes)} memes + {len(sfx_foley)} foley")
    print(f"    Memes vídeo: {len(memes)}")

    # Caps sem vídeo
    print(f"\n  CAPS SEM VIDEO (precisam gerar):")
    generated_caps = set()
    for v in videos:
        for i in range(1, 20):
            if f"capitulo-{i}" in v.name or f"cap{i:02d}" in v.name:
                generated_caps.add(i)
    for cap in caps:
        try:
            num = int(cap.name.split("cap")[1])
        except (ValueError, IndexError):
            continue
        if num not in generated_caps:
            n = len(list(cap.glob("*.jpg")))
            print(f"    cap{num:02d}: {n} painéis (pronto pra gerar)")

    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    main()
