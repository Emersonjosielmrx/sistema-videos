# -*- coding: utf-8 -*-
"""status.py — Status report rápido do projeto historias-em-frames.

Mostra: vídeos gerados, cache stats, últimas gerações, fila pendente.
"""
import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent))

PROJECT_DIR = Path(__file__).resolve().parent.parent
VIDEOS_DIR = PROJECT_DIR / "workspace" / "videos"
SHORTS_DIR = VIDEOS_DIR / "_shorts"
QUARANTINE_DIR = VIDEOS_DIR / "_quarantine"
NARR_CACHE = PROJECT_DIR / "workspace" / "narration_cache"
IMG_CACHE = PROJECT_DIR / "workspace" / "images"
QUEUE_PROGRESS = PROJECT_DIR / "workspace" / "queue_progress.json"
NIGHT_LOG = PROJECT_DIR / "logs" / "night-shift.md"


def _count_videos():
    """Conta vídeos por gênero."""
    counts = {}
    if not VIDEOS_DIR.exists():
        return counts
    for d in VIDEOS_DIR.iterdir():
        if d.is_dir() and not d.name.startswith("_"):
            n = len(list(d.rglob("*_FINAL*.mp4")))
            if n > 0:
                counts[d.name] = n
    return counts


def _recent_videos(n=5):
    """Últimos N vídeos gerados (por mtime)."""
    videos = list(VIDEOS_DIR.rglob("*_FINAL*.mp4"))
    videos.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return videos[:n]


def _cache_stats():
    """Stats de cache."""
    narr = len(list(NARR_CACHE.glob("*.wav"))) if NARR_CACHE.exists() else 0
    imgs = len(list(IMG_CACHE.rglob("*.png"))) if IMG_CACHE.exists() else 0
    return {"narration": narr, "images": imgs}


def _queue_status():
    """Status da fila."""
    if QUEUE_PROGRESS.exists():
        try:
            p = json.loads(QUEUE_PROGRESS.read_text(encoding="utf-8"))
            return f"em andamento (ultimo job: {p.get('last_index', -1) + 1})"
        except Exception:
            pass
    return "sem fila ativa"


def show_status():
    print("=" * 60)
    print("STATUS — Historias em Frames")
    print(f"  Data: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"  Projeto: {PROJECT_DIR}")
    print("=" * 60)

    # Vídeos por gênero
    counts = _count_videos()
    total = sum(counts.values())
    print(f"\nVideos gerados: {total} total")
    for g, n in sorted(counts.items()):
        print(f"  {g}: {n}")

    # Shorts
    n_shorts = len(list(SHORTS_DIR.rglob("*.mp4"))) if SHORTS_DIR.exists() else 0
    print(f"\nShorts: {n_shorts}")

    # Quarentena
    n_quarantine = len(list(QUARANTINE_DIR.glob("*.mp4"))) if QUARANTINE_DIR.exists() else 0
    print(f"Quarentena: {n_quarantine}")

    # Cache
    cache = _cache_stats()
    print(f"\nCache:")
    print(f"  Narration: {cache['narration']} audios")
    print(f"  Images: {cache['images']} imagens")

    # Últimos vídeos
    recent = _recent_videos(5)
    if recent:
        print(f"\nUltimos videos:")
        for v in recent:
            mtime = datetime.fromtimestamp(v.stat().st_mtime).strftime("%m-%d %H:%M")
            size = v.stat().st_size / (1024 * 1024)
            print(f"  [{mtime}] {v.parent.name}/{v.name} ({size:.1f}MB)")

    # Fila
    print(f"\nFila: {_queue_status()}")

    # Night shift
    if NIGHT_LOG.exists():
        lines = NIGHT_LOG.read_text(encoding="utf-8").strip().splitlines()
        last = lines[-1] if lines else "sem registro"
        print(f"Night shift (ultimo): {last}")

    print("=" * 60)


if __name__ == "__main__":
    show_status()
