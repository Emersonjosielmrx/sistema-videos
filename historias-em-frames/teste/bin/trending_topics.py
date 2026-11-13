# -*- coding: utf-8 -*-
"""trending_topics.py - Sugestao de temas baseados em trends.

Scrape Google Trends e fallback pra lista evergreen curada.
Cache de 6h (trends mudam rapido).
"""
import json, time, urllib.request, sys, re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hp_common import PROJECT_DIR, log

TRENDS_CACHE = PROJECT_DIR / "workspace" / "cache" / "trends.json"
TRENDS_CACHE.parent.mkdir(parents=True, exist_ok=True)
CACHE_TTL_S = 6 * 3600

EVERGREEN_THEMES = {
    "superacao": [
        "garoto que dormia na rua e virou medico",
        "mulher que perdeu tudo e construiu um imperio",
        "menino surdo que virou musico famoso",
        "ex-presidiario que virou pastor",
        "imigrante que ficou milionario",
        "garota bullied virou modelo",
        "morador de rua inventou app",
        "cego que escalou Everest",
        "menina da favela entrou na NASA",
        "pai solo criou 5 filhos formados"
    ],
    "terror": [
        "enfermeira que ouve vozes no turno da noite",
        "a casa que ninguem aluga",
        "o elevador para no andar que nao existe",
        "mensagens do celular de alguem morto",
        "a boneca que muda de lugar",
        "o espelho que mostra outra pessoa",
        "camera de seguranca gravou impossivel",
        "quarto de hotel que nao esta no mapa",
        "a voz que responde quando esta sozinho",
        "o passageiro que ninguem viu descer"
    ],
    "misterio": [
        "corpo encontrado na sala trancada por dentro",
        "mulher desapareceu no meio da festa",
        "pacote chega todo mes sem remetente",
        "vizinho que nunca envelhece",
        "foto antiga com alguem que nao deveria estar la"
    ],
    "romance": [
        "reencontro com primeiro amor apos 20 anos",
        "a carta que nunca foi enviada",
        "vizinhos que se odeiam ate tempestade",
        "casados por contrato que se apaixonam",
        "dois estranhos presos no elevador 3 horas"
    ],
    "comedia": [
        "confundiu enterro com casamento",
        "entrevista de emprego deu tudo errado",
        "mensagem enviada pro grupo errado",
        "encontro as cegas com a propria ex",
        "estagiario mandou email pro CEO"
    ],
    "motivacional": [
        "5 habitos que separam os 1% dos 99%",
        "regra dos 5 segundos que muda decisoes",
        "segredo japones pra viver 100 anos",
        "tecnica que elimina procrastinacao",
        "por que voce deve falhar mais rapido"
    ],
    "curiosidades": [
        "o que acontece no corpo quando dorme",
        "cor que nao existe mas voce ve",
        "animal biologicamente imortal",
        "lugar na Terra onde nunca choveu",
        "material mais caro do universo"
    ],
    "drama": [
        "escolha entre salvar filho ou marido",
        "segredo guardado por 30 anos",
        "ultima mensagem antes do acidente",
        "irmao voltou depois de dado como morto",
        "heranca que destruiu familia"
    ],
    "fantasia": [
        "garoto acordou com magia nas maos",
        "espada que so obedece quem nao quer poder",
        "reino dentro de um livro",
        "maldecao que transforma em pedra",
        "magia que custa uma memoria"
    ],
    "religioso": [
        "jovem desafiou exercito com uma pedra",
        "mulher tocou o manto e foi curada",
        "rei pediu sabedoria em vez de riqueza",
        "filho prodigo voltou pra casa",
        "tempestade obedeceu a uma voz"
    ]
}


def _fetch_google_trends():
    """Tenta buscar trends do Google (fallback silencioso se falhar)."""
    try:
        url = "https://trends.google.com.br/trending/rss?geo=BR"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        resp = urllib.request.urlopen(req, timeout=15)
        content = resp.read().decode("utf-8")
        titles = re.findall(r"<title><!.CDATA.(.+?).{2}]></title>", content)
        return titles[:20] if titles else []
    except Exception:
        return []


def suggest_themes(genero="superacao", n=3, use_trending=True):
    """Sugere temas pra geracao de videos."""
    themes = []

    if use_trending and TRENDS_CACHE.exists():
        try:
            cached = json.loads(TRENDS_CACHE.read_text(encoding="utf-8"))
            if time.time() - cached.get("ts", 0) < CACHE_TTL_S:
                themes = cached.get("trends", [])
        except Exception:
            pass

    if use_trending and not themes:
        trends = _fetch_google_trends()
        if trends:
            themes = trends
            TRENDS_CACHE.write_text(json.dumps({"ts": time.time(), "trends": trends},
                                    ensure_ascii=False), encoding="utf-8")

    evergreen = EVERGREEN_THEMES.get(genero, EVERGREEN_THEMES["superacao"])

    if themes:
        mixed = themes[:n//2] + evergreen[:n - n//2]
        return mixed[:n]

    seed = int(time.time() / 3600) + hash(genero)
    start = seed % max(1, len(evergreen) - n)
    return evergreen[start:start + n]


def get_random_theme(genero="superacao"):
    """Retorna 1 tema aleatorio (pra modo continuous)."""
    themes = suggest_themes(genero, n=5, use_trending=False)
    idx = int(time.time()) % len(themes)
    return themes[idx]
