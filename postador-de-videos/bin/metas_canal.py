"""Metas pelo NORMAL de cada canal (dona 10/11: "as metas têm que ser com base na média daquele canal e não fixas
como 10 em 10; o que quero saber é quando algo está melhor do que de fato deveria").

Inscritos: ganho de HOJE contra a média de ganho por dia dos últimos 7 dias do canal (painel/historico.jsonl, que o
painel_canais grava várias vezes por dia, mais a série própria de quem chama). Avisa em 2x, 4x, 8x... o normal.
Views: views do vídeo contra a média dos vídeos do canal com mais de 2 dias. Avisa em 3x, 10x, 30x, 100x.
Desligar e voltar às metas fixas: METAS_RELATIVAS=0.
"""
import json
import os
import statistics
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

LIGADO = os.environ.get("METAS_RELATIVAS", "1") != "0"
HIST = Path(r"D:\postador-de-videos\painel\historico.jsonl")
NIVEIS_INSCRITOS = (2, 4, 8, 16, 32)
NIVEIS_VIEWS = (3, 10, 30, 100)
MIN_GANHO_INSCRITOS = 3   # +1 ou +2 num canal que ganha 0 por dia não é notícia
MIN_VIEWS = 500           # canal pequeno: 3x de 20 views não é notícia
_CACHE = {}


def _series_hist():
    """{slug: {"AAAA-MM-DD": inscritos no fim do dia}} a partir do historico.jsonl do painel."""
    if "hist" not in _CACHE:
        s = {}
        try:
            for linha in HIST.read_text(encoding="utf-8").splitlines():
                try:
                    r = json.loads(linha)
                    s.setdefault(r["slug"], {})[r["ts"][:10]] = int(r["inscritos"])
                except (ValueError, KeyError, TypeError):
                    continue
        except OSError:
            pass
        _CACHE["hist"] = s
    return _CACHE["hist"]


def anotar(serie, valor, hoje=None):
    """Grava o valor de agora como o do dia (o último do dia fica). serie = dict guardado no estado de quem chama."""
    serie[(hoje or date.today()).isoformat()] = int(valor)
    for d in sorted(serie)[:-40]:  # 40 dias bastam
        serie.pop(d)


def inscritos_hoje(slug, agora, serie_propria=None, hoje=None):
    """(base, ganho, normal): base = inscritos no fim de ontem; normal = ganho médio por dia (7 dias) ou None."""
    hoje = hoje or date.today()
    s = dict(_series_hist().get(slug, {}))
    s.update(serie_propria or {})
    dias = sorted(d for d in s if d < hoje.isoformat())
    if not dias:
        return None, 0, None
    base = s[dias[-1]]
    inicio = (hoje - timedelta(days=8)).isoformat()
    janela = [d for d in dias if d >= inicio]
    normal = None
    if len(janela) >= 3:  # pelo menos 2 dias de ganho medidos
        d0, d1 = date.fromisoformat(janela[0]), date.fromisoformat(janela[-1])
        normal = max(0.0, (s[janela[-1]] - s[janela[0]]) / max(1, (d1 - d0).days))
    return base, int(agora) - base, normal


def nivel(valor, normal, niveis, minimo):
    """Maior nível k (de `niveis`) com valor >= k * normal e valor >= minimo; 0 = dentro do normal."""
    if valor < minimo:
        return 0
    ref = max(float(normal or 0), 1.0)
    return max([k for k in niveis if valor >= k * ref], default=0)


def mediana_views(videos, agora=None):
    """Views típicas do canal: MÉDIA dos vídeos públicos com mais de 2 dias (vídeo novo ainda está subindo).
    10/11: a mediana dava 0-2 views na maioria dos canais (quase todo vídeo parado) e qualquer vídeo virava "2.000×"."""
    agora = agora or datetime.now(timezone.utc)
    maduros = []
    for v in videos:
        try:
            pub = datetime.fromisoformat(v["pub"].replace("Z", "+00:00"))
        except (KeyError, ValueError, AttributeError):
            continue
        if agora - pub >= timedelta(days=2) and v.get("privacy", "public") == "public":
            maduros.append(v["views"])
    return statistics.mean(maduros) if len(maduros) >= 5 else None


def n(x):
    return f"{int(round(x)):,}".replace(",", ".")


def vezes(valor, normal):
    r = valor / max(float(normal or 0), 1.0)
    return f"{r:.1f}".replace(".", ",").replace(",0", "") + "×"
