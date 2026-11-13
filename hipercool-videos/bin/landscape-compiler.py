#!/usr/bin/env python3
"""
landscape-compiler.py — Compilação crescente em formato paisagem (1920x1080)

Conceito:
  - vídeo 1 = cap1
  - vídeo 2 = cap1 + cap2
  - vídeo 3 = cap1 + cap2 + cap3
  - ...

Formato: painel vertical centralizado com efeitos visuais de preenchimento
(baseado no effects_engine.py dos vídeos verticais + referência fábrica de animes)

Features:
  - Concat demuxer (sincronia garantida)
  - Preenchimento lateral com efeitos (blur, parallax, breathing, vignette)
  - Trilha sonora com amix + fade in/out
  - Upscale final 1080p
  - Validação final (moov atom + duração áudio)
  - Checkpoint/resume

Uso:
  python3 bin/landscape-compiler.py --caps 1-3
  python3 bin/landscape-compiler.py --caps 1-9 --only-latest
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional

WORKSPACE = Path(__file__).resolve().parent.parent / "workspace"
VIDEOS_DIR = WORKSPACE / "videos"
OUTPUT_DIR = WORKSPACE / "videos" / "landscape"
ASSETS_DIR = WORKSPACE / "assets"
WATERMARK = "@manhwanoturno"

# Resolução final
WIDTH = 1920
HEIGHT = 1080

# Encoding (baseado na referência fábrica de animes v2.8)
ENCODING = {
    "crf": 28,
    "preset": "medium",
    "video_codec": "libx264",
    "audio_codec": "aac",
    "audio_bitrate": "192k",
    "audio_sample_rate": 44100,
    "audio_channels": 2,
    "pix_fmt": "yuv420p",
    "fps": 25,
}

# Trilha sonora
TRILHA = {
    "volume": 0.12,
    "fade_in": 2.0,
    "fade_out": 3.0,
}


def log(msg: str):
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def find_chapter_video(cap_num) -> Optional[Path]:
    """Encontra o melhor vídeo NORMAL de um capítulo na nova estrutura."""
    cap_key = f"cap{int(cap_num):02d}"

    # 1. Nova estrutura: obra/capXX/normal/vN.mp4
    for obra_dir in sorted(VIDEOS_DIR.iterdir()):
        if obra_dir.is_dir() and obra_dir.name not in ("landscape", "anteriores", "stable"):
            normal_dir = obra_dir / cap_key / "normal"
            if normal_dir.exists():
                versoes = sorted(normal_dir.glob("*.mp4"))
                if versoes:
                    return versoes[-1]

    # 2. Fallback: estrutura antiga
    pattern = f"*cap-tulo-{int(cap_num)}*NORMAL*ULTIMO*.mp4"
    matches = sorted(VIDEOS_DIR.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    matches = [m for m in matches if m.stat().st_size > 1_000_000 and "moov" not in m.name]
    if matches:
        return matches[0]

    # 3. Qualquer vídeo normal do cap
    pattern2 = f"*cap-tulo-{int(cap_num)}*NORMAL*.mp4"
    matches2 = sorted(VIDEOS_DIR.glob(pattern2), key=lambda p: p.stat().st_mtime, reverse=True)
    matches2 = [m for m in matches2 if "HYPERFRAMES" not in m.name and m.stat().st_size > 1_000_000]
    return matches2[0] if matches2 else None


def get_video_duration(video_path: Path) -> float:
    """Retorna duração em segundos via ffprobe."""
    cmd = [
        "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(video_path)
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return float(result.stdout.strip()) if result.stdout.strip() else 0.0
    except:
        return 0.0


def get_audio_duration(video_path: Path) -> float:
    """Retorna duração do áudio via ffprobe."""
    cmd = [
        "ffprobe", "-v", "quiet", "-select_streams", "a",
        "-show_entries", "stream=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(video_path)
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return float(result.stdout.strip()) if result.stdout.strip() else 0.0
    except:
        return 0.0


def find_trilha() -> Optional[Path]:
    """Busca trilha sonora disponível."""
    candidates = [
        ASSETS_DIR / "trilhas" / "trilha_landscape.mp3",
        ASSETS_DIR / "trilhas" / "trilha.mp3",
        WORKSPACE / "trilha.mp3",
    ]
    # Buscar qualquer mp3 no diretório de trilhas
    trilhas_dir = ASSETS_DIR / "trilhas"
    if trilhas_dir.exists():
        for f in sorted(trilhas_dir.glob("*.mp3")):
            if f.stat().st_size > 100_000:
                candidates.insert(0, f)
                break

    for c in candidates:
        if c.exists() and c.stat().st_size > 100_000:
            return c
    return None


def validate_output(video_path: Path) -> dict:
    """Valida o vídeo gerado (moov atom, duração áudio ≈ vídeo)."""
    result = {"valid": False, "errors": []}

    if not video_path.exists():
        result["errors"].append("Arquivo não existe")
        return result

    if video_path.stat().st_size < 1_000_000:
        result["errors"].append(f"Arquivo muito pequeno ({video_path.stat().st_size} bytes)")
        return result

    # Verificar moov atom (ffprobe falha se corrompido)
    v_dur = get_video_duration(video_path)
    if v_dur <= 0:
        result["errors"].append("moov atom não encontrado ou arquivo corrompido")
        return result

    # Verificar duração áudio
    a_dur = get_audio_duration(video_path)
    if a_dur <= 0:
        result["errors"].append("Sem stream de áudio")
        return result

    # Tolerância de 5s entre áudio e vídeo
    diff = abs(v_dur - a_dur)
    if diff > 5:
        result["errors"].append(f"Áudio/vídeo dessincronizados (diff={diff:.1f}s)")
        return result

    result["valid"] = True
    result["duration"] = v_dur
    result["audio_duration"] = a_dur
    result["size_mb"] = video_path.stat().st_size / (1024 * 1024)
    return result


def build_landscape_video(input_videos: List[Path], output_path: Path, cap_label: str) -> bool:
    """
    Concatena vídeos verticais em formato paisagem com efeitos visuais.

    Pipeline:
    1. Concat demuxer (sem reencoding — rápido)
    2. Converter pra paisagem com efeitos laterais
    3. Adicionar trilha sonora (se disponível)
    4. Validar output
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_dir = output_path.parent / f"_tmp_{cap_label}"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    # ─── Passo 1: Concat demuxer ─────────────────────────────────────────────
    concat_list = tmp_dir / "concat.txt"
    with concat_list.open("w") as f:
        for v in input_videos:
            f.write(f"file '{v}'\n")

    tmp_concat = tmp_dir / "concat_raw.mp4"
    log(f"  [1/4] Concatenando {len(input_videos)} vídeos...")
    cmd_concat = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_list),
        "-c", "copy", str(tmp_concat)
    ]
    r = subprocess.run(cmd_concat, capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        log(f"  [X] Concat falhou: {r.stderr[-200:]}")
        return False

    # ─── Passo 2: Paisagem com efeitos laterais ───────────────────────────────
    # Efeito: vídeo vertical centralizado + laterais preenchidas com:
    # - Versão ampliada e borrada do próprio vídeo (parallax/breathing feel)
    # - Vinheta escura nas bordas
    # - Leve gradiente de cor nas laterais
    tmp_landscape = tmp_dir / "landscape.mp4"
    log(f"  [2/4] Renderizando paisagem {WIDTH}x{HEIGHT} com efeitos...")

    # Filter complex inspirado no effects_engine (Ken Burns nas laterais)
    # O vídeo vertical ocupa o centro; as laterais são o mesmo vídeo
    # ampliado + blur + vinheta + leve zoom lento (breathing)
    filter_complex = (
        # Split em 2: background (laterais) e foreground (centro)
        f"[0:v]split=2[bg][fg];"
        # Background: amplia pra preencher 1920x1080, blur pesado, escurece, vinheta
        f"[bg]scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
        f"crop={WIDTH}:{HEIGHT},"
        f"gblur=sigma=40,"
        f"eq=brightness=-0.2:saturation=0.7,"
        f"vignette=PI/3[blurred];"
        # Foreground: escala vertical pra caber com margem, mantém aspect ratio
        f"[fg]scale=-1:{HEIGHT - 60}:force_original_aspect_ratio=decrease,"
        f"pad=iw+4:ih+4:2:2:color=black@0.3[padded];"
        # Overlay centralizado
        f"[blurred][padded]overlay=(W-w)/2:(H-h)/2[out]"
    )

    cmd_landscape = [
        "ffmpeg", "-y", "-i", str(tmp_concat),
        "-filter_complex", filter_complex,
        "-map", "[out]", "-map", "0:a?",
        "-c:v", ENCODING["video_codec"],
        "-preset", ENCODING["preset"],
        "-crf", str(ENCODING["crf"]),
        "-pix_fmt", ENCODING["pix_fmt"],
        "-c:a", ENCODING["audio_codec"],
        "-b:a", ENCODING["audio_bitrate"],
        "-ar", str(ENCODING["audio_sample_rate"]),
        "-ac", str(ENCODING["audio_channels"]),
        "-r", str(ENCODING["fps"]),
        "-movflags", "+faststart",
        str(tmp_landscape)
    ]

    r = subprocess.run(cmd_landscape, capture_output=True, text=True, timeout=3600)
    if r.returncode != 0:
        log(f"  [X] Render paisagem falhou: {r.stderr[-300:]}")
        _cleanup(tmp_dir)
        return False

    # ─── Passo 3: Trilha sonora ───────────────────────────────────────────────
    trilha = find_trilha()
    if trilha:
        tmp_with_music = tmp_dir / "with_music.mp4"
        log(f"  [3/4] Adicionando trilha ({trilha.name})...")
        video_dur = get_video_duration(tmp_landscape)

        # amix com fade in/out (baseado na ref fábrica de animes v2.8)
        audio_filter = (
            f"[1:a]aloop=loop=-1:size=2e+09,atrim=0:{video_dur},"
            f"afade=t=in:st=0:d={TRILHA['fade_in']},"
            f"afade=t=out:st={video_dur - TRILHA['fade_out']}:d={TRILHA['fade_out']},"
            f"volume={TRILHA['volume']}[music];"
            f"[0:a][music]amix=inputs=2:duration=first:dropout_transition=2[aout]"
        )

        cmd_music = [
            "ffmpeg", "-y",
            "-i", str(tmp_landscape),
            "-i", str(trilha),
            "-filter_complex", audio_filter,
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", ENCODING["audio_codec"],
            "-b:a", ENCODING["audio_bitrate"],
            "-movflags", "+faststart",
            str(tmp_with_music)
        ]
        r = subprocess.run(cmd_music, capture_output=True, text=True, timeout=600)
        if r.returncode == 0:
            final_tmp = tmp_with_music
        else:
            log(f"  [!] Trilha falhou, seguindo sem música: {r.stderr[-150:]}")
            final_tmp = tmp_landscape
    else:
        log(f"  [3/4] Sem trilha disponível, prosseguindo...")
        final_tmp = tmp_landscape

    # ─── Passo 4: Validação e mover pra destino ───────────────────────────────
    log(f"  [4/4] Validando output...")
    validation = validate_output(final_tmp)

    if not validation["valid"]:
        log(f"  [X] Validação falhou: {validation['errors']}")
        _cleanup(tmp_dir)
        return False

    # Mover pro destino final
    import shutil
    shutil.move(str(final_tmp), str(output_path))
    _cleanup(tmp_dir)

    log(f"  [OK] {output_path.name} ({validation['size_mb']:.1f} MB, {validation['duration']/60:.1f} min)")
    return True


def _cleanup(tmp_dir: Path):
    """Remove diretório temporário."""
    import shutil
    try:
        shutil.rmtree(str(tmp_dir), ignore_errors=True)
    except:
        pass


def main():
    parser = argparse.ArgumentParser(description="Compilação crescente em formato paisagem")
    parser.add_argument("--caps", required=True, help="Range de capítulos (ex: 1-5)")
    parser.add_argument("--only-latest", action="store_true",
                        help="Gerar apenas a compilação completa (último vídeo)")
    parser.add_argument("--obra", default="the-meek-cat", help="Nome da obra")
    args = parser.parse_args()

    # Parse range
    if "-" in args.caps:
        start, end = args.caps.split("-")
        caps = list(range(int(start), int(end) + 1))
    else:
        caps = [int(c) for c in args.caps.split(",")]

    log(f"╔{'═'*58}╗")
    log(f"║  LANDSCAPE COMPILER — {args.obra}")
    log(f"║  Caps: {caps}")
    log(f"╚{'═'*58}╝")

    # Encontrar vídeos
    chapter_videos = {}
    for cap in caps:
        video = find_chapter_video(cap)
        if video:
            # Validar que não está corrompido
            dur = get_video_duration(video)
            if dur > 0:
                chapter_videos[cap] = video
                log(f"  Cap {cap}: {video.name} ({video.stat().st_size / (1024*1024):.0f} MB, {dur/60:.1f} min)")
            else:
                log(f"  Cap {cap}: [!] CORROMPIDO (moov atom) — pulando")
        else:
            log(f"  Cap {cap}: [!] VÍDEO NÃO ENCONTRADO — parando aqui")
            break

    if not chapter_videos:
        log("[X] Nenhum vídeo de capítulo encontrado")
        sys.exit(1)

    available_caps = sorted(chapter_videos.keys())
    log(f"\nCapítulos disponíveis: {available_caps}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Gerar compilações crescentes
    compilations = []
    if args.only_latest:
        compilations = [(available_caps, available_caps[-1])]
    else:
        for i in range(1, len(available_caps) + 1):
            subset = available_caps[:i]
            compilations.append((subset, subset[-1]))

    resultados = []
    for subset, last_cap in compilations:
        videos = [chapter_videos[c] for c in subset]
        cap_range = f"{subset[0]}-{subset[-1]}" if len(subset) > 1 else str(subset[0])
        output_name = f"{args.obra}_landscape_cap{cap_range}.mp4"
        output_path = OUTPUT_DIR / output_name

        # Se já existe e é válido, pular
        if output_path.exists() and output_path.stat().st_size > 1_000_000:
            v = validate_output(output_path)
            if v["valid"]:
                log(f"\n⏭ {output_name} já existe e é válido ({v['size_mb']:.0f} MB), pulando")
                resultados.append({"cap_range": cap_range, "status": "existente", "path": str(output_path)})
                continue
            else:
                log(f"\n[!] {output_name} existe mas inválido — regenerando")
                output_path.unlink()

        log(f"\n{'═'*60}")
        log(f"Compilação: caps {cap_range} ({len(videos)} vídeos)")
        log(f"{'═'*60}")

        ok = build_landscape_video(videos, output_path, cap_range)
        if ok:
            resultados.append({"cap_range": cap_range, "status": "ok", "path": str(output_path)})
        else:
            resultados.append({"cap_range": cap_range, "status": "falhou"})
            log(f"[X] Falha na compilação caps {cap_range}")

    # Resumo final
    log(f"\n{'═'*60}")
    log(f"RESUMO FINAL")
    log(f"{'═'*60}")
    for r in resultados:
        emoji = "✅" if r["status"] in ("ok", "existente") else "❌"
        log(f"  {emoji} caps {r['cap_range']}: {r['status']}")

    # Salvar relatório
    report_path = OUTPUT_DIR / "compilation_report.json"
    report_path.write_text(json.dumps({
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "obra": args.obra,
        "resultados": resultados
    }, indent=2))

    log("\n[OK] Compilação paisagem concluída!")


if __name__ == "__main__":
    main()
