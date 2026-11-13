"""Sistema de flags: cada subsistema tem um .on/.off em pos_producao/flags/.

Uso:
    from pos_producao.flags import is_on, set_flag, list_flags, DEFAULT_STATE

Flags sao consultadas pelo cron antes de cada subsistema rodar.
Toggles (.bat no desktop) escrevem .on/.off aqui.

Layout:
    pos_producao/flags/
        cron_video.on       (gera novos videos Veo)
        pos_video.on        (pos-producao incremental)
        cron_pos_retro.off  (retroativo: processa backlog)
        voz_whatsapp.off    (voz injetada no audio)
"""

import os
import time
from pathlib import Path

_BASE = Path(__file__).resolve().parent
FLAGS_DIR = _BASE / "flags"

# estado padrao quando o flag nao existe: ON pros obrigatorios, OFF pros opcionais
DEFAULT_STATE = {
    "cron_video": True,
    "pos_video": True,
    "cron_pos_retro": False,  # desligado por padrao (gera carga alta)
    "voz_whatsapp": False,    # desligado por padrao (sobrecarga CPU)
}


def _flag_path(nome: str) -> Path:
    return FLAGS_DIR / f"{nome}.flag"


def is_on(nome: str) -> bool:
    """Retorna True se o subsistema esta ligado.

    Se o arquivo de flag nao existir, usa DEFAULT_STATE.
    """
    p = _flag_path(nome)
    if not p.exists():
        return DEFAULT_STATE.get(nome, False)
    try:
        with open(p, "r", encoding="utf-8") as f:
            v = f.read().strip().lower()
        return v in ("on", "1", "true", "sim", "yes")
    except Exception:
        return DEFAULT_STATE.get(nome, False)


def is_off(nome: str) -> bool:
    return not is_on(nome)


def set_flag(nome: str, on: bool) -> bool:
    """Liga/desliga subsistema. Retorna estado novo."""
    FLAGS_DIR.mkdir(parents=True, exist_ok=True)
    p = _flag_path(nome)
    with open(p, "w", encoding="utf-8") as f:
        f.write("on" if on else "off")
    return on


def toggle(nome: str) -> bool:
    """Inverte estado. Retorna estado novo."""
    return set_flag(nome, not is_on(nome))


def list_flags() -> dict:
    """Retorna estado atual de todos os flags conhecidos."""
    return {n: is_on(n) for n in DEFAULT_STATE}


def _log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [flags] {msg}", flush=True)


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 2:
        cmd = sys.argv[1]
        if cmd == "list":
            for n, v in list_flags().items():
                _log(f"{n}: {'ON' if v else 'OFF'}")
        elif cmd in ("on", "off", "toggle") and len(sys.argv) >= 3:
            nome = sys.argv[2]
            if cmd == "on":
                novo = set_flag(nome, True)
            elif cmd == "off":
                novo = set_flag(nome, False)
            else:
                novo = toggle(nome)
            _log(f"{nome} -> {'ON' if novo else 'OFF'}")
        else:
            print("uso: flags.py [list | on <nome> | off <nome> | toggle <nome>]")
    else:
        for n, v in list_flags().items():
            print(f"{n}: {'ON' if v else 'OFF'}")