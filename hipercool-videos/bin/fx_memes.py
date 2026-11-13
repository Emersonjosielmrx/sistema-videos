# -*- coding: utf-8 -*-
"""fx_memes.py — memes visuais (figurinha + reação tela cheia) no passe final.

Catálogo em config/memes_catalogo.json (copiado de historias-em-frames).
Escolha: agente LLM ou fallback por tags. Resultado: lista de memes para
o passe_final (overlays ffmpeg).
"""
import json
import os
import random
import re
from pathlib import Path

from hp_common import PROJECT_DIR, log

CATALOGO_PATH = PROJECT_DIR / "config" / "memes_catalogo.json"
CATALOGO_FALLBACK = Path(r"D:\historias-em-frames\config\memes_catalogo.json")

# palavras/frases INTEIRAS que o narrador fala (vocabulário dos canais de referência) -> emoção
GATILHOS = {
    "choque": ["eita", "caramba", "caraca", "rapaz do céu", "meu deus", "pelo amor de deus", "que isso",
               "misericórdia", "não acredito", "impossível", "olha isso", "levou um susto", "toma um susto"],
    "confusão": ["como assim", "ué", "hein", "peraí", "entendi nada", "não entende", "sem entender"],
    "deboche": ["coitado", "coitada", "tadinho", "tadinha", "já era", "trouxa", "não aprende"],
    "vergonha": ["sem graça", "que vergonha", "envergonhada", "envergonhado", "constrangedor", "constrangida"],
    "alegria": ["conseguiu", "venceu", "vitória", "comemora", "comemoram"],
    "tristeza": ["chorando", "chora", "triste", "sozinho", "sozinha", "se foi"],
    "raiva": ["desgraçado", "maldito", "canalha", "cretino", "ousadia", "furioso", "furiosa", "irritado", "irritada"],
}
# emoção -> tags do catálogo (deboche e raiva têm poucos memes com a tag exata)
TAGS = {
    "choque": ["choque", "susto", "surpresa", "reação extrema", "pânico"],
    "confusão": ["confusão", "dúvida", "questionamento", "confuso"],
    "deboche": ["deboche", "sarcasmo", "ironia", "julgamento"],
    "vergonha": ["constrangimento", "awkward", "desconforto"],
    "alegria": ["alegria", "felicidade", "sucesso", "vitória"],
    "tristeza": ["tristeza", "choro", "decepção"],
    "raiva": ["raiva", "frustração", "desaprovação"],
}

_catalogo = None

def _carregar():
    global _catalogo
    if _catalogo is not None:
        return _catalogo
    for p in (CATALOGO_PATH, CATALOGO_FALLBACK):
        if p.exists():
            try:
                raw = json.loads(p.read_text(encoding="utf-8"))
                _catalogo = [v for v in raw.values() if v.get("ok") and Path(v["file"]).exists()]
                log(f"  [memes] Catálogo: {len(_catalogo)} memes disponíveis")
                return _catalogo
            except (OSError, ValueError):
                continue
    _catalogo = []
    return _catalogo


def _por_tags(tags_query):
    """Filtra memes cujas tags contêm alguma das queries."""
    cat = _carregar()
    tags_q = [t.lower() for t in tags_query]
    return [m for m in cat if any(t.lower() in tags_q for t in m.get("tags", []))]


_TERMOS = sorted(((tuple(t.split()), e) for e, ts in GATILHOS.items() for t in ts), key=lambda x: -len(x[0]))
# emoção forte = o meme INTERROMPE (tela cheia com o som dele, o vídeo para); o resto vira figurinha estampada
INTERROMPE = {"choque", "deboche", "vergonha", "raiva"}
INTERROMPE_DUR = (1.2, 3.5)  # s: só memes com som nessa faixa


def _toks(texto):
    return [re.sub(r"[^\w]", "", w.lower()) for w in (texto or "").split()]


def _emocao(toks, i):
    """Emoção do gatilho que começa na palavra i (frase inteira), ou None. "por que isso?" é pergunta, não choque."""
    return next((e for seq, e in _TERMOS if tuple(toks[i:i + len(seq)]) == seq
                 and not (seq[0] == "que" and i and toks[i - 1] == "por")), None)


def escolher_memes(palavras_tempo, total_dur, config=None, evitar=()):
    """Figurinhas estampadas (sem som, no centro) pelas palavras com tempo.

    palavras_tempo: lista de {"w": str, "s": float, "e": float}; total_dur: duração do vídeo;
    config: dict com figurinha_s (intervalo mínimo); evitar: janelas (ini, fim) sem figurinha (interrupções).
    Retorna lista de {"t", "dur", "estilo": "figurinha", "arquivo", "has_audio"}.
    """
    cat = _carregar()
    if not cat or not palavras_tempo:
        return []
    fig_intervalo = (config or {}).get("figurinha_s", 25)
    toks = [re.sub(r"[^\w]", "", str(w.get("w", "")).lower()) for w in palavras_tempo]
    memes_out, usados, ultimo_fig = [], set(), -fig_intervalo
    for i, w in enumerate(palavras_tempo):
        t = w.get("s")
        if (t is None or t <= 2.0 or t >= total_dur - 2.0 or t - ultimo_fig < fig_intervalo
                or any(a <= t <= b for a, b in evitar)):
            continue
        emocao = _emocao(toks, i)
        if not emocao:
            continue
        candidatos = [m for m in (_por_tags(TAGS[emocao]) or cat) if m["file"] not in usados] or cat
        m = random.choice(candidatos)
        usados.add(m["file"])
        memes_out.append({"t": t, "dur": min(m.get("duration", 2.0), 2.5), "estilo": "figurinha",
                          "arquivo": m["file"], "has_audio": m.get("has_audio", False)})
        ultimo_fig = t
    log(f"  [memes] {len(memes_out)} figurinhas estampadas")
    return memes_out


def escolher_interrupcoes(falas, intervalo_s=60, inicio_s=10, fim_s=15):
    """Onde um meme INTERROMPE o vídeo (tela cheia com som), logo DEPOIS da fala.

    falas: [(idx_clip, texto_pt, ini_s, fim_s)] na ordem do vídeo. Só emoção forte (INTERROMPE), no máx. 1 a cada
    intervalo_s, nunca nos primeiros inicio_s nem nos últimos fim_s. Retorna [(idx_clip, meme)]."""
    cat = [m for m in _carregar() if m.get("has_audio") and Path(m["file"]).suffix.lower() == ".mp4"
           and INTERROMPE_DUR[0] <= m.get("duration", 0) <= INTERROMPE_DUR[1]]
    if not cat or not falas:
        return []
    total = falas[-1][3]
    out, usados, ultimo = [], set(), -intervalo_s
    for idx, texto, ini, fim in falas:
        if fim < inicio_s or fim > total - fim_s or fim - ultimo < intervalo_s:
            continue
        toks = _toks(texto)
        emocao = next((e for e in (_emocao(toks, i) for i in range(len(toks))) if e), None)
        if emocao not in INTERROMPE:
            continue
        cands = [m for m in cat if m["file"] not in usados and any(t.lower() in TAGS[emocao] for t in m.get("tags", []))]
        if not cands:
            continue
        m = random.choice(cands)
        usados.add(m["file"])
        out.append((idx, m))
        ultimo = fim
    return out


def montar_clip_meme(meme, out_path, w, h, fps=30, crf="20"):
    """Clip do meme no MESMO formato dos clips do vídeo (w x h, fps, h264 yuv420p, aac) pra entrar no concat:
    imagem cobrindo a tela (corta o que sobra) com fundo borrado, som do meme nivelado. True se gerou."""
    import subprocess
    dur = min(float(meme.get("duration", 2.0)), INTERROMPE_DUR[1])
    vf = (f"[0:v]fps={fps},split[a][b];[a]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},"
          f"boxblur=20:2[fundo];[b]scale={w}:{h}:force_original_aspect_ratio=decrease[meio];"
          f"[fundo][meio]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]")
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", meme["file"], "-filter_complex", vf, "-map", "[v]", "-map", "0:a",
           "-af", "loudnorm=I=-16:TP=-2,aresample=48000", "-t", f"{dur:.2f}", "-r", str(fps),
           "-c:v", "libx264", "-preset", "fast", "-crf", crf, "-g", "30", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", str(out_path)]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=120)
    except Exception as e:  # noqa: BLE001
        log(f"  [memes] clip de interrupção falhou ({Path(meme['file']).name}): {str(e)[:100]}")
        return False
    return Path(out_path).exists() and Path(out_path).stat().st_size > 0
