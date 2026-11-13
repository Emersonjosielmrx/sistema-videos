# -*- coding: utf-8 -*-
"""auto_adjust.py — Auto-ajuste de parametros (feedback loop).

Le performance_summary.json e ajusta pesos de producao por genero.
Generos com mais videos recebem peso menor (diversidade).
Generos sem producao em 3+ dias recebem boost.
"""
import json
import random
from pathlib import Path
from datetime import datetime

PROJECT_DIR = Path(__file__).resolve().parent.parent
SUMMARY_FILE = PROJECT_DIR / "workspace" / "performance_summary.json"
WEIGHTS_FILE = PROJECT_DIR / "workspace" / "genre_weights.json"

ALL_GENRES = [
    "superacao", "terror", "misterio", "romance",
    "comedia", "drama", "fantasia", "motivacional",
    "curiosidades", "religioso",
]

# Peso base uniforme
BASE_WEIGHT = 1.0
# Boost pra generos inativos (por dia de inatividade)
INACTIVITY_BOOST_PER_DAY = 0.3
# Penalidade por excesso de producao (por video acima da media)
OVERPRODUCTION_PENALTY = 0.15
# Dias sem producao que dispara o boost
INACTIVITY_THRESHOLD = 3


def _load_summary():
    """Carrega o performance_summary.json."""
    if SUMMARY_FILE.exists():
        try:
            return json.loads(SUMMARY_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return None


def get_genre_weights():
    """Calcula pesos por genero baseado em historico de producao.

    Retorna dict {genero: float_weight} onde pesos maiores = mais prioridade.
    """
    summary = _load_summary()

    weights = {g: BASE_WEIGHT for g in ALL_GENRES}

    if not summary or not summary.get("by_genre"):
        return weights

    by_genre = summary["by_genre"]
    now = datetime.now()

    # Calcular media de videos por genero
    counts = [info.get("count", 0) for info in by_genre.values()]
    avg_count = sum(counts) / len(counts) if counts else 0

    for g in ALL_GENRES:
        info = by_genre.get(g)

        if not info:
            # Genero nunca produzido: boost maximo
            weights[g] = BASE_WEIGHT + (INACTIVITY_BOOST_PER_DAY * 10)
            continue

        # Penalizar overproduction
        excess = info.get("count", 0) - avg_count
        if excess > 0:
            weights[g] -= excess * OVERPRODUCTION_PENALTY

        # Boost por inatividade
        if info.get("last_generated"):
            try:
                last = datetime.fromisoformat(info["last_generated"])
                days_since = (now - last).days
                if days_since >= INACTIVITY_THRESHOLD:
                    weights[g] += days_since * INACTIVITY_BOOST_PER_DAY
            except Exception:
                weights[g] += INACTIVITY_BOOST_PER_DAY * 5

        # Garantir peso minimo positivo
        weights[g] = max(0.1, weights[g])

    return weights


def weighted_genre_choice(weights=None):
    """Escolhe proximo genero probabilisticamente baseado nos pesos.

    Generos com peso maior tem mais chance de serem escolhidos.
    """
    if weights is None:
        weights = get_genre_weights()

    genres = list(weights.keys())
    w_values = [weights[g] for g in genres]

    # random.choices usa pesos como probabilidade relativa
    chosen = random.choices(genres, weights=w_values, k=1)
    return chosen[0]


def save_weights():
    """Calcula e salva pesos atuais em genre_weights.json."""
    weights = get_genre_weights()
    output = {
        "generated_at": datetime.now().isoformat(),
        "weights": weights,
        "suggestion": weighted_genre_choice(weights),
    }
    WEIGHTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    WEIGHTS_FILE.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    return output


if __name__ == "__main__":
    result = save_weights()
    print("Pesos por genero:")
    for g, w in sorted(result["weights"].items(), key=lambda x: -x[1]):
        print(f"  {g}: {w:.2f}")
    print(f"\nSugestao: {result['suggestion']}")
