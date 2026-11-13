#!/usr/bin/env python3
"""Mede o RITMO dos narradores humanos de referência e compara com o nosso (pedido do dono, 17/10/2026).

Fonte das referências: os .vtt automáticos do YouTube em D:/hipercool-materiais/referencias_narradores/<canal>/,
que trazem o instante de CADA palavra (<00:00:01.480><c> palavra</c>). Do nosso lado: o áudio do capítulo
transcrito pelo Groq (tempo por palavra, sempre pelo proxy).

Métricas, iguais dos dois lados (só fala: intervalos > 4 s são cortes/música e ficam fora):
  ppm            palavras por minuto (média)
  ppm_cv         variação da velocidade entre janelas de 10 s (desvio/média) — "voz estável demais" = baixo
  pausas_min     pausas > 0,45 s por minuto
  pausa_longa_min pausas > 1,0 s por minuto
  ioi_cv         variação do intervalo entre o começo de uma palavra e da seguinte (ritmo dentro da frase)
E as muletas: 1-3-gramas mais frequentes por 1000 palavras.

    python bin/medir_narradores.py                  # referências (até 40 vídeos por canal)
    python bin/medir_narradores.py --nosso <mp4>    # + o nosso vídeo
Saída: D:/hipercool-materiais/referencias_narradores/_medidas/ (json + md).
"""
import argparse
import json
import re
import statistics as st
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

REF = Path(r"D:/hipercool-materiais/referencias_narradores")
SAIDA = REF / "_medidas"
CORTE = 4.0
_TS = re.compile(r"<(\d+):(\d+):(\d+\.\d+)><c>\s*([^<]+?)</c>")
_LINHA = re.compile(r"^(\d+):(\d+):(\d+\.\d+) -->")


def _s(h, m, s):
    return int(h) * 3600 + int(m) * 60 + float(s)


def palavras_vtt(path):
    """[(t_inicio, palavra)] de um .vtt automático do YouTube (só as linhas com tempo por palavra)."""
    out, cue = [], None
    for linha in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = _LINHA.match(linha)
        if m:
            cue = _s(*m.groups())
            continue
        if "<c>" not in linha or cue is None:
            continue
        primeira = linha.split("<", 1)[0].strip()
        if primeira:
            out.append((cue, primeira))
        for h, mi, se, w in _TS.findall(linha):
            out.append((_s(h, mi, se), w.strip()))
    out.sort()
    # o vtt repete a linha anterior sem tempo: tira duplicatas de mesmo instante
    vistos, limpo = set(), []
    for t, w in out:
        k = (round(t, 2), w)
        if k not in vistos and w:
            vistos.add(k)
            limpo.append((t, w))
    return limpo


def metricas(pal):
    if len(pal) < 60:
        return None
    ts = [t for t, _ in pal]
    ioi = [b - a for a, b in zip(ts, ts[1:]) if 0 < b - a <= CORTE]
    fala_s = sum(ioi)
    if fala_s < 30:
        return None
    pausas = [x for x in ioi if x > 0.45]
    longas = [x for x in ioi if x > 1.0]
    # velocidade em janelas de 10 s de FALA (pula buracos > CORTE)
    janelas, ini, n = [], ts[0], 0
    for a, b in zip(ts, ts[1:]):
        if b - a > CORTE:
            ini, n = b, 0
            continue
        n += 1
        if b - ini >= 10:
            janelas.append(n * 60 / (b - ini))
            ini, n = b, 0
    curtos = [x for x in ioi if x <= 0.45]  # dentro da frase
    return {
        "palavras": len(pal), "fala_min": round(fala_s / 60, 2),
        "ppm": round(len(ioi) * 60 / fala_s, 1),
        "ppm_cv": round(st.pstdev(janelas) / st.mean(janelas), 3) if len(janelas) > 3 else None,
        "pausas_min": round(len(pausas) / (fala_s / 60), 1),
        "pausa_longa_min": round(len(longas) / (fala_s / 60), 1),
        "pausa_media_s": round(st.mean(pausas), 2) if pausas else None,
        "ioi_cv": round(st.pstdev(curtos) / st.mean(curtos), 3) if len(curtos) > 20 else None,
    }


def _norm(w):
    return re.sub(r"[^\wà-ú]", "", w.lower())


def ngramas(pal, n):
    ws = [_norm(w) for _t, w in pal]
    ws = [w for w in ws if w]
    return Counter(" ".join(ws[i:i + n]) for i in range(len(ws) - n + 1)), len(ws)


def media(lst, k):
    v = [x[k] for x in lst if x and x.get(k) is not None]
    return round(st.median(v), 3) if v else None


CHAVES = ["ppm", "ppm_cv", "pausas_min", "pausa_longa_min", "pausa_media_s", "ioi_cv"]


def medir_canais(max_por_canal=40):
    res = {}
    total_ng = {1: Counter(), 2: Counter(), 3: Counter()}
    total_w = 0
    for canal in sorted(p for p in REF.iterdir() if p.is_dir() and not p.name.startswith(("_", "."))):
        vtts = sorted(canal.glob("*.vtt"))[:max_por_canal]
        ms = []
        for v in vtts:
            pal = palavras_vtt(v)
            m = metricas(pal)
            if m:
                ms.append(m)
                for n in (1, 2, 3):
                    c, nw = ngramas(pal, n)
                    total_ng[n].update(c)
                    if n == 1:
                        total_w += nw
        if ms:
            res[canal.name] = {"videos": len(ms), **{k: media(ms, k) for k in CHAVES}}
            print(f"{canal.name:20} {len(ms):3d} vídeos  " + "  ".join(f"{k}={res[canal.name][k]}" for k in CHAVES))
    return res, total_ng, total_w


def medir_nosso(mp4):
    import fx_acabamento as fx
    tmp = SAIDA / "_tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    words = fx._transcrever_groq(str(mp4), tmp) or []
    pal = [(w["s"], w["w"]) for w in words]
    return metricas(pal), pal


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nosso", action="append", default=[])
    ap.add_argument("--max", type=int, default=40)
    a = ap.parse_args()
    SAIDA.mkdir(parents=True, exist_ok=True)
    canais, ng, nw = medir_canais(a.max)
    nossos = {}
    for mp4 in a.nosso:
        m, pal = medir_nosso(mp4)
        nossos[Path(mp4).name] = m
        (SAIDA / f"nosso_{Path(mp4).stem[:40]}_palavras.json").write_text(
            json.dumps(pal, ensure_ascii=False), encoding="utf-8")
        print(f"NOSSO {Path(mp4).name[:40]}: {m}")
    muletas = {n: [(g, round(c * 1000 / max(1, nw), 2)) for g, c in ng[n].most_common(120)] for n in (1, 2, 3)}
    (SAIDA / "medidas.json").write_text(json.dumps({"canais": canais, "nossos": nossos, "muletas_por_mil": muletas,
                                                    "palavras_total": nw}, ensure_ascii=False, indent=1),
                                        encoding="utf-8")
    print(f"gravado em {SAIDA / 'medidas.json'}")


if __name__ == "__main__":
    main()
