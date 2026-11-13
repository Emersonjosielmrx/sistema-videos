# -*- coding: utf-8 -*-
"""postar_fila.py — Posta os vídeos da fila no YouTube respeitando quota diária.

Lê workspace/posting_queue.json (gerado por montar_fila.py) e posta N por dia.
Suporta dry-run. Registra postados em logs/posted_videos.json.
"""
import os
import sys
import json
import time
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent))

from hp_common import PROJECT_DIR, log

QUEUE_FILE = PROJECT_DIR / "workspace" / "posting_queue.json"
POSTED_LOG = PROJECT_DIR / "logs" / "posted_videos.json"
MAX_PER_DAY = int(os.environ.get("MAX_POSTS_PER_DAY", "6"))


def _load_queue():
    if QUEUE_FILE.exists():
        try:
            return json.loads(QUEUE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def _load_posted():
    if POSTED_LOG.exists():
        try:
            return json.loads(POSTED_LOG.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def _save_posted(posted):
    POSTED_LOG.parent.mkdir(parents=True, exist_ok=True)
    POSTED_LOG.write_text(json.dumps(posted, ensure_ascii=False, indent=2), encoding="utf-8")


def _save_queue(queue):
    QUEUE_FILE.write_text(json.dumps(queue, ensure_ascii=False, indent=2), encoding="utf-8")


def _post_video(item, canal=None):
    """Posta um vídeo. Retorna True/False."""
    video_path = item.get("video", "")
    if not video_path or not Path(video_path).exists():
        log(f"  ! Arquivo nao existe: {video_path}")
        return False

    try:
        import youtube_poster
        canais = youtube_poster._load_canais()
        # Usa canal passado ou primeiro disponível
        c = None
        if canal:
            c = youtube_poster._find_canal(canais, canal)
        if not c and canais:
            c = canais[0]
        if not c:
            log("  ! Nenhum canal configurado")
            return False

        is_short = item.get("is_short", False)
        titulo = item.get("titulo", "Historia")[:100]
        descricao = item.get("description") or item.get("hashtags", "")
        tags = item.get("hashtags", "").replace("#", "").split()

        video_id = youtube_poster.upload(
            video_path=video_path,
            titulo=titulo,
            descricao=descricao,
            tags=tags,
            canal=c,
            privacy="public",
        )
        log(f"  + Postado: {titulo[:40]} → {video_id}")
        return True

    except ImportError:
        log("  ! youtube_poster nao disponivel")
        return False
    except Exception as e:
        log(f"  ! Erro ao postar: {e}")
        return False


def post_queue(max_today=None, canal=None, dry_run=False, delay=30):
    """Posta N vídeos da fila de hoje."""
    max_t = max_today or MAX_PER_DAY
    queue = _load_queue()
    posted = _load_posted()
    posted_paths = {p.get("video") for p in posted}

    # Filtra já postados
    pending = [item for item in queue if item.get("video") not in posted_paths]

    if not pending:
        log("Fila vazia — nada a postar")
        return 0

    # Posta até o limite diário
    today_posted = 0
    today_str = datetime.now().strftime("%Y-%m-%d")
    today_count = sum(1 for p in posted if p.get("posted_at", "").startswith(today_str))

    if today_count >= max_t:
        log(f"Quota diaria atingida ({today_count}/{max_t})")
        return 0

    remaining = max_t - today_count
    to_post = pending[:remaining]

    log(f"POSTAR FILA: {len(to_post)} videos (quota restante: {remaining}/{max_t})")

    for i, item in enumerate(to_post):
        log(f"\n  [{i+1}/{len(to_post)}] {item.get('titulo', '?')[:50]}")

        if dry_run:
            log(f"    DRY RUN: {item.get('video', '?')}")
            continue

        ok = _post_video(item, canal=canal)

        if ok:
            record = {
                "video": item["video"],
                "titulo": item.get("titulo", ""),
                "genero": item.get("genero", ""),
                "posted_at": datetime.now().isoformat(),
                "canal": canal or "default",
            }
            posted.append(record)
            _save_posted(posted)
            today_posted += 1

        if i < len(to_post) - 1:
            time.sleep(delay)

    # Remove postados da fila
    if not dry_run:
        new_queue = [item for item in queue if item.get("video") not in posted_paths
                     and item.get("video") not in {p.get("video") for p in posted}]
        _save_queue(new_queue)

    log(f"\nPostados hoje: {today_posted}")
    return today_posted


def main():
    parser = argparse.ArgumentParser(description="Postar fila de videos no YouTube")
    parser.add_argument("--max", type=int, default=None, help="Max posts hoje")
    parser.add_argument("--canal", default=None, help="Nome/ID do canal")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--delay", type=int, default=30, help="Delay entre posts (s)")
    args = parser.parse_args()

    n = post_queue(max_today=args.max, canal=args.canal,
                   dry_run=args.dry_run, delay=args.delay)

    if args.dry_run:
        print(f"DRY RUN: {n or 'todos'} seriam postados")
    else:
        print(f"Postados: {n}")


if __name__ == "__main__":
    main()
