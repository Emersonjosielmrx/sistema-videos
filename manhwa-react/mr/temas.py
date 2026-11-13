"""Gravacao deitada e longa com VARIOS assuntos (ex.: react de videos diferentes, opiniao + parte financeira): divide por
tema antes de virar video completo + cortes (pedido do dono em 12/10; a de 06/10 foi dividida a mao em parte1/parte2).

Cada tema vira um arquivo (stream copiado, sem re-render) em work/<slug>/temas/<nome>_temaN.mp4 e segue o fluxo grande:
grande.empacotar (video completo em grandes/<canal>/) + pipeline.process (cortes em cortes/<canal>/).
Audio e transcricao ficam no cache de work/<slug>/ (os mesmos do pipeline); os temas em work/<slug>/temas.json.
"""
from pathlib import Path

from .common import log, load_json, save_json, ffmpeg
from . import probe as P, audio as A, transcribe as T, editorial as ED
from .llm import ask_json

MIN_TEMA = 240  # s: tema mais curto que isso junta com o vizinho (nao vale um video completo)

INSTRUCOES = """Voce e o editor de uma rede de canais de react no YouTube. Esta gravacao HORIZONTAL de {dur_min:.0f} min foi feita de uma vez
e pode ter VARIOS assuntos (ex.: react de videos diferentes, opiniao, parte financeira, tutorial). Cada assunto vai virar um video
COMPLETO separado, postado no canal certo. Os tempos da transcricao estao em [minutos:segundos].
Canais disponiveis (slug - nicho):
{canais}

Responda SOMENTE com um JSON valido:
{{"temas": [{{"inicio": 0, "fim": 123.4, "tema": "assunto em poucas palavras", "tipo": "react", "canal": "slug", "motivo": "por que este canal"}}]}}
Regras:
- "inicio" e "fim" em SEGUNDOS desde o comeco da gravacao.
- "tipo": "react" quando o criador reage a um video/anime/filme/serie; "aula" quando e aula, workshop, palestra, tutorial ou
  conversa do proprio criador ensinando (sem video reagido).
- Corte so na TROCA DE ASSUNTO (outro video reagido, mudanca clara de conversa), numa pausa entre frases, nunca no meio de uma frase.
- Cada tema com pelo menos {min_min:.0f} min; trecho menor que isso vai junto com o tema vizinho.
- Temas na ordem do video, sem sobreposicao. Pode deixar de fora trechos mortos (ajustando camera, silencio, conversa sem assunto),
  mas nao corte conteudo bom.
- Se a gravacao inteira e um assunto so, devolva 1 tema de 0 ate o fim.
- Nao invente: use a transcricao."""


def _work(cfg, video):
    from .pipeline import slugify
    w = Path(cfg["paths"]["work"]) / slugify(Path(video).stem)
    w.mkdir(parents=True, exist_ok=True)
    return w


def _transcricao(cfg, video, work):
    from .pipeline import _cached
    info = _cached(work / "probe.json", lambda: P.probe(cfg, video))
    raw_wav, clean_wav = work / "raw.wav", work / "clean.wav"
    if not raw_wav.exists():
        A.extract_wav(cfg, video, raw_wav)
    if not clean_wav.exists():
        A.clean_audio(cfg, raw_wav, clean_wav)
    tx = _cached(work / "transcript.json", lambda: T.transcribe(cfg, clean_wav))
    return info["duration"], tx["segments"]


def _limpar(lista, dur, slugs):
    """Ordena, corta sobreposicao e junta tema curto com o vizinho (fica o assunto/canal do mais longo)."""
    def num(x, padrao):
        try:
            return float(x if x is not None else padrao)
        except (TypeError, ValueError):
            return None

    validos = []
    for t in lista or []:
        if isinstance(t, dict) and num(t.get("inicio"), 0) is not None and num(t.get("fim"), dur) is not None:
            validos.append((num(t.get("inicio"), 0), num(t.get("fim"), dur), t))
    ok = []
    for a, b, t in sorted(validos, key=lambda x: x[0]):
        a, b = max(0.0, a), min(dur, b)
        if ok and a < ok[-1]["fim"]:
            a = ok[-1]["fim"]
        if b - a >= 1:
            ok.append({"inicio": round(a, 2), "fim": round(b, 2), "tema": str(t.get("tema") or "").strip(),
                       "tipo": "aula" if t.get("tipo") == "aula" else "react",
                       "canal": t.get("canal") if t.get("canal") in slugs else None})
    while len(ok) > 1:
        curtos = [i for i, t in enumerate(ok) if t["fim"] - t["inicio"] < MIN_TEMA]
        if not curtos:
            break
        i = curtos[0]
        j = i - 1 if i > 0 else i + 1
        a, b = sorted((i, j))
        maior = max(ok[a], ok[b], key=lambda t: t["fim"] - t["inicio"])
        ok[a] = dict(maior, inicio=ok[a]["inicio"], fim=ok[b]["fim"])
        del ok[b]
    return ok or [{"inicio": 0.0, "fim": round(dur, 2), "tema": "", "tipo": "react", "canal": None}]


def cfg_do_tema(cfg, tema):
    """Tema de AULA vai para o canal de aulas (config.json > aulas), com o aviso para o editorial; react segue normal."""
    aulas = cfg.get("aulas") or {}
    if (tema or {}).get("tipo") == "aula" and aulas.get("canal"):
        return dict(cfg, forcar={"canal": aulas["canal"], "contexto": aulas.get("contexto", "")})
    return cfg


def temas(cfg, video, force=False):
    """Temas da gravacao [{inicio, fim, tema, canal}] (cache work/<slug>/temas.json)."""
    work = _work(cfg, video)
    cache = work / "temas.json"
    if cache.exists() and not force:
        return load_json(cache)
    dur, segments = _transcricao(cfg, video, work)
    chans = cfg.get("channels") or []
    instr = INSTRUCOES.format(dur_min=dur / 60, min_min=MIN_TEMA / 60,
                              canais="\n".join(f"- {c['slug']} - {c.get('niche', '')}" for c in chans))
    resp = ask_json(cfg, instr, "TRANSCRICAO:\n" + ED.transcript_text(segments), timeout=600) or {}
    lista = _limpar(resp.get("temas"), dur, {c["slug"] for c in chans})
    save_json(lista, cache)
    return lista


def dividir(cfg, video, force=False):
    """Corta a gravacao nos temas. Devolve [(arquivo, tema)] (1 por tema); com 1 tema so, [(video, tema)] (nao corta)."""
    video = Path(video)
    lista = temas(cfg, video, force)
    if len(lista) <= 1:
        log(f"temas: {video.name} tem 1 assunto so ({lista[0].get('tipo')}) - vai inteiro")
        return [(video, lista[0])]
    pasta = _work(cfg, video) / "temas"
    pasta.mkdir(parents=True, exist_ok=True)
    saidas = []
    for n, t in enumerate(lista, 1):
        out = pasta / f"{video.stem}_tema{n}.mp4"
        if force or not out.exists():
            ffmpeg(cfg, ["-ss", f"{t['inicio']:.2f}", "-i", str(video), "-t", f"{t['fim'] - t['inicio']:.2f}", "-map", "0",
                         "-c", "copy", "-avoid_negative_ts", "make_zero", "-movflags", "+faststart", str(out)])
        log(f"temas: {out.name} {t['inicio'] / 60:.1f}-{t['fim'] / 60:.1f} min | {t['tipo']}: {t['tema']} ({t['canal'] or '?'})")
        saidas.append((out, t))
    return saidas
