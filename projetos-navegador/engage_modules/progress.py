"""
progress.py — Gerenciamento do progresso de engajamento.

OBJETIVO:
    Lê e salva o mega_engage_progress.json, que rastreia
    quais contas já engajaram quais vídeos.

ESTRUTURA DO JSON:
    {
        "https://youtube.com/watch?v=XYZ": {
            "engaged_by": ["conta1", "conta2"],
            "channel": "inovaremanhwaverse",
            "lang": "en",
            "actions": [
                {
                    "acc": "conta1",
                    "liked": true,
                    "commented": true,
                    "subscribed": false,
                    "comment": "Great video!",
                    "ts": "2026-07-07 12:00:00"
                }
            ]
        }
    }

DEPENDENCIAS:
    - config.py (PROGRESS_FILE path)
    - json (stdlib)
"""
import json
from .config import PROGRESS_FILE


def load_progress():
    """
    Lê o progresso do disco.

    Returns:
        dict onde cada chave é uma URL de vídeo e o valor
        contém "engaged_by" (lista de contas) e "actions" (detalhes)
    """
    if PROGRESS_FILE.exists():
        return json.loads(PROGRESS_FILE.read_text("utf-8"))
    return {}


def save_progress(progress):
    """
    Salva o progresso de volta no disco.
    Chamado ao final de cada lote.

    Args:
        progress: dict completo de progresso
    """
    PROGRESS_FILE.write_text(
        json.dumps(progress, ensure_ascii=False),
        encoding="utf-8"
    )


def count_total_engagements(progress):
    """
    Conta quantas ações já foram feitas no total.

    Args:
        progress: dict de progresso

    Returns:
        int com o total de engajamentos (soma de engaged_by de todos os vídeos)
    """
    return sum(len(v.get("engaged_by", [])) for v in progress.values())
