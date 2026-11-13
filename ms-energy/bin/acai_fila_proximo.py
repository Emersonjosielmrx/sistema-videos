# -*- coding: utf-8 -*-
r"""acai_fila_proximo.py — tarefa Acai_Postar (30/30 min): posta o PRÓXIMO item da fila_para_postar do açaí
(paleta C, dona 05/11 13h: "e as outras postagens?"). Alterna carrossel e reel; reel do arquivado sem reel.mp4 é
finalizado na hora (selo + cartão C + trilha). Mínimo 25 min entre posts. Legenda sempre com os 2 endereços e os
2 números (acai_postar_fila.legenda_final). Só 1 rodando por vez (trava de arquivo).
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, r"D:\ms-energy\bin")
import acai  # noqa: E402
import acai_postar_fila as apf  # noqa: E402

FILA = Path(r"D:\ms-energy\videos\acai\fila_para_postar")
TRAVA = Path(r"D:\ms-energy\cache\acai_fila.lock")
SO_CARROSSEL = True  # 05/11 17h dona: "não posta reels por hora no açaí, posta só os outros" (False = volta a alternar)
INTERVALO_MIN = 19  # 05/11 15h dona: "faça de 20 min" (tarefa roda de 10 em 10 min)


def _ultimo():
    ts = [json.loads(p.read_text("utf-8")).get("em") for p in FILA.glob("*/postado.json")]
    ts = [datetime.fromisoformat(t) for t in ts if t]
    return max(ts) if ts else None


def _pendentes():
    car = sorted(p for p in FILA.glob("carrossel_*_C") if not (p / "postado.json").exists() and list(p.glob("*.jpg")))
    ree = []
    for p in sorted(FILA.glob("arquivado_*")):
        if (p / "postado.json").exists() or not (p / "base.mp4").exists():
            continue
        info = json.loads((p / "info.json").read_text("utf-8"))
        ree.append((-info.get("palavras", 0), p))  # quem fala mais primeiro
    return car, [p for _, p in sorted(ree)]


def main():
    if TRAVA.exists() and (datetime.now().timestamp() - TRAVA.stat().st_mtime) < 1800:
        return acai.log("[fila] outra rodada no ar — saio")
    TRAVA.write_text(str(os.getpid()))
    try:
        u = _ultimo()
        if u and (datetime.now() - u).total_seconds() / 60 < INTERVALO_MIN:
            return acai.log(f"[fila] último post há {(datetime.now() - u).total_seconds() / 60:.0f} min — espero")
        car, ree = _pendentes()
        if SO_CARROSSEL:
            ree = []
        postados = [json.loads(p.read_text("utf-8")) for p in FILA.glob("*/postado.json")]
        ultimo_reel = sorted(postados, key=lambda x: x.get("em", ""))[-1].get("link", "").count("/reel/") if postados else 0
        ordem = (car + ree) if ultimo_reel else (ree + car)
        if not ordem:
            return acai.log("[fila] nada pendente")
        alvo = ordem[0]
        if alvo.name.startswith("arquivado_") and not (alvo / "reel.mp4").exists():
            import acai_finalizar_C  # noqa: F401
            from PIL import Image
            import acai_arquivados as aa
            aa.finalizar(alvo, (61, 15, 59), Image.open(acai_finalizar_C.CARTAO))
        apf.postar(alvo)
    finally:
        TRAVA.unlink(missing_ok=True)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
