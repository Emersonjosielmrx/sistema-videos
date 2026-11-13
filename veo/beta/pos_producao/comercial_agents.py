# -*- coding: utf-8 -*-
"""comercial_agents.py — multi-agente que PROJETA o comercial Veo de cada produto.

PROBLEMA que resolve: o prompt fixo antigo ("a narrator says ...") fazia o Veo
gerar só SOM AMBIENTE (ex: telefone tocando) e ignorar a VOZ. Comercial sem
fala não vende. Aqui um pipeline de agentes projeta cada comercial pra ser o
melhor possível E pra garantir que o Veo FALE.

Segredo técnico p/ o Veo 3 falar (não só som ambiente):
  - tem que haver uma PESSOA visível falando OLHANDO pra câmera (não só o produto);
  - a fala tem que ser LITERAL, curta e entre aspas: 'A woman says: "..."';
  - marcar lip-sync explícito ("lips moving, speaking directly to camera");
  - som ambiente é secundário; a FALA é o foco.

Pipeline (espelha agents.py, chamadas diretas ao llm_client — sem overhead):
  1. Estrategista de Produto  -> ângulo de venda + dor do cliente (JSON)
  2. Roteirista de Comercial  -> fala PT-BR curta falável em 8s + quem fala
  3. Diretor de Comercial     -> prompt Veo cinematográfico c/ pessoa falando
  4. Crítico de Comercial     -> nota (vende? a fala vai ser falada?), regenera

Uso:
    from comercial_agents import projetar_comercial
    r = projetar_comercial(produto_dict)   # -> {"prompt": ..., "fala": ..., "score": ...}
"""
import json
import logging
import os
import sys
from pathlib import Path

_BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BASE))
log = logging.getLogger("comercial_agents")


def _llm(system, user, modelo=None):
    """Chamada única ao llm_client (gateway pro -> chaves). modelo opcional."""
    from llm_client import _call_gemini_native, _call_openai_compat, is_openai_compat
    old = os.environ.get("LLM_MODEL")
    if modelo:
        os.environ["LLM_MODEL"] = modelo
    try:
        if is_openai_compat():
            return _call_openai_compat(system, user)
        return _call_gemini_native(system, user)
    finally:
        if modelo:
            if old:
                os.environ["LLM_MODEL"] = old
            else:
                os.environ.pop("LLM_MODEL", None)


def _parse_json(txt):
    """Extrai 1o JSON válido de txt (tolera markdown/lixo em volta)."""
    txt = (txt or "").strip()
    if txt.startswith("```"):
        txt = txt.split("```", 2)[1]
        if txt.startswith("json"):
            txt = txt[4:]
        txt = txt.strip()
    s, e = txt.find("{"), txt.rfind("}")
    if s >= 0 and e > s:
        txt = txt[s:e + 1]
    return json.loads(txt)


# palavras comuns que o LLM as vezes escreve SEM acento -> o Veo (e qualquer TTS)
# le errado ("voce"->"voke"). Corrigimos SO NA FALA (nao no prompt ingles).
# Mesmo principio do CTA ElevenLabs (ver memoria tts-ptbr-acentos).
_ACENTOS = {
    "voce": "você", "voces": "vocês", "vc": "você",
    "nao": "não", "sao": "são", "entao": "então", "nao?": "não?",
    "atencao": "atenção", "ligacao": "ligação", "ligacoes": "ligações",
    "automatico": "automático", "automatica": "automática",
    "inteligencia": "inteligência", "negocio": "negócio", "negocios": "negócios",
    "voce.": "você.", "so": "só", "ja": "já", "esta": "está", "estao": "estão",
    "dinheiro": "dinheiro", "lucro": "lucro", "video": "vídeo", "videos": "vídeos",
    "hora": "hora", "horas": "horas", "gratis": "grátis", "facil": "fácil",
    "rapido": "rápido", "musica": "música", "voce,": "você,",
    "aqui": "aqui", "ai": "aí", "porem": "porém", "alem": "além",
    "ninguem": "ninguém", "alguem": "alguém", "tambem": "também",
    "sem": "sem", "mes": "mês", "meses": "meses", "estrategia": "estratégia",
    "concorrencia": "concorrência", "experiencia": "experiência",
    "eficiencia": "eficiência", "paciencia": "paciência", "urgencia": "urgência",
    "producao": "produção", "solucao": "solução", "solucoes": "soluções",
    "conversao": "conversão", "gestao": "gestão", "decisao": "decisão",
    "voce?": "você?", "voce!": "você!", "nao!": "não!", "e?": "é?",
    "publico": "público", "unico": "único", "otimo": "ótimo", "pratico": "prático",
    "credito": "crédito", "obvio": "óbvio", "proprio": "próprio",
    "comercio": "comércio", "usuario": "usuário", "relatorio": "relatório",
    "e": "e",  # 'e' conjuncao fica; 'é' verbo tratado abaixo
}


# 'e' sozinho quase sempre e o verbo "é" na fala publicitaria ("isso é ouro").
# tratamos separado pra nao trocar a conjuncao "e" (X e Y). heuristica simples:
# nao mexemos em 'e' automatico (risco de erro) — o LLM ja e instruido a acentuar.


def _acentuar_fala(fala: str) -> str:
    """Repoe acentos nas palavras comuns da FALA (case-insensitive, preserva
    a caixa da 1a letra). NAO toca em pontuacao/estrutura — so troca a palavra."""
    import re
    if not fala:
        return fala

    def _troca(m):
        w = m.group(0)
        base = w.lower()
        if base in _ACENTOS:
            corr = _ACENTOS[base]
            # preserva Maiuscula inicial
            if w[:1].isupper():
                corr = corr[:1].upper() + corr[1:]
            return corr
        return w

    # \b nao pega bem acentos, mas a entrada aqui e sem acento -> ok
    return re.sub(r"[A-Za-zÀ-ÿ]+", _troca, fala)


# ---------------------------------------------------------------------------
# Agente 1 — Estrategista de Produto
# ---------------------------------------------------------------------------
def _estrategista(produto: dict) -> dict:
    """Define o ângulo de venda e a dor do cliente do produto."""
    system = (
        "Voce e estrategista de marketing de resposta direta. Responda APENAS JSON "
        "puro (sem markdown), comecando com { e terminando com }."
    )
    user = (
        f"Produto: {produto.get('nome')}\n"
        f"O que faz: {produto.get('descricao')}\n"
        f"Beneficio curto: {produto.get('cta_curto')}\n"
        f"Pitch: {produto.get('cta_longo')}\n\n"
        f"Defina o comercial de 8 segundos. Responda SO com este JSON:\n"
        f'{{"dor": "a dor #1 do cliente em 1 frase", '
        f'"angulo": "o angulo de venda mais forte em 1 frase", '
        f'"emocao": "a emocao que vende (medo de perder/alivio/ganancia/curiosidade)", '
        f'"publico": "quem compra isso"}}'
    )
    try:
        return _parse_json(_llm(system, user, "gemini-flash-lite-latest"))
    except Exception as e:
        log.warning(f"[estrategista] fallback: {e}")
        return {"dor": produto.get("descricao", ""),
                "angulo": produto.get("cta_curto", ""),
                "emocao": "curiosidade", "publico": "empreendedores"}


# ---------------------------------------------------------------------------
# Agente 2 — Roteirista de Comercial (a FALA que o Veo vai falar)
# ---------------------------------------------------------------------------
def _roteirista(produto: dict, estrategia: dict) -> dict:
    """Cria a fala falada (curta, PT-BR, cabe em 8s) + quem fala."""
    system = (
        "Voce e roteirista de comerciais de 8 segundos para redes sociais, em "
        "portugues brasileiro. A fala DEVE caber em ~8s (no maximo 18 palavras), "
        "soar natural falada em voz alta, com gancho na 1a frase e um CTA no fim. "
        "NAO use o numero de telefone na fala (vai no card depois). "
        "CRITICO: escreva a fala com ACENTUACAO CORRETA em portugues (você, não, "
        "atenção, automático, é, já) — sem acento a voz do video le errado. "
        "Responda APENAS JSON puro."
    )
    user = (
        f"Produto: {produto.get('nome')}\n"
        f"Dor do cliente: {estrategia.get('dor')}\n"
        f"Angulo: {estrategia.get('angulo')}\n"
        f"Emocao: {estrategia.get('emocao')}\n\n"
        f"Escreva a fala que UMA PESSOA vai dizer olhando pra camera neste "
        f"comercial de 8s. Responda SO com este JSON:\n"
        f'{{"personagem": "quem fala (ex: empreendedor cansado, jovem animada)", '
        f'"fala": "a fala literal em pt-BR, max 18 palavras, com gancho e CTA", '
        f'"tom": "como fala (ex: animado, confiante, aliviado)"}}'
    )
    try:
        d = _parse_json(_llm(system, user, "gemini-flash-lite-latest"))
        # trava de tamanho: fala curta cabe em 8s
        fala = (d.get("fala") or "").strip().strip('"')
        if len(fala.split()) > 22:
            fala = " ".join(fala.split()[:22])
        # repoe acentos SO na fala (o Veo/TTS le "voce" errado) — nao mexe no resto
        d["fala"] = _acentuar_fala(fala)
        return d
    except Exception as e:
        log.warning(f"[roteirista] fallback: {e}")
        return {"personagem": "empreendedor",
                "fala": _acentuar_fala(produto.get("cta_curto", produto.get("nome", ""))),
                "tom": "confiante"}


# ---------------------------------------------------------------------------
# Agente 3 — Diretor de Comercial (o prompt Veo que GARANTE fala)
# ---------------------------------------------------------------------------
def _diretor(produto: dict, estrategia: dict, roteiro: dict,
             orientacao: str = "9:16") -> str:
    """Monta o prompt Veo em ingles com pessoa falando a fala literal PT-BR.
    orientacao: '9:16' (vertical/shorts, default) ou '16:9' (lateral/deitado)."""
    _lateral = str(orientacao).replace(" ", "") in ("16:9", "horizontal", "lateral")
    _fmt = "horizontal 16:9" if _lateral else "vertical 9:16"
    system = (
        f"You write Veo 3 video prompts (English) for 8s {_fmt} product "
        "commercials. CRITICAL: the video MUST have a person speaking OUT LOUD "
        "to the camera (lips moving, lip-sync), NOT just ambient sound. Structure: "
        "'[person] looks at camera and says in Brazilian Portuguese: \"<fala>\". "
        "[scene with the product]. [visual style]. Their lips move naturally, "
        "clear voice, upbeat commercial.' Keep it under 60 words. Reply with the "
        "prompt ONLY, no markdown, no quotes around the whole thing."
    )
    user = (
        f"Product: {produto.get('nome')} ({produto.get('descricao')})\n"
        f"Character speaking: {roteiro.get('personagem')}\n"
        f"Tone: {roteiro.get('tom')}\n"
        f"EXACT line they must say in Brazilian Portuguese: \"{roteiro.get('fala')}\"\n"
        f"Selling angle: {estrategia.get('angulo')}\n\n"
        f"Write the Veo prompt. The person MUST speak that exact line out loud "
        f"to the camera (lip-sync), with the product visible in the scene. "
        f"{_fmt.capitalize()}, 8 seconds, cinematic, upbeat advertising music."
    )
    try:
        p = _llm(system, user, "gemini-flash-lite-latest").strip().strip('"')
        return p
    except Exception as e:
        log.warning(f"[diretor] fallback: {e}")
        fala = roteiro.get("fala", produto.get("cta_curto", ""))
        return (
            f"A {roteiro.get('personagem','person')} looks directly at the camera "
            f"and says out loud in Brazilian Portuguese: \"{fala}\", lips moving "
            f"naturally, clear voice. The {produto.get('nome')} product glows on a "
            f"phone screen beside them. Modern cinematic ad, {_fmt}, 8 seconds, "
            f"upbeat music."
        )


# ---------------------------------------------------------------------------
# Agente 4 — Crítico de Comercial
# ---------------------------------------------------------------------------
def _critico(produto: dict, prompt: str, fala: str) -> dict:
    """Avalia: vende? a fala vai ser FALADA (nao so som ambiente)? 0-10."""
    system = (
        "Voce e diretor criativo de agencia. Responda APENAS JSON puro."
    )
    user = (
        f"Avalie este prompt de comercial Veo 3 (8s) do produto {produto.get('nome')}:\n"
        f"PROMPT: {prompt}\n"
        f"FALA: {fala}\n\n"
        f"Criterios 1-10: (1) garante PESSOA FALANDO a fala em voz alta com "
        f"lip-sync (nao so som ambiente)? (2) vende o produto? (3) gancho forte? "
        f"(4) fala natural e curta pra 8s? Responda SO com:\n"
        f'{{"score": 8, "fala_garantida": 8, "vende": 8, "issues": [], "sugestoes": []}}'
    )
    try:
        r = _parse_json(_llm(system, user, "gemini-flash-latest"))
        if "score" not in r:
            ks = [r.get(k, 0) for k in ("fala_garantida", "vende")]
            r["score"] = sum(ks) // len(ks) if ks else 6
        return r
    except Exception as e:
        log.warning(f"[critico] fallback: {e}")
        return {"score": 7, "issues": [], "sugestoes": []}


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------
def projetar_comercial(produto: dict, max_retries: int = 1,
                       orientacao: str = "9:16") -> dict:
    """Roda o pipeline e retorna {prompt, fala, personagem, tom, score, history}.

    orientacao: '9:16' (vertical, default) ou '16:9' (lateral/deitado).
    Nunca levanta excecao — em pior caso cai num prompt fallback decente.
    """
    history = []
    estrategia = _estrategista(produto)
    history.append({"agente": "estrategista", "out": estrategia})

    melhor = None
    it = 0
    while it <= max_retries:
        it += 1
        roteiro = _roteirista(produto, estrategia)
        prompt = _diretor(produto, estrategia, roteiro, orientacao=orientacao)
        aval = _critico(produto, prompt, roteiro.get("fala", ""))
        history.append({"agente": "roteirista", "iter": it, "out": roteiro})
        history.append({"agente": "diretor", "iter": it, "out": prompt})
        history.append({"agente": "critico", "iter": it, "out": aval})
        cand = {
            "prompt": prompt, "fala": roteiro.get("fala"),
            "personagem": roteiro.get("personagem"), "tom": roteiro.get("tom"),
            "score": aval.get("score", 0), "iteracoes": it, "history": history,
            "produto_id": produto.get("id"),
        }
        if melhor is None or cand["score"] > melhor["score"]:
            melhor = cand
        if cand["score"] >= 8:
            break
    return melhor


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s",
                        datefmt="%H:%M:%S")
    cat = json.loads((_BASE / "pos_producao" / "assets" / "produtos.json").read_text(encoding="utf-8"))
    prods = [p for p in cat["produtos"] if p.get("prioridade") == "top"]
    for p in prods[:2]:
        print(f"\n=== {p['nome']} ===")
        r = projetar_comercial(p)
        print(f"score: {r['score']}/10  it={r['iteracoes']}")
        print(f"personagem: {r['personagem']} | tom: {r['tom']}")
        print(f"fala: {r['fala']}")
        print(f"prompt: {r['prompt']}")
