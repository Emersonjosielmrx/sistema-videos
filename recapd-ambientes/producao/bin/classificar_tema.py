#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""classificar_tema.py — Classifica tema/canal de vídeo via LLM analisando transcrição.

Recebe a transcrição de um vídeo e retorna qual(is) canal(is) de YouTube deve(m) recebê-lo,
baseado em análise de conteúdo via LLM. Suporta múltiplos temas (segmentação temporal).
"""
import sys
import json
from pathlib import Path

# Adiciona fabrica-viral ao path para importar llm_client
sys.path.insert(0, str(Path(__file__).parent.parent / "fabrica-viral"))

try:
    from llm_client import chat_json, chat_fast
except ImportError:
    print("[classificar] ERRO: não foi possível importar llm_client", file=sys.stderr)
    sys.exit(1)

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")


# Mapeamento de categorias para canais (carregado de youtube_canais.json)
CANAIS_JSON = Path("D:/credenciais-canais/youtube_canais.json")

# Categorias principais de conteúdo
CATEGORIAS = {
    "ia": ["IA", "inteligência artificial", "machine learning", "deep learning", "ChatGPT", "Claude", "tecnologia IA"],
    "financeiro": ["finanças", "investimento", "economia", "mercado", "ações", "cripto", "dinheiro"],
    "motivacao": ["motivação", "autoajuda", "desenvolvimento pessoal", "sucesso", "inspiração"],
    "politica": ["política", "governo", "eleição", "democracia", "partido"],
    "entretenimento": ["entretenimento", "curiosidade", "viral", "absurdo", "humor"],
    "educacao": ["educação", "aprendizado", "ensino", "conhecimento", "ciência"],
    "anime": ["anime", "manhwa", "manga", "otaku"],
    "gaming": ["game", "jogo", "gamer", "gameplay"],
    "musica": ["música", "canção", "artista", "show"],
    "danca": ["dança", "coreografia", "ballet"],
}


def carregar_canais():
    """Carrega mapeamento de categorias para canais do youtube_canais.json."""
    if not CANAIS_JSON.exists():
        print(f"[classificar] AVISO: {CANAIS_JSON} não encontrado", file=sys.stderr)
        return {}

    try:
        with open(CANAIS_JSON, "r", encoding="utf-8") as f:
            canais_raw = json.load(f)

        # Monta mapeamento categoria -> lista de nomes de canal
        mapa = {}
        for canal in canais_raw:
            nome = canal.get("nome", "").lower()
            if not nome:
                continue

            # Detecção simples por palavras-chave no nome do canal
            if any(kw in nome for kw in ["ia", "artificial", "tech"]):
                mapa.setdefault("ia", []).append(canal["nome"])
            if any(kw in nome for kw in ["financ", "invest", "dinheir", "econom"]):
                mapa.setdefault("financeiro", []).append(canal["nome"])
            if any(kw in nome for kw in ["motiv", "sucesso", "inspiração"]):
                mapa.setdefault("motivacao", []).append(canal["nome"])
            if any(kw in nome for kw in ["polít", "eleição", "govern"]):
                mapa.setdefault("politica", []).append(canal["nome"])
            if any(kw in nome for kw in ["absurd", "fofos", "viral", "risada", "piada"]):
                mapa.setdefault("entretenimento", []).append(canal["nome"])
            if any(kw in nome for kw in ["anime", "manhwa", "manga", "otaku"]):
                mapa.setdefault("anime", []).append(canal["nome"])
            if any(kw in nome for kw in ["game", "gaming"]):
                mapa.setdefault("gaming", []).append(canal["nome"])
            if any(kw in nome for kw in ["música", "music", "dança", "danç"]):
                mapa.setdefault("musica", []).append(canal["nome"])

        return mapa
    except Exception as e:
        print(f"[classificar] Erro ao carregar canais: {e}", file=sys.stderr)
        return {}


def classificar_tema_simples(transcricao, idioma="pt"):
    """Classifica um tema único via LLM. Retorna categoria ou None."""
    if not transcricao or len(transcricao) < 20:
        return None

    prompt = f"""Analise a transcrição abaixo e classifique o tema principal do vídeo.

TRANSCRIÇÃO ({idioma}):
{transcricao[:3000]}

CATEGORIAS DISPONÍVEIS:
- ia: Inteligência Artificial, tecnologia, ChatGPT, automação
- financeiro: Finanças, investimentos, economia, mercado
- motivacao: Motivação, desenvolvimento pessoal, sucesso
- politica: Política, governo, eleições
- entretenimento: Humor, curiosidades, viral, absurdos
- educacao: Educação, ciência, conhecimento
- anime: Anime, manhwa, manga
- gaming: Games, jogos, gameplay
- musica: Música, artistas, shows
- danca: Dança, coreografia

Responda APENAS com o nome da categoria (uma palavra). Se não se encaixar em nenhuma, responda "geral".
"""

    messages = [{"role": "user", "content": prompt}]
    resposta = chat_fast(messages, max_tokens=50, temperature=0.2)

    if not resposta:
        return None

    categoria = resposta.strip().lower()
    if categoria in CATEGORIAS or categoria == "geral":
        return categoria

    return None


def classificar_temas_multiplos(transcricao, idioma="pt", segmentos=None):
    """Classifica múltiplos temas em um vídeo (para segmentação temporal).

    Args:
        transcricao: texto completo da transcrição
        idioma: idioma detectado
        segmentos: lista opcional de {inicio, fim, texto} para análise por trecho

    Returns:
        Lista de dicts: [{"categoria": str, "inicio": float, "fim": float, "confianca": float}]
    """
    if not transcricao or len(transcricao) < 20:
        return []

    # Se não tem segmentos, analisa o texto completo em janelas de tempo
    if not segmentos:
        # Divide em chunks de ~500 palavras
        palavras = transcricao.split()
        chunks = []
        chunk_size = 500
        for i in range(0, len(palavras), chunk_size):
            chunk_texto = " ".join(palavras[i:i+chunk_size])
            chunks.append({
                "texto": chunk_texto,
                "indice": i // chunk_size
            })
    else:
        # Usa os segmentos com timestamp
        chunks = [{"texto": seg["texto"], "inicio": seg["inicio"], "fim": seg["fim"]}
                  for seg in segmentos if seg.get("texto")]

    if not chunks:
        return []

    # Monta prompt para o LLM
    chunks_texto = "\n\n".join([
        f"--- TRECHO {i+1} ---\n{c['texto'][:800]}"
        for i, c in enumerate(chunks[:10])  # Limita a 10 trechos
    ])

    prompt = f"""Analise os trechos da transcrição abaixo e identifique os TEMAS/ASSUNTOS discutidos.

TRANSCRIÇÃO EM TRECHOS ({idioma}):
{chunks_texto}

CATEGORIAS:
- ia: IA, tecnologia, ChatGPT
- financeiro: finanças, investimentos
- motivacao: motivação, sucesso
- politica: política, governo
- entretenimento: humor, curiosidades
- educacao: educação, ciência
- anime: anime, manhwa
- gaming: games, jogos
- musica: música
- danca: dança
- geral: não se encaixa

Para CADA TRECHO que você analisou, identifique:
1. O tema principal (uma das categorias acima)
2. Confiança da classificação (0.0 a 1.0)

Responda em JSON:
{{
  "temas": [
    {{"trecho": 1, "categoria": "ia", "confianca": 0.9}},
    {{"trecho": 2, "categoria": "politica", "confianca": 0.85}}
  ]
}}

Apenas JSON, sem explicações.
"""

    messages = [{"role": "user", "content": prompt}]
    resposta = chat_json(messages, max_tokens=1024)

    if not resposta or not isinstance(resposta, dict):
        # Fallback: classifica tudo como um tema único
        tema_unico = classificar_tema_simples(transcricao, idioma)
        return [{"categoria": tema_unico or "geral", "confianca": 0.5}]

    temas_raw = resposta.get("temas", [])
    if not temas_raw:
        return []

    # Mapeia de volta para os chunks originais (com timestamps se disponível)
    resultado = []
    for tema in temas_raw:
        idx = tema.get("trecho", 1) - 1
        if idx < 0 or idx >= len(chunks):
            continue

        chunk = chunks[idx]
        item = {
            "categoria": tema.get("categoria", "geral"),
            "confianca": float(tema.get("confianca", 0.5))
        }

        # Adiciona timestamps se disponível
        if "inicio" in chunk and "fim" in chunk:
            item["inicio"] = chunk["inicio"]
            item["fim"] = chunk["fim"]

        resultado.append(item)

    return resultado


def selecionar_canal(categoria, canais_disponiveis=None):
    """Seleciona um canal da categoria. Retorna nome do canal ou None."""
    if canais_disponiveis is None:
        canais_disponiveis = carregar_canais()

    candidatos = canais_disponiveis.get(categoria, [])
    if not candidatos:
        # Fallback para categoria geral/entretenimento
        candidatos = canais_disponiveis.get("entretenimento", [])

    if not candidatos:
        print(f"[classificar] AVISO: nenhum canal encontrado para categoria '{categoria}'", file=sys.stderr)
        return None

    # Valida que o canal existe no youtube_canais.json
    canal_escolhido = candidatos[0]

    # Carrega youtube_canais.json para validar
    try:
        with open(CANAIS_JSON, "r", encoding="utf-8") as f:
            canais_raw = json.load(f)

        # Procura match exato ou parcial
        for canal_data in canais_raw:
            nome = canal_data.get("nome", "")
            if nome.lower() == canal_escolhido.lower() or canal_escolhido.lower() in nome.lower():
                return canal_data["nome"]  # Retorna nome exato do JSON

        print(f"[classificar] AVISO: canal '{canal_escolhido}' não encontrado em youtube_canais.json", file=sys.stderr)
        return None
    except Exception as e:
        print(f"[classificar] Erro ao validar canal: {e}", file=sys.stderr)
        return canal_escolhido  # Retorna mesmo assim como fallback


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: classificar_tema.py <transcricao_json>", file=sys.stderr)
        print("  transcricao_json: arquivo JSON com {texto_completo, segmentos, idioma}", file=sys.stderr)
        sys.exit(1)

    transcricao_path = Path(sys.argv[1])
    if not transcricao_path.exists():
        print(f"Arquivo não encontrado: {transcricao_path}", file=sys.stderr)
        sys.exit(1)

    with open(transcricao_path, "r", encoding="utf-8") as f:
        dados = json.load(f)

    texto = dados.get("texto_completo", "")
    segmentos = dados.get("segmentos", [])
    idioma = dados.get("idioma", "pt")

    print(f"[classificar] Analisando transcrição ({len(texto)} chars, idioma={idioma})", file=sys.stderr)

    # Classifica temas
    temas = classificar_temas_multiplos(texto, idioma, segmentos)

    # Carrega canais disponíveis
    canais_map = carregar_canais()

    # Associa cada tema a um canal
    resultado = []
    for tema in temas:
        canal = selecionar_canal(tema["categoria"], canais_map)
        resultado.append({
            **tema,
            "canal": canal
        })

    print(json.dumps({
        "temas": resultado,
        "num_temas": len(resultado)
    }, ensure_ascii=False, indent=2))
