"""Escolha de trilha de fundo por mood a partir do acervo compartilhado (moods.json).

Seguranca de copyright: por padrao (music.safe_only=true) so entram faixas de fonte livre (mixkit) ou da pasta
`trilhas/prioritarias` (aprovadas pelo usuario), nunca as da blocklist. Com safe_only=false entra qualquer faixa fora da blocklist.

Selecao (adaptada do hipercool bin/fx_music.py, 16/10):
  * trilhas/prioritarias/ (as "em alta" que o dono separou) vem primeiro: ~85% das vezes que existe uma do clima
    (music.prefer_priority, music.priority_chance). O clima de cada uma esta em prioritarias/climas.json; arquivo
    sem entrada la vale pra neutro/calmo. Aqui a blocklist vale tambem pra elas (no hipercool nao).
  * fora delas: catalogo moods.json sem a blocklist, sem toque de celular/efeito sonoro/meme e sem faixa com
    menos de 1 min (a trilha entra em loop no short; antes saiu ate "Undertale Sound Effect - Taking Damage").
  * evita as faixas dos ultimos videos (work/trilhas_recentes.json).
"""
import json
import random
import re
import subprocess
from pathlib import Path
from .common import log

MOODS = ["tense_dramatic", "sad_emotional", "romantic_sexy", "funny_lighthearted", "neutral_chill", "calm_chill"]
FALLBACK_ORDER = {
    "tense_dramatic": ["neutral_chill", "calm_chill"],
    "sad_emotional": ["calm_chill", "neutral_chill"],
    "romantic_sexy": ["calm_chill", "neutral_chill"],
    "funny_lighthearted": ["neutral_chill", "calm_chill"],
    "neutral_chill": ["calm_chill", "funny_lighthearted"],
    "calm_chill": ["neutral_chill", "sad_emotional"],
}
PRIORIDADE_DIR = "prioritarias"
MIN_DUR_S = 60.0
N_RECENTES = 16
# lixo pra fundo de fala: toque de celular, efeito sonoro, meme, versao zoada (mesma lista do hipercool)
LIXO_RE = re.compile(r"ringtone|toque|nokia|ear ?rape|sound effect|efeitos? sonoros?|taking damage|"
                     r"high pitch|singing|low quality|cpf cancelado|sikeira|flauta|flute|fail|meme|"
                     r"y2mate.*chicken|door ?bell", re.I)
_duracoes = None


def _blocklist(cfg):
    p = cfg["music"].get("blocklist")
    if not p or not Path(p).exists():
        return set()
    try:
        d = json.load(open(p, encoding="utf-8"))
        items = d.get("blocklist", d) if isinstance(d, dict) else d
        # cada item e {"arquivo": ..., "bloquear": true}: o str() do dict inteiro nunca batia com o nome (16/10)
        return {(x.get("arquivo") if isinstance(x, dict) else str(x)).lower() for x in items
                if not isinstance(x, dict) or (x.get("arquivo") and x.get("bloquear", True))}
    except Exception:  # noqa: BLE001
        return set()


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


def _duracao(cfg, path):
    """Duracao da faixa em s (ffprobe, com cache por nome+tamanho em work/trilhas_duracao.json)."""
    global _duracoes
    arq = Path(cfg["paths"]["work"]) / "trilhas_duracao.json"
    if _duracoes is None:
        _duracoes = _ler_json(arq, {})
    try:
        chave = f"{path.name}|{path.stat().st_size}"
    except OSError:
        return 0.0
    if chave not in _duracoes:
        try:
            r = subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                               capture_output=True, text=True, timeout=15)
            _duracoes[chave] = float(r.stdout.strip())
        except (ValueError, subprocess.SubprocessError, OSError):
            _duracoes[chave] = 0.0
        _gravar_json(arq, _duracoes)
    return _duracoes[chave]


def _prioritarias(lib, tracks, block):
    """{mood: [Path]} da pasta prioritarias/. Clima do climas.json da pasta; senao do moods.json; senao neutro/calmo."""
    pasta = lib / PRIORIDADE_DIR
    if not pasta.is_dir():
        return {}
    climas = {k: (v if isinstance(v, dict) else {"climas": v})
              for k, v in _ler_json(pasta / "climas.json", {}).items() if not k.startswith("_")}
    no_catalogo = {}
    for m, lst in tracks.items():
        for t in lst:
            if t.get("file"):
                no_catalogo.setdefault(Path(t["file"]).name, []).append(m)
    out = {}
    for f in sorted(pasta.iterdir()):
        if f.suffix.lower() not in (".mp3", ".wav", ".m4a", ".ogg", ".opus") or f.name.lower() in block:
            continue
        for m in climas.get(f.name, {}).get("climas") or no_catalogo.get(f.name) or ["neutral_chill", "calm_chill"]:
            out.setdefault(m, []).append(f)
    return out


def _candidates(cfg, tracks, mood, block, safe_only, lib):
    out = []
    for t in tracks.get(mood, []):
        f = t.get("file")
        if not f or f.lower() in block or Path(f).name.lower() in block or LIXO_RE.search(f):
            continue
        p = lib / f
        pri = lib / "prioritarias" / f
        src = str(t.get("source_id", ""))
        is_safe = src.startswith("mixkit") or pri.exists()
        if safe_only and not is_safe:
            continue
        path = p if p.exists() else pri
        if path.exists() and _duracao(cfg, path) >= MIN_DUR_S:
            out.append((t, path, is_safe))
    return out


def _escolher(paths, recentes, rng):
    """Uma das faixas: prefere as que nao tocaram nos ultimos videos; senao a que tocou ha mais tempo."""
    novas = [p for p in paths if p.name not in recentes]
    if novas:
        return rng.choice(novas)
    return max(paths, key=lambda p: recentes.index(p.name))  # recentes[0] e a ultima tocada


def pick_track(cfg, mood, seed=None):
    M = cfg["music"]
    lib = Path(cfg["paths"].get("music_library", ""))
    idx = lib / "moods.json"
    if not idx.exists():
        log("musica: moods.json nao encontrado")
        return None
    tracks = json.load(open(idx, encoding="utf-8")).get("tracks", {})
    tracks = {m: (lst if isinstance(lst, list) else [lst]) for m, lst in tracks.items()}
    mood = mood if mood in tracks else M.get("default_mood", "neutral_chill")
    rng = random.Random(seed)
    # faixas originais geradas localmente (MusicGen) tem prioridade quando existem
    if M.get("prefer_generated", True):
        try:
            from .musicgen import pool_candidates
            gen = pool_candidates(cfg, mood)
            if gen:
                p = rng.choice(gen)
                log(f"musica: {mood} -> {p.name} (gerada localmente)")
                return p
        except Exception:  # noqa: BLE001
            pass
    block = _blocklist(cfg)
    safe_only = M.get("safe_only", True)
    prio = _prioritarias(lib, tracks, block) if M.get("prefer_priority", True) else {}
    usar_prio = rng.random() < float(M.get("priority_chance", 0.85))
    rec_arq = Path(cfg["paths"]["work"]) / "trilhas_recentes.json"
    recentes = _ler_json(rec_arq, [])
    for m in [mood] + FALLBACK_ORDER.get(mood, []):
        escolhida, origem = None, ""
        if usar_prio and prio.get(m):
            escolhida, origem = _escolher(prio[m], recentes, rng), " (prioritaria)"
        else:
            cands = _candidates(cfg, tracks, m, block, safe_only, lib)
            if cands:
                pri = [c for c in cands if c[0].get("priority") or c[0].get("favorite")]
                pool = pri if pri else cands
                escolhida = _escolher([c[1] for c in pool], recentes, rng)
                if not any(c[2] for c in pool if c[1] == escolhida):
                    origem = " (fonte nao verificada)"
                if recentes and escolhida.name == recentes[0] and prio.get(m):  # catalogo de 1 faixa: nao repete o video anterior
                    escolhida, origem = _escolher(prio[m], recentes, rng), " (prioritaria)"
            elif prio.get(m):  # sorteio nao caiu na prioritaria, mas o catalogo do mood esta vazio
                escolhida, origem = _escolher(prio[m], recentes, rng), " (prioritaria)"
        if escolhida:
            log(f"musica: {mood}{'' if m == mood else ' -> ' + m} -> {escolhida.name}{origem}")
            _gravar_json(rec_arq, ([escolhida.name] + [r for r in recentes if r != escolhida.name])[:N_RECENTES])
            return escolhida
    log(f"musica: nenhuma faixa {'livre ' if safe_only else ''}para '{mood}'; sem trilha")
    return None
