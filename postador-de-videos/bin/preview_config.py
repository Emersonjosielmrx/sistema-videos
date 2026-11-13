#!/usr/bin/env python3
"""preview_config.py — modo de PREVIEW por config externa (sem editar código).

Lê workspace/_PREVIEW.json. Se {"enabled": true}, força trilha e/ou efeito de
transição em TODO corte, pra a usuária ver na prática. Apagar o arquivo ou pôr
"enabled": false volta ao comportamento normal. Zero alteração de código.

Formato do _PREVIEW.json:
{
  "enabled": true,
  "force_trilha": "phonk_drift_atmospheric_infraction_LHae9zvUfug.mp3",  // nome do .mp3 em trilhas/ (ou null)
  "force_efeito": "fire",   // fire|water|ice|tear|smoke|lightning|glitch|tvoff|shockwave|disintegrate|... (ou null)
  "nota": "texto livre só pra você lembrar do que é esse teste"
}
"""
import json
import os
from pathlib import Path

_PROJ = Path(__file__).resolve().parent.parent
_PREVIEW_FILE = _PROJ / "workspace" / "_PREVIEW.json"

_cache = None


def _load():
    global _cache
    if _cache is not None:
        return _cache
    # env PREVIEW_OFF=1 desliga tudo, independente do arquivo
    if os.environ.get("PREVIEW_OFF") == "1":
        _cache = {}
        return _cache
    try:
        if _PREVIEW_FILE.exists():
            data = json.loads(_PREVIEW_FILE.read_text(encoding="utf-8"))
            _cache = data if data.get("enabled") else {}
        else:
            _cache = {}
    except Exception:
        _cache = {}
    return _cache


def enabled():
    return bool(_load())


def force_trilha():
    """Nome do .mp3 a forçar como trilha única, ou None."""
    return _load().get("force_trilha") or None


def force_efeito():
    """Nome do efeito de transição a forçar em todo corte, ou None."""
    return _load().get("force_efeito") or None
