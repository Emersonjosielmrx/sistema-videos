# -*- coding: utf-8 -*-
"""fx_music.py — TRILHA SONORA (fixa e dinâmica por clima).
add_background_music, add_dynamic_music, prioritárias. Importa fx_detect (SFX_DIR, mood).

Parte do motor de efeitos — mapa completo na fachada effects_engine.py.
Split mecânico verbatim do _PRE_SPLIT_effects_engine.py.bak (2026-07-04).
"""
import random
import subprocess
import os
import re
from pathlib import Path
from fx_assets import QP
from fx_detect import SFX_DIR, detect_mood_from_text




# Ganho da trilha por mood: romântica/calma/triste mais BAIXA; ação/tensão mais alta.
MOOD_MUSIC_GAIN = {
    "romantic_sexy": 0.55, "calm_chill": 0.60, "sad_emotional": 0.60,
    "neutral_chill": 0.72, "funny_lighthearted": 0.80,
    "tense_dramatic": 0.95, "action": 1.0,
}


def _mood_gain(mood):
    return MOOD_MUSIC_GAIN.get((mood or "").strip().lower(), 0.72)


# ── Nível-alvo da trilha (LUFS). Mais negativo = mais baixa/discreta. ──────────
# O usuário pediu trilha "naturalmente baixa, mas NIVELADA" entre faixas (uma de
# game e uma romântica calma têm masterização nativa diferente; o loudnorm iguala
# as duas pro MESMO volume percebido). -28 LUFS = bem atrás da narração.
MUSIC_TARGET_LUFS = -28.0


def add_background_music(video_path, music_path, out_path,
                         music_volume=0.10, fade_in=3, fade_out=3,
                         music_lufs=MUSIC_TARGET_LUFS, extra_gain=1.0,
                         duck=True):
    """Mixa UMA trilha de fundo no vídeo, com loudness nivelada e ducking.

    Conceito (o que cada parte resolve):
    - `loudnorm=I=music_lufs` → mede a loudness real da faixa e a traz pro alvo.
      É isto que NIVELA faixas com masterização diferente (game alta vs romântica
      baixa saem no mesmo volume percebido). Aplicado UMA vez só por faixa.
    - `volume=extra_gain` → ajuste fino POR MOOD aplicado DEPOIS do loudnorm
      (romântica/calma um pouco mais baixa, ação um pouco mais alta). Como vem
      depois do loudnorm, a hierarquia por mood não é desfeita.
    - Ducking BIDIRECIONAL: a música abaixa quando há narração
      (`sidechaincompress`) E sobe nos trechos sem diálogo. O lado "sobe no
      silêncio" vem de um ganho base maior + o sidechain só puxa pra baixo na voz.

    Parâmetros:
    - music_lufs=None  → PULA o loudnorm (usar quando a faixa JÁ foi normalizada
      antes, pra não medir/achatar duas vezes).
    - duck=False       → mixa sem ducking (trilha constante).
    """
    if not music_path or not Path(music_path).exists():
        # Sem trilha disponível: copia o vídeo como está (não é erro fatal).
        subprocess.run(["cp", str(video_path), str(out_path)], check=True)
        return True

    # Duração do vídeo (pra loopar a trilha e posicionar o fade-out).
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "csv=p=0", str(video_path)],
            capture_output=True, text=True, timeout=10,
        )
        video_dur = float(result.stdout.strip())
    except Exception:
        video_dur = 60.0

    # 1) loudnorm (nivela) — só se music_lufs definido.
    norm = f"loudnorm=I={music_lufs}:TP=-2:LRA=11," if music_lufs is not None else ""

    # 2) Monta a faixa de música: loop infinito → corta no tamanho do vídeo →
    #    nivela (loudnorm) → ganho por mood (extra_gain) → fade in/out nas pontas.
    music_chain = (
        f"[1:a]aloop=loop=-1:size=3e+07,atrim=0:{video_dur},"
        f"{norm}volume={extra_gain:.3f},"
        f"afade=t=in:st=0:d={fade_in},"
        f"afade=t=out:st={video_dur - fade_out}:d={fade_out}[music];"
    )

    if duck:
        # 3) Ducking: a narração (stream 0) comprime a música quando há voz.
        #    threshold baixo + ratio alto = a música "deita" sob a fala e volta a
        #    subir sozinha nos silêncios (release longo = subida suave).
        music_filter = (
            music_chain +
            f"[music][0:a]sidechaincompress=threshold=0.05:ratio=12:attack=20:release=350[music_ducked];"
            f"[0:a][music_ducked]amix=inputs=2:duration=first:dropout_transition=2[aout]"
        )
    else:
        music_filter = (
            music_chain +
            f"[0:a][music]amix=inputs=2:duration=first:dropout_transition=2[aout]"
        )

    # Loudnorm FINAL de master (opt-in via MASTER_LOUDNORM=1). O mix sai ~-25 LUFS
    # (trilha "naturalmente baixa" + voz), mas o YouTube normaliza pra ~-14 LUFS e
    # só ABAIXA, nunca sobe → o vídeo fica baixo. Este passo traz o MASTER inteiro
    # pro alvo antes do upload. Alvo configurável (MASTER_LUFS, default -14).
    if os.environ.get("MASTER_LOUDNORM", "0") == "1":
        _tgt = os.environ.get("MASTER_LUFS", "-14")
        music_filter = music_filter.replace(
            "[aout]", "[premaster];[premaster]loudnorm=I=%s:TP=-1.5:LRA=11[aout]" % _tgt, 1)

    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-i", str(music_path),
        "-filter_complex", music_filter,
        "-map", "0:v", "-map", "[aout]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", QP["audio_bitrate"], "-ar", "44100", "-ac", "2",
        "-shortest",
        str(out_path),
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=180)
        return True
    except Exception as e:
        # Qualquer falha no mix → entrega o vídeo sem trilha (nunca perde o vídeo).
        subprocess.run(["cp", str(video_path), str(out_path)], check=True)
        return True


# Subpasta cuja simples PRESENÇA do arquivo marca a trilha como prioritária.
# O usuário controla a prioridade no Explorer: arrastar o .mp3 pra dentro de
# `trilhas/prioritarias/` aumenta a chance dele tocar; tirar de lá volta ao normal.
# Não precisa editar JSON nenhum — a pasta é a fonte da verdade da prioridade.
PRIORITARIAS_SUBDIR = "prioritarias"


def _is_prioritaria(file_name, trilhas_dir):
    """True se existe uma cópia do arquivo dentro de trilhas/prioritarias/."""
    if not file_name:
        return False
    return (Path(trilhas_dir) / PRIORITARIAS_SUBDIR / file_name).exists()


def _resolve_track(file_name, trilhas_dir):
    """Acha o .mp3 da trilha, olhando PRIMEIRO em prioritarias/ e depois na raiz.

    Assim o usuário pode mover o arquivo livremente entre as duas pastas sem
    quebrar a reprodução — onde estiver, o código encontra.
    Retorna um Path existente, ou None se não achar em lugar nenhum.
    """
    if not file_name:
        return None
    prio = Path(trilhas_dir) / PRIORITARIAS_SUBDIR / file_name
    if prio.exists():
        return prio
    raiz = Path(trilhas_dir) / file_name
    return raiz if raiz.exists() else None


def _get_track_info(track_data, trilhas_dir=None, no_copyright=False):
    """Sorteia UMA trilha da lista do mood, com peso (weighted random).

    Uma trilha ganha peso 3 (3× mais chance) se QUALQUER destes for verdade:
    - tem "priority": true ou "favorite": true no moods.json, OU
    - o arquivo dela está dentro da pasta trilhas/prioritarias/ (controle manual
      do usuário pelo Explorer — ver _is_prioritaria).
    Trilhas comuns têm peso 1.
    """
    if isinstance(track_data, list):
        if not track_data:
            return {}
        weighted = []
        for t in track_data:
            in_folder = _is_prioritaria(t.get("file"), trilhas_dir) if trilhas_dir else False
            if no_copyright and t.get("copyright_risk"):
                continue
            weight = 3 if (t.get("priority") or t.get("favorite") or in_folder) else 1
            weighted.extend([t] * weight)
        return random.choice(weighted)
    return track_data


def add_dynamic_music(video_path, locucoes, out_path, trilhas_dir,
                      music_volume=0.08, block_size=8, no_copyright=False):
    """Adiciona trilha dinâmica que muda conforme o clima do manhwa.

    Divide as locuções em blocos, detecta o mood de cada bloco,
    e monta uma trilha composta com crossfade entre músicas diferentes.
    """
    import json as _json

    trilhas_dir = Path(trilhas_dir)
    moods_file = trilhas_dir / "moods.json"

    # PREVIEW: força UMA trilha em todo o vídeo (config externa, sem editar código).
    try:
        import preview_config as _pv
        _ft = _pv.force_trilha()
    except Exception:
        _ft = None
    if _ft:
        _forced = _resolve_track(_ft, trilhas_dir) or (trilhas_dir / _ft)
        if Path(_forced).exists():
            import sys as _sys
            print(f"  [PREVIEW] trilha forçada: {Path(_forced).name}", file=_sys.stderr, flush=True)
            return add_background_music(video_path, _forced, out_path, music_volume,
                                        extra_gain=0.0, duck=True)
        else:
            import sys as _sys
            print(f"  [PREVIEW] trilha '{_ft}' não encontrada, seguindo normal", file=_sys.stderr, flush=True)

    if not moods_file.exists():
        # Fallback: trilha única
        default_track = trilhas_dir / "neutral_chill.mp3"
        if not default_track.exists():
            default_track = trilhas_dir.parent / "trilha.mp3"
        return add_background_music(video_path, default_track, out_path, music_volume)

    moods_data = _json.loads(moods_file.read_text())
    tracks = moods_data.get("tracks", {})

    # Obter duração do vídeo
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "csv=p=0", str(video_path)],
            capture_output=True, text=True, timeout=10,
        )
        video_dur = float(result.stdout.strip())
    except Exception:
        video_dur = 60.0

    # Detectar mood por bloco de painéis
    n_panels = len(locucoes)
    blocks = []
    for i in range(0, n_panels, block_size):
        block_text = " ".join(
            loc.get("text", "") for loc in locucoes[i:i+block_size]
        )
        mood = detect_mood_from_text(block_text)
        blocks.append(mood)

    if not blocks:
        blocks = ["neutral_chill"]

    # Se todos os blocos têm o mesmo mood, usar trilha única
    unique_moods = list(dict.fromkeys(blocks))  # preservar ordem

    if len(unique_moods) == 1:
        track_key = unique_moods[0]
        track_info = _get_track_info(tracks.get(track_key, {}), trilhas_dir, no_copyright)
        # Resolve olhando prioritarias/ primeiro; cai em neutral_chill se sumir.
        track_file = _resolve_track(track_info.get("file", "neutral_chill.mp3"), trilhas_dir) \
            or _resolve_track("neutral_chill.mp3", trilhas_dir)
        # Lyria fallback pra mood unico
        if not track_file and os.environ.get("LYRIA_MOOD_FALLBACK", "0") == "1":
            try:
                import omniroute_music
                generated = omniroute_music.generate_mood_track(track_key)
                if generated:
                    track_file = generated
            except Exception:
                pass
        if not track_file:
            track_file = trilhas_dir / "neutral_chill.mp3"
        # mood único: nivela uma vez aqui, com ganho do mood e ducking bidirecional.
        return add_background_music(video_path, track_file, out_path, music_volume,
                                    extra_gain=_mood_gain(track_key), duck=True)

    # Trilha composta: concatenar as trilhas por bloco com crossfade
    # Duração de cada bloco = video_dur / len(blocks)
    block_dur = video_dur / len(blocks)
    # crossfade entre blocos: clamp pra nunca exceder o bloco (blocos curtos).
    crossfade = max(0.5, min(2.0, block_dur * 0.4))

    # LOG DETALHADO da trilha dinâmica
    import sys
    print(f"  [TRILHA] Vídeo: {video_dur:.1f}s | Blocos: {len(blocks)} | Duração/bloco: {block_dur:.1f}s", file=sys.stderr, flush=True)
    print(f"  [TRILHA] Moods detectados: {blocks}", file=sys.stderr, flush=True)
    print(f"  [TRILHA] Moods únicos: {unique_moods}", file=sys.stderr, flush=True)

    # Montar trilha composta concatenando trechos de cada música
    tmp_dir = Path(str(video_path)).parent
    composed_music = tmp_dir / "_composed_music.mp3"

    # Extrair trecho de cada trilha
    segments = []
    for i, mood in enumerate(blocks):
        track_key = mood
        track_data = tracks.get(track_key, tracks.get("neutral_chill", {}))
        track_info = _get_track_info(track_data, trilhas_dir, no_copyright)
        # Resolve olhando prioritarias/ primeiro; cai em neutral_chill se sumir.
        track_file = _resolve_track(track_info.get("file", "neutral_chill.mp3"), trilhas_dir) \
            or _resolve_track("neutral_chill.mp3", trilhas_dir)
        # Lyria fallback: gerar trilha por mood se não tem local
        if not track_file and os.environ.get("LYRIA_MOOD_FALLBACK", "0") == "1":
            try:
                import omniroute_music
                generated = omniroute_music.generate_mood_track(mood)
                if generated:
                    track_file = generated
            except Exception:
                pass
        if not track_file:
            continue
        print(f"  [TRILHA] Bloco {i+1}/{len(blocks)}: mood={mood} → {track_file.name}", file=sys.stderr, flush=True)

        seg_path = tmp_dir / f"_music_seg_{i:02d}.mp3"
        # É TROCA de mood? (primeiro bloco conta como "entrada" também.)
        is_change = (i == 0) or (blocks[i] != blocks[i - 1])

        # Ganho por mood (hierarquia): romântica/calma mais baixa, ação mais alta.
        mood_gain = _mood_gain(mood)

        # Bump SÓ na troca: nos primeiros ~1.5s do bloco que estreia um mood novo,
        # a trilha sobe um pouco pra você perceber que a música mudou. Blocos que
        # repetem o mesmo mood do bloco anterior NÃO recebem bump.
        bump = "volume=1.6:enable='between(t,0,1.5)'," if is_change else ""

        # Nivelamento: loudnorm UMA vez aqui (por faixa) → mesmo volume percebido
        # entre faixas de masterização diferente. O composto final NÃO re-normaliza
        # (add_background_music recebe music_lufs=None), pra não medir duas vezes.
        # SEM afade aqui: o acrossfade entre segmentos faz a sobreposição (um sobe
        # enquanto o outro desce), então NÃO há buraco de silêncio na troca.
        # Cada segmento tem block_dur + crossfade de material pra haver overlap.
        start_offset = (i * 10) % max(1, int(track_info.get("duration_seconds", 60)) - int(block_dur))
        cmd = [
            "ffmpeg", "-y", "-ss", str(start_offset),
            "-i", str(track_file), "-t", f"{block_dur + crossfade:.1f}",
            "-af", (
                f"loudnorm=I={MUSIC_TARGET_LUFS}:TP=-2:LRA=11,"
                f"volume={mood_gain:.3f},"
                f"{bump}"
                f"aresample=44100"
            ),
            "-c:a", "libmp3lame", "-b:a", "128k",
            str(seg_path),
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=30)
            segments.append(seg_path)
        except Exception:
            pass

    if not segments:
        # Fallback
        track_file = trilhas_dir / "neutral_chill.mp3"
        return add_background_music(video_path, track_file, out_path, music_volume)

    # Concatenar segmentos com ACROSSFADE (sobreposição) — sem buraco de silêncio.
    # acrossfade junta 2 entradas por vez; encadeamos N segmentos numa só passada.
    if len(segments) == 1:
        subprocess.run(["cp", str(segments[0]), str(composed_music)], check=True)
    else:
        inputs = []
        for s in segments:
            inputs += ["-i", str(s)]
        # Encadeia: [0][1]acrossfade->[x1]; [x1][2]acrossfade->[x2]; ...
        parts = []
        prev = "[0:a]"
        for k in range(1, len(segments)):
            out_lbl = f"[x{k}]" if k < len(segments) - 1 else "[mout]"
            parts.append(
                f"{prev}[{k}:a]acrossfade=d={crossfade:.1f}:c1=tri:c2=tri{out_lbl}"
            )
            prev = out_lbl
        fc = ";".join(parts)
        cmd = ["ffmpeg", "-y", *inputs, "-filter_complex", fc,
               "-map", "[mout]", "-c:a", "libmp3lame", "-b:a", "160k",
               str(composed_music)]
        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=120)
        except Exception:
            # Fallback: concat seco (volta ao comportamento antigo, mas não perde a trilha)
            seg_list = tmp_dir / "_music_segments.txt"
            with open(seg_list, "w") as f:
                for s in segments:
                    f.write(f"file '{s}'\n")
            try:
                subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0",
                                "-i", str(seg_list), "-c", "copy", str(composed_music)],
                               check=True, capture_output=True, timeout=60)
            except Exception:
                subprocess.run(["cp", str(segments[0]), str(composed_music)], check=True)

    # Ponto O: stinger (riser) nos pontos de TROCA de clima
    change_times = [i * block_dur for i in range(1, len(blocks)) if blocks[i] != blocks[i - 1]]
    riser = SFX_DIR / "riser.wav"
    if change_times and riser.exists():
        stung = tmp_dir / "_music_stung.mp3"
        inputs = ["-i", str(composed_music)]
        parts = []
        for k, t in enumerate(change_times):
            inputs += ["-i", str(riser)]
            ms = int(t * 1000)
            parts.append(f"[{k+1}:a]adelay={ms}|{ms},volume=0.5[s{k}]")
        mix_in = "".join(f"[s{k}]" for k in range(len(change_times)))
        fc = ";".join(parts) + (f";[0:a]{mix_in}amix=inputs={len(change_times)+1}:"
                                f"duration=first:dropout_transition=0[mout]")
        try:
            subprocess.run(["ffmpeg", "-y", *inputs, "-filter_complex", fc,
                            "-map", "[mout]", "-c:a", "libmp3lame", "-b:a", "160k", str(stung)],
                           check=True, capture_output=True, timeout=60)
            if stung.exists() and stung.stat().st_size > 0:
                stung.replace(composed_music)
        except Exception:
            pass

    # Mix final: o composto JÁ foi nivelado por segmento (loudnorm) e já tem o
    # ganho por mood. Por isso music_lufs=None (não re-normalizar) e extra_gain=1.0
    # (não aplicar ganho de novo). O ducking bidirecional acontece aqui.
    result = add_background_music(video_path, composed_music, out_path,
                                  music_volume, music_lufs=None,
                                  extra_gain=1.0, duck=True)

    # Cleanup
    for s in segments:
        try:
            s.unlink()
        except Exception:
            pass
    for f in [tmp_dir / "_music_segments.txt", composed_music]:
        try:
            f.unlink()
        except Exception:
            pass

    return result


def _save_to_cache_if_valid(out_path_str, clip_hash_val):
    if clip_hash_val and Path(out_path_str).exists() and Path(out_path_str).stat().st_size > 1000:
        try:
            shutil.copy2(out_path_str, str(CACHE_DIR / f"{clip_hash_val}.mp4"))
        except Exception:
            pass
