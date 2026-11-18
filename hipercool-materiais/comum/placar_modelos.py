r"""placar_modelos.py — placar do Hydrogen x Gemini 3.8 nos consertos de código (dona 18/11: "como o Hydrogen está
indo, modelo novo, acompanhar se é inferior ou superior ao Gemini 3.8").

Cada caixa de código chama registrar(lugar, modelo, entregou, segundos, obs) depois de cada tentativa; o relatório da
ronda lê resumo(). Arquivo: D:\video-fila\estado\placar_modelos.jsonl (1 linha por tentativa). Nunca levanta.
PLACAR_MODELOS=0 desliga a gravação.
"""
import json
import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ARQ = Path(r"D:\video-fila\estado\placar_modelos.jsonl")


def _familia(modelo):
    m = (modelo or "").lower()
    if "hydrogen" in m:
        return "Hydrogen"
    if "gemini-3.8" in m or "gemini-3-8" in m:
        return "Gemini 3.8"
    return modelo or "?"


def registrar(lugar, modelo, entregou, segundos=None, obs=""):
    if os.environ.get("PLACAR_MODELOS", "1") == "0":
        return
    try:
        ARQ.parent.mkdir(parents=True, exist_ok=True)
        with ARQ.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"em": datetime.now().isoformat(timespec="seconds"), "lugar": lugar, "modelo": modelo,
                                "familia": _familia(modelo), "entregou": bool(entregou),
                                "s": round(segundos) if segundos is not None else None, "obs": str(obs)[:160]},
                               ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001
        pass


def resumo(dias=None):
    """{familia: {"tentativas", "entregou", "pct", "mediana_s", "lugares": {lugar: [tent, ok]}}} — dias=None = tudo."""
    out = defaultdict(lambda: {"tentativas": 0, "entregou": 0, "_s": [], "lugares": defaultdict(lambda: [0, 0])})
    try:
        linhas = ARQ.read_text(encoding="utf-8").splitlines()
    except OSError:
        return {}
    for l in linhas:
        try:
            d = json.loads(l)
        except ValueError:
            continue
        if dias and (datetime.now() - datetime.fromisoformat(d["em"])).days >= dias:
            continue
        r = out[d["familia"]]
        r["tentativas"] += 1
        r["lugares"][d["lugar"]][0] += 1
        if d["entregou"]:
            r["entregou"] += 1
            r["lugares"][d["lugar"]][1] += 1
            if d.get("s") is not None:
                r["_s"].append(d["s"])
    res = {}
    for k, r in out.items():
        s = sorted(r["_s"])
        res[k] = {"tentativas": r["tentativas"], "entregou": r["entregou"],
                  "pct": round(100 * r["entregou"] / r["tentativas"]) if r["tentativas"] else 0,
                  "mediana_s": s[len(s) // 2] if s else None, "lugares": {a: b for a, b in r["lugares"].items()}}
    return res
