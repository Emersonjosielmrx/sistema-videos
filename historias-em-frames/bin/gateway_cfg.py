"""gateway_cfg.py — endereco e chave do gateway OmniRoute num lugar so.

Antes a chave estava escrita em 8 arquivos (alguns ja no GitHub) e o claude_client usava
uma chave diferente, desativada (403) — trocar/rotacionar exigia editar todos.
Agora: secrets/omniroute.json (fora do git) {"base_url": ..., "api_key": ...},
com override por env OMNIROUTE_BASE_URL / OMNIROUTE_API_KEY.
"""
import json
import os
from pathlib import Path

_ARQ = Path(__file__).resolve().parent.parent / "secrets" / "omniroute.json"
_cfg = None


def _load():
    global _cfg
    if _cfg is None:
        try:
            j = json.loads(_ARQ.read_text(encoding="utf-8"))
        except Exception:
            j = {}
        _cfg = {
            "base": (os.environ.get("OMNIROUTE_BASE_URL") or j.get("base_url") or "").rstrip("/"),
            "key": os.environ.get("OMNIROUTE_API_KEY") or j.get("api_key") or "",
        }
    return _cfg


def base():
    return _load()["base"]


def key():
    return _load()["key"]


def url(path):
    return base() + path


def bearer():
    return "Bearer " + key()


def ok():
    """True se ha base e chave configuradas (o doctor checa isto)."""
    c = _load()
    return bool(c["base"] and c["key"])
