# -*- coding: utf-8 -*-
"""ab_tracker.py - A/B testing de titulos com tracking de performance.

Salva 3 variantes de titulo por video, permite trocar apos medir CTR.
Integra com viralizador.py pra gerar as variantes.
"""
import json
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hp_common import PROJECT_DIR, log

AB_DIR = PROJECT_DIR / "workspace" / "ab_tests"
AB_DIR.mkdir(parents=True, exist_ok=True)


def save_variants(story_id, titulos, genero="superacao"):
    """Salva variantes de titulo pra um video.

    Args:
        story_id: id do video
        titulos: lista de titulos alternativos (3+)
        genero: genero (pra analytics futuro)

    Returns:
        Path do arquivo de variantes
    """
    data = {
        "story_id": story_id,
        "genero": genero,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "active_variant": 0,
        "variants": [
            {"idx": i, "titulo": t, "views": 0, "ctr": 0.0, "active_since": None}
            for i, t in enumerate(titulos[:4])
        ],
    }

    path = AB_DIR / f"{story_id}.json"
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"  ab_tracker: salvas {len(data['variants'])} variantes pra {story_id}")
    return path


def get_active_title(story_id):
    """Retorna o titulo ativo atual."""
    path = AB_DIR / f"{story_id}.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    idx = data.get("active_variant", 0)
    variants = data.get("variants", [])
    if idx < len(variants):
        return variants[idx]["titulo"]
    return variants[0]["titulo"] if variants else None


def switch_variant(story_id, new_idx=None):
    """Troca pra proxima variante (ou pra indice especifico).

    Returns:
        novo titulo ativo ou None
    """
    path = AB_DIR / f"{story_id}.json"
    if not path.exists():
        return None

    data = json.loads(path.read_text(encoding="utf-8"))
    variants = data.get("variants", [])
    if not variants:
        return None

    if new_idx is not None:
        data["active_variant"] = min(new_idx, len(variants) - 1)
    else:
        data["active_variant"] = (data.get("active_variant", 0) + 1) % len(variants)

    idx = data["active_variant"]
    variants[idx]["active_since"] = time.strftime("%Y-%m-%d %H:%M:%S")

    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"  ab_tracker: {story_id} trocou pra variante {idx}: {variants[idx]['titulo'][:50]}")
    return variants[idx]["titulo"]


def update_metrics(story_id, variant_idx, views=0, ctr=0.0):
    """Atualiza metricas de uma variante (chamado apos consultar YT Analytics)."""
    path = AB_DIR / f"{story_id}.json"
    if not path.exists():
        return False

    data = json.loads(path.read_text(encoding="utf-8"))
    variants = data.get("variants", [])
    if variant_idx < len(variants):
        variants[variant_idx]["views"] = views
        variants[variant_idx]["ctr"] = ctr
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return True
    return False


def should_switch(story_id, min_views=100, min_ctr=4.0):
    """Verifica se deve trocar de variante baseado em CTR.

    Returns:
        True se CTR esta abaixo do threshold e ha variante nao testada
    """
    path = AB_DIR / f"{story_id}.json"
    if not path.exists():
        return False

    data = json.loads(path.read_text(encoding="utf-8"))
    variants = data.get("variants", [])
    active = data.get("active_variant", 0)

    if active >= len(variants):
        return False

    current = variants[active]
    if current["views"] < min_views:
        return False

    if current["ctr"] < min_ctr:
        untested = [v for v in variants if v["idx"] != active and v["views"] == 0]
        return len(untested) > 0

    return False


def list_tests():
    """Lista todos os A/B tests ativos."""
    tests = []
    for f in AB_DIR.glob("*.json"):
        data = json.loads(f.read_text(encoding="utf-8"))
        active_idx = data.get("active_variant", 0)
        variants = data.get("variants", [])
        tests.append({
            "story_id": data["story_id"],
            "genero": data.get("genero"),
            "active_title": variants[active_idx]["titulo"] if active_idx < len(variants) else "?",
            "n_variants": len(variants),
        })
    return tests
