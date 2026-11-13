"""Transcricao com timestamps por palavra.

Motor principal: Groq (whisper-large-v3, ~2 s por video, melhor qualidade). Fallback: faster-whisper local.
"""
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path
from .common import log
from . import groq_api, limitador

# O MKL falha com "mkl_malloc" nesta maquina quando a memoria/pagefile esta apertada; sem MKL o ctranslate2 carrega normal.
os.environ.setdefault("CT2_USE_MKL", "0")

_model_cache = {}


# ----------------------------------------------------------------------------- util
def load_audio_16k(wav):
    """Le o wav (soundfile), mixa para mono e reamostra para 16 kHz (evita depender do PyAV)."""
    import numpy as np
    import soundfile as sf
    from scipy.signal import resample_poly
    from math import gcd
    data, sr = sf.read(str(wav), dtype="float32", always_2d=True)
    mono = data.mean(axis=1)
    if sr != 16000:
        g = gcd(sr, 16000)
        mono = resample_poly(mono, 16000 // g, sr // g).astype(np.float32)
    return np.ascontiguousarray(mono, dtype=np.float32)


def _segments_from_words(words, max_gap=0.7, max_words=18):
    """Agrupa palavras em segmentos por pausas (quando o motor nao devolve segmentos)."""
    segs, cur = [], []
    for w in words:
        if cur and (w["s"] - cur[-1]["e"] > max_gap or len(cur) >= max_words or cur[-1]["w"].endswith((".", "!", "?"))):
            segs.append(cur)
            cur = []
        cur.append(w)
    if cur:
        segs.append(cur)
    out = []
    for ws in segs:
        out.append({"start": ws[0]["s"], "end": ws[-1]["e"], "text": " ".join(w["w"] for w in ws), "words": ws,
                    "avg_p": sum(w["p"] for w in ws) / len(ws)})
    return out


# ----------------------------------------------------------------------------- groq
def _groq_request_via_proxy(audio_path, lang):
    """Transcreve pelo groq_api.py (com proxy Webshare e rodízio de chaves)."""
    return groq_api.transcrever(audio_path, idioma=lang or "pt", palavras=True, timeout=300)


def _duration(wav):
    import soundfile as sf
    try:
        return sf.info(str(wav)).duration
    except Exception:  # noqa: BLE001
        return 0.0


def transcribe_groq(cfg, wav, lang):
    """Groq aceita ate 25 MB por arquivo (~13 min de wav 16 kHz mono): audio maior vai em pedacos de chunk_s
    segundos com sobreposicao, e cada palavra fica com o pedaco que a cobre melhor."""
    T = cfg["transcribe"]
    if not groq_api.chaves():
        log("groq: sem chaves")
        return None
    model = T.get("groq_model", "whisper-large-v3")
    chunk, overlap = float(T.get("groq_chunk_s", 600)), float(T.get("groq_overlap_s", 4))
    total = _duration(wav) or chunk
    n = max(1, int(-(-total // chunk)))
    words, segs = [], []
    for i in range(n):
        a0 = i * chunk
        tmp = Path(tempfile.gettempdir()) / f"mr_groq_{int(time.time())}_{i}.wav"
        cmd = [cfg["paths"]["ffmpeg"], "-y", "-loglevel", "error"]
        if n > 1:
            cmd += ["-ss", f"{a0:.3f}", "-t", f"{chunk + overlap:.3f}"]
        subprocess.run(cmd + ["-i", str(wav), "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(tmp)], check=True)
        try:
            j = _groq_request_via_proxy(tmp, lang)
        finally:
            tmp.unlink(missing_ok=True)
        if j is None:
            log(f"groq: falhou no pedaco {i + 1}/{n}")
            return None
        # janela que este pedaco "possui": do meio da sobreposicao anterior ao meio da proxima
        lo = a0 + (overlap / 2 if i > 0 else 0)
        hi = a0 + chunk + overlap / 2 if i < n - 1 else float("inf")
        cw = [{"w": (w.get("word") or "").strip(), "s": a0 + float(w["start"]), "e": a0 + float(w["end"]), "p": 0.9}
              for w in (j.get("words") or []) if (w.get("word") or "").strip()]
        cw = [w for w in cw if lo <= w["s"] < hi]
        # na emenda os dois pedacos ouvem a mesma palavra com tempos um pouco diferentes: fica so a primeira
        tail = words[-4:]
        cw = [w for w in cw if not any(_norm_txt(w["w"]) == _norm_txt(t["w"]) and abs(w["s"] - t["s"]) < 1.5 for t in tail)]
        words.extend(cw)
        for s in (j.get("segments") or []):
            a, b = a0 + float(s["start"]), a0 + float(s["end"])
            if not (lo <= a < hi):
                continue
            ws = [w for w in cw if a - 0.01 <= w["s"] < b + 0.01]
            texto = (s.get("text") or "").strip()
            if b > hi and ws:  # segmento atravessa a emenda: o resto do texto vem no proximo pedaco
                texto = " ".join(w["w"] for w in ws)
            segs.append({"start": a, "end": b, "text": texto, "words": ws,
                         "avg_p": float(min(1.0, max(0.0, 1.0 + float(s.get("avg_logprob", -0.1)))))})
        if n > 1:
            log(f"groq: pedaco {i + 1}/{n} ok ({len(cw)} palavras)")
    words.sort(key=lambda w: w["s"])
    segs.sort(key=lambda s: s["start"])
    if not segs:
        segs = _segments_from_words(words)
    log(f"transcricao (groq {model}): {len(segs)} segmentos, {len(words)} palavras" + (f" em {n} pedacos" if n > 1 else ""))
    return {"segments": segs, "words": words, "language": lang, "engine": f"groq:{model}"}


# ----------------------------------------------------------------------------- local
def _model_dir(cfg, size):
    for key in ("whisper_models", "whisper_models_fallback"):
        root = cfg["paths"].get(key)
        if root and (Path(root) / f"models--Systran--faster-whisper-{size}").exists():
            return root
    return cfg["paths"]["whisper_models"]


def get_model(cfg, size=None):
    T = cfg["transcribe"]
    size = size or T["model"]
    if size in _model_cache:
        return _model_cache[size]
    from faster_whisper import WhisperModel
    root = _model_dir(cfg, size)
    Path(root).mkdir(parents=True, exist_ok=True)
    log(f"carregando whisper '{size}' ({T['compute_type']}, {T['cpu_threads']} threads) de {root}")
    try:
        m = WhisperModel(size, device="cpu", compute_type=T["compute_type"], cpu_threads=T["cpu_threads"], download_root=root)
    except RuntimeError as e:
        if "mkl_malloc" not in str(e):
            raise
        log("whisper: mkl_malloc falhou; tentando de novo com 1 thread em 5s")
        time.sleep(5)
        os.environ["MKL_NUM_THREADS"] = "1"
        m = WhisperModel(size, device="cpu", compute_type=T["compute_type"], cpu_threads=1, download_root=root)
    _model_cache[size] = m
    return m


def transcribe_local(cfg, wav, lang, size=None):
    T = cfg["transcribe"]
    model = get_model(cfg, size)
    audio = load_audio_16k(wav)
    segs, info = model.transcribe(audio, language=lang, word_timestamps=True, vad_filter=True,
                                  vad_parameters=dict(min_silence_duration_ms=T["vad_min_silence_ms"], speech_pad_ms=120),
                                  beam_size=T["beam_size"], condition_on_previous_text=False,
                                  initial_prompt="Vamos ver... Então, tipo, né? Hum, é... caramba, mano!")
    segments, words = [], []
    for s in segs:
        ws = [{"w": w.word.strip(), "s": float(w.start), "e": float(w.end), "p": float(w.probability)} for w in (s.words or []) if w.word.strip()]
        seg = {"start": float(s.start), "end": float(s.end), "text": s.text.strip(), "words": ws,
               "avg_p": (sum(w["p"] for w in ws) / len(ws)) if ws else 0.0}
        segments.append(seg)
        words.extend(ws)
    log(f"transcricao (local {size or T['model']}): {len(segments)} segmentos, {len(words)} palavras")
    return {"segments": segments, "words": words, "language": lang, "engine": f"local:{size or T['model']}"}


# ----------------------------------------------------------------------------- limpeza de alucinacoes
def _norm_txt(t):
    import re
    import unicodedata
    t = unicodedata.normalize("NFKD", t.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9 ]+", "", t).strip()


def clean_hallucinations(res):
    """Remove segmentos tipicos de alucinacao do Whisper sobre musica/ruido: texto curtissimo esticado no tempo
    ou o mesmo texto repetido 3+ vezes seguidas."""
    segs = res["segments"]
    keep = []
    i = 0
    removed = 0
    while i < len(segs):
        s = segs[i]
        t = _norm_txt(s["text"])
        j = i
        while j + 1 < len(segs) and _norm_txt(segs[j + 1]["text"]) == t:
            j += 1
        run = j - i + 1
        stretched = len(t) <= 3 and (s["end"] - s["start"]) >= 1.5
        if (run >= 3 and len(t) <= 12) or stretched:
            removed += run
            i = j + 1
            continue
        keep.append(s)
        i += 1
    if removed:
        kept_ids = {id(s) for s in keep}
        words = [w for s in keep for w in s.get("words", [])]
        res["segments"] = keep
        res["words"] = words if words else [w for w in res["words"] if any(s["start"] - 0.01 <= w["s"] <= s["end"] + 0.01 for s in keep)]
        log(f"transcricao: {removed} segmento(s) de alucinacao removido(s)")
    return res


# ----------------------------------------------------------------------------- entrada
def transcribe(cfg, wav, lang=None, size=None):
    """Retorna {'segments': [...], 'words': [...], 'engine': ...}; tempos em segundos no timeline do wav."""
    lang = lang or cfg["channel"].get("language", "pt")
    engine = cfg["transcribe"].get("engine", "groq")
    if engine == "groq" and not size:
        if limitador.restante("groq"):
            log(f"groq em pausa pelo limitador ({limitador.restante('groq') // 60} min); usando whisper local")
        else:
            res = transcribe_groq(cfg, wav, lang)
            if res is None:
                limitador.falhou("groq", "todas as chaves/proxies falharam")
            else:
                limitador.ok("groq")
            if res and res["words"]:
                return clean_hallucinations(res)
            log("groq indisponivel; usando whisper local")
    return clean_hallucinations(transcribe_local(cfg, wav, lang, size))
