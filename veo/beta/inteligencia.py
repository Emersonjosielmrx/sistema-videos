# -*- coding: utf-8 -*-
"""Camada de inteligencia de conteudo: personas, keywords virais, timing, CTA.

Modulo ISOLADO — importado por agents.py e cron_gerar_video_llm.py.
Nada aqui abre Chrome nem chama API pesada; sao heuristicas + leitura de cache.

Objetivo: transformar o "cerebro" que decide O QUE cada video fala em algo
guiado por PUBLICO (persona por canal) e por DADOS REAIS (keywords das falas
que mais viralizaram), alem de dar hora certa (timing) e fechar o video com
CTA + gancho de re-watch (loop) — os dois maiores multiplicadores de alcance.

Tudo retrocompativel: se algo faltar, cai em defaults seguros.
"""
import os
import re
import json
import datetime
from collections import Counter, defaultdict

BASE = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE = os.path.join(BASE, "logs", "video_cache.json")
PADROES_FILE = os.path.join(BASE, "logs", "padroes_viralizacao.json")


# ---------------------------------------------------------------------------
# PERSONAS por canal (Tier 3) — quem assiste, qual a dor, como fala
# ---------------------------------------------------------------------------
# Chave = tema (o mesmo campo usado em CANAIS). Cada persona guia o tom da fala
# e o visual. Sem persona cadastrada -> _PERSONA_DEFAULT.
PERSONAS = {
    "Releitura de Cenas Famosas": {
        "publico": "fas de cinema e cultura pop, 16-30",
        "dor": "nostalgia e vontade de ver o impossivel refeito",
        "tom": "epico, cinefilo, cheio de referencia",
        "gatilho": "reconhecimento ('eu conheco essa cena!') + surpresa",
    },
    "Micro-aulas e Tutoriais": {
        "publico": "curiosos que querem aprender rapido, 18-40",
        "dor": "falta de tempo, querem sacada util em segundos",
        "tom": "professor direto, pratico, sem enrolacao",
        "gatilho": "utilidade imediata ('salva isso')",
    },
    "Erros da IA (AI Fails)": {
        "publico": "publico geral que curte humor de internet, 14-30",
        "dor": "querem rir e compartilhar algo absurdo",
        "tom": "zoeiro, ironico, comeco de piada",
        "gatilho": "riso + incredulidade ('a IA fez o que?')",
    },
    "Visuais Psicodelicos": {
        "publico": "amantes de arte visual e satisfying, 16-35",
        "dor": "querem hipnose visual pra relaxar/prender",
        "tom": "misterioso, sensorial, poucas palavras",
        "gatilho": "fascinio visual ('nao consigo parar de olhar')",
    },
    "Trocadilhos Visuais Literais": {
        "publico": "publico esperto que curte sacada de linguagem, 18-35",
        "dor": "querem o 'aha' de um trocadilho bem feito",
        "tom": "espirituoso, brincalhao",
        "gatilho": "sacada inteligente + riso",
    },
    "Fofura em Situacoes Bizarras": {
        "publico": "amantes de pet e fofura, maioria feminino 16-40",
        "dor": "querem 'aaaw' e alivio emocional",
        "tom": "meigo, caloroso, exclamativo",
        "gatilho": "fofura + estranheza ('que isso???')",
    },
    "Citacoes Motivacionais": {
        "publico": "pessoas buscando animo/superacao, 20-45",
        "dor": "querem um empurrao emocional pra virar o dia",
        "tom": "inspirador, firme, quase discurso",
        "gatilho": "identificacao + esperanca",
    },
    "Fatos Rapidos Chocantes": {
        "publico": "curiosos viciados em 'voce sabia', 14-40",
        "dor": "querem munição de conversa/curiosidade",
        "tom": "urgente, revelador, olho arregalado",
        "gatilho": "choque ('eu nao sabia disso')",
    },
    "Visualizacao de Musica": {
        "publico": "jovens que consomem musica e trend, 14-28",
        "dor": "querem vibe/estetica pra compartilhar",
        "tom": "vibrante, ritmado, cool",
        "gatilho": "vibe + reconhecimento de som/trend",
    },
    "Educacao Financeira": {
        "publico": "jovens adultos endividados ou querendo investir, 20-40",
        "dor": "medo de ficar pra tras financeiramente",
        "tom": "confiante, revelador, quase 'segredo dos ricos'",
        "gatilho": "medo de perder + ganancia ('o banco esconde')",
    },
    "Desmentindo Mitos": {
        "publico": "ceticos e curiosos, 18-45",
        "dor": "querem descobrir que estavam sendo enganados",
        "tom": "investigativo, provocador",
        "gatilho": "'voce foi enganado a vida toda'",
    },
    "Curiosidades Estranhas": {
        "publico": "fas de fatos bizarros, 14-35",
        "dor": "querem o esquisito que ninguem conta",
        "tom": "intrigante, meio sombrio",
        "gatilho": "estranheza ('isso e real?')",
    },
    "Fatos Medicos e Biologicos": {
        "publico": "curiosos sobre o proprio corpo, 16-45",
        "dor": "querem entender o corpo de forma simples",
        "tom": "didatico com pitada de nojo/uau",
        "gatilho": "'seu corpo faz isso agora'",
    },
    "Talassofobia e Vida Marinha": {
        "publico": "fascinados/assustados pelo oceano, 16-35",
        "dor": "medo + fascinio pelo desconhecido profundo",
        "tom": "tenso, sombrio, sussurro de documentario",
        "gatilho": "medo do abismo ('o que tem la embaixo')",
    },
    "Exercicios e Nutricao": {
        "publico": "quem quer resultado na academia, 18-40",
        "dor": "esforco sem resultado, informacao conflitante",
        "tom": "direto, coach, anti-mito",
        "gatilho": "'voce ta sabotando seus ganhos'",
    },
    "Noticias sobre Inteligencia Artificial": {
        "publico": "entusiastas de tech, 18-40",
        "dor": "medo de ficar obsoleto, FOMO de IA",
        "tom": "urgente, jornalistico, 'acabou de sair'",
        "gatilho": "FOMO ('a IA acabou de...')",
    },
    "Visualizacao de Recordes": {
        "publico": "publico geral fa de 'o maior/mais rapido', 12-35",
        "dor": "querem se impressionar com extremos",
        "tom": "grandioso, de arena",
        "gatilho": "escala absurda ('impossivel')",
    },
    "Piadas contadas por IA": {
        "publico": "quem quer rir rapido, 14-35",
        "dor": "querem uma risada facil pra mandar no grupo",
        "tom": "comico, timing de stand-up",
        "gatilho": "riso + 'manda pro grupo'",
    },
    "Cenarios Hipoteticos": {
        "publico": "sonhadores e curiosos, 14-35",
        "dor": "querem imaginar o impossivel",
        "tom": "imaginativo, 'e se...'",
        "gatilho": "curiosidade especulativa",
    },
    "Humor Nonsense e Surreal": {
        "publico": "geracao meme, humor absurdo, 14-28",
        "dor": "querem o inesperado sem sentido que viraliza",
        "tom": "caotico, surreal, sem logica",
        "gatilho": "'que? kkkk' + share",
    },
    "Ilusoes e Puzzles Visuais": {
        "publico": "curiosos que gostam de desafio visual, 12-40",
        "dor": "querem testar a propria percepcao",
        "tom": "provocador, desafiador",
        "gatilho": "desafio ('seu cerebro vai bugar')",
    },
    "Morphing Satisfatorio": {
        "publico": "fas de satisfying/transicao, 14-30",
        "dor": "querem o prazer visual da transformacao",
        "tom": "hipnotico, fluido",
        "gatilho": "satisfacao visual + loop",
    },
    "Camera Lenta Extrema": {
        "publico": "fas de slow-mo e detalhe, 14-35",
        "dor": "querem ver o que o olho nao capta",
        "tom": "dramatico, contemplativo",
        "gatilho": "revelacao em detalhe",
    },
    "ETs em Situacoes Engracadas": {
        "publico": "humor + ficcao, 12-30",
        "dor": "querem rir de alienigena em contexto BR",
        "tom": "comico, brasileiro, absurdo",
        "gatilho": "riso + brasilidade ('ET brasileiro')",
    },
    "Robos Tentando Ser Humanos": {
        "publico": "fas de tech + humor, 14-32",
        "dor": "querem o comico do robo falhando em ser gente",
        "tom": "comico, meio fofo, meio esquisito",
        "gatilho": "riso + estranheza",
    },
}

_PERSONA_DEFAULT = {
    "publico": "jovens brasileiros 16-35 no TikTok/Reels/Shorts",
    "dor": "querem entretenimento rapido que valha o compartilhamento",
    "tom": "energico, direto, brasileiro natural",
    "gatilho": "curiosidade + surpresa nos primeiros segundos",
}


def get_persona(tema: str) -> dict:
    """Retorna a persona do canal (por tema). Nunca falha."""
    return PERSONAS.get(tema, _PERSONA_DEFAULT)


def persona_brief(tema: str) -> str:
    """Frase curta pra injetar no prompt do LLM descrevendo o publico-alvo."""
    p = get_persona(tema)
    return (f"PUBLICO-ALVO: {p['publico']}. "
            f"DOR/DESEJO: {p['dor']}. "
            f"TOM DE VOZ: {p['tom']}. "
            f"GATILHO EMOCIONAL: {p['gatilho']}.")


# ---------------------------------------------------------------------------
# GANCHO VISUAL + CTA + LOOP (Tier 2/3)
# ---------------------------------------------------------------------------
# Instrucao de gancho VISUAL nos primeiros frames (o scroll acontece antes da
# fala terminar; precisa de movimento/choque no frame 1).
HOOK_VISUAL_INSTR = (
    "CRITICO: o primeiro frame (0-1s) precisa de um GANCHO VISUAL forte — "
    "movimento brusco, expressao de choque, cor vibrante ou elemento inesperado "
    "que impeca o scroll ANTES da fala comecar. Nada de abertura lenta/estatica."
)

# CTA leves por gatilho — anexados como direcao (nao viram fala falada crua).
CTA_POOL = [
    "comenta o que voce achou",
    "segue pra nao perder o proximo",
    "manda pra alguem que precisa ver isso",
    "salva esse video",
]

# Gancho de LOOP: fechar o video conectando com o comeco (re-watch).
LOOP_INSTR = (
    "Se possivel, feche o video conectando visualmente com o primeiro frame "
    "(gancho de loop) pra estimular o re-watch."
)


def cta_para_tema(tema: str) -> str:
    """Escolhe um CTA coerente com o gatilho da persona (deterministico por dia)."""
    p = get_persona(tema)
    gat = (p.get("gatilho") or "").lower()
    if "share" in gat or "grupo" in gat or "manda" in gat:
        return "manda pra alguem que precisa ver isso"
    if "salva" in gat or "utilidade" in gat:
        return "salva esse video pra nao esquecer"
    if "riso" in gat or "kkk" in gat:
        return "marca aquele amigo pra rir junto"
    # roda pelo dia do ano pra variar sem depender de random
    return CTA_POOL[datetime.date.today().toordinal() % len(CTA_POOL)]


# ---------------------------------------------------------------------------
# KEYWORDS VIRAIS realimentadas (Tier 4)
# ---------------------------------------------------------------------------
_STOPWORDS = {
    "que", "para", "com", "uma", "voce", "esse", "essa", "isso", "aqui",
    "agora", "sua", "seu", "mais", "como", "pelo", "pela", "todo", "toda",
    "sem", "tem", "foi", "vai", "sao", "ser", "ter", "dar", "ver", "por",
    "dos", "das", "nao", "mas", "num", "numa", "ate", "seus", "suas", "essa",
    "você", "vocês", "está", "então", "são", "não", "até", "têm", "minha",
    "meu", "fazer", "pelo", "aos", "nas", "nos", "quando", "onde", "porque",
}


def _load_cache():
    if not os.path.exists(CACHE_FILE):
        return []
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def keywords_virais(tema: str = None, top_n: int = 8, min_amostra: int = 5):
    """Palavras mais frequentes nas falas que MAIS viralizaram (por views reais).

    Usa metrics.views quando existe; se ainda nao ha views (loop de metricas
    frio), cai pro critic score como proxy. Filtra por tema se informado.
    Retorna lista de palavras (str). Vazio se amostra insuficiente.
    """
    cache = _load_cache()
    if tema:
        cache = [c for c in cache if c.get("tema") == tema]
    if len(cache) < min_amostra:
        return []

    com_views = [c for c in cache if c.get("metrics", {}).get("views")]
    if len(com_views) >= min_amostra:
        base = sorted(com_views, key=lambda c: c["metrics"]["views"], reverse=True)
        metrica = "views"
    else:
        # fallback: usa critic score como proxy enquanto metrics estao frias
        base = sorted(cache, key=lambda c: c.get("score", 0), reverse=True)
        metrica = "score"

    top = base[:max(1, len(base) // 3)]  # top terco
    txt = " ".join(c.get("fala", "") for c in top).lower()
    palavras = [w for w in re.findall(r"[a-zà-úâ-û0-9]+", txt)
                if len(w) > 3 and w not in _STOPWORDS]
    if not palavras:
        return []
    return [w for w, _ in Counter(palavras).most_common(top_n)]


def keywords_brief(tema: str) -> str:
    """Frase pra injetar no LLM com as palavras que estao performando."""
    kws = keywords_virais(tema)
    if not kws:
        return ""
    return ("PALAVRAS QUE ESTAO PERFORMANDO neste canal (use naturalmente 1-2, "
            "sem forcar): " + ", ".join(kws) + ".")


# ---------------------------------------------------------------------------
# A/B de GANCHOS (Tier 2) — classifica a familia da abertura e aprende qual
# funciona por canal quando as metricas chegam.
# ---------------------------------------------------------------------------
# Familias de gancho (o "tipo" da primeira frase). Servem pra medir qual
# abertura performa em cada canal — nao pra forcar, so pra aprender.
HOOK_FAMILIES = {
    "pergunta": ["?", "sera que", "voce sabia", "e se", "por que", "quem"],
    "choque": ["atencao", "urgente", "acabou de", "ninguem", "nunca",
               "pare", "cuidado", "chocante", "bizarro", "proibido"],
    "comando": ["pare de", "faca", "nao faca", "jogue", "salva", "olha",
                "escuta", "presta atencao", "esqueca"],
    "primeira_pessoa": ["eu ", "meu ", "minha ", "achei que", "testei",
                        "gastei", "descobri"],
    "segredo": ["segredo", "esconde", "escondem", "ninguem te conta",
                "verdade sobre", "o que nao te contaram"],
}


def classificar_gancho(fala) -> str:
    """Classifica a familia da PRIMEIRA frase de uma fala. Nunca falha.

    Aceita string ou lista (multi-fala). Retorna nome da familia ou 'outro'.
    """
    if isinstance(fala, list):
        primeira = fala[0] if fala else ""
    else:
        # multi-fala vem como 'a | b | c'
        primeira = str(fala or "").split("|")[0]
    t = primeira.lower().strip()
    if not t:
        return "outro"
    # Ordem por ESPECIFICIDADE (mais especifico primeiro), senao "pare" cairia
    # em choque antes de comando, e "segredo" perderia pra outra familia.
    ordem = ["segredo", "comando", "primeira_pessoa", "pergunta", "choque"]
    for familia in ordem:
        for m in HOOK_FAMILIES.get(familia, []):
            if m in t:
                return familia
    return "outro"


def ranking_ganchos(tema: str = None, min_amostra: int = 8) -> dict:
    """Media de views por familia de gancho (por canal se tema informado).

    Retorna {familia: avg_views}. Vazio se ainda nao ha metricas suficientes.
    So considera videos com metrics.views (dados REAIS, nao critic score).
    """
    cache = _load_cache()
    if tema:
        cache = [c for c in cache if c.get("tema") == tema]
    com_views = [c for c in cache if c.get("metrics", {}).get("views")]
    if len(com_views) < min_amostra:
        return {}
    soma = defaultdict(list)
    for c in com_views:
        fam = c.get("hook_family") or classificar_gancho(c.get("fala", ""))
        soma[fam].append(c["metrics"]["views"])
    return {fam: sum(v) / len(v) for fam, v in soma.items() if v}


def melhor_gancho(tema: str) -> str:
    """Familia de gancho que mais performa neste canal, ou '' se sem dados."""
    rank = ranking_ganchos(tema)
    if not rank:
        return ""
    return max(rank.items(), key=lambda kv: kv[1])[0]


# ---------------------------------------------------------------------------
# TIMING de pico por canal/publico (Tier 3)
# ---------------------------------------------------------------------------
# Janelas de pico (hora local BR) tipicas por natureza do publico. Usadas como
# BONUS na escolha de canal — nao bloqueiam nada, so priorizam quem esta no
# horario mais quente pra aquele publico.
#   default: picos gerais de short-form BR (almoco, fim de tarde, noite)
_PICO_DEFAULT = [(11, 13), (17, 19), (20, 23)]
_PICO_POR_TEMA = {
    # conteudo util/estudo — manha e horario comercial
    "Micro-aulas e Tutoriais": [(7, 9), (12, 14), (19, 22)],
    "Educacao Financeira": [(7, 9), (12, 14), (19, 22)],
    "Exercicios e Nutricao": [(6, 8), (17, 20)],
    # entretenimento/humor — noite forte
    "Erros da IA (AI Fails)": [(12, 14), (19, 23)],
    "Humor Nonsense e Surreal": [(12, 14), (20, 24)],
    "Piadas contadas por IA": [(12, 14), (20, 24)],
    "ETs em Situacoes Engracadas": [(12, 14), (20, 24)],
    "Stand-up IA": [(20, 24)],
    # relax/satisfying — noite tarde
    "Visuais Psicodelicos": [(21, 24), (0, 2)],
    "Morphing Satisfatorio": [(21, 24), (0, 2)],
    "Talassofobia e Vida Marinha": [(21, 24), (0, 1)],
    # noticias tech — manha (ciclo de noticia)
    "Noticias sobre Inteligencia Artificial": [(7, 10), (12, 14), (18, 20)],
}


def bonus_horario(tema: str, agora: datetime.datetime = None) -> float:
    """Bonus [0..1] se o horario atual cai no pico do publico daquele tema.

    1.0 = dentro do pico; 0.3 = fora. Usado como peso na escolha de canal.
    """
    agora = agora or datetime.datetime.now()
    h = agora.hour
    janelas = _PICO_POR_TEMA.get(tema, _PICO_DEFAULT)
    for ini, fim in janelas:
        # janela pode cruzar meia-noite (ex: (21, 24) ou (0, 2))
        if ini <= fim:
            if ini <= h < fim:
                return 1.0
        else:
            if h >= ini or h < fim:
                return 1.0
    return 0.3


# ---------------------------------------------------------------------------
# Teste rapido
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    tema = sys.argv[1] if len(sys.argv) > 1 else "Educacao Financeira"
    print("=== persona ===")
    print(persona_brief(tema))
    print("\n=== keywords virais ===")
    print(keywords_virais(tema) or "(amostra insuficiente)")
    print("\n=== keywords_brief ===")
    print(keywords_brief(tema) or "(vazio)")
    print("\n=== cta ===")
    print(cta_para_tema(tema))
    print("\n=== bonus_horario agora ===")
    print(f"{bonus_horario(tema):.1f}")
