# -*- coding: utf-8 -*-
"""_segredos.py — chaves lidas de fora do código.

Ordem: variável de ambiente > arquivo em D:\\postador-de-videos\\secrets\\.
Nunca coloque chave direto num .py (ele acaba copiado pra backups/snapshots).
"""
import os
from pathlib import Path

SECRETS = Path(__file__).resolve().parent.parent / "secrets"


def _ler(env, arquivo):
    v = os.environ.get(env)
    if v:
        return v.strip()
    p = SECRETS / arquivo
    try:
        return p.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        raise RuntimeError(f"chave ausente: defina {env} ou crie {p}") from None


def omniroute_auth():
    """Header Authorization do OmniRoute ('Bearer sk-...')."""
    return "Bearer " + _ler("OMNIROUTE_KEY", "omniroute_key.txt")
