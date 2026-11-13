"""anime_probe.py — mede duração de mídia via ffprobe.

Módulo pequeno e isolado. Só faz uma coisa: dizer quantos segundos
tem um arquivo de vídeo ou de áudio. Sem estado, sem efeitos colaterais.
"""
import subprocess


def _probe_duration(path, stream_selector):
    """Roda ffprobe e retorna a duração (segundos) do stream pedido.

    stream_selector: "a:0" pra áudio, "v:0" pra vídeo.
    Retorna 0.0 se não conseguir medir (arquivo inválido/inexistente).
    """
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error",
             "-select_streams", stream_selector,
             "-show_entries", "stream=duration",
             "-of", "csv=s=x:p=0", str(path)],
            capture_output=True, text=True, timeout=30,
        )
        return float(out.stdout.strip())
    except Exception:
        return 0.0


def audio_duration(path):
    """Duração (s) da primeira trilha de áudio."""
    return _probe_duration(path, "a:0")


def video_duration(path):
    """Duração (s) da primeira trilha de vídeo."""
    return _probe_duration(path, "v:0")


def video_dimensions(path):
    """Retorna (largura, altura) em pixels do vídeo. (0, 0) se não conseguir medir."""
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height",
             "-of", "csv=s=x:p=0", str(path)],
            capture_output=True, text=True, timeout=30,
        )
        w, h = out.stdout.strip().split("x")
        return int(w), int(h)
    except Exception:
        return 0, 0


def is_vertical(path, ratio_max=0.9):
    """True se o vídeo é vertical/retrato (adequado a Short 9:16 nativo).

    ratio_max: teto de largura/altura pra considerar vertical. 0.9 dá margem
    (um 9:16 real tem ratio ~0.56; 16:9 tem ~1.78). Só é confiável pós-download —
    a descoberta do YouTube não expõe dimensão de forma barata."""
    w, h = video_dimensions(path)
    if w <= 0 or h <= 0:
        return False
    return (w / h) < ratio_max
