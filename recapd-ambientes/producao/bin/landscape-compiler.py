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
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional

WORKSPACE = Path(__file__).resolve().parent.parent / "workspace"
VIDEOS_DIR = WORKSPACE / "videos"
OUTPUT_DIR = WORKSPACE / "videos" / "landscape"
ASSETS_DIR = WORKSPACE / "assets"
WATERMARK = "@InovareManhwaVerse"

# Resolução final
WIDTH = 1920
HEIGHT = 1080

# Encoding (baseado na referência fábrica de animes v2.8)
ENCODING = {
    "crf": 28,
    "preset": "ultrafast",
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


def find_chapter_video(cap_num, engine="edge") -> Optional[Path]:
    """Encontra o melhor vídeo NORMAL de um capítulo na estrutura edge/gemini."""
    cap_key = f"cap{int(cap_num):02d}"

    # 1. Estrutura nova: obra/capXX/{engine}/normal/vN.mp4
    for obra_dir in sorted(VIDEOS_DIR.iterdir()):
        if obra_dir.is_dir() and obra_dir.name not in ("landscape", "anteriores", "stable"):
            # Preferir gemini se existir, senão edge
            for eng in ([engine, "gemini", "edge"] if engine == "gemini" else [engine, "edge"]):
                normal_dir = obra_dir / cap_key / eng / "normal"
                if normal_dir.exists():
                    versoes = sorted(normal_dir.glob("v*.mp4"))
                    if versoes:
                        return versoes[-1]

    # 2. Fallback: estrutura antiga (obra/capXX/normal/)
    for obra_dir in sorted(VIDEOS_DIR.iterdir()):
        if obra_dir.is_dir() and obra_dir.name not in ("landscape", "anteriores", "stable"):
            normal_dir = obra_dir / cap_key / "normal"
            if normal_dir.exists():
                versoes = sorted(normal_dir.glob("v*.mp4"))
                if versoes:
                    return versoes[-1]

    return None


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


def _concat_copy(videos, out_path, tmp_dir, tag):
    """Concat demuxer (-c copy) de uma lista. Retorna True/False."""
    lst = tmp_dir / f"_cc_{tag}.txt"
    with lst.open("w", encoding="utf-8") as f:
        for v in videos:
            f.write(f"file '{Path(v).as_posix()}'\n")
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(out_path)]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=1200)
        return r.returncode == 0 and Path(out_path).exists() and Path(out_path).stat().st_size > 0
    except Exception:
        return False


def concat_hierarquico(input_videos, out_path, tmp_dir):
    """T11: merge em ÁRVORE com retry adaptativo (porte do fluxo 4).
    Junta em grupos de batch (default 30); se um grupo falha, reduz o batch (×0.5, min 5) e
    refaz; depois mergeia os resultados, nível a nível, até sobrar 1. Limpa temporários de
    níveis anteriores. Retorna True/False. Atrás de LS_HIERARCHICAL=1 no caller."""
    batch = int(os.environ.get("LS_BATCH", "30"))
    min_batch = 5
    nivel = 0
    atuais = [str(v) for v in input_videos]
    if len(atuais) <= 1:
        if atuais:
            import shutil as _sh
            _sh.copy2(atuais[0], out_path)
            return True
        return False
    while len(atuais) > 1 and nivel < 10:
        nivel += 1
        proximos = []
        i = 0
        gidx = 0
        b = batch
        while i < len(atuais):
            grupo = atuais[i:i + b]
            gout = tmp_dir / f"_h{nivel}_{gidx}.mp4"
            if len(grupo) == 1:
                proximos.append(grupo[0]); i += b; gidx += 1; continue
            ok = _concat_copy(grupo, gout, tmp_dir, f"{nivel}_{gidx}")
            if not ok:
                # retry adaptativo: reduz o batch e refaz ESTE grupo
                nb = max(min_batch, int(b * 0.5))
                if nb < b:
                    log(f"  [hier] nível {nivel} grupo {gidx} falhou (n={len(grupo)}) → batch {b}→{nb}")
                    b = nb
                    continue  # reprocessa do mesmo i com batch menor
                log(f"  ✗ [hier] grupo {gidx} falhou mesmo com batch mínimo")
                return False
            proximos.append(str(gout)); i += b; gidx += 1
        log(f"  [hier] nível {nivel}: {len(atuais)} → {len(proximos)}")
        atuais = proximos
    if len(atuais) == 1:
        import shutil as _sh
        _sh.copy2(atuais[0], out_path)
        return True
    return False


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
    # T11: merge hierárquico (LS_HIERARCHICAL=1) — robusto p/ muitos vídeos. Senão, concat único.
    if os.environ.get("LS_HIERARCHICAL", "0") == "1" and len(input_videos) > 1:
        log(f"  [1/4] modo HIERÁRQUICO (árvore + retry adaptativo)")
        if not concat_hierarquico(input_videos, tmp_concat, tmp_dir):
            log("  ✗ Concat hierárquico falhou")
            return False
    else:
        cmd_concat = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(concat_list),
            "-c", "copy", str(tmp_concat)
        ]
        r = subprocess.run(cmd_concat, capture_output=True, text=True, timeout=600)
        if r.returncode != 0:
            log(f"  ✗ Concat falhou: {r.stderr[-200:]}")
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
    # T10 (LS_FILTERS=1): troca o blur fixo por um fundo 16:9 do banco (fluxo 3,
    # anti-repetição). Fallback total → blur fixo se o módulo falhar.
    filter_complex = None
    if os.environ.get("LS_FILTERS", "0") == "1":
        try:
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            import landscape_filters as _lf
            _nome, _fc = _lf.pick_filter(WIDTH, HEIGHT)
            filter_complex = _fc + "[out]"
            log(f"  [LS_FILTERS] fundo 16:9: {_nome}")
        except Exception as _e:
            log(f"  ⚠ LS_FILTERS falhou ({_e}) → blur fixo")
            filter_complex = None
    if filter_complex is None:
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

    r = subprocess.run(cmd_landscape, capture_output=True, text=True, timeout=14400)
    if r.returncode != 0:
        log(f"  ✗ Render paisagem falhou: {r.stderr[-300:]}")
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
            log(f"  ⚠ Trilha falhou, seguindo sem música: {r.stderr[-150:]}")
            final_tmp = tmp_landscape
    else:
        log(f"  [3/4] Sem trilha disponível, prosseguindo...")
        final_tmp = tmp_landscape

    # ─── Passo 4: Validação e mover pra destino ───────────────────────────────
    log(f"  [4/4] Validando output...")
    validation = validate_output(final_tmp)

    if not validation["valid"]:
        log(f"  ✗ Validação falhou: {validation['errors']}")
        _cleanup(tmp_dir)
        return False

    # Mover pro destino final
    import shutil
    shutil.move(str(final_tmp), str(output_path))
    _cleanup(tmp_dir)

    log(f"  ✓ {output_path.name} ({validation['size_mb']:.1f} MB, {validation['duration']/60:.1f} min)")
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
    parser.add_argument("--engine", default="edge", choices=["edge", "gemini"],
                        help="Qual engine de voz usar como fonte (edge ou gemini)")
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
        video = find_chapter_video(cap, engine=args.engine)
        if video:
            # Validar que não está corrompido
            dur = get_video_duration(video)
            if dur > 0:
                chapter_videos[cap] = video
                log(f"  Cap {cap}: {video.name} ({video.stat().st_size / (1024*1024):.0f} MB, {dur/60:.1f} min)")
            else:
                log(f"  Cap {cap}: ⚠ CORROMPIDO (moov atom) — pulando")
        else:
            log(f"  Cap {cap}: ⚠ VÍDEO NÃO ENCONTRADO — parando aqui")
            break

    if not chapter_videos:
        log("✗ Nenhum vídeo de capítulo encontrado")
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
                log(f"\n⚠ {output_name} existe mas inválido — regenerando")
                output_path.unlink()

        log(f"\n{'═'*60}")
        log(f"Compilação: caps {cap_range} ({len(videos)} vídeos)")
        log(f"{'═'*60}")

        ok = build_landscape_video(videos, output_path, cap_range)
        if ok:
            resultados.append({"cap_range": cap_range, "status": "ok", "path": str(output_path)})
        else:
            resultados.append({"cap_range": cap_range, "status": "falhou"})
            log(f"✗ Falha na compilação caps {cap_range}")

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

    log("\n✓ Compilação paisagem concluída!")


if __name__ == "__main__":
    main()
