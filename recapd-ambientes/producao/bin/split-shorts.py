#!/usr/bin/env python3
"""split-shorts.py — Corta um vídeo longo em múltiplos Shorts (~55-60s) com CTA no final.

Corta em silêncios naturais (nunca no meio de uma fala), adiciona tela de CTA
no final de cada parte com áudio padrão e imagem do último frame.

Uso:
    python bin/split-shorts.py --video workspace/videos/capitulo-2/VIDEO.mp4 \
        --obra "The Meek Cat" --capitulo 2 [--plan workspace/meta/cap2_shorts_plan.json]

Se --plan não for passado, detecta silêncios automaticamente.
"""
import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT / "bin"))
import config as cfg  # parâmetros centralizados (bin/config.py)

W, H, FPS = 1080, 1920, 30
CTA_DURATION = cfg.SHORTS_CTA_DUR       # duração do CTA final (s)
TARGET_PART_DUR = cfg.SHORTS_TARGET_DUR # alvo por parte
MIN_PART_DUR = cfg.SHORTS_MIN_DUR       # mínimo por parte
MAX_PART_DUR = cfg.SHORTS_MAX_DUR       # máximo (cabe no 60s dos Shorts com CTA)


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def detect_silences(video_path, noise_db=None, min_dur=None):
    """Detecta pontos de silêncio (transições entre falas). Cacheado por md5 do
    vídeo — re-analisar o mesmo arquivo é caro e desnecessário."""
    noise_db = cfg.SILENCE_NOISE_DB if noise_db is None else noise_db
    min_dur = cfg.SILENCE_MIN_DUR if min_dur is None else min_dur
    _cache = None
    try:
        _md5 = cfg.md5_file(video_path)
        if _md5:
            _cdir = PROJECT / "workspace" / "silence_cache"
            _cdir.mkdir(parents=True, exist_ok=True)
            _cache = _cdir / f"{_md5}_{noise_db}_{min_dur}.json"
            if _cache.exists():
                return json.loads(_cache.read_text())
    except Exception:
        pass

    r = subprocess.run([
        "ffmpeg", "-i", str(video_path), "-af",
        f"silencedetect=noise={noise_db}dB:d={min_dur}",
        "-f", "null", "-"
    ], capture_output=True, text=True, timeout=300)

    silences = []
    for line in r.stderr.split('\n'):
        m = re.search(r'silence_end: ([\d.]+)', line)
        if m:
            silences.append(float(m.group(1)))
    if _cache:
        try:
            _cache.write_text(json.dumps(silences))
        except Exception:
            pass
    return silences


def plan_cuts(total_dur, silences):
    """Planeja cortes nos silêncios mais próximos do target de ~55s."""
    cuts = [0.0]
    cursor = 0.0

    for target_end in range(TARGET_PART_DUR, int(total_dur), TARGET_PART_DUR):
        best = None
        best_dist = 999
        for s in silences:
            dist = abs(s - target_end)
            if dist < best_dist and s > cursor + MIN_PART_DUR:
                best = s
                best_dist = dist
        if best and best_dist < 15:
            # silêncio bom PERTO do alvo → corta nele (transição natural)
            cuts.append(best)
            cursor = best
        else:
            # sem silêncio bom perto (o mais próximo está longe demais) → NÃO aceita
            # o silêncio distante (dava partes degeneradas tipo "29s"). Corta no ALVO
            # forçado, respeitando o mínimo por parte.
            forced = min(float(target_end), total_dur - 1.0)
            if forced > cursor + MIN_PART_DUR:
                cuts.append(forced)
                cursor = forced

    cuts.append(total_dur)
    return sorted(set(cuts))


def get_duration(path):
    """Retorna duração de um arquivo de mídia."""
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, timeout=10
    )
    return float(r.stdout.strip())


def extract_last_frame(video_path, time_s, out_png):
    """Extrai 1 frame no tempo dado. Seek em 2 estágios: -ss GROSSO antes de -i
    (rápido, por keyframe ~1s antes) + -ss FINO depois de -i (preciso). Evita o
    decode-desde-o-início que estourava o timeout de 15s em MP4 grande (crash cap10).
    Retorna True só se o PNG saiu de verdade (senão o CTA cai no fundo preto)."""
    coarse = max(0.0, time_s - 1.0)
    subprocess.run([
        "ffmpeg", "-y",
        "-ss", f"{coarse:.2f}", "-i", str(video_path),
        "-ss", f"{time_s - coarse:.2f}",
        "-vframes", "1", "-q:v", "2", str(out_png)
    ], capture_output=True, timeout=60)
    return Path(out_png).exists() and Path(out_png).stat().st_size > 500


def build_cta_clip(last_frame_png, out_path, part_num, total_parts, obra):
    """Gera clip CTA de 3.5s: último frame escurecido + texto 'Parte X de Y'."""
    from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

    # Escurecer e borrar o último frame como background
    try:
        img = Image.open(last_frame_png).convert("RGB")
        # Redimensionar pra canvas
        sw, sh = W / img.width, H / img.height
        sc = max(sw, sh)
        img = img.resize((int(img.width * sc), int(img.height * sc)), Image.LANCZOS)
        left = (img.width - W) // 2
        top = (img.height - H) // 2
        img = img.crop((left, top, left + W, top + H))
        img = img.filter(ImageFilter.GaussianBlur(18))
        img = ImageEnhance.Brightness(img).enhance(0.35)
    except Exception:
        img = Image.new("RGB", (W, H), (10, 12, 24))

    draw = ImageDraw.Draw(img)

    # Fontes
    font_candidates = [
        # Windows PRIMEIRO (este projeto roda em Windows; sem isso o CTA cai no
        # load_default() minúsculo e feio — bug ativo do "PARTE X" sem estilo).
        "C:/Windows/Fonts/impact.ttf",
        "C:/Windows/Fonts/ariblk.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        # Mac / Linux (fallback)
        "/System/Library/Fonts/Supplemental/Impact.ttf",
        "/System/Library/Fonts/Supplemental/Arial Black.ttf",
        "/Library/Fonts/Impact.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    font_path = next((f for f in font_candidates if Path(f).exists()), None)

    from PIL import ImageFont
    font_big = ImageFont.truetype(font_path, 80) if font_path else ImageFont.load_default()
    font_med = ImageFont.truetype(font_path, 52) if font_path else ImageFont.load_default()
    font_sm = ImageFont.truetype(font_path, 40) if font_path else ImageFont.load_default()

    # Textos
    line1 = f"PARTE {part_num} DE {total_parts}"
    line2 = "CONTINUA NO PRÓXIMO VÍDEO! ➡️"
    line3 = "INSCREVA-SE 🔔"

    # Centralizar cada linha
    for text, font, y_pos, color in [
        (line1, font_big, H * 0.38, (255, 255, 255)),
        (line2, font_med, H * 0.50, (255, 214, 60)),
        (line3, font_sm, H * 0.62, (255, 70, 70)),
    ]:
        bbox = draw.textbbox((0, 0), text, font=font, stroke_width=6)
        tw = bbox[2] - bbox[0]
        x = (W - tw) // 2 - bbox[0]
        draw.text((x, int(y_pos)), text, font=font, fill=color,
                  stroke_width=6, stroke_fill=(0, 0, 0, 200))

    bg_path = Path(str(out_path) + "_cta_bg.jpg")
    img.save(str(bg_path), quality=85)

    # Gerar clip com zoom pulse sutil + áudio silencioso
    frames = int(CTA_DURATION * FPS)
    pulse = (f"zoompan=z='1+0.02*sin(on/{frames}*3.14159*3)':"
             f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
             f"d={frames}:s={W}x{H}:fps={FPS}")
    fade = f"fade=t=in:st=0:d=0.3:color=black"

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-t", f"{CTA_DURATION:.2f}", "-i", str(bg_path),
        "-f", "lavfi", "-t", f"{CTA_DURATION:.2f}", "-i", "anullsrc=r=44100:cl=stereo",
        "-filter_complex", f"[0:v]{pulse},{fade},format=yuv420p[v]",
        "-map", "[v]", "-map", "1:a",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23", "-g", "30",
        "-c:a", "aac", "-b:a", "192k", "-pix_fmt", "yuv420p",
        "-t", f"{CTA_DURATION:.2f}",
        str(out_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True, timeout=30)
    bg_path.unlink(missing_ok=True)
    return Path(out_path).exists()


def split_video(video_path, cuts, out_dir, obra, capitulo):
    """Corta o vídeo nas partes e adiciona CTA no final de cada uma."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    total_parts = len(cuts) - 1
    results = []

    for i in range(total_parts):
        start = cuts[i]
        end = cuts[i + 1]
        part_num = i + 1
        dur = end - start

        log(f"Parte {part_num}/{total_parts}: {start:.1f}s → {end:.1f}s ({dur:.1f}s)")

        # Salvaguarda: trecho degenerado (curto/negativo) crasha o ffmpeg e um short <3s é inútil.
        # Pula em vez de abortar TODA a geração de shorts do vídeo.
        if dur < 3.0 or start < 0:
            log(f"  ⚠ Parte {part_num}: trecho inválido ({dur:.1f}s) — pulando")
            continue

        # 1. Extrair parte (usando -ss ANTES de -i pra seek rápido por keyframe + re-encode pra corte exato)
        part_raw = out_dir / f"_part_{part_num:02d}_raw.mp4"
        cmd_cut = [
            "ffmpeg", "-y",
            "-ss", f"{start:.3f}",  # ANTES de -i: seek rápido por keyframe
            "-i", str(video_path),
            "-t", f"{dur:.3f}",     # duração da parte (não -to absoluto)
            # ultrafast: este _raw é INTERMEDIÁRIO (descartado após o concat, que
            # re-encoda de novo). Não precisa de qualidade aqui → corta o tempo de CPU.
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "20",
            "-c:a", "aac", "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-avoid_negative_ts", "make_zero",
            str(part_raw),
        ]
        _rc = subprocess.run(cmd_cut, capture_output=True, text=True, timeout=600)
        if _rc.returncode != 0 or not part_raw.exists() or part_raw.stat().st_size < 1000:
            log(f"  ⚠ Parte {part_num}: corte falhou (cod={_rc.returncode}) — 1 retry (lock de arquivo?)...")
            part_raw.unlink(missing_ok=True)
            import time as _t; _t.sleep(1.5)
            _rc = subprocess.run(cmd_cut, capture_output=True, text=True, timeout=600)
            if _rc.returncode != 0 or not part_raw.exists() or part_raw.stat().st_size < 1000:
                log(f"  ⚠ Parte {part_num}: falhou de novo — pulando este short.\n"
                    f"     stderr: {(_rc.stderr or '')[-500:]}")
                part_raw.unlink(missing_ok=True)
                continue

        # 2. Extrair último frame pra CTA
        last_frame = out_dir / f"_lastframe_{part_num:02d}.jpg"
        extract_last_frame(str(video_path), end - 0.5, last_frame)

        # 3. Gerar CTA clip
        cta_clip = out_dir / f"_cta_{part_num:02d}.mp4"
        build_cta_clip(last_frame, cta_clip, part_num, total_parts, obra)
        last_frame.unlink(missing_ok=True)

        # 4. Concatenar parte + CTA
        slug = re.sub(r'[^a-z0-9]+', '-', obra.lower()).strip('-')
        final_name = f"{slug}_cap{capitulo}_parte{part_num:02d}.mp4"
        final_path = out_dir / final_name

        concat_list = out_dir / f"_concat_{part_num:02d}.txt"
        with open(concat_list, "w") as f:
            f.write(f"file '{part_raw.name}'\n")
            f.write(f"file '{cta_clip.name}'\n")

        # Concat com re-encode (os codecs podem diferir entre parte_raw e cta). Timeout alto.
        cmd_concat = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(concat_list),
            "-c:v", "libx264", "-preset", "fast", "-crf", "23", "-g", "30",
        ]
        if cfg.LOUDNORM:  # volume parelho — YouTube pune volume irregular
            cmd_concat += ["-af", "loudnorm=I=-14:TP=-1.5:LRA=11"]
        cmd_concat += [
            "-c:a", "aac", "-b:a", "192k",
            "-threads", cfg.FFMPEG_THREADS,   # não travar a máquina toda
            "-movflags", "+faststart", "-pix_fmt", "yuv420p",
            str(final_path),
        ]
        _rc2 = subprocess.run(cmd_concat, capture_output=True, text=True, timeout=600)
        if _rc2.returncode != 0 or not final_path.exists() or final_path.stat().st_size < 1000:
            log(f"  ⚠ Parte {part_num}: concat falhou (ffmpeg cod={_rc2.returncode}) — pulando este short.\n"
                f"     stderr: {(_rc2.stderr or '')[-500:]}")
            for _t in (part_raw, cta_clip, concat_list):
                Path(_t).unlink(missing_ok=True)
            continue

        # Cleanup temporários
        for tmp in [part_raw, cta_clip, concat_list]:
            tmp.unlink(missing_ok=True)

        # Info
        final_dur = get_duration(final_path)
        size_mb = final_path.stat().st_size / (1024 * 1024)
        log(f"  ✓ {final_name} ({final_dur:.1f}s, {size_mb:.1f}MB)")

        results.append({
            "part": part_num,
            "file": str(final_path),
            "filename": final_name,
            "duration": round(final_dur, 1),
            "size_mb": round(size_mb, 1),
            "start": round(start, 1),
            "end": round(end, 1),
        })

    return results


def generate_metadata(results, obra, capitulo):
    """Gera metadados para cada Short (título, desc, tags)."""
    meta_all = {}
    total = len(results)

    for r in results:
        part = r["part"]
        title = f"{obra} Cap. {capitulo} | Parte {part}/{total} 🔥 #manhwa #recap"
        if len(title) > 100:
            title = f"{obra} Cap.{capitulo} Pt.{part}/{total} 🔥 #manhwa"

        _obra_tag = "#" + re.sub(r'[^A-Za-z0-9]', '', obra)  # hashtag DA OBRA (não mais fixa)
        desc = (
            f"📖 {obra} — Capítulo {capitulo}, Parte {part} de {total}\n"
            f"{'🔥 CONTINUA NA PARTE ' + str(part + 1) + '!' if part < total else '✅ FIM DO CAPÍTULO!'}\n\n"
            f"Recap dramática e envolvente deste manhwa coreano de romance/drama.\n\n"
            f"{_obra_tag} #Manhwa #Recap #Webtoon #Romance #Drama #Shorts\n\n"
            f"📌 INSCREVA-SE e ative o 🔔 para não perder nenhuma parte!"
        )

        tags = [
            obra, f"{obra} cap {capitulo}", "manhwa", "recap manhwa",
            "webtoon", "romance coreano", "drama", "shorts",
            f"parte {part}", "manhwa romance", "recap", obra.lower()
        ]

        meta_all[f"part_{part:02d}"] = {
            "pt": {"title": title, "description": desc, "tags": tags}
        }

    return meta_all


def main():
    ap = argparse.ArgumentParser(description="Corta vídeo em Shorts com CTA")
    ap.add_argument("--video", required=True, help="Vídeo fonte")
    ap.add_argument("--obra", required=True, help="Nome da obra")
    ap.add_argument("--capitulo", type=int, required=True, help="Número do capítulo")
    ap.add_argument("--plan", help="JSON com cortes pré-calculados (opcional)")
    ap.add_argument("--out-dir", help="Diretório de saída (default: workspace/shorts/<slug>)")
    args = ap.parse_args()

    video = Path(args.video)
    if not video.exists():
        print(f"ERRO: vídeo não encontrado: {video}", file=sys.stderr)
        sys.exit(1)

    # Pré-checagens (o D: vive cheio; o fonte pode estar corrompido/incompleto)
    _free = cfg.disk_free_gb("D:\\")
    if _free < cfg.MIN_DISK_GB:
        print(f"ERRO: só {_free:.1f}GB livres em D: (< {cfg.MIN_DISK_GB}GB). Libere espaço antes.", file=sys.stderr)
        sys.exit(1)
    _ok, _motivo = cfg.validar_video(video)
    if not _ok:
        print(f"ERRO: vídeo-fonte inválido/corrompido → {_motivo}", file=sys.stderr)
        sys.exit(1)

    total_dur = get_duration(video)
    log(f"Vídeo: {video.name} ({total_dur:.1f}s) | disco livre: {_free:.0f}GB")

    # Planejar cortes
    if args.plan and Path(args.plan).exists():
        plan = json.loads(Path(args.plan).read_text())
        cuts = plan["cuts"]
        log(f"Usando plano pré-calculado: {len(cuts) - 1} partes")
    else:
        log("Detectando silêncios para pontos de corte...")
        silences = detect_silences(video)
        cuts = plan_cuts(total_dur, silences)
        log(f"Planejados {len(cuts) - 1} cortes")

    # Output dir
    slug = re.sub(r'[^a-z0-9]+', '-', args.obra.lower()).strip('-')
    out_dir = Path(args.out_dir) if args.out_dir else (
        PROJECT / "workspace" / "shorts" / f"{slug}-cap{args.capitulo}")

    # Cortar
    log(f"Cortando em {len(cuts) - 1} Shorts...")
    results = split_video(video, cuts, out_dir, args.obra, args.capitulo)

    # Metadados
    meta = generate_metadata(results, args.obra, args.capitulo)
    meta_path = out_dir / "meta_shorts.json"
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2))

    # Sumário
    log(f"\n{'='*60}")
    log(f"✅ {len(results)} Shorts gerados em: {out_dir}")
    log(f"   Metadados: {meta_path}")
    total_size = sum(r["size_mb"] for r in results)
    log(f"   Tamanho total: {total_size:.0f} MB")
    for r in results:
        log(f"   Parte {r['part']:2d}: {r['duration']:.0f}s ({r['size_mb']:.1f}MB)")


if __name__ == "__main__":
    main()
