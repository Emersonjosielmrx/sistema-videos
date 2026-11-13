# -*- coding: utf-8 -*-
r"""prever_retencao.py — prevê a % assistida de um Short ANTES de postar, a partir das medidas físicas do vídeo
(duração, cortes/s, cortes nos 2 s, 1º corte, maior plano, volume, silêncio inicial, hora), treinado nos NOSSOS vídeos
que já têm % assistido no Studio (item 8 de CORTES_10_NOVO_29-10_PENDENTES.md: as linhas Claude Code Video e Produtos
têm 0–2 views, então nunca terão retenção medida tão cedo; a nota do júri não prevê views).

Honestidade embutida: o modelo é re-treinado a cada chamada com validação leave-one-out e DIZ se é confiável
(n ≥ 40 e correlação ≥ 0,5). Em 29/10: n=48, erro médio 20 pontos (chute pela mediana: 23), correlação 0,58,
acerto de "passa de 65%" 83% (base 73%). Ou seja: separa razoavelmente "vai segurar" de "não vai", não acerta o número.
Se não for confiável, a resposta vem com confiavel=false e o único caminho é postar e medir.

    python prever_retencao.py <video.mp4>          # imprime a previsão
    python prever_retencao.py --modelo             # só treina e mostra a qualidade
    from prever_retencao import prever; prever(r"...mp4") -> {"pct": 58, "faixa": [38, 78], "confiavel": True, ...}
"""
import json
import math
import sys
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
STUDIO = Path(r"D:\postador-de-videos\_analise\metricas_studio.json")
NOSSOS = AQUI / "medidas_nossos.jsonl"
MODELO = AQUI / "modelo_retencao.json"
COLS = ["dur", "cortes_s", "cortes_2s", "primeiro_corte", "maior_plano_s", "vol_2s", "vol_dif", "silencio_ini_s", "hora"]
LAMBDA = 3.0


def _dados():
    st = json.loads(STUDIO.read_text("utf-8"))
    feats = {}
    for l in NOSSOS.read_text("utf-8", errors="replace").splitlines():
        try:
            d = json.loads(l)
            feats[d["vid"]] = d
        except (ValueError, KeyError):
            continue
    X, y = [], []
    for vid, f in feats.items():
        m = st.get(vid) or {}
        try:
            pct = float(m.get("pct_media"))
            views = float(m.get("views") if m.get("views") not in (None, "None") else f.get("views") or 0)
        except (TypeError, ValueError):
            continue
        if views < 20:
            continue
        X.append(_vetor(f)); y.append(pct)
    return X, y


def _vetor(f):
    v = []
    for c in COLS:
        x = f.get(c)
        x = float(x) if x not in (None, "None") else 0.0
        if c == "dur":
            x = math.log1p(x)
        v.append(x)
    return v


def treinar():
    import numpy as np
    X, y = _dados()
    n = len(y)
    if n < 12:
        m = {"n": n, "confiavel": False, "motivo": "menos de 12 vídeos medidos", "em": datetime.now().isoformat(timespec="minutes")}
        MODELO.write_text(json.dumps(m, ensure_ascii=False, indent=1), "utf-8")
        return m
    X = np.array(X); y = np.array(y)
    mu, sd = X.mean(0), X.std(0) + 1e-9
    Z = np.hstack([(X - mu) / sd, np.ones((n, 1))])

    def fit(Za, ya):
        return np.linalg.solve(Za.T @ Za + LAMBDA * np.eye(Za.shape[1]), Za.T @ ya)
    pred = np.array([Z[i] @ fit(np.delete(Z, i, 0), np.delete(y, i)) for i in range(n)])
    mae = float(np.mean(np.abs(pred - y))); base = float(np.mean(np.abs(np.median(y) - y)))
    corr = float(np.corrcoef(pred, y)[0, 1]) if n > 2 else 0.0
    acc65 = float(np.mean((pred >= 65) == (y >= 65)))
    w = fit(Z, y)
    m = {"n": n, "mae": round(mae, 1), "mae_base": round(base, 1), "corr": round(corr, 2), "acerto_65": round(acc65, 2),
         "mediana_real": float(np.median(y)), "confiavel": bool(n >= 40 and corr >= 0.5 and mae < base),
         "pesos": {c: round(float(x), 3) for c, x in zip(COLS, w[:-1])}, "intercepto": round(float(w[-1]), 3),
         "mu": [float(a) for a in mu], "sd": [float(a) for a in sd], "em": datetime.now().isoformat(timespec="minutes")}
    MODELO.write_text(json.dumps(m, ensure_ascii=False, indent=1), "utf-8")
    return m


def modelo():
    try:
        m = json.loads(MODELO.read_text("utf-8"))
        if (datetime.now() - datetime.fromisoformat(m["em"])).total_seconds() < 6 * 3600 and "pesos" in m:
            return m
    except (OSError, ValueError, KeyError):
        pass
    return treinar()


def prever_features(f, hora=None):
    m = modelo()
    if "pesos" not in m:
        return {"pct": None, "confiavel": False, "motivo": m.get("motivo", "sem modelo"), "n": m.get("n", 0)}
    f = dict(f)
    f.setdefault("hora", hora if hora is not None else datetime.now().hour)
    v = _vetor(f)
    z = [(x - a) / b for x, a, b in zip(v, m["mu"], m["sd"])]
    pct = m["intercepto"] + sum(w * zi for w, zi in zip(m["pesos"].values(), z))
    pct = max(5.0, min(130.0, pct))
    return {"pct": round(pct), "faixa": [round(max(0, pct - m["mae"])), round(pct + m["mae"])], "confiavel": m["confiavel"],
            "passa_65": pct >= 65, "n": m["n"], "mae": m["mae"], "corr": m["corr"],
            "aviso": None if m["confiavel"] else f"modelo fraco (n={m['n']}, corr={m['corr']}): só direção, não o número"}


def prever(mp4, hora=None):
    import medir
    return {**prever_features(medir.medir(str(mp4)), hora), "arquivo": str(mp4)}


def main(a):
    if sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if not a or a[0] == "--modelo":
        m = treinar()
        print(json.dumps({k: m.get(k) for k in ("n", "mae", "mae_base", "corr", "acerto_65", "confiavel", "pesos", "em")}, ensure_ascii=False, indent=1))
        return 0
    print(json.dumps(prever(a[0]), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
