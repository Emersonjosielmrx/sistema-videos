# -*- coding: utf-8 -*-
r"""estoque_reels.py — Reels da Advance e da Globo gerados COM ANTECEDÊNCIA (dona 31/10/2026: "está gerando pra
estoque com antecedência?"). Antes cada horário gerava na hora (Veo leva 15-40 min e, sem cota no Flow, o horário
ficava sem Reel). Agora: se a conta tem menos de ALVO Reels prontos e não postados, gera 1 (--so-gerar); o horário de
postagem só pega o pronto. Tarefa Solares_Estoque (de 2 em 2 h, sem janela, 1 por vez).
"""
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PY = r"D:\veo\venv\Scripts\python.exe"
BIN = Path(r"D:\ms-energy\bin")
# 14/11 dona ("o estoque de Instagram das empresas tem que ter os mesmos 30 dias"): 30 Reels prontos por empresa
# (1/dia). Era 2. ESTOQUE_EMPRESAS_DIAS volta (ex.: 2).
import os
ALVO = int(os.environ.get("ESTOQUE_EMPRESAS_DIAS", "30"))
CONTAS = [("advance", BIN / "reel_advance.py", Path(r"D:\ms-energy\videos\reels_advance")),
          ("globo", BIN / "reel_globo.py", Path(r"D:\ms-energy\videos\reels_globo"))]


def prontos(pasta):
    n = 0
    for j in pasta.glob("*.json") if pasta.exists() else []:
        try:
            if not json.loads(j.read_text("utf-8")).get("postado") and j.with_suffix(".mp4").exists():
                n += 1
        except (OSError, ValueError):
            pass
    return n


# 01/11 (dona: "carrosséis também podem produzir em trios"): 1 carrossel pronto por empresa, gerado aqui com
# antecedência (cada um no seu processo: a marca da Globo troca o módulo na importação). O horário de post só publica.
CARROSSEIS = [("carrossel advance", BIN / "carrossel_advance.py", Path(r"D:\ms-energy\videos\carrosseis_advance")),
              ("carrossel globo", BIN / "carrossel_globo.py", Path(r"D:\ms-energy\videos\carrosseis_globo")),
              ("carrossel ms", BIN / "carrossel_ms.py", Path(r"D:\ms-energy\videos\carrosseis"))]


def carrosseis_prontos(pasta, dias=45):  # 14/11: estoque de 30 dias (era "feito nos últimos 3 dias")
    import time
    n = 0
    for m in pasta.glob("*/meta.json") if pasta.exists() else []:
        try:
            if (not json.loads(m.read_text("utf-8")).get("postado") and m.stat().st_mtime > time.time() - dias * 86400
                    and len(list(m.parent.glob("slide_*.jpg"))) == 6):
                n += 1
        except (OSError, ValueError):
            pass
    return n


def main():
    for nome, script, pasta in CARROSSEIS:
        if carrosseis_prontos(pasta) >= ALVO:  # 14/11: era "tem 1 pronto"
            continue
        r = subprocess.run([PY, str(script), "--so-gerar"], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=3600, creationflags=0x08000000)
        print(f"[{datetime.now():%d/%m %H:%M}] {nome}: gerar exit={r.returncode} | agora "
              f"{carrosseis_prontos(pasta)} pronto(s)", flush=True)
    for nome, script, pasta in CONTAS:
        n = prontos(pasta)
        print(f"[{datetime.now():%d/%m %H:%M}] {nome}: {n} Reel(s) pronto(s)", flush=True)
        if n >= ALVO:
            continue
        r = subprocess.run([PY, str(script), "--so-gerar"], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=3 * 3600, creationflags=0x08000000)
        fim = [ln for ln in (r.stdout or "").splitlines() if "aprovado" in ln.lower() or "STOP" in ln or "sem v" in ln]
        print(f"  {nome}: gerar exit={r.returncode} | {fim[-1].strip() if fim else '(sem linha final)'} | agora "
              f"{prontos(pasta)} pronto(s)", flush=True)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
