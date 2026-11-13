# -*- coding: utf-8 -*-
"""teste_extend_video.py — Testa extensão de vídeo via Flow Labs.

Pega um vídeo base (8s) e vai encadeando extend() pra ver até onde chega.
Cada iteração estende o resultado anterior, gerando:
  base.mp4 (8s) → base_ext1.mp4 (~16s) → base_ext2.mp4 (~24s) → ...

Uso:
  PYTHONUTF8=1 python teste_extend_video.py [--video PATH] [--conta APELIDO] [--max-ext N] [--prompt TEXTO]

Se --video não for passado, gera um vídeo novo de 8s primeiro.
"""
import argparse
import os
import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).resolve().parent.parent
VEO_BETA = Path("D:/veo/beta")
sys.path.insert(0, str(VEO_BETA))

FFPROBE = r"D:\hipercool-materiais\bin\ffprobe.exe"
OUT_DIR = BASE / "videos" / "extend_test"
OUT_DIR.mkdir(parents=True, exist_ok=True)

CONTA_SOLAR = "mundosolar1995"


def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"  [{ts}] {msg}", flush=True)


def duracao(path):
    try:
        r = subprocess.run(
            [FFPROBE, "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", str(path)],
            capture_output=True, text=True, timeout=15)
        return float(r.stdout.strip())
    except Exception:
        return 0.0


def tem_audio(path):
    try:
        r = subprocess.run(
            [FFPROBE, "-v", "error", "-select_streams", "a",
             "-show_entries", "stream=codec_type", "-of", "csv=p=0", str(path)],
            capture_output=True, text=True, timeout=15)
        return "audio" in r.stdout.strip()
    except Exception:
        return False


def gerar_video_base(conta, prompt_base=None):
    """Gera um vídeo de 8s como semente pra extensão."""
    import flow_bot
    prompt = prompt_base or (
        "A person standing on a rooftop with solar panels, speaking excitedly "
        "to camera about saving money on electricity. Bright sunlight, "
        "vibrant colors. 9:16 vertical portrait."
    )
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = str(OUT_DIR / f"base_{stamp}.mp4")
    log(f"Gerando vídeo base com conta '{conta}'...")
    path = flow_bot.generate(
        apelido=conta,
        prompt=prompt,
        out_path=out,
        log=log,
        aspect_ratio="9:16",
        duration="8S",
        model="Veo 3.1 - Fast",
        audio="Generate",
    )
    if path and Path(path).exists():
        dur = duracao(path)
        audio = tem_audio(path)
        log(f"Base OK: {dur:.1f}s, audio={'SIM' if audio else 'NAO'}, {path}")
        return path
    raise RuntimeError("Falha ao gerar vídeo base")


def estender(conta, video_path, iteracao, extend_prompt=None):
    """Estende o vídeo e retorna o path do resultado."""
    import flow_bot
    prompt = extend_prompt or "extend this video, continue the same scene smoothly with the same style and energy"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = str(OUT_DIR / f"ext{iteracao}_{stamp}.mp4")
    log(f"--- Extensão #{iteracao} ---")
    log(f"Input: {video_path} ({duracao(video_path):.1f}s)")
    path = flow_bot.extend(
        apelido=conta,
        video_path=video_path,
        extend_prompt=prompt,
        out_path=out,
        log=log,
        model="Veo 3.1 - Fast",
        audio="Generate",
    )
    if path and Path(path).exists():
        dur = duracao(path)
        audio = tem_audio(path)
        log(f"Ext#{iteracao} OK: {dur:.1f}s, audio={'SIM' if audio else 'NAO'}, {path}")
        return path
    raise RuntimeError(f"Extensão #{iteracao} falhou")


def main():
    parser = argparse.ArgumentParser(description="Teste de extensão de vídeo via Flow Labs")
    parser.add_argument("--video", help="Vídeo base (pula geração se passado)")
    parser.add_argument("--conta", default=CONTA_SOLAR, help=f"Conta CDP (default: {CONTA_SOLAR})")
    parser.add_argument("--max-ext", type=int, default=5, help="Máximo de extensões (default: 5)")
    parser.add_argument("--prompt", help="Prompt de extensão customizado")
    parser.add_argument("--prompt-base", help="Prompt pra geração do vídeo base")
    args = parser.parse_args()

    print("=" * 60)
    print("  TESTE DE EXTENSÃO DE VÍDEO — Flow Labs / Veo 3.1")
    print("=" * 60)
    print(f"  Conta: {args.conta}")
    print(f"  Max extensões: {args.max_ext}")
    print(f"  Saída: {OUT_DIR}")
    print()

    # 1) Vídeo base
    if args.video:
        video_atual = args.video
        if not Path(video_atual).exists():
            print(f"ERRO: vídeo não encontrado: {video_atual}")
            sys.exit(1)
        log(f"Usando vídeo base existente: {video_atual} ({duracao(video_atual):.1f}s)")
    else:
        try:
            video_atual = gerar_video_base(args.conta, args.prompt_base)
        except Exception as e:
            print(f"ERRO gerando base: {e}")
            sys.exit(1)

    # 2) Loop de extensões
    resultados = [{"iter": 0, "path": video_atual, "dur": duracao(video_atual), "audio": tem_audio(video_atual)}]

    for i in range(1, args.max_ext + 1):
        try:
            video_atual = estender(args.conta, video_atual, i, args.prompt)
            dur = duracao(video_atual)
            audio = tem_audio(video_atual)
            resultados.append({"iter": i, "path": video_atual, "dur": dur, "audio": audio})
            log(f"Acumulado: {dur:.1f}s total")
        except Exception as e:
            log(f"Extensão #{i} FALHOU: {e}")
            log("Parando aqui.")
            break

    # 3) Relatório
    print()
    print("=" * 60)
    print("  RELATÓRIO FINAL")
    print("=" * 60)
    print(f"  {'#':<5} {'Duração':<12} {'Áudio':<8} {'Arquivo'}")
    print(f"  {'-'*5} {'-'*12} {'-'*8} {'-'*40}")
    for r in resultados:
        label = "base" if r["iter"] == 0 else f"ext{r['iter']}"
        print(f"  {label:<5} {r['dur']:>8.1f}s   {'SIM' if r['audio'] else 'NAO':<8} {Path(r['path']).name}")

    dur_final = resultados[-1]["dur"]
    dur_base = resultados[0]["dur"]
    print()
    print(f"  Base: {dur_base:.1f}s → Final: {dur_final:.1f}s ({len(resultados)-1} extensões)")
    print(f"  Ganho: +{dur_final - dur_base:.1f}s ({dur_final/dur_base:.1f}x)")
    print()


if __name__ == "__main__":
    main()
