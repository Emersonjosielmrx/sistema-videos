#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""transcricao_video.py — Transcreve áudio de vídeo usando faster-whisper.

Reutiliza a infraestrutura existente de anime_fetch.py para transcrição.
Retorna transcrição com timestamps para permitir segmentação temporal.
"""
import sys
import os
import subprocess
from pathlib import Path

# Adiciona site-packages do sistema (onde faster-whisper está instalado)
if "faster_whisper" not in sys.modules:
    import site
    sys.path.append(r"C:\Users\Haylla\AppData\Local\Programs\Python\Python313\Lib\site-packages")
    sys.path.extend(site.getsitepackages())

# Configurações MKL/OMP antes de importar faster_whisper
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_DYNAMIC", "FALSE")
os.environ.setdefault("MKL_THREADING_LAYER", "SEQUENTIAL")

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def extrair_audio(video_path, out_wav=None, max_seconds=None):
    """Extrai áudio do vídeo como WAV mono 16kHz."""
    video = Path(video_path)
    if out_wav is None:
        out_wav = video.with_suffix(".transcricao.wav")
    else:
        out_wav = Path(out_wav)

    cmd = ["ffmpeg", "-y", "-i", str(video), "-vn", "-ac", "1", "-ar", "16000"]
    if max_seconds:
        cmd.extend(["-t", str(max_seconds)])
    cmd.extend(["-f", "wav", str(out_wav)])

    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=600)
        return out_wav
    except Exception as e:
        print(f"[transcricao] erro ao extrair áudio: {e}", file=sys.stderr)
        return None


def transcrever_com_timestamps(video_path, model_size="base", language=None, max_seconds=None):
    """Transcreve áudio retornando segmentos com timestamps.

    Args:
        video_path: caminho do vídeo
        model_size: tamanho do modelo Whisper (tiny/base/small/medium/large)
        language: idioma (pt/en/es, None=auto-detect)
        max_seconds: limita duração processada

    Returns:
        dict com:
            "texto_completo": str - transcrição completa
            "idioma": str - idioma detectado
            "segmentos": list de {"inicio": float, "fim": float, "texto": str}
    """
    print(f"[transcricao] Processando {video_path}", file=sys.stderr)

    # Extrai áudio
    wav_path = extrair_audio(video_path, max_seconds=max_seconds)
    if not wav_path or not wav_path.exists():
        return None

    try:
        from faster_whisper import WhisperModel

        print(f"[transcricao] Carregando modelo Whisper ({model_size})...", file=sys.stderr)
        model = WhisperModel(
            model_size,
            device="cpu",
            compute_type="int8",
            cpu_threads=2,
            num_workers=1,
            download_root=str(Path.cwd() / "models")
        )

        print(f"[transcricao] Transcrevendo áudio...", file=sys.stderr)
        segments_iter, info = model.transcribe(
            str(wav_path),
            language=language,
            vad_filter=True,  # filtra silêncios
            word_timestamps=False
        )

        segmentos = []
        textos = []
        for seg in segments_iter:
            segmentos.append({
                "inicio": seg.start,
                "fim": seg.end,
                "texto": seg.text.strip()
            })
            textos.append(seg.text.strip())

        resultado = {
            "texto_completo": " ".join(textos),
            "idioma": info.language,
            "segmentos": segmentos,
            "duracao_audio": info.duration if hasattr(info, 'duration') else None
        }

        print(f"[transcricao] Concluído: {len(segmentos)} segmentos, idioma={info.language}", file=sys.stderr)

        # Limpa WAV temporário
        try:
            wav_path.unlink()
        except:
            pass

        return resultado

    except Exception as e:
        print(f"[transcricao] Erro na transcrição: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return None


def transcrever_simples(video_path, model_size="base", language=None):
    """Transcreve retornando apenas o texto completo (sem timestamps)."""
    resultado = transcrever_com_timestamps(video_path, model_size, language)
    if resultado:
        return resultado["texto_completo"], resultado["idioma"]
    return None, None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: transcricao_video.py <video_path> [model_size] [language]", file=sys.stderr)
        print("  model_size: tiny/base/small/medium/large (padrão: base)", file=sys.stderr)
        print("  language: pt/en/es/None (padrão: auto-detect)", file=sys.stderr)
        sys.exit(1)

    video = sys.argv[1]
    model = sys.argv[2] if len(sys.argv) > 2 else "base"
    lang = sys.argv[3] if len(sys.argv) > 3 else None
    if lang and lang.lower() in ("none", "auto"):
        lang = None

    import json
    resultado = transcrever_com_timestamps(video, model, lang)

    if resultado:
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
        sys.exit(0)
    else:
        print("Erro na transcrição", file=sys.stderr)
        sys.exit(1)
