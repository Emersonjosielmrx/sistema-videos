# -*- coding: utf-8 -*-
"""branch_story.py - Historias com finais alternativos (escolha o final).

Gera 80%% tronco comum + 3 finais diferentes = 3 videos.
Ideal pra romance (feliz/tragico), terror (sobrevive/morre), misterio (culpado A/B/C).
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hp_common import PROJECT_DIR, log
import story_writer

BRANCH_DIR = PROJECT_DIR / "workspace" / "branches"
BRANCH_DIR.mkdir(parents=True, exist_ok=True)


def generate_branched_story(genero="romance", tema=None, n_cenas=15, n_endings=3):
    """Gera historia com tronco comum + finais alternativos.

    Args:
        genero: genero da historia
        tema: tema central
        n_cenas: total de cenas no tronco
        n_endings: quantos finais alternativos (2-3)

    Returns:
        dict com trunk (cenas comuns) e endings (lista de listas de cenas)
    """
    trunk_cenas = max(3, int(n_cenas * 0.8))
    ending_cenas = n_cenas - trunk_cenas

    log(f"  branch: gerando tronco ({trunk_cenas} cenas) + {n_endings} finais ({ending_cenas} cenas cada)")

    trunk_story = story_writer.generate_story(genero, tema, trunk_cenas)
    if not trunk_story:
        return None

    trunk = trunk_story["cenas"]
    titulo_base = trunk_story.get("titulo", "Historia")

    last_scene_text = trunk[-1].get("texto", "") if trunk else ""

    endings = []
    ending_labels = ["FINAL A - O Esperado", "FINAL B - A Surpresa", "FINAL C - O Sombrio"]

    for i in range(min(n_endings, 3)):
        ending_tema = f"Continue esta historia com um final {['esperado e satisfatorio', 'surpreendente e inesperado', 'sombrio e ambiguo'][i]}. Ultima cena: {last_scene_text[:100]}"
        ending_story = story_writer.generate_story(genero, ending_tema, ending_cenas)
        if ending_story:
            endings.append({
                "label": ending_labels[i],
                "cenas": ending_story["cenas"],
                "titulo": f"{titulo_base} ({ending_labels[i]})",
            })
        else:
            log(f"  branch: falhou gerando final {i+1}")

    if not endings:
        log("  branch: nenhum final gerado")
        return None

    result = {
        "titulo_base": titulo_base,
        "genero": genero,
        "trunk": trunk,
        "endings": endings,
        "tags": trunk_story.get("tags", []),
    }

    cache_path = BRANCH_DIR / f"{genero}_{titulo_base[:20].replace(' ','_')}.json"
    cache_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"  branch: OK - {len(endings)} finais gerados")
    return result


def build_full_stories(branched):
    """Expande um resultado branched em N historias completas (trunk + ending).

    Returns:
        list de dicts no formato padrao do story_writer (prontos pro pipeline)
    """
    if not branched:
        return []

    stories = []
    for ending in branched["endings"]:
        story = {
            "titulo": ending["titulo"],
            "tags": branched.get("tags", []),
            "genero": branched["genero"],
            "cenas": branched["trunk"] + ending["cenas"],
        }
        stories.append(story)

    return stories
