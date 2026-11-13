# -*- coding: utf-8 -*-
"""montar_fila.py — Monta a fila de postagem (o que postar, onde, quando).

Escaneia workspace/videos/ por vídeos prontos (não postados) e cria uma fila
ordenada por prioridade (gênero variado, shorts intercalados).
Output: workspace/posting_queue.json
"""
import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parent))

from hp_common import PROJECT_DIR, VIDEOS_DIR, log

QUEUE_FILE = PROJECT_DIR / "workspace" / "posting_queue.json"
POSTED_LOG = PROJECT_DIR / "logs" / "posted_videos.json"
SHORTS_DIR = VIDEOS_DIR / "_shorts"

# Slots de horário ideal pra postar (BRT)
POSTING_SLOTS = ["06:40", "09:00", "12:00", "15:00", "18:00", "20:00"]
MAX_PER_DAY = int(os.environ.get("MAX_POSTS_PER_DAY", "6"))


def _load_posted():
    if POSTED_LOG.exists():
        try:
            return json.loads(POSTED_LOG.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def _already_posted(video_path, posted):
    return any(p.get("video") == str(video_path) for p in posted)


def _find_ready_videos():
    """Encontra vídeos _ULTIMO (mais recentes) não postados."""
    posted = _load_posted()
    ready = []

    for genre_dir in VIDEOS_DIR.iterdir():
        if not genre_dir.is_dir() or genre_dir.name.startswith("_"):
            continue
        for video in genre_dir.rglob("*_ULTIMO.mp4"):
            if _already_posted(video, posted):
                continue
            # Busca metadata
            meta_candidates = list(video.parent.glob("*.json"))
            meta = {}
            for mc in meta_candidates:
                try:
                    m = json.loads(mc.read_text(encoding="utf-8"))
                    if m.get("video") or m.get("titulo"):
                        meta = m
                        break
                except Exception:
                    pass
            ready.append({
                "video": str(video),
                "genero": genre_dir.name,
                "titulo": meta.get("titulo_viral", meta.get("titulo", video.stem)),
                "hashtags": meta.get("hashtags", ""),
                "description": meta.get("hashtags", ""),
                "size_mb": round(video.stat().st_size / (1024 * 1024), 1),
                "created": datetime.fromtimestamp(video.stat().st_mtime).isoformat(),
            })

    return ready


def _find_ready_shorts():
    """Encontra shorts não postados."""
    posted = _load_posted()
    shorts = []

    if not SHORTS_DIR.exists():
        return shorts

    for meta_file in sorted(SHORTS_DIR.rglob("*.json")):
        try:
            meta = json.loads(meta_file.read_text(encoding="utf-8"))
            video_path = meta.get("file", "")
            if not video_path or not Path(video_path).exists():
                continue
            if _already_posted(video_path, posted):
                continue
            shorts.append({
                "video": video_path,
                "genero": "short",
                "titulo": meta.get("title", ""),
                "hashtags": meta.get("hashtags", ""),
                "description": meta.get("description", ""),
                "is_short": True,
                "size_mb": round(Path(video_path).stat().st_size / (1024 * 1024), 1),
            })
        except Exception:
            pass

    return shorts


def build_queue(max_per_day=None):
    """Monta fila intercalando gêneros e shorts."""
    max_d = max_per_day or MAX_PER_DAY
    videos = _find_ready_videos()
    shorts = _find_ready_shorts()

    # Intercala: video, short, video, short...
    queue = []
    vi, si = 0, 0

    # Varia gêneros (não postar 3 do mesmo gênero seguido)
    videos.sort(key=lambda x: x["genero"])
    generos_usados = []

    while (vi < len(videos) or si < len(shorts)) and len(queue) < max_d * 3:
        # Prefere video se não repetiu gênero
        if vi < len(videos):
            v = videos[vi]
            if generos_usados[-2:].count(v["genero"]) < 2:
                queue.append(v)
                generos_usados.append(v["genero"])
                vi += 1
                continue
            else:
                vi += 1

        # Short entre vídeos
        if si < len(shorts) and len(queue) % 2 == 1:
            queue.append(shorts[si])
            si += 1
            continue

        if vi < len(videos):
            queue.append(videos[vi])
            generos_usados.append(videos[vi]["genero"])
            vi += 1
        elif si < len(shorts):
            queue.append(shorts[si])
            si += 1
        else:
            break

    # Atribui slots de horário
    base_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    day_offset = 0

    for i, item in enumerate(queue):
        slot_idx = i % len(POSTING_SLOTS)
        if slot_idx == 0 and i > 0:
            day_offset += 1
        h, m = POSTING_SLOTS[slot_idx].split(":")
        scheduled = base_date + timedelta(days=day_offset, hours=int(h), minutes=int(m))
        item["scheduled_at"] = scheduled.isoformat()
        item["slot"] = POSTING_SLOTS[slot_idx]

    # Salva fila
    QUEUE_FILE.write_text(json.dumps(queue, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"Fila montada: {len(queue)} itens ({len(videos)} videos + {len(shorts)} shorts)")
    log(f"  Arquivo: {QUEUE_FILE}")

    return queue


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Montar fila de postagem")
    parser.add_argument("--max-per-day", type=int, default=None)
    parser.add_argument("--show", action="store_true", help="Mostra fila atual")
    args = parser.parse_args()

    if args.show:
        if QUEUE_FILE.exists():
            queue = json.loads(QUEUE_FILE.read_text(encoding="utf-8"))
            for i, item in enumerate(queue):
                print(f"  {i+1}. [{item.get('slot', '?')}] {item.get('genero', '?')}: "
                      f"{item.get('titulo', '?')[:50]} ({item.get('size_mb', 0)}MB)")
            print(f"\nTotal: {len(queue)} itens")
        else:
            print("Nenhuma fila montada ainda")
        return

    build_queue(max_per_day=args.max_per_day)


if __name__ == "__main__":
    main()
