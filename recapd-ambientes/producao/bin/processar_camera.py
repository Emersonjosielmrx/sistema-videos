#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""processar_camera.py — Processa vídeo com crop/upscale para isolar câmera.

Aplica crop fixo 600×490 de (x=60, y=0) e upscale para Full HD 1920×1080.
Otimizado para velocidade com preset ultrafast.
"""
import sys
import subprocess
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def processar_camera_isolada(video_input, video_output, crop_params=None):
    """Processa vídeo isolando apenas a câmera.

    Args:
        video_input: caminho do vídeo original
        video_output: caminho do vídeo processado
        crop_params: dict com {w, h, x, y} ou None para padrão fixo

    Returns:
        True se sucesso, False caso contrário
    """
    video_input = Path(video_input)
    video_output = Path(video_output)

    if not video_input.exists():
        print(f"[processar_camera] Erro: vídeo não encontrado: {video_input}", file=sys.stderr)
        return False

    # Parâmetros fixos de crop (mesmos do processamento manual anterior)
    if crop_params is None:
        crop_params = {
            "w": 600,
            "h": 490,
            "x": 60,
            "y": 0
        }

    crop_w = crop_params["w"]
    crop_h = crop_params["h"]
    crop_x = crop_params["x"]
    crop_y = crop_params["y"]

    # Dimensões finais Full HD
    final_w = 1920
    final_h = 1080

    print(f"[processar_camera] Processando {video_input.name}", file=sys.stderr)
    print(f"[processar_camera] Crop: {crop_w}×{crop_h} de ({crop_x},{crop_y})", file=sys.stderr)
    print(f"[processar_camera] Upscale: {final_w}×{final_h}", file=sys.stderr)

    # Filtro FFmpeg: crop + scale
    vf = f"crop={crop_w}:{crop_h}:{crop_x}:{crop_y},scale={final_w}:{final_h}:flags=fast_bilinear"

    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(video_input),
        "-vf", vf,
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "23",
        "-c:a", "copy",
        str(video_output)
    ]

    try:
        print(f"[processar_camera] Executando FFmpeg...", file=sys.stderr)
        inicio = time.time()

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=1800,
            encoding="utf-8",
            errors="replace"
        )

        duracao = time.time() - inicio

        if result.returncode != 0:
            print(f"[processar_camera] FFmpeg falhou (rc={result.returncode})", file=sys.stderr)
            print(f"[processar_camera] stderr: {result.stderr[-500:]}", file=sys.stderr)
            return False

        # Aguarda 5 segundos para garantir que o arquivo está completamente escrito
        time.sleep(5)

        # Verifica se o arquivo foi criado e é válido
        if not video_output.exists():
            print(f"[processar_camera] Erro: arquivo de saída não foi criado", file=sys.stderr)
            return False

        # Verifica integridade com ffprobe
        probe_cmd = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height,duration",
            "-of", "csv=p=0",
            str(video_output)
        ]

        probe_result = subprocess.run(
            probe_cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        if probe_result.returncode != 0:
            print(f"[processar_camera] Erro: arquivo corrompido (ffprobe falhou)", file=sys.stderr)
            return False

        # Parse das dimensões
        try:
            info = probe_result.stdout.strip().split(",")
            width = int(info[0])
            height = int(info[1])

            if width != final_w or height != final_h:
                print(f"[processar_camera] AVISO: dimensões incorretas {width}×{height}", file=sys.stderr)

            print(f"[processar_camera] ✓ Processado: {width}×{height} em {duracao:.1f}s", file=sys.stderr)
            return True

        except (ValueError, IndexError) as e:
            print(f"[processar_camera] Erro ao validar dimensões: {e}", file=sys.stderr)
            return False

    except subprocess.TimeoutExpired:
        print(f"[processar_camera] Timeout (>30min)", file=sys.stderr)
        return False
    except Exception as e:
        print(f"[processar_camera] Erro: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False


def processar_lote(pasta_entrada, pasta_saida, sufixo="_fullhd"):
    """Processa todos os vídeos de uma pasta.

    Args:
        pasta_entrada: pasta com vídeos originais
        pasta_saida: pasta para vídeos processados
        sufixo: sufixo adicionado ao nome do arquivo

    Returns:
        Número de vídeos processados com sucesso
    """
    pasta_entrada = Path(pasta_entrada)
    pasta_saida = Path(pasta_saida)

    if not pasta_entrada.exists():
        print(f"[processar_camera] Pasta de entrada não existe: {pasta_entrada}", file=sys.stderr)
        return 0

    pasta_saida.mkdir(parents=True, exist_ok=True)

    # Lista vídeos
    videos = list(pasta_entrada.glob("*.mp4"))
    videos.extend(pasta_entrada.glob("*.mkv"))
    videos.extend(pasta_entrada.glob("*.avi"))

    if not videos:
        print(f"[processar_camera] Nenhum vídeo encontrado em {pasta_entrada}", file=sys.stderr)
        return 0

    print(f"[processar_camera] Encontrados {len(videos)} vídeos", file=sys.stderr)

    sucessos = 0
    for video in videos:
        nome_saida = video.stem + sufixo + video.suffix
        caminho_saida = pasta_saida / nome_saida

        if caminho_saida.exists():
            print(f"[processar_camera] Pulando {video.name} (já processado)", file=sys.stderr)
            continue

        if processar_camera_isolada(video, caminho_saida):
            sucessos += 1
        else:
            print(f"[processar_camera] Falha ao processar {video.name}", file=sys.stderr)

    return sucessos


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: processar_camera.py <video_entrada> <video_saida>", file=sys.stderr)
        print("  ou: processar_camera.py --lote <pasta_entrada> <pasta_saida>", file=sys.stderr)
        sys.exit(1)

    if sys.argv[1] == "--lote":
        if len(sys.argv) < 4:
            print("Uso: processar_camera.py --lote <pasta_entrada> <pasta_saida>", file=sys.stderr)
            sys.exit(1)

        pasta_in = sys.argv[2]
        pasta_out = sys.argv[3]

        n = processar_lote(pasta_in, pasta_out)
        print(f"\n[processar_camera] {n} vídeos processados com sucesso", file=sys.stderr)
        sys.exit(0 if n > 0 else 1)

    else:
        video_in = sys.argv[1]
        video_out = sys.argv[2]

        sucesso = processar_camera_isolada(video_in, video_out)
        sys.exit(0 if sucesso else 1)
