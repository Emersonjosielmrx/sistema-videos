# -*- coding: utf-8 -*-
"""performance_dashboard.py — Dashboard de performance de producao.

Coleta metricas dos videos gerados, sumariza por genero,
e sugere qual genero produzir em seguida (diversidade).
"""
import json
from pathlib import Path
from datetime import datetime, timedelta

PROJECT_DIR = Path(__file__).resolve().parent.parent
from hp_common import VIDEOS_DIR  # noqa: E402  (hipercool-materiais)
SUMMARY_FILE = PROJECT_DIR / "workspace" / "performance_summary.json"


def collect_metrics():
    """Le todos os metadata JSONs de workspace/videos/ e extrai metricas."""
    metrics = []

    if not VIDEOS_DIR.exists():
        return metrics

    for meta_file in VIDEOS_DIR.rglob("*.json"):
        # Ignorar queue/postagem files
        if "queue" in meta_file.name or "posted" in meta_file.name:
            continue
        try:
            data = json.loads(meta_file.read_text(encoding="utf-8"))
            # So pegar JSONs que sao metadata de video (tem titulo + genero)
            if not data.get("titulo") or not data.get("genero"):
                continue
            metrics.append({
                "titulo": data.get("titulo", ""),
                "genero": data.get("genero", "desconhecido"),
                "duracao_s": data.get("duracao_s", 0),
                "n_cenas": data.get("n_cenas", 0),
                "generated_at": data.get("generated_at",
                    datetime.fromtimestamp(meta_file.stat().st_mtime).isoformat()),
                "story_id": data.get("story_id", ""),
                "quality": data.get("quality", "med"),
                "features": data.get("features", []),
                "warnings": data.get("warnings", []),
                "file": str(meta_file),
            })
        except Exception:
            continue

    return metrics


def summary_by_genre(metrics=None):
    """Retorna dict {genero: {count, avg_duration, last_generated, total_duration}}."""
    if metrics is None:
        metrics = collect_metrics()

    summary = {}
    for m in metrics:
        g = m["genero"]
        if g not in summary:
            summary[g] = {
                "count": 0,
                "total_duration": 0,
                "durations": [],
                "last_generated": None,
            }
        summary[g]["count"] += 1
        summary[g]["total_duration"] += m.get("duracao_s", 0)
        summary[g]["durations"].append(m.get("duracao_s", 0))

        gen_at = m.get("generated_at")
        if gen_at:
            if summary[g]["last_generated"] is None or gen_at > summary[g]["last_generated"]:
                summary[g]["last_generated"] = gen_at

    # Calcular medias e limpar
    for g in summary:
        durs = summary[g].pop("durations")
        summary[g]["avg_duration"] = round(sum(durs) / len(durs), 1) if durs else 0

    return summary


def suggest_next_genre(history=None):
    """Sugere qual genero produzir em seguida baseado em diversidade.

    Prioriza generos menos produzidos recentemente (>3 dias sem producao).
    """
    if history is None:
        history = summary_by_genre()

    all_genres = [
        "superacao", "terror", "misterio", "romance",
        "comedia", "drama", "fantasia", "motivacional",
        "curiosidades", "religioso",
    ]

    now = datetime.now()
    scores = {}

    for g in all_genres:
        info = history.get(g)
        if not info:
            # Genero nunca produzido = prioridade maxima
            scores[g] = 100.0
            continue

        # Menos videos = mais prioridade
        count_score = max(0, 10 - info["count"])

        # Mais dias desde ultimo = mais prioridade
        days_since = 0
        if info.get("last_generated"):
            try:
                last = datetime.fromisoformat(info["last_generated"])
                days_since = (now - last).days
            except Exception:
                days_since = 7

        time_score = min(days_since * 3, 30)  # cap em 30

        scores[g] = count_score + time_score

    # Retornar genero com maior score
    if not scores:
        return "superacao"

    return max(scores, key=scores.get)


def save_summary():
    """Coleta metricas, gera summary e salva em workspace/performance_summary.json."""
    metrics = collect_metrics()
    summary = summary_by_genre(metrics)
    suggestion = suggest_next_genre(summary)

    output = {
        "generated_at": datetime.now().isoformat(),
        "total_videos": len(metrics),
        "by_genre": summary,
        "suggested_next": suggestion,
    }

    SUMMARY_FILE.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_FILE.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    return output


if __name__ == "__main__":
    result = save_summary()
    print(f"Total videos: {result['total_videos']}")
    print(f"Generos: {list(result['by_genre'].keys())}")
    print(f"Sugestao: {result['suggested_next']}")
