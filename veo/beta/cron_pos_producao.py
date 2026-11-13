# -*- coding: utf-8 -*-
"""Cron paralelo para pos-producao. Roda incremental OU retroativo.

Diferencas vs cron_gerar_video_llm.py:
- NAO gera videos (isso eh responsabilidade do cron principal).
- Processa os mp4 existentes em videos/ -> videos_pos/ com o pipeline.
- Respeita os flags em pos_producao/flags/ (pausa instantanea se desligar).
- 2 modos:
    --incremental (padrao): processa o que ainda nao tem saida
    --retro:                processa o backlog (gasta mais CPU)

Uso:
    python cron_pos_producao.py                     # incremental
    python cron_pos_producao.py --retro             # retroativo
    python cron_pos_producao.py --retro --limite 5  # retroativo limitado

    ou via .bat:
        Veo_POS_RODAR.bat
        Veo_POS_RODAR.bat retroativo 3
"""

import argparse
import os
import sys
import time

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(BASE, "pos_producao"))
import sem_janela  # noqa: F401,E402  (filhos sem janela na tela - dono, 15/10; item BX-02)

from pos_producao.flags import is_on, list_flags
from pos_producao.runner import run_pipeline


def _log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [cron_pos] {msg}", flush=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--incremental", action="store_true", default=True)
    p.add_argument("--retro", action="store_true",
                   help="modo retroativo (recursivo + processa backlog)")
    p.add_argument("--limite", type=int, default=0,
                   help="limite de videos nesta passada (0 = usa config.yaml)")
    args = p.parse_args()
    recursive = bool(args.retro)

    _log("estado dos flags:")
    for nome, val in list_flags().items():
        _log(f"  {nome}: {'ON' if val else 'OFF'}")

    if not is_on("pos_video"):
        _log("pos_video OFF - nada a fazer")
        return 0
    if recursive and not is_on("cron_pos_retro"):
        _log("cron_pos_retro OFF - retroativo desligado")
        return 0

    modo = "retroativo" if recursive else "incremental"
    _log(f"rodando pipeline {modo}")

    if args.limite > 0:
        # override pontual via env (lido pelo runner se expandir depois)
        # por enquanto, sobrescreve direto via cfg na memoria
        from pos_producao import config as cfg_mod
        cfg = cfg_mod.load_config()
        cfg["max_videos_per_run"] = args.limite
        cfg_mod._cache = cfg

    n = run_pipeline(dry_run=False, recursive=recursive)
    _log(f"concluido: {n} video(s) processado(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())