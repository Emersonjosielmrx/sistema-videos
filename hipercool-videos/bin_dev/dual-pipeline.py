#!/usr/bin/env python3
"""dual-pipeline.py — Gera 4 vídeos a partir dos mesmos painéis/áudios.

Fluxo:
  1. Fase compartilhada (1x): Visão + Narração LLM + TTS -> gera áudios + descrições
  2. Ramificação A (Normal): Pipeline padrão com effects_engine -> vídeo + censurado
  3. Ramificação B (HyperFrames): Karaokê GSAP, animação breathing/parallax -> vídeo + censurado

Resultado: 4 arquivos MP4 na pasta workspace/videos/
  - hipercool_<slug>_<ts>_NORMAL.mp4
  - hipercool_<slug>_<ts>_NORMAL_CENSURADO.mp4
  - hipercool_<slug>_<ts>_HYPERFRAMES.mp4
  - hipercool_<slug>_<ts>_HYPERFRAMES_CENSURADO.mp4

Uso:
  python bin/dual-pipeline.py --panels-dir workspace/panels/the-meek-cat-cap01/ \\
      --titulo "The Meek Cat — Capítulo 1" --max-panels 120

NOTA: Os áudios são reusados do TTS cache. Esta execução NÃO consome tokens extras de
LLM/TTS a menos que --force-llm/--force-tts seja passado — nesse caso só o Branch A
os gera (o Branch B reusa do cache).
"""
import argparse
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
VIDEOS_DIR = PROJECT_DIR / "workspace" / "videos"
PYTHON = Path(sys.executable)  # cross-platform: usa o interpretador atual (venv Scripts/python.exe no Windows, venv/bin/python no *nix)

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", file=sys.stderr)

def run_branch(label, output_suffix, panels_dir, titulo, max_panels, extra_args=None):
    """Executa uma branch do pipeline (Normal ou HyperFrames).

    Usa --output-suffix para que o próprio hiper-pipeline.py nomeie os arquivos
    corretamente (sem necessidade de renomeação pós-execução).
    """
    cmd = [
        str(PYTHON), str(PROJECT_DIR / "bin" / "hiper-pipeline.py"),
        "--panels-dir", str(panels_dir),
        "--titulo", titulo,
        "--max-panels", str(max_panels),
        "--subtitles", "--karaoke", "--censura",
        "--output-suffix", f"_{output_suffix}",
        "--skip-notify",
    ]
    if extra_args:
        cmd.extend(extra_args)

    log(f"═══ BRANCH {label} ({output_suffix}) — {titulo} ═══")
    result = subprocess.run(cmd, capture_output=False,
                            timeout=int(os.environ.get("BRANCH_TIMEOUT_S", "21600")))  # default 6h (era 2h — quota fazia estourar)
    if result.returncode != 0:
        log(f"  [X] Branch {label} falhou (exit code {result.returncode})")
        return None

    # O hiper-pipeline.py deixa arquivos com _ULTIMO no final.
    # Precisamos renomeá-los para o nome final sem _ULTIMO.
    slug = re.sub(r"[^a-z0-9]+", "-", titulo.lower().strip())[:60]

    # Renomear *_{output_suffix}_ULTIMO.mp4 -> *_{output_suffix}.mp4
    for f in VIDEOS_DIR.glob(f"hipercool_{slug}_*{output_suffix}_ULTIMO.mp4"):
        new_name = f.with_name(f.name.replace("_ULTIMO", ""))
        f.rename(new_name)
        log(f"  [OK] {label}: {new_name.name} ({new_name.stat().st_size / (1024 * 1024):.1f} MB)")

    # Renomear *_{output_suffix}_CENSURADO_ULTIMO.mp4 -> *_{output_suffix}_CENSURADO.mp4
    for f in VIDEOS_DIR.glob(f"hipercool_{slug}_*{output_suffix}_CENSURADO_ULTIMO.mp4"):
        new_name = f.with_name(f.name.replace("_ULTIMO", ""))
        f.rename(new_name)
        log(f"  [OK] {label} censurado: {new_name.name} ({new_name.stat().st_size / (1024 * 1024):.1f} MB)")

    # Verificar se pelo menos o vídeo não-censurado foi gerado
    main_video = sorted(
        VIDEOS_DIR.glob(f"hipercool_{slug}_*{output_suffix}.mp4"),
        key=os.path.getmtime, reverse=True
    )
    if main_video:
        return main_video[0]
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Dual pipeline: gera 4 vídeos (Normal + HyperFrames, cada um + censurado)")
    parser.add_argument("--panels-dir", required=True,
                        help="Diretório com painéis já cortados")
    parser.add_argument("--titulo", "-t", required=True,
                        help="Título do manhwa/capítulo")
    parser.add_argument("--max-panels", type=int, default=120)
    parser.add_argument("--force-llm", action="store_true",
                        help="Força nova narração LLM (só no primeiro branch)")
    parser.add_argument("--force-tts", action="store_true",
                        help="Força nova geração TTS (só no primeiro branch)")
    args = parser.parse_args()

    panels_dir = Path(args.panels_dir)
    if not panels_dir.is_dir():
        print(f"ERRO: {panels_dir} não existe", file=sys.stderr)
        sys.exit(1)

    log(f"╔══════════════════════════════════════════════════════════════╗")
    log(f"║  DUAL PIPELINE: {args.titulo}")
    log(f"║  Painéis: {panels_dir}")
    log(f"║  Saída: 4 vídeos (Normal + HyperFrames × Original + Censurado)")
    log(f"╚══════════════════════════════════════════════════════════════╝")

    start_time = time.time()

    # ─── Branch A: Normal ────────────────────────────────────────────
    extra_a = []
    if args.force_llm:
        extra_a.append("--force-llm")
    if args.force_tts:
        extra_a.append("--force-tts")

    video_a = run_branch(
        label="A",
        output_suffix="NORMAL",
        panels_dir=panels_dir,
        titulo=args.titulo,
        max_panels=args.max_panels,
        extra_args=extra_a,
    )

    # ─── Branch B: HyperFrames (reusa cache de narração/TTS) ────────
    video_b = run_branch(
        label="B",
        output_suffix="HYPERFRAMES",
        panels_dir=panels_dir,
        titulo=args.titulo,
        max_panels=args.max_panels,
        extra_args=["--animated", "--hyperframes-karaoke"],
    )

    elapsed = time.time() - start_time
    log(f"\n╔══════════════════════════════════════════════════════════════╗")
    log(f"║  RESULTADO FINAL ({elapsed/60:.1f} min)")
    log(f"║")
    for label, v in [("NORMAL", video_a), ("HYPERFRAMES", video_b)]:
        if v:
            log(f"║  [OK] {label:12s}: {v.name}")
        else:
            log(f"║  [X] {label:12s}: FALHOU")
    log(f"║")
    log(f"║  Versões CENSURADAS geradas junto (se houver painéis +18)")
    log(f"╚══════════════════════════════════════════════════════════════╝")

    # Listar todos os vídeos gerados
    slug = re.sub(r"[^a-z0-9]+", "-", args.titulo.lower().strip())[:60]
    all_videos = sorted(VIDEOS_DIR.glob(f"hipercool_{slug}_*.mp4"),
                        key=os.path.getmtime, reverse=True)
    if all_videos:
        log(f"\n  Vídeos gerados para '{args.titulo}':")
        for v in all_videos[:8]:
            if "_CENSURADO" in v.name or "_NORMAL" in v.name or "_HYPERFRAMES" in v.name:
                size_mb = v.stat().st_size / (1024 * 1024)
                log(f"    • {v.name} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
