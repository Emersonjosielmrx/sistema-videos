"""anime_segments.py — corta o vídeo-fonte em clipes sincronizados com a narração.

Módulo isolado que faz o loop principal:
  1. narra cada frase (anime_tts)
  2. mede a duração real do áudio (anime_probe)
  3. corta a fatia correspondente do vídeo-fonte, descaracterizada (fx_clips)

Retorna a lista de caminhos dos clipes gerados, na ordem.
O offset no vídeo-fonte dá loop quando a soma das falas passa do fim do vídeo.
"""
import os
import logging
from pathlib import Path

from fx_clips import build_clip_from_video
from anime_probe import audio_duration, video_duration
from fx_detect import pick_sfx_for_text, sfx_duration
from anime_tts import narrate


def build_segments(video_path, lines, out_dir, audio_dir=None, orient="landscape"):
    """Gera um clipe por frase. Retorna (clips, entries).

    clips:   [caminhos_dos_clipes] na ordem.
    entries: [(texto, duracao_s), ...] alinhado aos clipes (pra legenda).

    video_path: mp4 fonte (anime cru).
    lines: lista de frases do roteiro.
    out_dir: Path onde salvar os clip_N.mp4 (por orientação).
    audio_dir: Path onde ficam os audio_N.wav. Default = out_dir. Passar um
               dir COMPARTILHADO faz o áudio TTS ser gerado 1x e reusado nas
               duas orientações (não regera nem gasta proxy à toa).
    orient: "landscape" (16:9) ou "vertical" (9:16) — controla o enquadramento
            via env ANIME_ORIENT lido dentro de build_clip_from_video.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    audio_dir = Path(audio_dir) if audio_dir else out_dir
    audio_dir.mkdir(parents=True, exist_ok=True)

    os.environ["ANIME_ORIENT"] = orient

    src_dur = video_duration(video_path)  # pra dar loop no corte
    global_time = 0.0
    clips = []
    entries = []
    sfx_durs = []

    for i, line in enumerate(lines):
        audio_wav = narrate(line, audio_dir / f"audio_{i}.wav")
        if audio_wav is None:
            logging.error(f"[segments] pulando frase {i} (TTS falhou)")
            continue

        clip_dur = audio_duration(audio_wav)
        if clip_dur <= 0:
            logging.error(f"[segments] áudio {i} sem duração — pulando")
            continue

        cut_at = global_time % src_dur if src_dur > 0 else global_time
        clip_out = str(out_dir / f"clip_{i}.mp4")
        logging.info(f"[segments/{orient}] clipe {i}: corte@{cut_at:.1f}s dur={clip_dur:.2f}s")

        sfx_path, _sfx_vol = pick_sfx_for_text(line, "")  # retorna (path, volume)
        sfx_dur = sfx_duration(sfx_path) if sfx_path else 0.0
        
        ok = build_clip_from_video(
            video_source=video_path,
            audio_path=str(audio_wav),
            out_path=clip_out,
            panel_idx=i,
            effects_mgr=None,
            global_start_t=cut_at,
            clip_duration=clip_dur,
            subtitles=line,
            sfx=sfx_path
        )
        # avança o tempo mesmo se o clipe falhar, pra manter o alinhamento do corte.
        global_time += clip_dur
        if not ok:
            logging.error(f"[segments/{orient}] clipe {i} inválido — pulando (não entra no concat)")
            continue
        clips.append(clip_out)
        entries.append((line, clip_dur))
        sfx_durs.append(sfx_dur)

    return clips, entries, sfx_durs
