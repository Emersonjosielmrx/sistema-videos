"""Plano de cortes (EDL): silencios, vicios de linguagem, retakes e trechos removidos pelo editorial."""
import re
import difflib
import unicodedata
from .common import log


def _norm(txt):
    t = unicodedata.normalize("NFKD", txt.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9 ]+", " ", t).strip()


def _union(intervals):
    ivs = sorted([list(i) for i in intervals if i[1] > i[0]])
    out = []
    for a, b in ivs:
        if out and a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out


def silence_cuts(cfg, silences, duration, part=(0.0, None)):
    C = cfg["cuts"]
    p0 = part[0]
    p1 = part[1] if part[1] is not None else duration
    cuts = []
    for s, e in silences:
        if e is None:
            e = duration
        s, e = max(s, p0), min(e, p1)
        if e <= s:
            continue
        if s <= p0 + 0.01:                       # silencio inicial: comeca falando
            b = e - C["margin_before"]
            if b > p0:
                cuts.append([p0, b])
        elif e >= p1 - 0.01:                     # silencio final
            a = s + C["margin_after"]
            if a < p1:
                cuts.append([a, p1])
        else:
            a = s + C["margin_after"] + C["pause_keep"] / 2
            b = e - C["margin_before"] - C["pause_keep"] / 2
            if b - a >= 0.08:
                cuts.append([a, b])
    return cuts


def filler_cuts(cfg, words):
    C = cfg["cuts"]
    if not C.get("remove_fillers"):
        return []
    rx = re.compile(C["filler_regex"])
    cuts = []
    for w in words:
        if w.get("speaker") == "content":
            continue
        t = _norm(w["w"])
        if t and rx.match(t) and (w["e"] - w["s"]) >= C["filler_min_duration"]:
            cuts.append([w["s"] - 0.03, w["e"] + 0.03])
            w["filler"] = True
    if cuts:
        log(f"vicios de linguagem removidos: {len(cuts)}")
    return cuts


def retake_cuts(cfg, segments):
    C = cfg["cuts"]
    if not C.get("remove_retakes"):
        return []
    cuts = []
    creator = [s for s in segments if s.get("speaker") != "content"]
    for prev, cur in zip(creator, creator[1:]):
        a, b = _norm(prev["text"]), _norm(cur["text"])
        if len(a.split()) < 3 or len(b.split()) < 3:
            continue
        r = difflib.SequenceMatcher(None, a, b).ratio()
        if r >= C["retake_similarity"] and (cur["start"] - prev["end"]) < 3.0:
            cuts.append([prev["start"] - 0.05, cur["start"] - 0.02])
            prev["retake"] = True
            log(f"retake detectado ({r:.2f}): '{prev['text'][:40]}' -> removido")
    return cuts


def build_keeps(cfg, duration, cuts, part=(0.0, None)):
    C = cfg["cuts"]
    p0 = part[0]
    p1 = part[1] if part[1] is not None else duration
    cuts = _union([[max(p0, a), min(p1, b)] for a, b in cuts] + [[0, p0], [p1, duration]])
    keeps, t = [], 0.0
    for a, b in cuts:
        if a > t:
            keeps.append([t, a])
        t = max(t, b)
    if t < duration:
        keeps.append([t, duration])
    keeps = [k for k in keeps if k[1] - k[0] >= C["min_segment"]]
    merged = []
    for k in keeps:
        if merged and k[0] - merged[-1][1] < 0.06:
            merged[-1][1] = k[1]
        else:
            merged.append(list(k))
    return merged


def plan(cfg, duration, silences, words, segments, extra_cuts=(), part=(0.0, None)):
    cuts = []
    if cfg["cuts"].get("enabled", True):
        cuts += silence_cuts(cfg, silences, duration, part)
        cuts += filler_cuts(cfg, words)
        cuts += retake_cuts(cfg, segments)
    cuts += [[c[0], c[1]] for c in extra_cuts]
    keeps = build_keeps(cfg, duration, cuts, part)
    kept = sum(b - a for a, b in keeps)
    p_len = (part[1] if part[1] is not None else duration) - part[0]
    log(f"cortes: {len(keeps)} trechos mantidos, {p_len:.1f}s -> {kept:.1f}s ({100*(1-kept/max(p_len,0.01)):.0f}% removido)")
    return keeps


class Timeline:
    """Mapeia tempos do video original para o video cortado."""

    def __init__(self, keeps):
        self.keeps = keeps
        self.offsets = []
        acc = 0.0
        for a, b in keeps:
            self.offsets.append(acc)
            acc += b - a
        self.duration = acc

    def map(self, t):
        for (a, b), off in zip(self.keeps, self.offsets):
            if t < a:
                return off
            if t <= b:
                return off + (t - a)
        return self.duration

    def inside(self, t):
        return any(a <= t <= b for a, b in self.keeps)

    def remap_words(self, words):
        out = []
        for w in words:
            mid = (w["s"] + w["e"]) / 2
            if not self.inside(mid):
                continue
            nw = dict(w)
            nw["s"] = self.map(w["s"])
            nw["e"] = max(self.map(w["e"]), nw["s"] + 0.08)
            out.append(nw)
        return out

    def segment_starts(self):
        return list(self.offsets)


def trim_keeps(keeps, max_dur, tolerance=1.08):
    """Garante que a soma dos trechos nao passe de max_dur (corta pelo fim)."""
    total = sum(b - a for a, b in keeps)
    if total <= max_dur * tolerance:
        return keeps
    out, acc = [], 0.0
    for a, b in keeps:
        if acc >= max_dur:
            break
        room = max_dur - acc
        if b - a > room:
            out.append([a, a + room])
            acc += room
            break
        out.append([a, b])
        acc += b - a
    log(f"duracao limitada: {total:.1f}s -> {acc:.1f}s (max {max_dur}s)")
    return out


def long_silences(silences, min_len):
    return [[s, e] for s, e in silences if e is not None and (e - s) >= min_len]
