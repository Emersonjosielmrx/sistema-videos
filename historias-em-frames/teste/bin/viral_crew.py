# -*- coding: utf-8 -*-
"""viral_crew.py — Sistema multi-agente de metadados VIRAIS.

Gera titulo/descricao/tags no PADRAO_DOC_POSTAGEM.md, otimizados pro YouTube,
usando 3 "agentes" especialistas (em vez de 1 prompt so):

  1. Estrategista de Gancho  -> titulo com curiosity-gap (ate 100 chars)
  2. Redator SEO             -> descricao (hook + resumo sem spoiler + CTA + disclaimer IA)
  3. Especialista de Tags    -> hashtags/tags por tendencia do genero

Diferenca vs viralizador.py (single prompt): aqui cada papel roda seu proprio
prompt com temperatura e constraints especificas, depois agregamos. Resultado
costuma ter titulo mais forte e tags mais nichadas.

--------------------------------------------------------------------
 COMO LIGAR/DESLIGAR (sem mexer em codigo): config/settings.json
   "usar_crew_viral": true|false   (default false = usa o viralizador leve)
--------------------------------------------------------------------

MODELO/GATEWAY: usa o gateway do settings do Claude/Antigravity
(ANTHROPIC_BASE_URL + ANTHROPIC_API_KEY), formato OpenAI-compat, modelo
'gemini/gemini-pro-latest' (o "pro latest" pedido).

IMPORTANTE sobre o gateway: ele so responde modelos Gemini em modo STREAMING.
Nao tente non-stream — trava >90s sem resposta. Por isso TODAS as chamadas
aqui usam stream=True e agregam os chunks no final.

FALLBACK: se o crew falhar (gateway offline / quota / timeout), CAI no
viralizador.py (Gemini direto por chave) e, em ultimo caso, no template.
Assim a producao 10h nunca trava por causa de metadados.

IMPLEMENTACAO: este modulo NAO usa o framework CrewAI — usa o OpenAI Python
SDK direto. O CrewAI 1.x empacota LiteLLM que detecta "gemini" no model e
manda pra /v1:streamGenerateContent (endpoint Gemini nativo) que NAO e o que
nosso gateway expoe (ele expoe /v1/chat/completions OpenAI). Sem o framework
temos controle total e nenhum mistério de roteamento.

CUSTO: 3 chamadas LLM por video. Em quota apertada, deixe usar_crew_viral=false
— o viralizador leve (1-2 chamadas) cobre o padrao.
"""
import os
import json
import time
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
_SETTINGS_CANDIDATES = [
    Path(os.environ.get("CLAUDE_SETTINGS", "")),
    Path.home() / ".claude-vscode" / "settings.json",
    Path.home() / ".claude" / "settings.json",
]

# modelo "pro latest" preferido. Override por env.
# IMPORTANTE: no gateway atual (proxy webshared), o gemini-pro-latest retorna
# 502 InternalServerError / timeout. O gemini-2.5-flash e o que responde bem
# (via streaming). Se um dia o pro-latest voltar, basta desativar o fallback.
_CREW_MODEL = os.environ.get("VIRAL_CREW_MODEL", "gemini/gemini-2.5-flash")
_CREW_FALLBACKS = ["gemini/gemini-2.5-flash", "gemini/gemini-2.5-pro"]


# ============================================================
# CONFIG / GATEWAY
# ============================================================

def _gateway_env():
    """Le base_url + api_key do settings do Claude (o gateway do proxy)."""
    base = os.environ.get("ANTHROPIC_BASE_URL")
    key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")
    if base and key:
        return base, key
    for f in _SETTINGS_CANDIDATES:
        try:
            if f and f.exists():
                env = json.loads(f.read_text(encoding="utf-8")).get("env", {})
                base = env.get("ANTHROPIC_BASE_URL")
                key = env.get("ANTHROPIC_API_KEY") or env.get("ANTHROPIC_AUTH_TOKEN")
                if base and key:
                    return base, key
        except Exception:
            continue
    return None, None


def _client():
    """Cria o client OpenAI apontando pro gateway. None se indisponivel."""
    base, key = _gateway_env()
    if not (base and key):
        return None
    try:
        from openai import OpenAI
    except Exception:
        return None
    base_v1 = base.rstrip("/")
    if not base_v1.endswith("/v1"):
        base_v1 += "/v1"
    try:
        return OpenAI(api_key=key, base_url=base_v1, timeout=180.0, max_retries=0)
    except Exception:
        return None


# ============================================================
# CHAMADA STREAMING
# ============================================================

def _stream_chat(client, system, user, temperature=0.9, max_tokens=1200, timeout=180):
    """Uma chamada de chat em STREAMING (o gateway so responde assim).
    Tenta o modelo configurado; em caso de erro, tenta os fallbacks 1x cada.
    Usado em paralelo por 3 agentes — evita cascata de retries pra nao
    saturar o gateway."""
    t0 = time.time()
    modelos = [_CREW_MODEL] + [m for m in _CREW_FALLBACKS if m != _CREW_MODEL]
    tried = set()
    for modelo in modelos:
        if modelo in tried:
            continue
        tried.add(modelo)
        try:
            stream = client.chat.completions.create(
                model=modelo,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                timeout=timeout,
            )
            out = []
            for chunk in stream:
                try:
                    d = chunk.choices[0].delta.content or ""
                except Exception:
                    d = ""
                if d:
                    out.append(d)
            txt = "".join(out).strip()
            if txt:
                return txt, time.time() - t0
            print(f"[viral_crew] {modelo} retornou vazio", file=__import__('sys').stderr)
        except Exception as e:
            print(f"[viral_crew] {modelo} falhou: {type(e).__name__}: {str(e)[:120]}",
                  file=__import__('sys').stderr)
            continue
    return None, time.time() - t0


def _parse_json_block(text):
    """Extrai o 1o objeto JSON de um texto (o LLM as vezes embrulha em ```json)."""
    if not text:
        return None
    s = text.strip()
    if "```" in s:
        partes = s.split("```")
        s = next((p for p in partes if p.strip().startswith("{")), s)
        if s.lstrip().startswith("json"):
            s = s.split("json", 1)[1].lstrip()
    a, b = s.find("{"), s.rfind("}")
    if a >= 0 and b > a:
        try:
            return json.loads(s[a:b + 1])
        except Exception:
            return None
    return None


# ============================================================
# AGENTES (cada um e um system+user prompt especialista)
# ============================================================

_SYS_TITULO = (
    "Voce e um ESTRATEGISTA DE GANCHO VIRAL para YouTube Shorts BR. "
    "Crie TRES titulos DIFERENTES (cada um ate 90 caracteres) com curiosity-gap "
    "forte que faz a pessoa PARAR o scroll, sem clickbait mentiroso nem palavras "
    "que desmonetizam (morte explicita, sangue, violencia grafica). "
    "Varie o angulo: um emocional, um curioso/pergunta, um direto/impactante. "
    "Use maiusculas/minusculas naturais. NUNCA use aspas nos titulos. "
    "Responda EXCLUSIVAMENTE um JSON: {\"titulos\":[\"t1\",\"t2\",\"t3\"]}. "
    "Sem markdown, sem texto antes ou depois."
)


# palavras-gatilho que aumentam CTR em shorts BR (curiosity/emocao)
_GATILHOS = (
    "voce", "nunca", "segredo", "descobr", "verdade", "ninguem", "por que",
    "porque", "como", "o que", "quando", "ele", "ela", "eu", "final", "reviravolta",
    "chocante", "inacreditavel", "surpreend", "ultimo", "primeiro", "20 anos",
    "anos depois", "de repente", "ate que",
)


def _score_titulo(t):
    """Heuristica simples de 'viralidade' de um titulo. Maior = melhor.
    Considera: tamanho ideal (40-70), palavras-gatilho, presenca de numero,
    pontuacao de suspense (... ou ?). NAO substitui teste real de CTR, mas
    escolhe o melhor entre as 3 opcoes do LLM de forma consistente."""
    if not t:
        return -1
    s = t.strip()
    low = s.lower()
    score = 0.0
    n = len(s)
    # tamanho: 40-70 chars e o sweet spot de shorts
    if 40 <= n <= 70:
        score += 3
    elif 30 <= n < 40 or 70 < n <= 85:
        score += 1.5
    elif n > 90:
        score -= 2
    # palavras-gatilho (ate 4 pontos)
    hits = sum(1 for g in _GATILHOS if g in low)
    score += min(hits, 4) * 1.0
    # numero no titulo chama atencao
    if any(c.isdigit() for c in s):
        score += 1.5
    # suspense
    if "..." in s or s.endswith("?"):
        score += 1.0
    # penaliza CAPS LOCK total (parece spam)
    letras = [c for c in s if c.isalpha()]
    if letras and sum(1 for c in letras if c.isupper()) / len(letras) > 0.7:
        score -= 1.5
    return score


def _melhor_titulo(txt_json, fallback):
    """Extrai os titulos do JSON, escolhe o de maior score. fallback se falhar.
    Tolera JSON TRUNCADO (o flash as vezes corta no meio) extraindo as strings
    entre aspas do array via regex."""
    titulos = []
    data = _parse_json_block(txt_json)
    if data and isinstance(data.get("titulos"), list):
        titulos = [str(t).strip().strip('"').strip("'").strip()
                   for t in data["titulos"] if str(t).strip()]
    # JSON truncado / sem fechar: pega as strings entre aspas depois de "titulos"
    if not titulos and txt_json and '"titulos"' in txt_json:
        import re
        trecho = txt_json.split('"titulos"', 1)[1]
        # captura "<texto sem aspas>" — pega titulos completos, ignora o cortado
        titulos = [m.strip() for m in re.findall(r'"([^"]{8,100})"', trecho)]
    # ultimo recurso: 1a linha do texto cru
    if not titulos and txt_json:
        linha = txt_json.strip().split("\n")[0].strip().strip('"').strip("'")
        # so aceita se nao parecer JSON quebrado
        if linha and not linha.startswith("{"):
            titulos = [linha]
    if not titulos:
        return fallback, []
    ranked = sorted(titulos, key=_score_titulo, reverse=True)
    return ranked[0][:100], ranked

_SYS_DESCRICAO = (
    "Voce e um REDATOR SEO de YouTube BR. Escreva uma descricao envolvente em portugues: "
    "1a linha = HOOK forte (1 frase). 2-4 linhas = resumo SEM spoiler do final. "
    "Linha com CTA de inscricao. Termine com: 'Historia 100% ficcional gerada por "
    "inteligencia artificial.'. Use quebras de linha entre secoes. Sem hashtags (isso "
    "e papel de outro agente). Maximo ~1500 caracteres."
)

_SYS_TAGS = (
    "Voce e um ESPECIALISTA EM HASHTAGS/TAGS do YouTube BR. "
    "Para o video abaixo, gere 12-15 tags/hashtags que misturam: amplo "
    "(shorts, viral, fyp, historias) com nicho do genero/tema. "
    "Responda EXCLUSIVAMENTE um objeto JSON no formato "
    '{"tags":["tag1","tag2","tag3",...]}. Sem markdown, sem comentarios, '
    'sem texto antes ou depois. Apenas o JSON cru.'
)


def _ctx(genero, tema, titulo_base, cenas):
    """Monta o contexto compartilhado entre os 3 agentes."""
    resumo = ""
    try:
        partes = []
        for c in (cenas or [])[:4]:
            t = (c.get("narracao") or c.get("texto") or "").split(".")[0].strip()
            if t:
                partes.append(t)
        resumo = " / ".join(partes)[:600]
    except Exception:
        resumo = ""
    return (
        f"Genero: {genero}\n"
        f"Tema: {tema}\n"
        f"Titulo base (pior caso): {titulo_base}\n"
        f"Primeiras cenas: {resumo}\n"
        "Publico-alvo: YouTube Shorts vertical, Brasil. Historia 100% ficcional gerada por IA."
    )


# ============================================================
# ORQUESTRADOR (executa os 3 agentes em paralelo = mais rapido)
# ============================================================

def _rodar_agentes(client, ctx_str, titulo_base, deadline_s=180):
    """Roda os 3 agentes SEQUENCIALMENTE (o gateway enfileira quando recebe
    3 requests simultaneas e retorna vazio). Agrega resultados.
    Retorna dict {titulo, descricao, tags} ou {} se falhar."""
    user_titulo = f"Contexto:\n{ctx_str}\n\nGere 3 titulos virais diferentes."
    user_desc   = f"Contexto:\n{ctx_str}\n\nEscreva a descricao completa."
    user_tags   = f"Contexto:\n{ctx_str}\n\nListe as tags."

    t0 = time.time()
    # 3 titulos em JSON -> escolhe o de maior score. max_tokens alto porque o
    # gemini-2.5-flash gasta tokens em reasoning antes do JSON.
    txt_titulo, dt_t = _stream_chat(client, _SYS_TITULO, user_titulo,
                                    temperature=0.95, max_tokens=1000)
    titulo, titulos_ranked = _melhor_titulo(txt_titulo, titulo_base)
    if time.time() - t0 > deadline_s or not titulo:
        return {}
    txt_desc, dt_d = _stream_chat(client, _SYS_DESCRICAO, user_desc,
                                  temperature=0.80, max_tokens=1200)
    if time.time() - t0 > deadline_s:
        return {"titulo": titulo[:100] or titulo_base,
                "descricao": (txt_desc or "").strip()[:5000],
                "tags": [], "_tempo_s": round(time.time() - t0, 1),
                "_parcial": True}
    txt_tags, dt_g = _stream_chat(client, _SYS_TAGS, user_tags,
                                  temperature=0.40, max_tokens=800)
    elapsed = time.time() - t0

    if not titulo:
        return {}

    titulo = titulo[:100] or titulo_base
    descricao = (txt_desc or "").strip()[:5000]
    tags_raw = _parse_json_block(txt_tags or "")
    tags = []
    if tags_raw and isinstance(tags_raw.get("tags"), list):
        tags = [str(t).lstrip("#").strip() for t in tags_raw["tags"] if str(t).strip()][:15]

    if not (titulo and descricao and tags):
        return {"titulo": titulo, "descricao": descricao, "tags": tags,
                "_tempo_s": round(elapsed, 1), "_parcial": True}

    return {"titulo": titulo, "descricao": descricao, "tags": tags,
            "_tempo_s": round(elapsed, 1),
            "_titulos_avaliados": titulos_ranked[:3],
            "_timings": {"titulo": round(dt_t, 1),
                         "descricao": round(dt_d, 1),
                         "tags": round(dt_g, 1)}}


# ============================================================
# FUNCAO PUBLICA
# ============================================================

def gerar_metadados(titulo_base, genero, tema, cenas, timeout=180):
    """Roda o crew de 3 agentes e retorna dict {titulo, descricao, tags:[...]}.
    Retorna None se o crew nao estiver disponivel/falhar (caller usa fallback)."""
    client = _client()
    if client is None:
        return None
    try:
        ctx_str = _ctx(genero, tema, titulo_base, cenas)
        return _rodar_agentes(client, ctx_str, titulo_base, deadline_s=timeout)
    except Exception:
        return None


# ============================================================
# SMOKE TEST
# ============================================================

if __name__ == "__main__":
    base, key = _gateway_env()
    print("gateway:", base, "| key:", ("OK" if key else "FALTA"))
    print("modelo:", _CREW_MODEL)
    out = gerar_metadados("Ele voltou depois de 20 anos", "drama",
                          "pai reencontra filho", [{"narracao": "Vinte anos se passaram."}])
    print(json.dumps(out, ensure_ascii=False, indent=2) if out else "CREW INDISPONIVEL (usa fallback)")
