# -*- coding: utf-8 -*-
"""Repositorio de falas e cenarios vencedores.

Analisa o video_cache.json, identifica os videos com maior views/likes,
e expoe funcoes para alimentar o pipeline LLM com exemplos vencedores.

Uso:
  from vencedoras import get_exemplos_falas, get_exemplos_cenarios
  falas_vencedoras = get_exemplos_falas(tema, top_n=10)
  cenarios_vencedores = get_exemplos_cenarios(tema, top_n=10)
"""
import os, json, math
from datetime import datetime

CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "logs", "video_cache.json")


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)


def score_virali(item):
    """Score de viralidade: combina views+likes+recencia."""
    metrics = item.get("metrics", {})
    if not metrics.get("views"):
        return 0
    views = metrics["views"]
    likes = metrics.get("likes", 0)
    # Engagement bonus
    eng = (likes + metrics.get("comments", 0)) / max(views, 1)
    # Decay temporal: itens < 7 dias tem bonus
    try:
        ts = datetime.fromisoformat(item.get("ts", ""))
        age_days = (datetime.now() - ts).days
        decay = math.exp(-age_days / 30)  # 30 dias half-life
    except Exception:
        decay = 1.0
    return (views * 0.7 + likes * 5) * (1 + eng * 5) * decay


def get_top_virais(min_views=100, top_n=20):
    """Retorna top N videos com mais views."""
    if not os.path.exists(CACHE_FILE):
        return []
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        cache = json.load(f)
    ranked = [c for c in cache if c.get("metrics", {}).get("views", 0) >= min_views]
    ranked.sort(key=lambda c: score_virali(c), reverse=True)
    return ranked[:top_n]


def get_exemplos_falas(tema=None, top_n=10, min_views=100):
    """Retorna top N falas (opcionalmente filtradas por tema)."""
    top = get_top_virais(min_views=min_views, top_n=top_n * 3)
    if tema:
        top = [c for c in top if c.get("tema") == tema]
    return [c.get("fala", "") for c in top if c.get("fala")][:top_n]


def get_exemplos_cenarios(tema=None, top_n=10, min_views=100):
    """Retorna top N cenarios (opcionalmente filtrados por tema)."""
    top = get_top_virais(min_views=min_views, top_n=top_n * 3)
    if tema:
        top = [c for c in top if c.get("tema") == tema]
    return [c.get("cenario", "") for c in top if c.get("cenario")][:top_n]


def get_keywords_vencedoras(top_n=20):
    """Retorna palavras-chave mais frequentes nas falas vencedoras."""
    top = get_top_virais(min_views=100, top_n=top_n)
    if not top:
        return []
    import re
    from collections import Counter
    stopwords = {"que", "para", "com", "uma", "voce", "esse", "essa", "isso", "aqui", "agora", "sua", "seu", "mais", "como", "pelo", "pela", "todo", "toda", "sem", "tem", "foi", "vai", "ser", "ter", "dar", "ver", "ficar", "deixar", "pra"}
    todas = " ".join(c.get("fala", "") for c in top).lower()
    palavras = [w for w in re.findall(r'\w+', todas) if len(w) > 3 and w not in stopwords]
    return Counter(palavras).most_common(top_n)


def imprimir_relatorio():
    """Imprime relatorio legivel."""
    print("=" * 70)
    print("RELATORIO DE VENCEDORAS")
    print("=" * 70)
    print("\nTOP 10 VIDEOS VIRAIS:")
    for i, c in enumerate(get_top_virais(top_n=10), 1):
        m = c.get("metrics", {})
        print(f"  {i}. [{c['canal']}] views={m.get('views', 0)} likes={m.get('likes', 0)}")
        print(f"     fala: {c.get('fala', '')[:80]}")
    print("\nKEYWORDS VENCEDORAS:")
    for kw, count in get_keywords_vencedoras(top_n=15):
        print(f"  {kw}: {count}")


if __name__ == "__main__":
    imprimir_relatorio()
