# -*- coding: utf-8 -*-
"""split_shorts.py — Corta vídeo longo em Shorts (~55s) e prepara pra postagem.

Cada short é um segmento do vídeo original com fade in/out suave.
Gera metadata JSON pra cada short (título viral, hashtags, thumbnail).
"""
import os
import sys
import json
import math
import subprocess
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from hp_common import PROJECT_DIR, VIDEOS_DIR, log

SHORTS_DIR = VIDEOS_DIR / "_shorts"
SHORTS_DIR.mkdir(parents=True, exist_ok=True)

SHORT_DURATION = int(os.environ.get("SHORT_DURATION", "55"))
SHORT_OVERLAP = 2
MIN_SHORT_DURATION = 20


def _ffprobe_duration(path):
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True, timeout=15)
        return float(r.stdout.strip())
    except Exception:
        return 0.0


def janelas_por_cena(total_dur, cortes, dur=None, min_dur=MIN_SHORT_DURATION):
    """[(inicio, duracao)] cortando SO nos limites de cena (inicio de cada fala no video final, os `offsets` da
    legenda no story_pipeline), cada parte com ate `dur` s e pelo menos `min_dur`. Cena mais longa que `dur` = corta
    no tempo (como antes). Sobra final curta demais = descartada (como antes). Sem sobreposicao: o corte cai na troca
    de imagem, nao no meio de uma frase. Independe de silencio (com microcortes quase nao ha pausa)."""
    dur = dur or SHORT_DURATION
    limites = sorted({round(float(c), 3) for c in (cortes or []) if 0 < float(c) < total_dur})
    janelas, ini = [], 0.0
    while total_dur - ini >= min_dur:
        if total_dur - ini <= dur:
            janelas.append((ini, total_dur - ini))
            break
        ok = [b for b in limites if min_dur <= b - ini <= dur]
        sobra_ok = [b for b in ok if total_dur - b >= min_dur]  # nao deixar o final (o desfecho) curto demais
        fim = (sobra_ok or ok or [ini + dur])[-1]
        janelas.append((ini, fim - ini))
        ini = fim
    return janelas


def split_video(video_path, out_dir=None, duration=None, overlap=None, cortes=None):
    """Corta video em shorts. Retorna lista de paths gerados.

    cortes: instantes (s) de troca de cena no video final. Com eles (e HISTORIAS_SHORTS_POR_CENA=1 no pipeline)
    as partes terminam nas trocas de cena em vez de a cada `duration` s fixos com 2 s de sobreposicao."""
    video_path = Path(video_path)
    if not video_path.exists():
        log(f"Arquivo nao existe: {video_path}")
        return []

    dur = duration or SHORT_DURATION
    ovl = overlap if overlap is not None else SHORT_OVERLAP
    total_dur = _ffprobe_duration(str(video_path))

    if total_dur < MIN_SHORT_DURATION:
        log(f"Video muito curto pra shorts ({total_dur:.0f}s)")
        return []

    if cortes:
        janelas = janelas_por_cena(total_dur, cortes, dur)
        log(f"  cortes nas trocas de cena: {[round(a, 1) for a, _ in janelas]}")
    else:
        n_shorts = math.ceil(total_dur / (dur - ovl))
        janelas = [(i * (dur - ovl), min(dur, total_dur - i * (dur - ovl))) for i in range(n_shorts)]
    stem = video_path.stem.replace("_FINAL", "").replace("_CENSURADO", "")

    if out_dir:
        out = Path(out_dir)
    else:
        out = SHORTS_DIR / stem
    out.mkdir(parents=True, exist_ok=True)

    shorts = []
    for i, (start, actual_dur) in enumerate(janelas):
        if actual_dur < MIN_SHORT_DURATION:
            break

        out_path = out / f"{stem}_short{i+1:02d}.mp4"

        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start),
            "-i", str(video_path),
            "-t", str(actual_dur),
            "-vf", f"fade=in:0:12,fade=out:st={actual_dur-0.5}:d=0.5",
            "-af", f"afade=in:st=0:d=0.3,afade=out:st={actual_dur-0.5}:d=0.5",
            "-c:v", "libx264", "-crf", "23", "-preset", "fast",
            "-c:a", "aac", "-b:a", "192k",
            str(out_path),
        ]

        try:
            subprocess.run(cmd, capture_output=True, timeout=120)
            if out_path.exists() and out_path.stat().st_size > 10000:
                shorts.append(str(out_path))
                log(f"  + short {i+1}: {start:.0f}s-{start+actual_dur:.0f}s")
        except Exception as e:
            log(f"  ! short {i+1} falhou: {e}")

    log(f"  = {len(shorts)} shorts gerados de {video_path.name}")
    return shorts


def generate_shorts_metadata(shorts, titulo_original, genero="superacao"):
    """Gera metadata pra cada short (titulo viral, hashtags)."""
    try:
        from viralizador import generate_viral_titles, get_hashtags, sanitize_title
    except ImportError:
        def sanitize_title(t): return t
        def get_hashtags(g): return "#shorts #historia"
        def generate_viral_titles(t, g, n=1): return [t]

    metadata = []
    titles = generate_viral_titles(titulo_original, genero, n=len(shorts))

    for i, short_path in enumerate(shorts):
        title = titles[i] if i < len(titles) else sanitize_title(f"{titulo_original} pt.{i+1}")
        meta = {
            "file": short_path,
            "title": title,
            "description": f"{title}\n\n{get_hashtags(genero)}",
            "hashtags": get_hashtags(genero),
            "part": i + 1,
            "total_parts": len(shorts),
        }
        metadata.append(meta)

        meta_path = Path(short_path).with_suffix(".json")
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    return metadata


def main():
    parser = argparse.ArgumentParser(description="Split video em Shorts")
    parser.add_argument("video", help="Path do video pra cortar")
    parser.add_argument("--duration", type=int, default=SHORT_DURATION)
    parser.add_argument("--out-dir", default=None)
    parser.add_argument("--titulo", default=None, help="Titulo original (pra viral)")
    parser.add_argument("--genero", default="superacao")
    args = parser.parse_args()

    shorts = split_video(args.video, out_dir=args.out_dir, duration=args.duration)

    if shorts and args.titulo:
        generate_shorts_metadata(shorts, args.titulo, args.genero)

    if shorts:
        print(f"OK: {len(shorts)} shorts em {Path(shorts[0]).parent}")
    else:
        print("FALHOU: nenhum short gerado")
        sys.exit(1)


if __name__ == "__main__":
    main()
