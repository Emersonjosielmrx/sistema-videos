#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gerar_shorts.py — Gera shorts (clipes verticais) a partir de segmentos.

Extrai trechos do vídeo e formata para shorts (9:16, até 60s).
"""
import sys
import subprocess
import json
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def extrair_segmento(video_input, inicio, duracao, video_output):
    """Extrai um segmento do vídeo.

    Args:
        video_input: caminho do vídeo original
        inicio: timestamp inicial (segundos)
        duracao: duração do segmento (segundos)
        video_output: caminho do vídeo de saída

    Returns:
        True se sucesso, False caso contrário
    """
    cmd = [
        "ffmpeg",
        "-y",
        "-ss", str(inicio),
        "-i", str(video_input),
        "-t", str(duracao),
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "23",
        "-c:a", "copy",
        str(video_output)
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,
            encoding="utf-8",
            errors="replace"
        )

        return result.returncode == 0

    except Exception as e:
        print(f"[gerar_shorts] Erro ao extrair segmento: {e}", file=sys.stderr)
        return False


def formatar_short(video_input, video_output, target_width=1080, target_height=1920):
    """Formata vídeo para short (vertical 9:16).

    Args:
        video_input: vídeo horizontal
        video_output: vídeo vertical formatado
        target_width: largura alvo (padrão 1080)
        target_height: altura alvo (padrão 1920)

    Returns:
        True se sucesso, False caso contrário
    """
    # Estratégia: scale para caber na altura, depois crop central para a largura
    vf = f"scale=-1:{target_height},crop={target_width}:{target_height}"

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
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,
            encoding="utf-8",
            errors="replace"
        )

        return result.returncode == 0

    except Exception as e:
        print(f"[gerar_shorts] Erro ao formatar short: {e}", file=sys.stderr)
        return False


def gerar_short_de_segmento(video_input, segmento, pasta_saida, indice):
    """Gera um short a partir de um segmento.

    Args:
        video_input: vídeo original
        segmento: dict com {inicio, fim, categoria, canal}
        pasta_saida: pasta para salvar o short
        indice: índice do segmento

    Returns:
        Caminho do short gerado ou None
    """
    pasta_saida = Path(pasta_saida)
    pasta_saida.mkdir(parents=True, exist_ok=True)

    inicio = segmento["inicio"]
    fim = segmento["fim"]
    duracao = fim - inicio

    # Shorts têm limite de 60s
    if duracao > 60:
        duracao = 60
        print(f"[gerar_shorts] Segmento {indice} truncado para 60s", file=sys.stderr)

    if duracao < 5:
        print(f"[gerar_shorts] Segmento {indice} muito curto ({duracao:.1f}s), pulando", file=sys.stderr)
        return None

    categoria = segmento.get("categoria", "geral")

    # Nome do arquivo
    nome_base = f"short_{indice:02d}_{categoria}"
    temp_segmento = pasta_saida / f"{nome_base}_temp.mp4"
    short_final = pasta_saida / f"{nome_base}.mp4"

    print(f"[gerar_shorts] Gerando short {indice}: {categoria} ({duracao:.1f}s)", file=sys.stderr)

    # 1. Extrai o segmento
    if not extrair_segmento(video_input, inicio, duracao, temp_segmento):
        print(f"[gerar_shorts] Falha ao extrair segmento {indice}", file=sys.stderr)
        return None

    # 2. Formata para vertical (9:16)
    if not formatar_short(temp_segmento, short_final):
        print(f"[gerar_shorts] Falha ao formatar short {indice}", file=sys.stderr)
        temp_segmento.unlink(missing_ok=True)
        return None

    # Limpa temporário
    temp_segmento.unlink(missing_ok=True)

    print(f"[gerar_shorts] ✓ Short {indice} criado: {short_final.name}", file=sys.stderr)
    return short_final


def gerar_shorts_de_segmentos(video_input, segmentos, pasta_saida):
    """Gera shorts de todos os segmentos.

    Args:
        video_input: vídeo original
        segmentos: lista de segmentos (resultado de segmentar_video.py)
        pasta_saida: pasta para salvar os shorts

    Returns:
        Lista de shorts gerados: [{"path", "categoria", "canal", "duracao"}]
    """
    video_input = Path(video_input)
    if not video_input.exists():
        print(f"[gerar_shorts] Vídeo não encontrado: {video_input}", file=sys.stderr)
        return []

    shorts_gerados = []

    for i, seg in enumerate(segmentos, start=1):
        short_path = gerar_short_de_segmento(video_input, seg, pasta_saida, i)

        if short_path:
            shorts_gerados.append({
                "path": str(short_path),
                "categoria": seg.get("categoria", "geral"),
                "canal": seg.get("canal"),
                "duracao": seg["fim"] - seg["inicio"]
            })

    print(f"\n[gerar_shorts] {len(shorts_gerados)}/{len(segmentos)} shorts gerados", file=sys.stderr)
    return shorts_gerados


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: gerar_shorts.py <video_path> <segmentos_json> [pasta_saida]", file=sys.stderr)
        print("  video_path: vídeo original", file=sys.stderr)
        print("  segmentos_json: arquivo JSON com segmentos (de segmentar_video.py)", file=sys.stderr)
        print("  pasta_saida: opcional, padrão = mesmo diretório do vídeo/shorts/", file=sys.stderr)
        sys.exit(1)

    video_path = Path(sys.argv[1])
    segmentos_path = Path(sys.argv[2])

    if len(sys.argv) > 3:
        pasta_saida = Path(sys.argv[3])
    else:
        pasta_saida = video_path.parent / "shorts"

    if not video_path.exists():
        print(f"Vídeo não encontrado: {video_path}", file=sys.stderr)
        sys.exit(1)

    if not segmentos_path.exists():
        print(f"Arquivo de segmentos não encontrado: {segmentos_path}", file=sys.stderr)
        sys.exit(1)

    with open(segmentos_path, "r", encoding="utf-8") as f:
        dados_segmentos = json.load(f)

    segmentos = dados_segmentos.get("segmentos", [])

    if not segmentos:
        print("Nenhum segmento encontrado no JSON", file=sys.stderr)
        sys.exit(1)

    shorts = gerar_shorts_de_segmentos(video_path, segmentos, pasta_saida)

    # Salva resultado
    resultado_json = pasta_saida / "shorts_gerados.json"
    with open(resultado_json, "w", encoding="utf-8") as f:
        json.dump({
            "video_original": str(video_path),
            "num_shorts": len(shorts),
            "shorts": shorts
        }, f, ensure_ascii=False, indent=2)

    print(f"\nResultado salvo em: {resultado_json}", file=sys.stderr)
