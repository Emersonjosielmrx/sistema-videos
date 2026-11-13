#!/usr/bin/env python3
"""postar_hoje.py — POSTADOR DE VÍDEOS standalone (não depende do Claude/VS Code).

Roda TODAS as filas de postagem do dia de hoje. Chamado pelo Task Scheduler do
Windows (via postar-hoje.cmd), diariamente. Idempotente: só posta o que é do dia
e ainda não subiu; grava status no próprio JSON de cada fila.

Acha automaticamente qualquer fila_*.json em
  D:\\hipercool-producao\\_LEIA_POSTAR_VIDEOS\\
e roda o postar-fila.py pra cada uma. Loga em D:\\postador-de-videos\\logs\\.

Pra postar à mão: dê 2 cliques em postar-hoje.cmd (ou rode este arquivo).
"""
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PROD = Path(r"D:/postador-de-videos")
FILAS_DIR = PROD / "_LEIA_POSTAR_VIDEOS"
POSTAR_FILA = PROD / "bin" / "postar-fila.py"
PY = Path(r"D:/hipercool-videos/venv/Scripts/python.exe")
LOGDIR = Path(r"D:/postador-de-videos/logs")


def main():
    LOGDIR.mkdir(parents=True, exist_ok=True)
    hoje = datetime.now().strftime("%Y-%m-%d")
    logf = LOGDIR / f"postagem_{hoje}.log"
    filas = sorted(FILAS_DIR.glob("fila_*.json"))

    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")

    with open(logf, "a", encoding="utf-8") as log:
        def w(msg):
            line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
            try:
                print(line)
            except Exception:
                pass
            log.write(line + "\n")
            log.flush()

        w(f"===== POSTADOR rodando ({hoje}) — {len(filas)} fila(s) encontrada(s) =====")
        if not PY.exists():
            w(f"ERRO: python não encontrado em {PY}")
            return
        for fila in filas:
            w(f"----- fila: {fila.name} -----")
            try:
                r = subprocess.run(
                    [str(PY), str(POSTAR_FILA), "--plano", str(fila)],
                    capture_output=True, text=True, env=env, timeout=7200)
                log.write(r.stdout + "\n")
                if r.stderr:
                    log.write("STDERR:\n" + r.stderr + "\n")
                log.flush()
                try:
                    print(r.stdout)
                except Exception:
                    pass
                if r.returncode != 0:
                    w(f"AVISO: {fila.name} saiu com código {r.returncode}")
            except Exception as e:  # noqa
                w(f"ERRO ao rodar {fila.name}: {e}")
        w("===== POSTADOR fim =====\n")


if __name__ == "__main__":
    main()
