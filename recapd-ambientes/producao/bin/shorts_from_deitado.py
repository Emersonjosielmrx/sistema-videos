"""shorts_from_deitado.py — Gera shorts 9:16 a partir de um recap deitado 16:9.

Pega final_anime_deitado.mp4 (ou _ads), corta em ~55s nos silêncios,
aplica composição vertical (fundo borrado + vídeo centralizado), gera CTA.
Resultado: final_anime_short.mp4 (primeiro segmento) + shorts avulsos em shorts/.

Uso:
    python bin/shorts_from_deitado.py --video workspace/anime/<id>/final_anime_deitado.mp4
    python bin/shorts_from_deitado.py --video /path/to/video.mp4 --max-shorts 3
"""
import argparse
import json
import logging
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as cfg
from anime_compose import get_vertical_filtergraph

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

OUT_W, OUT_H, FPS = 1080, 1920, 30  # 31/10 regra da dona: nenhum vídeo sai com menos de 1080p (era 720x1280)
TARGET_DUR = cfg.SHORTS_TARGET_DUR
MIN_DUR = cfg.SHORTS_MIN_DUR


def get_duration(path):
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, timeout=10)
    return float(r.stdout.strip())


def detect_silences(video_path):
    r = subprocess.run([
        "ffmpeg", "-i", str(video_path), "-af",
        f"silencedetect=noise={cfg.SILENCE_NOISE_DB}dB:d={cfg.SILENCE_MIN_DUR}",
        "-f", "null", "-"
    ], capture_output=True, text=True, timeout=max(300, int(get_duration(video_path) * 1.5)))
    silences = []
    for line in r.stderr.split('\n'):
        m = re.search(r'silence_end: ([\d.]+)', line)
        if m:
            silences.append(float(m.group(1)))
    return silences


def plan_cuts(total_dur, silences):
    cuts = [0.0]
    cursor = 0.0
    for target_end in range(TARGET_DUR, int(total_dur), TARGET_DUR):
        best = None
        best_dist = 999
        for s in silences:
            dist = abs(s - target_end)
            if dist < best_dist and s > cursor + MIN_DUR:
                best = s
                best_dist = dist
        if best and best_dist < 15:
            cuts.append(best)
            cursor = best
        else:
            forced = min(float(target_end), total_dur - 1.0)
            if forced > cursor + MIN_DUR:
                cuts.append(forced)
                cursor = forced
    cuts.append(total_dur)
    return sorted(set(cuts))


def make_vertical_short(src, start, dur, out_path, cheio=False):
    """Corta um trecho e aplica composição vertical 9:16. cheio (02/11, cortes do longo): a imagem ENCHE a tela em pé
    — 16:9 ampliado até a altura toda com o corte no centro (manhwa = painel no meio) — em vez da faixa no meio do
    fundo borrado."""
    vf = get_vertical_filtergraph("[0:v]", "[vout]", OUT_W, OUT_H)
    if cheio:
        # metade da altura com a cena inteira por cima do fundo borrado já era o "encolhido"; aqui 78% da largura
        # original aparece cortada em pé + fundo borrado só nas bordas que sobram (painel largo não perde as pontas)
        vf = (f"[0:v]split=2[bg][fg];[bg]scale={OUT_W}:{OUT_H}:force_original_aspect_ratio=increase,"
              f"crop={OUT_W}:{OUT_H},gblur=sigma=18,eq=brightness=-0.12[b];"
              f"[fg]crop=iw*0.62:ih:iw*0.19:0,scale={OUT_W}:-2[f];[b][f]overlay=(W-w)/2:(H-h)/2[vout]")
    cmd = [
        "ffmpeg", "-y",
        "-ss", f"{start:.3f}",
        "-i", str(src),
        "-t", f"{dur:.3f}",
        "-filter_complex", vf,
        "-map", "[vout]", "-map", "0:a?",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23", "-g", "30",
        "-c:a", "aac", "-b:a", "192k",
        "-r", str(FPS),
        "-threads", cfg.FFMPEG_THREADS,
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(out_path),
    ]
    timeout = cfg.timeout_por_duracao(dur, base=60, por_seg=8)
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        logging.error(f"ffmpeg falhou: {r.stderr[-300:]}")
        return False
    return out_path.exists() and out_path.stat().st_size > 5000


def main():
    ap = argparse.ArgumentParser(description="Gera shorts 9:16 de um deitado 16:9")
    ap.add_argument("--video", required=True, help="Vídeo deitado fonte")
    ap.add_argument("--max-shorts", type=int, default=0, help="Limite de shorts (0=todos)")
    ap.add_argument("--first-only", action="store_true",
                    help="Gera só o primeiro short como final_anime_short.mp4 na mesma pasta")
    args = ap.parse_args()

    src = Path(args.video)
    if not src.exists():
        logging.error(f"Vídeo não encontrado: {src}")
        sys.exit(1)

    free = cfg.disk_free_gb("D:\\")
    if free < cfg.MIN_DISK_GB:
        logging.error(f"Disco cheio: {free:.1f}GB livres (< {cfg.MIN_DISK_GB}GB)")
        sys.exit(1)

    total_dur = get_duration(src)
    logging.info(f"Fonte: {src.name} ({total_dur:.0f}s)")

    silences = detect_silences(src)
    cuts = plan_cuts(total_dur, silences)
    n_parts = len(cuts) - 1
    logging.info(f"Planejados {n_parts} shorts")

    if args.first_only:
        start = cuts[0]
        dur = min(cuts[1] - cuts[0], cfg.SHORTS_MAX_DUR)
        out = src.parent / "final_anime_short.mp4"
        logging.info(f"Gerando short único: {start:.1f}s-{start+dur:.1f}s -> {out.name}")
        ok = make_vertical_short(src, start, dur, out)
        if ok:
            logging.info(f"OK: {out} ({get_duration(out):.1f}s)")
        else:
            logging.error("Falhou ao gerar short")
            sys.exit(1)
        return

    out_dir = src.parent / "shorts"
    out_dir.mkdir(parents=True, exist_ok=True)

    generated = 0
    for i in range(n_parts):
        if args.max_shorts > 0 and generated >= args.max_shorts:
            break
        start = cuts[i]
        end = cuts[i + 1]
        dur = end - start
        if dur < 3.0:
            continue

        part_num = i + 1
        out_path = out_dir / f"short_parte{part_num:02d}.mp4"
        logging.info(f"[{part_num}/{n_parts}] {start:.1f}s-{end:.1f}s ({dur:.1f}s)")

        ok = make_vertical_short(src, start, dur, out_path)
        if ok:
            logging.info(f"  OK: {out_path.name} ({get_duration(out_path):.1f}s)")
            generated += 1
        else:
            logging.warning(f"  FALHOU parte {part_num}")

    # Copia o primeiro short como final_anime_short.mp4 na pasta pai
    first = out_dir / "short_parte01.mp4"
    if first.exists():
        import shutil
        main_short = src.parent / "final_anime_short.mp4"
        shutil.copy2(str(first), str(main_short))
        logging.info(f"Copiado {first.name} -> {main_short.name}")

    logging.info(f"Gerados {generated}/{n_parts} shorts em {out_dir}")


if __name__ == "__main__":
    main()
