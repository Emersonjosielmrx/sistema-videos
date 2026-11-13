"""modelos_esgotados.py — registro único de "TODOS os modelos da fila falharam" (dona 29/10 21:30: "se ainda assim falhar
precisa estar no log para acionarmos mais modelos").

Cada melhorador (produtos, cortes, longo, ccv) chama `registrar(linha, papel, tentados)` quando percorre a fila inteira do
papel e nenhum respondeu. Fica uma linha por ocorrência em estado\\central\\modelos_esgotados.jsonl:
  {"em", "linha", "papel", "tentados": [{"modelo", "motivo"}], "fila_atual": [...]}

    python modelos_esgotados.py          # resume as últimas 24 h por linha/papel (quantas vezes a fila acabou)
"""
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

ARQ = Path(r"D:\video-fila\estado\central\modelos_esgotados.jsonl")


def registrar(linha, papel, tentados, fila=None):
    """tentados: [(modelo, motivo)] na ordem em que a fila foi percorrida. Nunca levanta erro (não pode travar a linha)."""
    try:
        ARQ.parent.mkdir(parents=True, exist_ok=True)
        reg = {"em": datetime.now().isoformat(timespec="seconds"), "linha": linha, "papel": papel,
               "tentados": [{"modelo": m, "motivo": str(x)[:160]} for m, x in tentados],
               "fila_atual": list(fila or [m for m, _ in tentados])}
        with ARQ.open("a", encoding="utf-8") as f:
            f.write(json.dumps(reg, ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001
        pass


def resumo(horas=24):
    from collections import Counter
    desde = (datetime.now() - timedelta(hours=horas)).isoformat()
    c, ult = Counter(), {}
    try:
        for ln in ARQ.read_text("utf-8").splitlines():
            try:
                r = json.loads(ln)
            except ValueError:
                continue
            if r["em"] >= desde:
                c[(r["linha"], r["papel"])] += 1
                ult[(r["linha"], r["papel"])] = r
    except OSError:
        pass
    if not c:
        print(f"nenhuma vez em {horas} h em que a fila inteira falhou")
        return
    for (linha, papel), n in c.most_common():
        u = ult[(linha, papel)]
        print(f"{n:3}x {linha:10} {papel:10} última {u['em']}: " +
              " | ".join(f"{t['modelo']} ({t['motivo'][:50]})" for t in u["tentados"]))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    resumo()
