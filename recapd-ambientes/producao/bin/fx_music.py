# -*- coding: utf-8 -*-
"""fx_music.py — TRILHA SONORA (fixa e dinâmica por clima).
add_background_music, add_dynamic_music, prioritárias. Importa fx_detect (SFX_DIR, mood).

Parte do motor de efeitos — mapa completo na fachada effects_engine.py.
Split mecânico verbatim do _PRE_SPLIT_effects_engine.py.bak (2026-07-04).
Versão de 16/10 igual à do historias-em-frames (seleção do hipercool, normalize=0, blocklist, UTF-8).
"""
import json
import random
import shutil
import subprocess
import os
import re
from pathlib import Path
from fx_assets import QP
from fx_detect import SFX_DIR, detect_mood_from_text
from hp_common import CACHE_DIR  # usado por _save_to_cache_if_valid (antes dava NameError)

try:
    import music_escalation
except ImportError:
    music_escalation = None




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

# ── Seleção (adaptada do hipercool bin/fx_music.py em 16/10) ─────────────────
# Sem toque de celular/efeito/meme, sem faixa com menos de 1 min, sem repetir as
# faixas dos últimos vídeos, e trechos seguidos do mesmo clima viram UMA faixa
# contínua (no máx. MAX_FAIXA_S; antes cada bloco sorteava outra música).
MIN_DUR_S = 60.0
MAX_FAIXA_S = float(os.environ.get("HIPER_TRILHA_MAX_S", "100"))
RECENTES_FILE = CACHE_DIR / "trilhas_recentes.json"
DURACOES_FILE = CACHE_DIR / "trilhas_duracao.json"
LIXO_RE = re.compile(r"ringtone|toque|nokia|ear ?rape|sound effect|efeitos? sonoros?|taking damage|"
                     r"high pitch|singing|low quality|cpf cancelado|sikeira|flauta|flute|fail|meme|"
                     r"y2mate.*chicken|door ?bell", re.I)
ULTIMAS_FAIXAS = []   # faixas da última trilha montada (o story_pipeline loga)
_duracoes = None


def _ler_json(p, padrao):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return padrao


def _gravar_json(p, d):
    try:
        Path(p).parent.mkdir(parents=True, exist_ok=True)
        Path(p).write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    except OSError:
        pass


def _duracao(path):
    """Duração da faixa em s (ffprobe, com cache por nome+tamanho)."""
    global _duracoes
    if _duracoes is None:
        _duracoes = _ler_json(DURACOES_FILE, {})
    path = Path(path)
    try:
        chave = f"{path.name}|{path.stat().st_size}"
    except OSError:
        return 0.0
    if chave not in _duracoes:
        try:
            r = subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0",
                                str(path)], capture_output=True, text=True, timeout=15)
            _duracoes[chave] = float(r.stdout.strip())
        except (ValueError, subprocess.SubprocessError, OSError):
            _duracoes[chave] = 0.0
        _gravar_json(DURACOES_FILE, _duracoes)
    return _duracoes[chave]


def _trechos(blocks, block_dur):
    """[(mood, duração)] — blocos seguidos do mesmo clima viram um trecho só; trecho mais longo
    que MAX_FAIXA_S é dividido (cada pedaço ganha outra faixa)."""
    blocks = list(blocks)
    for k in range(1, len(blocks) - 1):  # A B A -> A A A: um bloco isolado não troca a música
        if blocks[k - 1] == blocks[k + 1] != blocks[k]:
            blocks[k] = blocks[k - 1]
    runs = []
    for m in blocks:
        if runs and runs[-1][0] == m:
            runs[-1][1] += block_dur
        else:
            runs.append([m, block_dur])
    out = []
    for m, d in runs:
        n = max(1, int(-(-d // MAX_FAIXA_S)))
        out += [(m, d / n)] * n
    return out


VOZ_REF_LUFS = -18.5  # narração do edge (Francisca) medida em 27/10 — o -28 da trilha foi calibrado com ela


def _ganho_voz(video_path, video_dur):
    """dB pra levar a narração ao nível de referência (0 = já está; máx. +12). Falhou a medida = 0 (mix de antes)."""
    try:
        r = subprocess.run(["ffmpeg", "-nostats", "-i", str(video_path), "-vn", "-af", "ebur128=framelog=quiet",
                            "-f", "null", "-"], capture_output=True, text=True, timeout=max(120, video_dur * 0.5))
        m = re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)
        voz = float(m[-1])
    except (subprocess.SubprocessError, OSError, ValueError, IndexError):
        return 0.0
    if voz < -60:  # sem voz
        return 0.0
    ganho = max(0.0, min(12.0, VOZ_REF_LUFS - voz))
    import logging as _lg
    _lg.info(f"[trilha] narração {voz:.1f} LUFS -> +{ganho:.1f} dB (referência {VOZ_REF_LUFS})")
    return ganho if ganho >= 1.0 else 0.0


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
        shutil.copy2(str(video_path), str(out_path))
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
    # 27/10 (dona: "trilha muito alta"): o -28 da trilha foi calibrado com a narração do edge (~-18,5 LUFS); a voz
    # clonada sai mais baixa e varia por modelo, aí a música sobrava. A voz vai pro nível de referência antes do mix.
    ganho_voz = _ganho_voz(video_path, video_dur)
    voz_in = f"[0:a]volume={ganho_voz:.1f}dB,alimiter=limit=0.95[v0];" if ganho_voz else ""
    voz_ref = "[v0]" if ganho_voz else "[0:a]"

    # 2) Monta a faixa de música: loop infinito → corta no tamanho do vídeo →
    #    nivela (loudnorm) → ganho por mood (extra_gain) → fade in/out nas pontas.
    music_chain = (
        f"[1:a]aloop=loop=-1:size=3e+07,atrim=0:{video_dur},"
        f"{norm}volume={extra_gain:.3f},"
        f"afade=t=in:st=0:d={fade_in},"
        f"afade=t=out:st={video_dur - fade_out}:d={fade_out}[music];"
    )

    _em_pe = os.environ.get("ANIME_ORIENT", "").strip().lower() == "vertical"
    if duck:
        # 3) Ducking: a narração (stream 0) comprime a música quando há voz.
        #    threshold baixo + ratio alto = a música "deita" sob a fala e volta a
        #    subir sozinha nos silêncios (release longo = subida suave).
        music_filter = (
            voz_in + music_chain +
            f"{voz_ref}asplit=2[voz][sc0];"
            # 04/11 (pesquisador, area_mixagem: ideia do "unmumble", sem dependência nova): o compressor reagia ao
            # NÍVEL da voz — voz baixa quase não abaixava a trilha (queixa 29/10) e voz alta afundava demais. Agora o
            # sinal de controle é a voz achatada (filtro de fala + ganho + limitador): com voz = nível fixo, sem voz =
            # silêncio. E vem 90 ms ADIANTADO (atrim), então a trilha já está baixa na 1ª sílaba. ANIME_DUCK_VOZ=0 volta.
            + (f"[sc0]highpass=f=150,lowpass=f=4000,volume=24dB,"
               f"alimiter=limit={os.environ.get('ANIME_DUCK_NIVEL') or ('0.25' if _em_pe else '0.5')}:attack=1:release=60,"
               f"atrim=start=0.09,asetpts=PTS-STARTPTS[sc];"
               if os.environ.get("ANIME_DUCK_VOZ", "1") != "0" else "[sc0]anull[sc];") +
            # 29/10 dona (longo): "às vezes a voz fica baixa e a trilha sobe" — ANIME_DUCK_LIMIAR mais baixo faz a
            # trilha deitar também sob voz baixa (longo.json: 0,02; padrão 0,05)
            # 31/10 dona (Short 0v8l: "falta trilha"): nos Shorts os microcortes tiram as pausas, a voz é contínua e o
            # fator 12 deixava a trilha ~19 dB abaixo da voz o vídeo inteiro (medido: -34,4 LUFS x voz -15,8). Em pé:
            # limiar 0,10 e fator 4 = trilha ~15 dB abaixo (-31,2). O longo segue como estava.
            f"[music][sc]sidechaincompress=threshold="
            f"{os.environ.get('ANIME_DUCK_LIMIAR') or ('0.10' if _em_pe else '0.05')}:"
            f"ratio={os.environ.get('ANIME_DUCK_FATOR') or ('4' if _em_pe else '12')}:"
            f"attack=20:release=350[music_ducked];"
            f"[voz][music_ducked]amix=inputs=2:duration=first:dropout_transition=2:normalize=0[aout]"
        )
    else:
        # normalize=0: o padrão do amix derrubava a narração ~6 dB o vídeo todo (correção do hipercool)
        music_filter = (
            voz_in + music_chain +
            f"{voz_ref}[music]amix=inputs=2:duration=first:dropout_transition=2:normalize=0[aout]"
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
        # 26/10: 180 s fixos eram pra Short; o longo de 1 h estourava e saía SEM trilha, calado. Tempo ∝ duração.
        subprocess.run(cmd, check=True, capture_output=True, timeout=max(180, video_dur * 1.5))
        return True
    except Exception as e:
        # Qualquer falha no mix → entrega o vídeo sem trilha (nunca perde o vídeo), mas AVISA no log.
        import sys as _sys
        err = getattr(e, "stderr", b"") or b""
        print(f"  [TRILHA] FALHOU o mix ({type(e).__name__}) — vídeo sai SEM trilha: "
              f"{err[-400:].decode('utf-8', 'replace') if isinstance(err, bytes) else str(err)[-400:]}",
              file=_sys.stderr, flush=True)
        shutil.copy2(str(video_path), str(out_path))
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


_BLOCK = None


def _blocklist_copyright():
    """Nomes (minusculo) de trilhas BLOQUEADAS por copyright: lista curada em
    hipercool-materiais/_curadoria/copyright_blocklist.json (a mesma do manhwa-react:
    Method Man, Pokemon, Netflix, Kirby...). Sem ela essas faixas entravam no sorteio."""
    global _BLOCK
    if _BLOCK is None:
        _BLOCK = set()
        try:
            import json as _json
            base = (Path(__file__).resolve().parent.parent / "workspace" / "assets").resolve().parent
            p = Path(os.environ.get("COPYRIGHT_BLOCKLIST", str(base / "_curadoria" / "copyright_blocklist.json")))
            d = _json.load(open(p, encoding="utf-8"))
            for it in (d.get("blocklist", []) if isinstance(d, dict) else d):
                if isinstance(it, dict):
                    if it.get("bloquear", True) and it.get("arquivo"):
                        _BLOCK.add(str(it["arquivo"]).lower())
                else:
                    _BLOCK.add(str(it).lower())
            # 21/10: faixa NÃO CLASSIFICADA (nome fora de "conhecidas", baixada depois — Hans Zimmer entrou assim)
            # fica fora do sorteio até alguém classificar; liberadas_extra valem; prioritarias/ não passa por aqui
            if isinstance(d, dict) and d.get("conhecidas"):
                conhecidas = {x.lower() for x in d["conhecidas"]} | {x.lower() for x in (d.get("liberadas_extra") or [])}
                pasta = p.parent.parent / "assets" / "trilhas"
                for f in pasta.iterdir() if pasta.is_dir() else []:
                    if f.is_file() and f.name.lower() not in conhecidas:
                        _BLOCK.add(f.name.lower())
        except Exception:
            pass
    return _BLOCK


def _get_track_info(track_data, trilhas_dir=None, no_copyright=False, evitar=(), recentes=()):
    """Sorteia UMA trilha da lista do mood, com peso (weighted random).

    Uma trilha ganha peso 3 (3× mais chance) se QUALQUER destes for verdade:
    - tem "priority": true ou "favorite": true no moods.json, OU
    - o arquivo dela está dentro da pasta trilhas/prioritarias/ (controle manual
      do usuário pelo Explorer — ver _is_prioritaria).
    Trilhas comuns têm peso 1. Fora do sorteio: blocklist, lixo (LIXO_RE) e faixa
    com menos de MIN_DUR_S. Prefere faixa fora de `evitar` (já usada nesta trilha)
    e que não tocou nos últimos vídeos; senão a que tocou há mais tempo.
    """
    if isinstance(track_data, list):
        if not track_data:
            return {}
        weighted = []
        bloqueadas = _blocklist_copyright()
        for t in track_data:
            f = str(t.get("file", ""))
            if no_copyright and t.get("copyright_risk"):
                continue
            if not f or Path(f).name.lower() in bloqueadas or LIXO_RE.search(f):
                continue
            if trilhas_dir:
                p = _resolve_track(f, trilhas_dir)
                if not p or _duracao(p) < MIN_DUR_S:
                    continue
            in_folder = _is_prioritaria(f, trilhas_dir) if trilhas_dir else False
            weight = 3 if (t.get("priority") or t.get("favorite") or in_folder) else 1
            weighted.extend([t] * weight)
        if not weighted:
            return {}
        nome = lambda t: Path(str(t["file"])).name  # noqa: E731
        livres = [t for t in weighted if nome(t) not in evitar] or weighted
        novas = [t for t in livres if nome(t) not in recentes]
        if novas:
            return random.choice(novas)
        recentes = list(recentes)
        return max(livres, key=lambda t: recentes.index(nome(t)))  # recentes[0] é a última tocada
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

    moods_data = _json.loads(moods_file.read_text(encoding="utf-8"))  # sem encoding o Windows lê em cp1252
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

    # -- MUSIC ESCALATION (feature exclusiva) — curva de intensidade narrativa --
    # A trilha sobe no clímax (penúltimo bloco) e desce na resolução (último).
    # Gera um multiplicador por bloco (0.6-1.15) aplicado sobre o mood_gain.
    trechos = _trechos(blocks, video_dur / len(blocks))
    recentes = _ler_json(RECENTES_FILE, [])
    escalation = None
    if music_escalation is not None and os.environ.get("MUSIC_ESCALATION", "1") == "1" and len(trechos) > 2:
        try:
            _pseudo_cenas = [{"mood": m} for m, _ in trechos]
            _intens = music_escalation.analyze_narrative_arc(_pseudo_cenas)
            # mapeia intensidade 0-1 → multiplicador 0.6-1.15 (não estoura o mix)
            escalation = [round(0.6 + 0.55 * x, 3) for x in _intens]
        except Exception:
            escalation = None

    # Se todos os blocos têm o mesmo mood, usar trilha única
    unique_moods = list(dict.fromkeys(blocks))  # preservar ordem

    global ULTIMAS_FAIXAS
    if len(trechos) == 1:
        track_key = trechos[0][0]
        track_info = _get_track_info(tracks.get(track_key, {}), trilhas_dir, no_copyright, recentes=recentes)
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
        ULTIMAS_FAIXAS = [Path(track_file).name]
        _gravar_json(RECENTES_FILE, (ULTIMAS_FAIXAS + [r for r in recentes if r not in ULTIMAS_FAIXAS])[:16])
        # mood único: nivela uma vez aqui, com ganho do mood e ducking bidirecional.
        return add_background_music(video_path, track_file, out_path, music_volume,
                                    extra_gain=_mood_gain(track_key), duck=True)

    # Trilha composta: uma faixa por TRECHO de clima (blocos seguidos do mesmo mood
    # = uma faixa contínua, no máx. MAX_FAIXA_S), com crossfade na troca.
    # crossfade: clamp pra nunca exceder o trecho mais curto.
    crossfade = max(0.5, min(2.0, min(d for _, d in trechos) * 0.4))

    # LOG DETALHADO da trilha dinâmica
    import sys
    print(f"  [TRILHA] Vídeo: {video_dur:.1f}s | Blocos: {len(blocks)} | Trechos: {[(m, round(d)) for m, d in trechos]}", file=sys.stderr, flush=True)
    print(f"  [TRILHA] Moods detectados: {blocks}", file=sys.stderr, flush=True)

    # Montar trilha composta concatenando trechos de cada música
    tmp_dir = Path(str(video_path)).parent
    composed_music = tmp_dir / "_composed_music.mp3"

    # Extrair trecho de cada trilha
    segments, usadas = [], []
    for i, (mood, block_dur) in enumerate(trechos):
        track_key = mood
        track_data = tracks.get(track_key, tracks.get("neutral_chill", {}))
        track_info = _get_track_info(track_data, trilhas_dir, no_copyright, evitar=set(usadas), recentes=recentes)
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
        print(f"  [TRILHA] Trecho {i+1}/{len(trechos)}: mood={mood} {block_dur:.0f}s → {track_file.name}", file=sys.stderr, flush=True)

        seg_path = tmp_dir / f"_music_seg_{i:02d}.mp3"
        # É TROCA de mood? (primeiro trecho conta como "entrada" também.)
        is_change = (i == 0) or (trechos[i][0] != trechos[i - 1][0])

        # Ganho por mood (hierarquia): romântica/calma mais baixa, ação mais alta.
        mood_gain = _mood_gain(mood)

        # Escalada narrativa: multiplica o ganho pela curva de intensidade do bloco.
        if escalation and i < len(escalation):
            mood_gain *= escalation[i]

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
        # Começa perto do início (pula no máx. 15 s de intro); faixa curta entra em loop.
        tdur = _duracao(track_file)
        start_offset = random.uniform(0, min(15.0, tdur - block_dur - crossfade)) \
            if tdur > block_dur + crossfade + 1 else 0.0
        loop = ["-stream_loop", "-1"] if tdur - start_offset < block_dur + crossfade else []
        cmd = [
            "ffmpeg", "-y", *loop, "-ss", f"{start_offset:.1f}",
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
            usadas.append(track_file.name)
        except Exception:
            pass

    if not segments:
        # Fallback
        track_file = trilhas_dir / "neutral_chill.mp3"
        return add_background_music(video_path, track_file, out_path, music_volume)

    # Concatenar segmentos com ACROSSFADE (sobreposição) — sem buraco de silêncio.
    # acrossfade junta 2 entradas por vez; encadeamos N segmentos numa só passada.
    if len(segments) == 1:
        shutil.copy2(str(segments[0]), str(composed_music))
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
            subprocess.run(cmd, check=True, capture_output=True, timeout=max(120, video_dur * 0.3))
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
                shutil.copy2(str(segments[0]), str(composed_music))

    ULTIMAS_FAIXAS = usadas
    _gravar_json(RECENTES_FILE, (list(dict.fromkeys(usadas)) + [r for r in recentes if r not in usadas])[:16])

    # Ponto O: stinger (riser) nos pontos de TROCA de clima
    change_times, t = [], 0.0
    for k in range(1, len(trechos)):
        t += trechos[k - 1][1]
        if trechos[k][0] != trechos[k - 1][0]:
            change_times.append(t)
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
        # normalize=0: sem isso o amix dividia a trilha inteira pelo nº de entradas (2 trocas = 1/3 do volume)
        fc = ";".join(parts) + (f";[0:a]{mix_in}amix=inputs={len(change_times)+1}:"
                                f"duration=first:dropout_transition=0:normalize=0[mout]")
        try:
            subprocess.run(["ffmpeg", "-y", *inputs, "-filter_complex", fc,
                            "-map", "[mout]", "-c:a", "libmp3lame", "-b:a", "160k", str(stung)],
                           check=True, capture_output=True, timeout=max(60, video_dur * 0.2))
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
