"""_concat_safe: concatena segmentos normalizando audio pra duracao do video.

Concat comum (ffmpeg -f concat -c copy) infla a duracao final quando o
audio de um segmento eh maior que o video do mesmo segmento. Este helper
faz 3 passos:
  1. concatena os videos (sem audio) via -c:v copy
  2. concatena os audios via filter_complex com normalizacao de duracao
     (apad se audio menor, atrim se maior) - gera silencio se segmento
     nao tem audio
  3. junta video + audio com -shortest pra garantir duracao exata

Uso: _concat_safe(['a.mp4', 'b.mp4'], saida.mp4)
"""

import subprocess
from pathlib import Path

_FFMPEG = r"D:\hipercool-materiais\bin\ffmpeg.exe"
_FFPROBE = r"D:\hipercool-materiais\bin\ffprobe.exe"


def _ffprobe_dur(mp4):
    try:
        r = subprocess.run(
            [_FFPROBE, "-v", "error",
             "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1", str(mp4)],
            capture_output=True, text=True, timeout=10)
        for linha in (r.stdout or "").splitlines():
            if linha.startswith("duration="):
                return float(linha.split("=", 1)[1])
    except Exception:
        pass
    return 0.0


def _ffprobe_has_audio(mp4):
    try:
        r = subprocess.run(
            [_FFPROBE, "-v", "error",
             "-select_streams", "a", "-show_entries", "stream=codec_type",
             "-of", "default=noprint_wrappers=1", str(mp4)],
            capture_output=True, text=True, timeout=10)
        return "codec_type=audio" in (r.stdout or "")
    except Exception:
        return False


def _concat_safe(lista_mp4, saida):
    """Concatena segmentos normalizando audio.

    Args:
      lista_mp4: lista de paths (str ou Path)
      saida: Path do arquivo final
    Returns:
      bool: True se ok
    """
    lista = saida.parent / f"_lista_{saida.stem}.txt"
    linhas = [f"file '{Path(p).resolve()}'" for p in lista_mp4]
    lista.write_text("\n".join(linhas), encoding="utf-8")

    seg_dur = [_ffprobe_dur(mp4) for mp4 in lista_mp4]

    tmp_video = saida.parent / f"_tmp_v_{saida.stem}.mp4"
    tmp_audio = saida.parent / f"_tmp_a_{saida.stem}.aac"

    # passo 1: video concat (re-encoda pra 30fps CFR - sem isso o mix de fps
    # diferentes infla a duracao via stream copy)
    cmd1 = [
        _FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", str(lista),
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
        "-r", "30", "-pix_fmt", "yuv420p",
        "-an", "-vsync", "cfr",
        str(tmp_video),
    ]
    r1 = subprocess.run(cmd1, capture_output=True, text=True, timeout=120)

    # passo 2: audio normalizado
    audio_inputs = []
    audio_filters = []
    idx = 0
    for i, mp4 in enumerate(lista_mp4):
        has_a = _ffprobe_has_audio(mp4)
        d = seg_dur[i] if seg_dur[i] > 0 else 1.0
        if has_a:
            audio_inputs += ["-i", str(mp4)]
            audio_filters.append(f"[{idx}:a]apad=whole_dur={d:.3f},atrim=0:{d:.3f},asetpts=PTS-STARTPTS[a{i}]")
            idx += 1
        else:
            audio_inputs += ["-f", "lavfi", "-t", f"{d:.3f}",
                             "-i", f"anullsrc=channel_layout=mono:sample_rate=44100"]
            audio_filters.append(f"[{idx}:a]atrim=0:{d:.3f},asetpts=PTS-STARTPTS[a{i}]")
            idx += 1
    concat_audio = "".join(f"[a{i}]" for i in range(len(lista_mp4)))
    fc = ";".join(audio_filters) + f";{concat_audio}concat=n={len(lista_mp4)}:v=0:a=1[outa]"
    cmd2 = [
        _FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
        *audio_inputs,
        "-filter_complex", fc,
        "-map", "[outa]",
        "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
        str(tmp_audio),
    ]
    r2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=120)

    # passo 3: junta video + audio (com -shortest pra truncar)
    cmd3 = [
        _FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(tmp_video),
        "-i", str(tmp_audio),
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
        "-shortest",
        "-movflags", "+faststart",
        str(saida),
    ]
    r3 = subprocess.run(cmd3, capture_output=True, text=True, timeout=60)

    # cleanup
    for tmp in (tmp_video, tmp_audio, lista):
        try:
            tmp.unlink()
        except Exception:
            pass

    if r1.returncode != 0 or r2.returncode != 0 or r3.returncode != 0:
        if r2.stderr:
            print(f"[concat_safe] audio stderr={r2.stderr[:300]}", flush=True)
        return False
    return saida.exists()