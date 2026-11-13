# -*- coding: utf-8 -*-
"""series_manager.py - Gerenciamento de series com arco narrativo.

Mantém story bible persistente entre partes, permite gerar continuacoes
automaticas com resumo do que ja aconteceu injetado no prompt.
"""
import json
import hashlib
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hp_common import PROJECT_DIR, log

SERIES_DIR = PROJECT_DIR / "workspace" / "series"
SERIES_DIR.mkdir(parents=True, exist_ok=True)


def _series_path(serie_id):
    d = SERIES_DIR / serie_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def create_series(serie_id, genero, tema, n_parts=3, personagens=None):
    """Cria uma nova serie com arco planejado.

    Args:
        serie_id: slug unico (ex: 'garoto-dj')
        genero: genero da historia
        tema: tema central
        n_parts: numero de partes planejadas
        personagens: lista de nomes dos personagens principais

    Returns:
        dict com a bible da serie
    """
    sp = _series_path(serie_id)
    bible_path = sp / "bible.json"

    if bible_path.exists():
        log(f"  series: '{serie_id}' ja existe, retornando bible existente")
        return json.loads(bible_path.read_text(encoding="utf-8"))

    bible = {
        "serie_id": serie_id,
        "genero": genero,
        "tema": tema,
        "n_parts_planned": n_parts,
        "personagens": personagens or [],
        "arco": {
            "setup": "Parte 1: Apresentacao do mundo e conflito inicial",
            "confronto": f"Partes 2-{max(2, n_parts-1)}: Escalada, obstaculos, revelacoes",
            "resolucao": f"Parte {n_parts}: Climax e desfecho",
        },
        "parts": [],
        "created_at": datetime.now().isoformat(),
    }

    bible_path.write_text(json.dumps(bible, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"  series: criada '{serie_id}' ({n_parts} partes, genero={genero})")
    return bible


def get_bible(serie_id):
    """Retorna a bible de uma serie existente."""
    sp = _series_path(serie_id)
    bible_path = sp / "bible.json"
    if not bible_path.exists():
        return None
    return json.loads(bible_path.read_text(encoding="utf-8"))


def get_next_part_number(serie_id):
    """Retorna o numero da proxima parte a ser gerada."""
    bible = get_bible(serie_id)
    if not bible:
        return 1
    return len(bible.get("parts", [])) + 1


def build_continuation_prompt(serie_id):
    """Monta bloco de contexto pra injetar no prompt do Gemini ao gerar a proxima parte.

    Returns:
        str com resumo das partes anteriores e instrucoes de continuidade
    """
    bible = get_bible(serie_id)
    if not bible or not bible.get("parts"):
        return ""

    parts = bible["parts"]
    next_num = len(parts) + 1
    total = bible.get("n_parts_planned", 3)

    resumo_parts = []
    for p in parts[-3:]:
        resumo_parts.append(f"Parte {p['part_num']}: {p.get('resumo', p.get('titulo', '...'))}")

    position = "INICIO" if next_num == 1 else "MEIO" if next_num < total else "FINAL"

    block = f"""
CONTINUACAO DE SERIE: '{bible['serie_id']}' (Parte {next_num} de {total})
POSICAO NO ARCO: {position}
TEMA CENTRAL: {bible['tema']}
PERSONAGENS RECORRENTES: {', '.join(bible.get('personagens', ['Protagonista']))}

RESUMO DAS PARTES ANTERIORES:
{chr(10).join(resumo_parts)}

INSTRUCOES DE CONTINUIDADE:
- Mantenha os MESMOS personagens e suas caracteristicas
- A historia DEVE continuar de onde parou (nao recomecar)
- Referencie eventos anteriores naturalmente
- {'Resolva o conflito principal e de um desfecho satisfatorio' if position == 'FINAL' else 'Escale a tensao e termine com cliffhanger'}
- O titulo deve ter '(Parte {next_num})' no final
"""
    return block.strip()


def register_part(serie_id, part_num, titulo, resumo, video_path=None, cenas_resumo=None):
    """Registra uma parte concluida na bible da serie.

    Args:
        serie_id: id da serie
        part_num: numero da parte
        titulo: titulo do video gerado
        resumo: resumo de 1-2 frases do que aconteceu
        video_path: caminho do video (opcional)
        cenas_resumo: lista de textos das cenas (opcional, pra contexto futuro)
    """
    bible = get_bible(serie_id)
    if not bible:
        log(f"  series: '{serie_id}' nao encontrada")
        return False

    part_entry = {
        "part_num": part_num,
        "titulo": titulo,
        "resumo": resumo,
        "video_path": str(video_path) if video_path else None,
        "generated_at": datetime.now().isoformat(),
    }
    if cenas_resumo:
        part_entry["cenas_resumo"] = cenas_resumo[:5]

    existing = [p for p in bible["parts"] if p["part_num"] != part_num]
    existing.append(part_entry)
    existing.sort(key=lambda x: x["part_num"])
    bible["parts"] = existing

    sp = _series_path(serie_id)
    (sp / "bible.json").write_text(json.dumps(bible, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"  series: registrada parte {part_num} de '{serie_id}'")
    return True


def list_series():
    """Lista todas as series existentes."""
    series = []
    if not SERIES_DIR.exists():
        return series
    for d in SERIES_DIR.iterdir():
        if d.is_dir() and (d / "bible.json").exists():
            bible = json.loads((d / "bible.json").read_text(encoding="utf-8"))
            series.append({
                "id": bible["serie_id"],
                "genero": bible["genero"],
                "tema": bible["tema"],
                "parts_done": len(bible.get("parts", [])),
                "parts_planned": bible.get("n_parts_planned", 3),
            })
    return series


def generate_outro_cta(serie_id, part_num):
    """Gera texto CTA pro outro baseado na posicao na serie."""
    bible = get_bible(serie_id)
    total = bible.get("n_parts_planned", 3) if bible else 3

    if part_num >= total:
        return "OBRIGADO POR ASSISTIR A SERIE COMPLETA"
    return f"PARTE {part_num + 1} EM BREVE - INSCREVA-SE"
