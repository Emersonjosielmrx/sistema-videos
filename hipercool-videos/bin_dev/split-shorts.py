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

W, H, FPS = 1080, 1920, 30
IDIOMA = None  # --idioma (versão em outra língua): textos da tela final e dos metadados
CTA_DURATION = 3.5  # Duração do CTA final (segundos)
TARGET_PART_DUR = 55  # Alvo por parte (sem CTA)
MIN_PART_DUR = 30  # Mínimo por parte
MAX_PART_DUR = 58  # Máximo (pra caber no 60s dos Shorts com CTA)


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def detect_silences(video_path, noise_db=-35, min_dur=0.3):
    """Detecta pontos de silêncio no vídeo (transições naturais entre falas)."""
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
    return silences


def plan_cuts(total_dur, pontos):
    """Corta perto de TARGET_PART_DUR contado do corte ANTERIOR, só em pontos naturais
    (fronteira de painel ou silêncio) dentro de [MIN_PART_DUR, MAX_PART_DUR]."""
    pontos = sorted(p for p in pontos if 0 < p < total_dur)
    cuts = [0.0]
    while total_dur - cuts[-1] > MAX_PART_DUR:
        ini = cuts[-1]
        janela = [p for p in pontos if ini + MIN_PART_DUR <= p <= ini + MAX_PART_DUR]
        if janela:
            cuts.append(min(janela, key=lambda p: abs(p - (ini + TARGET_PART_DUR))))
        else:  # sem ponto natural na janela: o próximo que existir (Shorts aceitam até 3 min)
            depois = [p for p in pontos if p > ini + MAX_PART_DUR]
            cuts.append(depois[0] if depois else ini + TARGET_PART_DUR)
    if len(cuts) > 1 and total_dur - cuts[-1] < MIN_PART_DUR:
        cuts.pop()  # sobra curta demais entra na parte anterior
    cuts.append(total_dur)
    return cuts


def get_duration(path):
    """Retorna duração de um arquivo de mídia."""
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, timeout=10
    )
    return float(r.stdout.strip())


def extract_last_frame(video_path, time_s, out_png):
    """Extrai o último frame do vídeo no tempo dado."""
    subprocess.run([
        "ffmpeg", "-y", "-ss", f"{time_s:.2f}", "-i", str(video_path),
        "-vframes", "1", "-q:v", "2", str(out_png)
    ], capture_output=True, timeout=120)
    return Path(out_png).exists()


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

    # Fontes (antes só havia caminhos de Mac/Linux: no Windows caía na fonte padrão minúscula)
    import idiomas
    font_candidates = [
        idiomas.IDIOMAS.get(IDIOMA, {}).get("fonte_png", ""),
        r"D:\hipercool-materiais\assets\fonts\LuckiestGuy-Regular.ttf" if IDIOMA in (None, "pt", "it", "id", "fr", "en") else "",
        r"C:\Windows\Fonts\impact.ttf",
        "/System/Library/Fonts/Supplemental/Impact.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    font_path = next((f for f in font_candidates if f and Path(f).exists()), None)

    from PIL import ImageFont
    font_big = ImageFont.truetype(font_path, 80) if font_path else ImageFont.load_default()
    font_med = ImageFont.truetype(font_path, 52) if font_path else ImageFont.load_default()
    font_sm = ImageFont.truetype(font_path, 40) if font_path else ImageFont.load_default()

    # Textos (emoji sai do PNG: a fonte não tem os glifos)
    line1 = idiomas.texto(IDIOMA, "parte", x=part_num, y=total_parts)
    line2 = idiomas.texto(IDIOMA, "continua").replace(" ➡️", "")
    line3 = idiomas.texto(IDIOMA, "inscreva").replace(" 🔔", "")

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
    segmentos = cuts if cuts and isinstance(cuts[0], (list, tuple)) else list(zip(cuts, cuts[1:]))
    total_parts = len(segmentos)
    results = []

    for i, (start, end) in enumerate(segmentos):
        part_num = i + 1
        dur = end - start

        log(f"Parte {part_num}/{total_parts}: {start:.1f}s -> {end:.1f}s ({dur:.1f}s)")

        # 1. Extrair parte (usando -ss ANTES de -i pra seek rápido por keyframe + re-encode pra corte exato)
        part_raw = out_dir / f"_part_{part_num:02d}_raw.mp4"
        cmd_cut = [
            "ffmpeg", "-y",
            "-ss", f"{start:.3f}",  # ANTES de -i: seek rápido por keyframe
            "-i", str(video_path),
            "-t", f"{dur:.3f}",     # duração da parte (não -to absoluto)
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-avoid_negative_ts", "make_zero",
            str(part_raw),
        ]
        subprocess.run(cmd_cut, check=True, capture_output=True, timeout=600)

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
            "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart", "-pix_fmt", "yuv420p",
            str(final_path),
        ]
        subprocess.run(cmd_concat, check=True, capture_output=True, timeout=600)

        # Cleanup temporários
        for tmp in [part_raw, cta_clip, concat_list]:
            tmp.unlink(missing_ok=True)

        # Info
        final_dur = get_duration(final_path)
        size_mb = final_path.stat().st_size / (1024 * 1024)
        log(f"  [OK] {final_name} ({final_dur:.1f}s, {size_mb:.1f}MB)")

        results.append({
            "part": part_num,
            "inicio": round(start, 3),
            "fim": round(end, 3),
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
    hashtag_obra = "#" + re.sub(r"\W+", "", obra.title())

    import idiomas
    for r in results:
        part = r["part"]
        if IDIOMA:
            cap_txt, parte_txt = idiomas.texto(IDIOMA, "cap", n=capitulo), idiomas.texto(IDIOMA, "parte", x=part, y=total)
            title = f"{obra} {cap_txt} | {parte_txt} 🔥 #manhwa #recap"[:100]
            desc = (f"📖 {obra} — {cap_txt}, {parte_txt}\n"
                    f"{idiomas.texto(IDIOMA, 'continua_parte', n=part + 1) if part < total else idiomas.texto(IDIOMA, 'fim')}\n\n"
                    f"{hashtag_obra} #Manhwa #Recap #Webtoon #Shorts\n\n{idiomas.texto(IDIOMA, 'assine')}")
        else:
            title = f"{obra} Cap. {capitulo} | Parte {part}/{total} 🔥 #manhwa #recap"
            if len(title) > 100:
                title = f"{obra} Cap.{capitulo} Pt.{part}/{total} 🔥 #manhwa"
            desc = (
                f"📖 {obra} — Capítulo {capitulo}, Parte {part} de {total}\n"
                f"{'🔥 CONTINUA NA PARTE ' + str(part + 1) + '!' if part < total else '✅ FIM DO CAPÍTULO!'}\n\n"
                f"Recap dramática e envolvente deste manhwa coreano de romance/drama.\n\n"
                f"{hashtag_obra} #Manhwa #Recap #Webtoon #Romance #Drama #Shorts\n\n"
                f"📌 INSCREVA-SE e ative o 🔔 para não perder nenhuma parte!"
            )

        tags = [
            obra, f"{obra} cap {capitulo}", "manhwa", "recap manhwa",
            "webtoon", "romance coreano", "drama", "shorts",
            f"parte {part}", "manhwa romance", "recap", obra.lower()
        ]

        meta_all[f"part_{part:02d}"] = {
            "pt": {"title": title, "description": desc, "tags": tags},
            "inicio": r["inicio"], "fim": r["fim"], "arquivo": r["filename"],
        }

    return meta_all


def main():
    ap = argparse.ArgumentParser(description="Corta vídeo em Shorts com CTA")
    ap.add_argument("--video", required=True, help="Vídeo fonte")
    ap.add_argument("--obra", required=True, help="Nome da obra")
    ap.add_argument("--capitulo", type=int, required=True, help="Número do capítulo")
    ap.add_argument("--plan", help="JSON com cortes pré-calculados (opcional)")
    ap.add_argument("--out-dir", help="Diretório de saída (default: workspace/shorts/<slug>)")
    ap.add_argument("--idioma", help="versão em outra língua (hi/id/it/ru/th): textos da tela final e metadados")
    args = ap.parse_args()
    global IDIOMA
    IDIOMA = args.idioma

    video = Path(args.video)
    if not video.exists():
        print(f"ERRO: vídeo não encontrado: {video}", file=sys.stderr)
        sys.exit(1)

    total_dur = get_duration(video)
    log(f"Vídeo: {video.name} ({total_dur:.1f}s)")

    # Planejar cortes
    if args.plan and Path(args.plan).exists():
        plan = json.loads(Path(args.plan).read_text())
        cuts = plan["cuts"]
        log(f"Usando plano pré-calculado: {len(cuts) - 1} partes")
    else:
        # Fronteiras entre painéis (gravadas pelo pipeline no .meta.json) nunca cortam fala;
        # silêncio só pra vídeo sem meta (com trilha de fundo quase não há silêncio).
        meta_v = video.with_suffix(".meta.json")
        fronteiras = []
        if meta_v.exists():
            fronteiras = (json.loads(meta_v.read_text(encoding="utf-8")).get("acabamento") or {}).get("fronteiras") or []
        if fronteiras:
            log(f"Usando {len(fronteiras)} fronteiras de painel do .meta.json como pontos de corte")
            cuts = plan_cuts(total_dur, fronteiras)
        else:
            log("Detectando silêncios para pontos de corte...")
            cuts = plan_cuts(total_dur, detect_silences(video))
        log(f"Planejados {len(cuts) - 1} cortes")

    # Trecho com mais da metade do tempo censurado não vira Short (não engaja e chama bloqueio).
    # Descarta ANTES de cortar, pra numeração "Parte X de Y" (título e tela final) ficar contínua.
    segmentos = list(zip(cuts, cuts[1:]))
    meta_v = video.with_suffix(".meta.json")
    janelas = (json.loads(meta_v.read_text(encoding="utf-8")).get("censura") or {}).get("janelas", []) \
        if meta_v.exists() else []
    if janelas:
        def frac(a, b):
            return sum(max(0.0, min(b, y) - max(a, x)) for x, y in janelas) / max(0.01, b - a)
        pulados = [(a, b) for a, b in segmentos if frac(a, b) > 0.5]
        segmentos = [s for s in segmentos if s not in pulados]
        for a, b in pulados:
            log(f"Trecho {a:.0f}-{b:.0f}s pulado: {frac(a, b):.0%} censurado")

    # Output dir
    slug = re.sub(r'[^a-z0-9]+', '-', args.obra.lower()).strip('-')
    out_dir = Path(args.out_dir) if args.out_dir else (
        PROJECT / "workspace" / "shorts" / f"{slug}-cap{args.capitulo}")

    # Cortar
    log(f"Cortando em {len(segmentos)} Shorts...")
    results = split_video(video, segmentos, out_dir, args.obra, args.capitulo)

    # Metadados
    meta = generate_metadata(results, args.obra, args.capitulo)
    meta_path = out_dir / "meta_shorts.json"
    meta["_fonte"] = video.name
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

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
