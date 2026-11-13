#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""segmentar_video.py — Segmenta vídeo temporal e visualmente.

Detecta mudanças de tema (temporal) e mudanças visuais (câmera vs tela).
Retorna lista de segmentos com timestamps e tipo de conteúdo.
"""
import sys
import json
import subprocess
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def detectar_cenas_ffmpeg(video_path, threshold=0.4):
    """Detecta mudanças de cena via ffmpeg scene detection.

    Args:
        video_path: caminho do vídeo
        threshold: sensibilidade (0.0-1.0, padrão 0.4 = moderado)

    Returns:
        Lista de timestamps (segundos) onde há mudança visual significativa
    """
    print(f"[segmentar] Detectando cenas em {video_path}...", file=sys.stderr)

    cmd = [
        "ffmpeg", "-i", str(video_path),
        "-vf", f"select='gt(scene,{threshold})',showinfo",
        "-f", "null", "-"
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

        # Parse dos timestamps do showinfo
        cenas = []
        for line in result.stderr.splitlines():
            if "pts_time:" in line:
                try:
                    # Formato: pts_time:123.456
                    pts = line.split("pts_time:")[1].split()[0]
                    timestamp = float(pts)
                    cenas.append(timestamp)
                except (ValueError, IndexError):
                    continue

        print(f"[segmentar] {len(cenas)} mudanças de cena detectadas", file=sys.stderr)
        return sorted(cenas)

    except subprocess.TimeoutExpired:
        print("[segmentar] Timeout na detecção de cenas", file=sys.stderr)
        return []
    except Exception as e:
        print(f"[segmentar] Erro na detecção de cenas: {e}", file=sys.stderr)
        return []


def detectar_tipo_visual(video_path, timestamp, duracao_sample=2.0):
    """Detecta se um segmento é câmera ou tela compartilhada.

    Heurística simplificada: analisa mudanças de cena via ffmpeg.
    Muitas mudanças = tela (interface com animações).
    Poucas mudanças = câmera (pessoa relativamente estática).

    Args:
        video_path: caminho do vídeo
        timestamp: momento a analisar (segundos)
        duracao_sample: duração do sample a analisar

    Returns:
        "camera" ou "tela"
    """
    try:
        # Extrai sample do vídeo e conta frames com mudanças
        cmd = [
            "ffmpeg",
            "-ss", str(timestamp),
            "-i", str(video_path),
            "-t", str(duracao_sample),
            "-vf", "select='gt(scene,0.3)',showinfo",
            "-f", "null", "-"
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            encoding="utf-8",
            errors="replace"
        )

        # Conta quantas mudanças de cena no sample
        mudancas = result.stderr.count("pts_time:")

        # Heurística: > 3 mudanças em 2s = tela (interface animada)
        # <= 3 mudanças = câmera (pessoa parada ou se movendo pouco)
        if mudancas > 3:
            return "tela"
        else:
            return "camera"

    except Exception as e:
        print(f"[segmentar] Erro na detecção visual: {e}", file=sys.stderr)
        # Fallback: assume câmera
        return "camera"


def segmentar_por_tema(temas_classificados):
    """Agrupa temas consecutivos iguais em segmentos temporais.

    Args:
        temas_classificados: lista de {"categoria", "inicio", "fim", "confianca"}

    Returns:
        Lista de segmentos: {"categoria", "inicio", "fim", "canal"}
    """
    if not temas_classificados:
        return []

    segmentos = []
    tema_atual = None
    inicio_atual = None
    fim_atual = None
    canal_atual = None

    for tema in sorted(temas_classificados, key=lambda x: x.get("inicio", 0)):
        categoria = tema["categoria"]
        canal = tema.get("canal")
        inicio = tema.get("inicio", 0)
        fim = tema.get("fim", inicio + 30)  # fallback: 30s

        # Se mudou o tema, fecha o segmento anterior e abre novo
        if tema_atual != categoria:
            if tema_atual is not None:
                segmentos.append({
                    "categoria": tema_atual,
                    "canal": canal_atual,
                    "inicio": inicio_atual,
                    "fim": fim_atual
                })

            tema_atual = categoria
            canal_atual = canal
            inicio_atual = inicio
            fim_atual = fim
        else:
            # Mesmo tema, estende o segmento
            fim_atual = fim

    # Fecha último segmento
    if tema_atual is not None:
        segmentos.append({
            "categoria": tema_atual,
            "canal": canal_atual,
            "inicio": inicio_atual,
            "fim": fim_atual
        })

    return segmentos


def segmentar_por_visual(video_path, cenas_timestamps):
    """Segmenta por mudanças visuais (câmera vs tela).

    Args:
        video_path: caminho do vídeo
        cenas_timestamps: lista de timestamps de mudança de cena

    Returns:
        Lista de segmentos: {"tipo": "camera"/"tela", "inicio", "fim"}
    """
    if not cenas_timestamps:
        return []

    segmentos = []
    for i, ts in enumerate(cenas_timestamps):
        inicio = ts
        fim = cenas_timestamps[i+1] if i+1 < len(cenas_timestamps) else None

        tipo = detectar_tipo_visual(video_path, inicio)

        segmentos.append({
            "tipo": tipo,
            "inicio": inicio,
            "fim": fim
        })

    return segmentos


def mesclar_segmentos(segmentos_tema, segmentos_visual):
    """Mescla segmentação temporal (tema) com visual (câmera/tela).

    Estratégia: usa os segmentos de tema como base e anota tipo visual.

    Returns:
        Lista de segmentos completos: {"categoria", "canal", "tipo", "inicio", "fim"}
    """
    if not segmentos_tema:
        return []

    if not segmentos_visual:
        # Sem detecção visual, assume tudo como câmera
        return [{"tipo": "camera", **seg} for seg in segmentos_tema]

    resultado = []

    for seg_tema in segmentos_tema:
        inicio_tema = seg_tema["inicio"]
        fim_tema = seg_tema["fim"]

        # Encontra qual tipo visual predomina neste intervalo de tempo
        tipos_no_intervalo = []
        for seg_visual in segmentos_visual:
            inicio_vis = seg_visual["inicio"]
            fim_vis = seg_visual.get("fim", float("inf"))

            # Verifica sobreposição
            if inicio_vis < fim_tema and (fim_vis is None or fim_vis > inicio_tema):
                tipos_no_intervalo.append(seg_visual["tipo"])

        # Tipo predominante (ou "camera" como fallback)
        tipo = max(set(tipos_no_intervalo), key=tipos_no_intervalo.count) if tipos_no_intervalo else "camera"

        resultado.append({
            **seg_tema,
            "tipo": tipo
        })

    return resultado


def segmentar_video_completo(video_path, temas_classificados, detectar_visual=True):
    """Segmenta vídeo por tema E por tipo visual.

    Args:
        video_path: caminho do vídeo
        temas_classificados: resultado do classificar_tema.py
        detectar_visual: se True, detecta câmera vs tela

    Returns:
        Lista de segmentos: {"categoria", "canal", "tipo", "inicio", "fim", "duracao"}
    """
    print(f"[segmentar] Iniciando segmentação de {video_path}", file=sys.stderr)

    # 1. Segmentação temporal por tema
    segmentos_tema = segmentar_por_tema(temas_classificados)
    print(f"[segmentar] {len(segmentos_tema)} segmentos temáticos", file=sys.stderr)

    if not detectar_visual:
        return [{"tipo": "camera", **seg, "duracao": seg["fim"] - seg["inicio"]}
                for seg in segmentos_tema]

    # 2. Detecção de mudanças visuais
    cenas = detectar_cenas_ffmpeg(video_path, threshold=0.4)

    # 3. Classificação visual dos segmentos
    segmentos_visual = segmentar_por_visual(video_path, cenas)
    print(f"[segmentar] {len(segmentos_visual)} segmentos visuais", file=sys.stderr)

    # 4. Mescla as duas segmentações
    segmentos_finais = mesclar_segmentos(segmentos_tema, segmentos_visual)

    # Adiciona duração
    for seg in segmentos_finais:
        seg["duracao"] = seg["fim"] - seg["inicio"]

    print(f"[segmentar] {len(segmentos_finais)} segmentos finais", file=sys.stderr)
    return segmentos_finais


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: segmentar_video.py <video_path> <temas_json>", file=sys.stderr)
        print("  video_path: caminho do vídeo", file=sys.stderr)
        print("  temas_json: arquivo JSON com resultado de classificar_tema.py", file=sys.stderr)
        sys.exit(1)

    video_path = Path(sys.argv[1])
    temas_path = Path(sys.argv[2])

    if not video_path.exists():
        print(f"Vídeo não encontrado: {video_path}", file=sys.stderr)
        sys.exit(1)

    if not temas_path.exists():
        print(f"Arquivo de temas não encontrado: {temas_path}", file=sys.stderr)
        sys.exit(1)

    with open(temas_path, "r", encoding="utf-8") as f:
        dados_temas = json.load(f)

    temas = dados_temas.get("temas", [])

    segmentos = segmentar_video_completo(video_path, temas, detectar_visual=True)

    print(json.dumps({
        "video": str(video_path),
        "num_segmentos": len(segmentos),
        "segmentos": segmentos
    }, ensure_ascii=False, indent=2))
