# -*- coding: utf-8 -*-
"""fx_music.py — TRILHA SONORA (fixa e dinâmica por clima).

Parte do motor de efeitos (ver mapa completo em effects_engine.py).
Adiciona música de fundo ao vídeo já montado.

  add_background_music(video, music, out, volume)   trilha ÚNICA de fundo.
  add_dynamic_music(video, locucoes, out, trilhas)  troca a trilha conforme o
        CLIMA de cada trecho (usa detect_mood_from_text pra ler o mood).
  compose_dynamic_music(dur, locucoes, trilhas, tmp) só MONTA a trilha composta
        (sem mixar) — usada pelo fx_acabamento, que mixa tudo num passe só.
  _get_track_info(track)                            lê metadado da trilha.

Seleção de faixa:
  * trilhas/prioritarias/ (as que o dono separou, "em alta") vêm PRIMEIRO: ~85% das vezes que
    existe uma do clima. O clima de cada uma está em prioritarias/climas.json; arquivo novo
    jogado na pasta sem entrada lá vale pra neutro/calmo. Ficam fora da blocklist de copyright
    (escolha do dono; o risco é só reivindicação de Content ID, não strike).
  * fora delas: catálogo moods.json, sem a blocklist (_curadoria/copyright_blocklist.json),
    sem toque de celular/efeito/meme e sem faixa com menos de 1 min.
  * nenhuma faixa toca mais de HIPER_TRILHA_MAX_S (100 s) seguidos; trechos do mesmo clima
    viram uma faixa contínua; troca com crossfade; volume nivelado por trecho.
  * evita as faixas dos últimos vídeos (workspace/cache/trilhas_recentes.json).

Importa fx_detect (SFX_DIR, detect_mood_from_text). É o último da cadeia —
ninguém depende dele. Mexa aqui pra: volume da trilha, regra de troca de mood.
"""
import json
import random
import shutil
import subprocess
import os
import re
from pathlib import Path
from fx_detect import SFX_DIR, detect_mood_from_text

PROJECT_DIR = Path(__file__).resolve().parent.parent
BLOCKLIST_FILE = Path(os.environ.get("HIPERCOOL_MATERIAIS", r"D:\hipercool-materiais")) / "_curadoria" / "copyright_blocklist.json"
PRIORIDADE_DIR = "prioritarias"
CHANCE_PRIORIDADE = float(os.environ.get("HIPER_TRILHA_PRIORIDADE", "0.85"))
MAX_FAIXA_S = float(os.environ.get("HIPER_TRILHA_MAX_S", "100"))
MIN_DUR_S = 60.0
CROSSFADE_S = 2.5
RECENTES_FILE = PROJECT_DIR / "workspace" / "cache" / "trilhas_recentes.json"
DURACOES_FILE = PROJECT_DIR / "workspace" / "cache" / "trilhas_duracao.json"
# lixo pra fundo de narração: toque de celular, efeito sonoro, meme, versão zoada
LIXO_RE = re.compile(r"ringtone|toque|nokia|ear ?rape|sound effect|efeitos? sonoros?|taking damage|"
                     r"high pitch|singing|low quality|cpf cancelado|sikeira|flauta|flute|fail|meme|"
                     r"y2mate.*chicken|door ?bell", re.I)
FALLBACK_MOODS = {
    "tense_dramatic": ["neutral_chill", "calm_chill"],
    "sad_emotional": ["calm_chill", "neutral_chill"],
    "romantic_sexy": ["calm_chill", "neutral_chill"],
    "funny_lighthearted": ["neutral_chill", "calm_chill"],
    "neutral_chill": ["calm_chill", "funny_lighthearted"],
    "calm_chill": ["neutral_chill", "sad_emotional"],
}
ULTIMAS_FAIXAS = []   # faixas usadas na última trilha montada (vai pro meta do vídeo)
_blocked = None
_duracoes = None


def _blocked_names():
    """Nomes de arquivo bloqueados (lista de {"arquivo", "bloquear"} da curadoria) + faixas NÃO CLASSIFICADAS:
    nome fora de "conhecidas" (baixada depois da classificação de 21/10 — Hans Zimmer entrou assim) fica fora do
    sorteio até alguém classificar; as liberadas_extra valem."""
    global _blocked
    if _blocked is None:
        _blocked = set()
        try:
            d = json.loads(BLOCKLIST_FILE.read_text(encoding="utf-8"))
            for it in (d.get("blocklist", []) if isinstance(d, dict) else d):
                if isinstance(it, dict) and it.get("bloquear", True) and it.get("arquivo"):
                    _blocked.add(it["arquivo"].lower())
                elif isinstance(it, str):
                    _blocked.add(it.lower())
            conhecidas = {x.lower() for x in (d.get("conhecidas") or [])} if isinstance(d, dict) else set()
            liberadas = {x.lower() for x in (d.get("liberadas_extra") or [])} if isinstance(d, dict) else set()
            if conhecidas:
                pasta = Path(os.environ.get("HIPERCOOL_MATERIAIS", r"D:\hipercool-materiais")) / "assets" / "trilhas"
                for f in pasta.iterdir() if pasta.is_dir() else []:
                    n = f.name.lower()
                    if f.is_file() and n not in conhecidas and n not in liberadas:
                        _blocked.add(n)
        except (OSError, ValueError):
            pass
    return _blocked


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


def _climas_prioritarias(trilhas_dir):
    """{arquivo: {"climas": [...], "inicio": s}} do prioritarias/climas.json. Aceita a forma curta
    "arquivo": ["clima", ...]. inicio = segundo exato onde a faixa SEMPRE começa (o trecho que o dono
    quer, ex. a Montagem Bailão no 'clima perfeito, noite enluarada')."""
    bruto = _ler_json(Path(trilhas_dir) / PRIORIDADE_DIR / "climas.json", {})
    return {k: (v if isinstance(v, dict) else {"climas": v}) for k, v in bruto.items() if not k.startswith("_")}


def _prioritarias(tracks, trilhas_dir):
    """{mood: [Path]} das faixas da pasta prioritarias/. Clima vem do climas.json da pasta; senão do
    moods.json; arquivo sem nenhum dos dois vale pra neutro e calmo."""
    pasta = Path(trilhas_dir) / PRIORIDADE_DIR
    if not pasta.is_dir():
        return {}
    climas = _climas_prioritarias(trilhas_dir)
    no_catalogo = {}
    for m, lst in tracks.items():
        for t in (lst if isinstance(lst, list) else [lst]):
            if t.get("file"):
                no_catalogo.setdefault(t["file"], []).append(m)
    out = {}
    for f in sorted(pasta.iterdir()):
        if f.suffix.lower() not in (".mp3", ".wav", ".m4a", ".ogg", ".opus"):
            continue
        moods = climas.get(f.name, {}).get("climas") or no_catalogo.get(f.name) or ["neutral_chill", "calm_chill"]
        for m in moods:
            out.setdefault(m, []).append(f)
    return out


def _escolher(cands, evitar, recentes):
    """Uma das faixas candidatas: fora de `evitar` se der; prefere as que não tocaram nos últimos vídeos."""
    livres = [c for c in cands if c.name not in evitar] or cands
    novas = [c for c in livres if c.name not in recentes]
    if novas:
        return random.choice(novas)
    # a que tocou há mais tempo: recentes[0] é a ÚLTIMA tocada (era min = repetia a última; corrigido 16/10)
    return max(livres, key=lambda c: recentes.index(c.name))


def _pick_track_file(tracks, mood, trilhas_dir, evitar=(), recentes=()):
    """(Path, info, mood_usado) — faixa válida do mood (ou vizinho). Prioritárias primeiro."""
    block = _blocked_names()
    prio = _prioritarias(tracks, trilhas_dir)
    usar_prio = random.random() < CHANCE_PRIORIDADE
    for m in [mood] + FALLBACK_MOODS.get(mood, []):
        if usar_prio and prio.get(m):
            return _escolher(prio[m], evitar, list(recentes)), {}, m
        data = tracks.get(m, [])
        data = data if isinstance(data, list) else [data]
        ok = []
        for t in data:
            f = t.get("file")
            if not f or f.lower() in block or LIXO_RE.search(f):
                continue
            p = Path(trilhas_dir) / f
            if p.exists() and _duracao(p) >= MIN_DUR_S:
                ok.append(p)
        if ok:
            info = {}
            curadas = [Path(trilhas_dir) / t["file"] for t in data
                       if (t.get("priority") or t.get("favorite")) and Path(trilhas_dir) / t["file"] in ok]
            escolhida = _escolher(curadas or ok, evitar, list(recentes))
            for t in data:
                if t.get("file") == escolhida.name:
                    info = t
            return escolhida, info, m
        if prio.get(m):  # sorteio não caiu na prioridade, mas o catálogo do mood está vazio
            return _escolher(prio[m], evitar, list(recentes)), {}, m
    return None, {}, mood


def add_background_music(video_path, music_path, out_path,
                         music_volume=0.08, fade_in=3, fade_out=3):
    """Adiciona trilha sonora de fundo com ducking automático.

    A música fica baixa durante toda a narração (ducking),
    com fade in no início e fade out no final.
    """
    if not music_path or not Path(music_path).exists():
        # Sem música — copia direto
        shutil.copy2(str(video_path), str(out_path))
        return True

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

    # Trilha nivelada em loudness (faixas de masterizações diferentes soam iguais)
    # e amix SEM normalize (o normalize padrão derrubava a voz ~6 dB o vídeo todo).
    music_filter = (
        f"[1:a]aloop=loop=-1:size=3e+07,atrim=0:{video_dur},"
        f"loudnorm=I=-28:TP=-3:LRA=7,aresample=48000,"
        f"afade=t=in:st=0:d={fade_in},"
        f"afade=t=out:st={video_dur - fade_out}:d={fade_out}[music];"
        f"[0:a]asplit=2[voice][sc];"
        f"[music][sc]sidechaincompress=threshold=0.02:ratio=8:attack=30:release=500[music_ducked];"
        f"[voice][music_ducked]amix=inputs=2:duration=first:dropout_transition=2:normalize=0[aout]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-i", str(music_path),
        "-filter_complex", music_filter,
        "-map", "0:v", "-map", "[aout]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        str(out_path),
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=180)
        return True
    except Exception as e:
        # Fallback: sem música
        shutil.copy2(str(video_path), str(out_path))
        return True


def _get_track_info(track_data):
    """Retorna um dicionário de track, tratando opcionalmente listas de tracks.

    Se a lista tiver tracks marcadas (priority/favorite), escolhe SÓ entre elas.
    Senão, escolhe aleatório entre todas. Isso faz as trilhas curadas tocarem mais.
    """
    if isinstance(track_data, list):
        if not track_data:
            return {}
        preferred = [t for t in track_data if t.get("priority") or t.get("favorite")]
        return random.choice(preferred or track_data)
    return track_data


def add_dynamic_music(video_path, locucoes, out_path, trilhas_dir,
                      music_volume=0.08, block_size=8):
    """Adiciona trilha dinâmica que muda conforme o clima do manhwa.

    Divide as locuções em blocos, detecta o mood de cada bloco,
    e monta uma trilha composta com crossfade entre músicas diferentes.
    """
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "csv=p=0", str(video_path)],
            capture_output=True, text=True, timeout=10,
        )
        video_dur = float(result.stdout.strip())
    except Exception:
        video_dur = 60.0
    tmp_dir = Path(str(video_path)).parent
    music = compose_dynamic_music(video_dur, locucoes, trilhas_dir, tmp_dir, block_size)
    result = add_background_music(video_path, music, out_path, music_volume)
    if music and Path(music).name.startswith("_composed_music"):
        Path(music).unlink(missing_ok=True)
    return result


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


def compose_dynamic_music(video_dur, locucoes, trilhas_dir, tmp_dir, block_size=8):
    """Monta a trilha (uma faixa por trecho de clima, no máx. MAX_FAIXA_S cada) e devolve o caminho,
    sem mixar. Retorna None se não houver faixa utilizável."""
    global ULTIMAS_FAIXAS
    trilhas_dir = Path(trilhas_dir)
    tmp_dir = Path(tmp_dir)
    moods_file = trilhas_dir / "moods.json"
    if not moods_file.exists():
        default_track = trilhas_dir / "neutral_chill.mp3"
        return default_track if default_track.exists() else None

    tracks = json.loads(moods_file.read_text(encoding="utf-8")).get("tracks", {})

    # Detectar mood por bloco de painéis
    blocks = []
    for i in range(0, len(locucoes), block_size):
        block_text = " ".join(loc.get("text", "") for loc in locucoes[i:i + block_size])
        blocks.append(detect_mood_from_text(block_text))
    if not blocks:
        blocks = ["neutral_chill"]
    trechos = _trechos(blocks, video_dur / len(blocks))

    recentes = _ler_json(RECENTES_FILE, [])
    usadas, segments, faixas = [], [], []
    for i, (mood, dur) in enumerate(trechos):
        track_file, _, used = _pick_track_file(tracks, mood, trilhas_dir, evitar=set(usadas), recentes=recentes)
        if not track_file:
            continue
        print(f"  🎵 trecho {i} [{mood}{'' if used == mood else '->' + used}] {dur:.0f}s: {track_file.name}")
        tdur = _duracao(track_file)
        # começa no trecho fixo do climas.json; senão perto do início (pula no máx. 15 s de intro);
        # faixa curta demais entra em loop
        fixo = _climas_prioritarias(trilhas_dir).get(track_file.name, {}).get("inicio")
        if fixo is not None:
            ini = float(fixo)
        else:
            ini = random.uniform(0, min(15.0, tdur - dur - CROSSFADE_S)) if tdur > dur + CROSSFADE_S + 1 else 0.0
        seg_path = tmp_dir / f"_music_seg_{i:02d}.wav"
        loop = ["-stream_loop", "-1"] if tdur and tdur - ini < dur + CROSSFADE_S else []
        cmd = ["ffmpeg", "-y", "-v", "error", *loop, "-ss", f"{ini:.1f}", "-i", str(track_file),
               "-t", f"{dur + CROSSFADE_S:.2f}",
               "-af", "loudnorm=I=-20:TP=-2:LRA=9,aresample=48000,aformat=channel_layouts=stereo",
               str(seg_path)]
        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=120)
            segments.append(seg_path)
            usadas.append(track_file.name)
            faixas.append(track_file.name)
        except Exception:  # noqa: BLE001
            pass

    if not segments:
        return _pick_track_file(tracks, "neutral_chill", trilhas_dir)[0]

    # junta os trechos com crossfade (sem buraco de silêncio entre faixas)
    composed_music = tmp_dir / "_composed_music.mp3"
    if len(segments) == 1:
        ok = subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(segments[0]), "-c:a", "libmp3lame",
                             "-b:a", "192k", str(composed_music)], capture_output=True).returncode == 0
    else:
        ins = []
        for s in segments:
            ins += ["-i", str(s)]
        fc, prev = [], "[0:a]"
        for k in range(1, len(segments)):
            out = f"[x{k}]" if k < len(segments) - 1 else "[mout]"
            fc.append(f"{prev}[{k}:a]acrossfade=d={CROSSFADE_S}:c1=tri:c2=tri{out}")
            prev = out
        ok = subprocess.run(["ffmpeg", "-y", "-v", "error", *ins, "-filter_complex", ";".join(fc),
                             "-map", "[mout]", "-c:a", "libmp3lame", "-b:a", "192k", str(composed_music)],
                            capture_output=True, timeout=180).returncode == 0
    if not ok:
        shutil.copy2(segments[0], tmp_dir / "_composed_music.wav")
        composed_music = tmp_dir / "_composed_music.wav"

    # Ponto O: stinger (riser) nos pontos de TROCA de clima
    change_times, t = [], 0.0
    for k in range(1, len(trechos)):
        t += trechos[k - 1][1]
        if trechos[k][0] != trechos[k - 1][0]:
            change_times.append(t)
    riser = SFX_DIR / "riser.wav"
    if change_times and riser.exists() and composed_music.suffix == ".mp3":
        stung = tmp_dir / "_music_stung.mp3"
        inputs = ["-i", str(composed_music)]
        parts = []
        for k, t in enumerate(change_times):
            inputs += ["-i", str(riser)]
            ms = int(t * 1000)
            parts.append(f"[{k+1}:a]adelay={ms}|{ms},volume=0.5[s{k}]")
        mix_in = "".join(f"[s{k}]" for k in range(len(change_times)))
        fc = ";".join(parts) + (f";[0:a]{mix_in}amix=inputs={len(change_times)+1}:"
                                f"duration=first:dropout_transition=0:normalize=0[mout]")
        try:
            subprocess.run(["ffmpeg", "-y", *inputs, "-filter_complex", fc,
                            "-map", "[mout]", "-c:a", "libmp3lame", "-b:a", "192k", str(stung)],
                           check=True, capture_output=True, timeout=120)
            if stung.exists() and stung.stat().st_size > 0:
                stung.replace(composed_music)
        except Exception:
            pass

    # Cleanup dos pedaços (a trilha composta fica: quem chamou mixa e apaga)
    for s in segments:
        try:
            s.unlink()
        except Exception:
            pass

    ULTIMAS_FAIXAS = faixas
    _gravar_json(RECENTES_FILE, (list(dict.fromkeys(faixas)) + [r for r in recentes if r not in faixas])[:16])
    return composed_music
