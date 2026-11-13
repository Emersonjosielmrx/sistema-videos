"""fx_audio_final.py — passada FINAL de audio, com o video copiado (sem re-encode de imagem).

1. Sons por PALAVRA (gatilhos do manhwa-react, config/gatilhos_palavras.json) no instante
   REAL em que o narrador fala a palavra (WordBoundary). Liberados por genero: som de meme
   em terror/drama nao combina.
2. Som de AMBIENTE de cada cena a partir do `sfx_hint` que o roteiro ja gerava e ninguem
   usava ("heartbeat", "wind blowing", "thunder"...) -> sfx_foley / sfx.
3. Volume final em -14 LUFS (padrao YouTube; o react usa o mesmo). Antes saia ~-27 LUFS e o
   YouTube so ABAIXA volume, nunca sobe.

Flags: AUDIO_FINAL=1 (default), GATILHOS_PALAVRA=1, SFX_CENA=1, LUFS_ALVO=-14.
"""
import json
import os
import random
import re
import subprocess
import unicodedata
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
ASSETS = PROJECT_DIR / "workspace" / "assets"
TABELA = PROJECT_DIR / "config" / "gatilhos_palavras.json"

# gatilhos liberados por genero (nomes da tabela). None = todos.
GATILHOS_GENERO = {
    "comedia": None,
    "curiosidades": {"choque", "falha", "vitoria", "dinheiro", "wow", "tensao", "magica",
                     "noticia", "foto", "vidro", "velocidade", "soco"},
    "superacao": {"vitoria", "dinheiro", "wow", "tensao", "soco", "vidro", "noticia"},
    "motivacional": {"vitoria", "dinheiro", "wow", "tensao"},
    "romance": {"wow", "magica"},
    "terror": {"tensao"}, "misterio": {"tensao"}, "drama": {"tensao"},
    "religioso": set(), "fantasia": {"magica", "tensao"},
}
# nunca em narracao (disparariam o tempo todo: "nao", "que", "sono")
GATILHOS_FORA = {"nope", "que_isso", "sono", "peido"}

# sfx_hint (ingles/portugues) -> fragmentos de nome em sfx_foley / sfx
HINT_SOM = [
    (r"heart ?beat|batimento|coração|coracao", ["heartbeat"]),
    (r"thunder|trov", ["thunder"]),
    (r"rain|chuva", ["rain_loop"]),
    (r"wind|vento", ["wind_blow"]),
    (r"door|porta", ["door_open", "door_close"]),
    (r"footstep|passos", ["footsteps"]),
    (r"glass|vidro", ["glass_break"]),
    (r"bird|pássaro|passaro", ["birds_morning"]),
    (r"crowd.*(cheer|applau)|aplaus|torcida", ["crowd_cheer"]),
    (r"gasp|crowd", ["crowd_gasp"]),
    (r"explosion|explos", ["explosion_small", "explosion_big"]),
    (r"ocean|wave|mar\b|onda", ["ocean_waves"]),
    (r"phone|telefone|celular", ["phone_ring", "notification"]),
    (r"sword|espada", ["sword_slash", "sword_hit"]),
    (r"gun|tiro", ["gunshot"]),
    (r"punch|soco|hit", ["punch_hit"]),
    (r"chain|corrente", ["chain_rattle"]),
    (r"drone|tension|tensão|tensao|rumble|low hum", ["tension_drone"]),
    (r"creep|eerie|ghost|whisper|sinistr", ["creepy_ambience"]),
    (r"whoosh|swoosh", ["fast_whoosh", "slow_whoosh"]),
    (r"metal|clang", ["metal_clang"]),
    (r"magic|mágic|magic|chime|sparkle|brilho", ["magic_sparkle"]),
    (r"riser|crescendo|swell", ["dramatic_riser", "riser"]),
    (r"impact|boom|thud", ["deep_boom", "impact"]),
]


def ativo():
    return os.environ.get("AUDIO_FINAL", "1") == "1"


def _norm(t):
    t = unicodedata.normalize("NFKD", str(t).lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9 ]+", " ", t).strip()


_IDX = None


def _indice():
    """[(nome_normalizado, caminho)] de sfx_memes, sfx, sfx_extras e sfx_foley."""
    global _IDX
    if _IDX is None:
        _IDX = []
        for sub in ("sfx_foley", "sfx", "sfx_extras", "sfx_memes"):
            base = ASSETS / sub
            if base.exists():
                for p in base.rglob("*"):
                    if p.suffix.lower() in (".mp3", ".wav", ".ogg", ".m4a"):
                        _IDX.append((_norm(p.stem), p))
    return _IDX


def _dur(p):
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                            "-of", "csv=p=0", str(p)], capture_output=True, text=True, timeout=15)
        return float(r.stdout.strip())
    except Exception:
        return 99.0


def _acha_som(fragmentos, bloqueio, max_s, rnd, exato=False):
    idx = _indice()
    for frag in fragmentos:
        f = _norm(frag)
        if exato:
            cands = [p for n, p in idx if n == f]
        else:
            cands = [p for n, p in idx if f in n and not any(b in n for b in bloqueio)]
        rnd.shuffle(cands)
        for p in cands[:6]:
            if _dur(p) <= max_s:
                return p
    return None


def _tabela():
    try:
        T = json.load(open(TABELA, encoding="utf-8"))
    except Exception:
        return {"gatilhos": []}
    for g in T.get("gatilhos", []):
        g["_rx"] = re.compile(g["regex"])
        g["_next"] = re.compile(g["proxima"]) if g.get("proxima") else None
    return T


def gatilhos_palavra(palavras, genero, duracao, seed="x"):
    """palavras: [(ini, fim, palavra)] no tempo do video final -> [{t, file, gain_db, nome}]."""
    if os.environ.get("GATILHOS_PALAVRA", "1") != "1":
        return []
    T = _tabela()
    libera = GATILHOS_GENERO.get((genero or "").lower(), set())
    gat = [g for g in T.get("gatilhos", []) if g.get("nome") not in GATILHOS_FORA
           and (libera is None or g.get("nome") in libera)]
    if not gat:
        return []
    bloqueio = [_norm(b) for b in T.get("bloqueio_nomes", [])]
    cooldown = float(T.get("cooldown_s", 5.0))
    max_n = max(int(T.get("max_por_video", 6)), int(duracao / 20))
    gain = float(T.get("gain_db", -10))
    max_s = float(T.get("max_duracao_s", 2.6))
    rnd = random.Random(str(seed))
    out, ult = [], -99.0
    toks = [_norm(w) for _s, _e, w in palavras]
    for i, (ini, _fim, _w) in enumerate(palavras):
        if len(out) >= max_n:
            break
        tok = toks[i]
        if not tok or ini < 1.5 or ini > duracao - 1.0 or ini - ult < cooldown:
            continue
        for g in gat:
            if not g["_rx"].match(tok):
                continue
            if g["_next"] is not None and not g["_next"].match(toks[i + 1] if i + 1 < len(toks) else ""):
                continue
            snd = _acha_som(g.get("sons", []), bloqueio, max_s, rnd)
            if snd:
                out.append({"t": ini, "file": str(snd), "gain_db": gain, "nome": g.get("nome")})
                ult = ini
            break
    return out


def sons_de_cena(cenas, inicios, duracao, seed="x"):
    """sfx_hint de cada cena -> som de ambiente no inicio da cena (1 por cena, sem repetir)."""
    if os.environ.get("SFX_CENA", "1") != "1":
        return []
    rnd = random.Random(str(seed) + "c")
    out, ult_file = [], None
    for cena, t0 in zip(cenas, inicios):
        hint = (cena.get("sfx_hint") or "").lower()
        if not hint or t0 is None or t0 > duracao - 1.5:
            continue
        for rx, frags in HINT_SOM:
            if re.search(rx, hint):
                snd = _acha_som(frags, [], 6.0, rnd, exato=True) or _acha_som(frags, [], 6.0, rnd)
                if snd and str(snd) != ult_file:
                    out.append({"t": t0 + 0.15, "file": str(snd), "gain_db": -15, "nome": f"cena:{frags[0]}",
                                "max_s": 4.0})
                    ult_file = str(snd)
                break
    return out


def _medir(wav, alvo, tp):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(wav), "-af",
                        f"loudnorm=I={alvo}:TP={tp}:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True, timeout=600)
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr, re.S)
    return json.loads(m.group(0)) if m else None


def masterizar(video_in, video_out, eventos, tmp_dir, alvo=None):
    """Mistura os eventos de som no audio do video e normaliza (loudnorm 2 passadas).
    Video copiado. Retorna dict com o que foi feito, ou None se falhou."""
    alvo = float(alvo if alvo is not None else os.environ.get("LUFS_ALVO", "-14"))
    tp = -1.5
    tmp = Path(tmp_dir)
    mix = tmp / "_audio_mix.wav"
    eventos = sorted(eventos, key=lambda e: e["t"])[:24]
    ins, fc, rot = ["-i", str(video_in)], [], ["[0:a]aresample=48000,aformat=channel_layouts=stereo[a0]"]
    for k, e in enumerate(eventos, start=1):
        ms = max(0, int(e["t"] * 1000))
        dur = float(e.get("max_s", 2.6))
        ins += ["-i", e["file"]]
        rot.append(f"[{k}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{dur:.2f},"
                   f"afade=t=out:st={max(0.1, dur - 0.4):.2f}:d=0.4,volume={e['gain_db']}dB,"
                   f"adelay={ms}|{ms}[s{k}]")
    n = len(eventos) + 1
    mixes = "[a0]" + "".join(f"[s{k}]" for k in range(1, n))
    rot.append(f"{mixes}amix=inputs={n}:normalize=0:duration=first:dropout_transition=0[m]")
    fc = ";".join(rot)
    try:
        subprocess.run(["ffmpeg", "-y", *ins, "-filter_complex", fc, "-map", "[m]",
                        "-c:a", "pcm_s16le", str(mix)], check=True, capture_output=True, timeout=600)
        med = _medir(mix, alvo, tp)
        if med:
            ln = (f"loudnorm=I={alvo}:TP={tp}:LRA=11:measured_I={med['input_i']}:"
                  f"measured_TP={med['input_tp']}:measured_LRA={med['input_lra']}:"
                  f"measured_thresh={med['input_thresh']}:offset={med['target_offset']}:linear=true")
        else:
            ln = f"loudnorm=I={alvo}:TP={tp}:LRA=11"
        subprocess.run(["ffmpeg", "-y", "-i", str(video_in), "-i", str(mix),
                        "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                        "-af", ln + ",aresample=48000", "-c:a", "aac", "-b:a", "192k",
                        "-movflags", "+faststart", "-shortest", str(video_out)],
                       check=True, capture_output=True, timeout=600)
        ok = Path(video_out).exists() and Path(video_out).stat().st_size > 10000
        return {"eventos": len(eventos), "lufs_antes": (med or {}).get("input_i"), "alvo": alvo} if ok else None
    except Exception:
        return None
    finally:
        try:
            mix.unlink(missing_ok=True)
        except Exception:
            pass
