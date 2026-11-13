# -*- coding: utf-8 -*-
"""Multi-agent CrewAI para gerar prompts virais de video Veo.

4 agents:
  1. Trend Scout - analisa o que viraliza na categoria
  2. Hook Generator - cria fala viral em pt-BR (hook + body)
  3. Scenario Director - traduz para cenario visual otimizado pro Veo
  4. Quality Critic - Gemini Pro latest, avalia viral potential, regenera se < 7/10

Modelos:
  - Criativos (1-3): gemini-flash-lite-latest (barato, rapido)
  - Critico (4): gemini-flash-latest (mais forte, sem limite)

Usa llm_client.py para todas as chamadas (rotacao de chaves + fallback).
"""
import os
import sys
import json
import logging
from typing import Optional

log = logging.getLogger("agents")


# ---------------------------------------------------------------------------
# Wrapper para que CrewAI use nosso llm_client (em vez de OpenAI direto)
# ---------------------------------------------------------------------------
class GeminiFlashLiteLLM:
    """Wrapper LLM para CrewAI que usa nosso llm_client (Gemini Flash Lite)."""

    def __init__(self, model="gemini-flash-lite-latest", temperature=0.9):
        self.model = model
        self.temperature = temperature

    def _parse_messages(self, messages):
        """Converte CrewAI messages em (system, user) tuple."""
        system = ""
        user_parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                system += content + "\n"
            else:
                user_parts.append(content)
        return system.strip(), "\n".join(user_parts).strip()

    def invoke(self, messages, **kwargs):
        """Chamada principal (CrewAI/ChromaDB style)."""
        from llm_client import _call_gemini_native, _call_openai_compat, is_openai_compat
        system, user = self._parse_messages(messages)
        if is_openai_compat():
            return _call_openai_compat(system, user)
        # Sobrescreve o modelo da chamada
        old_model = os.environ.get("LLM_MODEL")
        os.environ["LLM_MODEL"] = self.model
        try:
            result = _call_gemini_native(system, user)
        finally:
            if old_model:
                os.environ["LLM_MODEL"] = old_model
            else:
                os.environ.pop("LLM_MODEL", None)
        return result

    def __call__(self, messages, **kwargs):
        """CrewAI pode chamar como funcao."""
        return self.invoke(messages, **kwargs)


# ---------------------------------------------------------------------------
# 4 Agents
# ---------------------------------------------------------------------------
AGENTS_CONFIG = [
    {
        "role": "Trend Scout",
        "goal": "Analisar o que viraliza na categoria {tema} e identificar ganchos, formatos e emocoes que funcionam.",
        "backstory": (
            "Voce e um analista de tendencias de TikTok/Reels/Shorts com 10 anos de experiencia. "
            "Voce ja analisou milhoes de videos virais e sabe que o segredo nao e算法. "
            "Os padroes que voce mapeou: hooks em 3 segundos, emocional forte, surpresa, "
            "controversia leve, demonstracao visual, identificacao com a dor. "
            "Voce sempre retorna em JSON estruturado para os outros agents consumirem."
        ),
        "model": "gemini-flash-lite-latest",
        "temperature": 0.7,
    },
    {
        "role": "Hook Generator",
        "goal": "Criar 1 fala viral em portugues brasileiro (max 12 palavras) para o canal {canal}.",
        "backstory": (
            "Voce e um copywriter especializado em TikTok. Suas falas sempre tem: "
            "gancho em 1 segundo, promessa de revelacao, tom conversacional, sem jargao. "
            "Voce nunca repete falas ja usadas. Sua fala e otima para audio/video curto."
        ),
        "model": "gemini-flash-lite-latest",
        "temperature": 0.95,
    },
    {
        "role": "Scenario Director",
        "goal": "Traduzir a fala em um cenario visual em INGLES otimizado para Veo 3.1 (vertical 9:16, cinematic).",
        "backstory": (
            "Voce e um diretor de cinema especializado em videos curtos virais. "
            "Suas descricoes tem: pessoa + acao + setting + lighting + estilo visual. "
            "Maximo 25 palavras, em INGLES, formato: 'Person [doing X] in [Y setting]. [Visual style]. 9:16.' "
            "Voce sempre pensa em como o frame vai ficar visualmente impactante."
        ),
        "model": "gemini-flash-lite-latest",
        "temperature": 0.85,
    },
    {
        "role": "Quality Critic",
        "goal": "Avaliar o prompt final (cenario + fala) e dar um score de 0-10 para viral potential. Se < 7, regenerar.",
        "backstory": (
            "Voce e um critico especializado em viral content. Voce avalia: "
            "(1) Hook em 1-3 segundos - tem? "
            "(2) Emocao - gera curiosidade, medo, surpresa, identificacao? "
            "(3) Visual - e cinematic e chamativo? "
            "(4) Clareza - a fala e natural? "
            "(5) Shareability - alguem mandaria para amigo? "
            "Voce retorna JSON: {score: 1-10, issues: [...], sugestoes: [...]}."
        ),
        "model": "gemini-flash-latest",  # PRO - mais forte, melhor julgamento
        "temperature": 0.3,
    },
]


# ---------------------------------------------------------------------------
# Funcao principal - roda o pipeline multi-agent
# ---------------------------------------------------------------------------
def run_pipeline(canal_nome: str, tema: str, exemplos_falas: list = None,
                 exemplos_cenarios: list = None, max_retries: int = 2,
                 multi_fala: bool = False) -> dict:
    """Roda o pipeline 4-agent. Retorna dict com fala, cenario, score, history.

    Args:
        canal_nome: nome do canal (ex: "Dicas Financeiras")
        tema: categoria (ex: "Educacao Financeira")
        exemplos_falas: falas ja geradas (anti-repeticao)
        exemplos_cenarios: cenarios ja gerados (anti-repeticao)
        max_retries: maximo de regeneracoes do critic
        multi_fala: se True, gera 2-3 falas por video (aumenta watchtime)

    Returns:
        {
            "fala": str OR list[str] (se multi_fala=True),
            "cenario": str,
            "prompt_final": str,
            "score": int,
            "iteracoes": int,
            "history": list  # log de cada passo
        }
    """
    exemplos_falas = exemplos_falas or []
    exemplos_cenarios = exemplos_cenarios or []

    log.info(f"[pipeline] iniciando para {canal_nome} ({tema}) multi_fala={multi_fala}")
    history = []

    # AGENT 1: Trend Scout
    log.info(f"[agent 1/4] Trend Scout -> analisando tema '{tema}'")
    trend_data = _agent_trend_scout(tema)
    history.append({"agent": "Trend Scout", "output": trend_data})

    fala = None
    cenario = None
    score = 0
    iteracao = 0

    while iteracao < max_retries + 1:
        iteracao += 1
        log.info(f"[pipeline] iteracao {iteracao}/{max_retries+1}")

        # AGENT 2: Hook Generator (multi ou single)
        if multi_fala:
            log.info(f"[agent 2/4] Hook Generator (multi) -> criando 3 falas")
            falas_novas = _agent_hook_generator_multi(
                canal_nome, tema, trend_data,
                exemplos_falas, n_falas=3
            )
            history.append({"agent": "Hook Generator (multi)", "iter": iteracao, "output": falas_novas})
            if falas_novas:
                fala = falas_novas
                exemplos_falas.extend(falas_novas)
                # Cenario multi-beat sincronizado com as falas
                log.info(f"[agent 3/4] Scenario Director (multi) -> criando cenario com beats")
                cenario_novo = _agent_scenario_director_multi(
                    canal_nome, tema, falas_novas, trend_data, exemplos_cenarios
                )
                history.append({"agent": "Scenario Director (multi)", "iter": iteracao, "output": cenario_novo})
                if cenario_novo:
                    cenario = cenario_novo
                    exemplos_cenarios.append(cenario)
        else:
            log.info(f"[agent 2/4] Hook Generator -> criando fala")
            fala_nova = _agent_hook_generator(canal_nome, tema, trend_data,
                                              exemplos_falas + ([fala] if fala else []))
            history.append({"agent": "Hook Generator", "iter": iteracao, "output": fala_nova})
            if fala_nova:
                fala = fala_nova
                exemplos_falas.append(fala)
            log.info(f"[agent 3/4] Scenario Director -> criando cenario")
            cenario_novo = _agent_scenario_director(canal_nome, tema, fala, trend_data,
                                                     exemplos_cenarios + ([cenario] if cenario else []))
            history.append({"agent": "Scenario Director", "iter": iteracao, "output": cenario_novo})
            if cenario_novo:
                cenario = cenario_novo
                exemplos_cenarios.append(cenario)

        # AGENT 4: Quality Critic (avalia fala + cenario)
        fala_para_critic = " | ".join(fala) if isinstance(fala, list) else (fala or "")
        log.info(f"[agent 4/4] Quality Critic -> avaliando")
        avaliacao = _agent_quality_critic(canal_nome, tema, fala_para_critic, cenario or "")
        history.append({"agent": "Quality Critic", "iter": iteracao, "output": avaliacao})
        score = avaliacao.get("score", 0)
        log.info(f"[critic] score={score}/10 issues={avaliacao.get('issues', [])[:2]}")

        if score >= 7:
            log.info(f"[pipeline] APROVADO com score {score}/10")
            break
        elif iteracao > max_retries:
            log.warning(f"[pipeline] max retries batidos, usando score {score}/10")
        else:
            log.info(f"[pipeline] score {score} < 7, regenerando (sugestoes: {avaliacao.get('sugestoes', [])[:2]})")

    # Combina cenario + fala (formato final do prompt)
    if cenario:
        if isinstance(fala, list):
            falas_join = " ... ".join(fala)
            if "{fala}" in cenario:
                prompt_final = cenario.replace("{fala}", falas_join)
            else:
                prompt_final = f"{cenario} They speak in Brazilian Portuguese: '{falas_join}'. 9:16 vertical portrait."
        else:
            if "{fala}" in cenario:
                prompt_final = cenario.replace("{fala}", fala)
            else:
                prompt_final = f"{cenario} They speak in Brazilian Portuguese: '{fala}'. 9:16 vertical portrait."
    else:
        if isinstance(fala, list):
            falas_join = " ... ".join(fala)
            prompt_final = f"Person speaking about {tema}. They speak in Brazilian Portuguese: '{falas_join}'. 9:16 vertical portrait."
        else:
            prompt_final = f"Person speaking about {tema}. They speak in Brazilian Portuguese: '{fala}'. 9:16 vertical portrait."

    # Se multi_fala, retorna fala como string joined para o cron
    fala_retorno = " | ".join(fala) if isinstance(fala, list) else fala

    return {
        "fala": fala_retorno,
        "cenario": cenario,
        "prompt_final": prompt_final,
        "score": score,
        "iteracoes": iteracao,
        "history": history,
        "multi_fala": multi_fala,
        "falas_list": fala if isinstance(fala, list) else [fala] if fala else [],
    }


# ---------------------------------------------------------------------------
# Implementacao de cada agent (chamada direta ao llm_client - sem overhead CrewAI)
# ---------------------------------------------------------------------------
def _agent_trend_scout(tema: str) -> dict:
    """Agent 1: Analisa tendencias da categoria."""
    from llm_client import _call_gemini_native, is_openai_compat, _call_openai_compat

    system = (
        "Voce e um analista de TikTok/Reels/Shorts. AVISO IMPORTANTE: voce DEVE responder com JSON puro, valido, sem markdown, sem comentarios antes ou depois. "
        "Comece a resposta diretamente com { e termine com }. "
        "NAO adicione explicacoes, NAO envolva em backticks, NAO faca analise previa."
    )
    user = (
        f"Analise o tema '{tema}' para videos curtos verticais (9:16, 8 segundos). "
        f"Responda SOMENTE com o JSON abaixo preenchido (sem texto adicional):\n"
        f'{{"emocoes_que_viralizam": ["curiosidade", "surpresa"], '
        f'"formatos_vencedores": ["hook forte", "demo"], '
        f'"ganchos_efetivos": ["voce nao acredita", "atencao"], '
        f'"cuidados": ["sem jargao", "max 12 palavras"], '
        f'"publico_alvo": "jovens 18-35"}}'
    )
    try:
        if is_openai_compat():
            txt = _call_openai_compat(system, user)
        else:
            txt = _call_gemini_native(system, user)
        txt = txt.strip()
        # Limpa possivel markdown
        if txt.startswith("```"):
            txt = txt.split("```", 2)[1]
            if txt.startswith("json"):
                txt = txt[4:]
            txt = txt.strip()
        # Tenta extrair primeiro JSON valido
        start = txt.find("{")
        end = txt.rfind("}")
        if start >= 0 and end > start:
            txt = txt[start:end+1]
        return json.loads(txt)
    except Exception as e:
        log.warning(f"[trend_scout] falhou: {e}")
        return {
            "emocoes_que_viralizam": ["curiosidade", "surpresa", "medo"],
            "formatos_vencedores": ["hook forte", "demonstracao"],
            "ganchos_efetivos": ["voce nao acredita", "atencao"],
            "cuidados": ["sem jargao"],
            "publico_alvo": "jovens 18-35",
        }


def _agent_hook_generator(canal_nome: str, tema: str, trend_data: dict,
                          exemplos: list) -> Optional[str]:
    """Agent 2: Gera fala viral. Suporta multi-fala (2-3 frases)."""
    from llm_client import gerar_fala_viral

    emocoes = trend_data.get("emocoes_que_viralizam", ["curiosidade"])
    ganchos = trend_data.get("ganchos_efetivos", ["voce nao vai acreditar"])
    emocao = emocoes[0] if emocoes else "curiosidade"
    gancho = ganchos[0] if ganchos else "voce nao vai acreditar"

    # Enriquece o system prompt com dados do trend scout
    try:
        fala = gerar_fala_viral(canal_nome, tema, exemplos=exemplos)
        return fala.strip().strip('"').strip("'") if fala else None
    except Exception as e:
        log.warning(f"[hook_generator] falhou: {e}")
        return None


def _agent_hook_generator_multi(canal_nome: str, tema: str, trend_data: dict,
                                exemplos: list, n_falas: int = 3) -> list:
    """Agent 2b: Gera N falas virais encadeadas (estrutura: GANCHO -> DESENVOLVIMENTO -> CTA).

    Retorna lista de falas, cada uma podendo virar um beat no Veo.
    """
    try:
        from llm_client import LLMClient
        client = LLMClient()
        prompt = f"""Crie {n_falas} falas curtas em portugues brasileiro para um video curto VERTICAL (TikTok/Reels/Shorts).

Canal: {canal_nome}
Tema: {tema}
Trending: {trend_data.get('emocoes_que_viralizam', ['curiosidade'])}
Ganchos: {trend_data.get('ganchos_efetivos', ['voce nao vai acreditar'])}

Estrutura obrigatoria:
- Fala 1 (GANCHO): max 10 palavras, prende atencao em 1.5s
- Fala 2 (CONFLITO): max 15 palavras, desenvolve o gancho
- Fala 3 (REVELACAO): max 12 palavras, conclusao surpreendente

Exemplos de ganchos que viralizam: 'Voce nao vai acreditar', 'Eu gastei X mas...', 'Ninguem te contou isso', 'O segredo que...'

Responda APENAS JSON valido:
{{"falas": ["fala 1", "fala 2", "fala 3"]}}"""
        resp = client.send(prompt, max_tokens=300)
        import re, json
        m = re.search(r'\{.*\}', resp, re.DOTALL)
        if m:
            data = json.loads(m.group(0))
            falas = data.get("falas", [])
            return [f.strip().strip('"').strip("'") for f in falas if f.strip()][:n_falas]
    except Exception as e:
        log.warning(f"[hook_multi] falhou: {e}")
    return []


def _agent_scenario_director(canal_nome: str, tema: str, fala: str,
                             trend_data: dict, exemplos_cenarios: list) -> Optional[str]:
    """Agent 3: Gera cenario visual."""
    from llm_client import gerar_prompt_viral

    try:
        cenario = gerar_prompt_viral(canal_nome, tema, fala, exemplos_cenarios=exemplos_cenarios)
        return cenario.strip().strip('"').strip("'") if cenario else None
    except Exception as e:
        log.warning(f"[scenario_director] falhou: {e}")
        return None


def _agent_scenario_director_multi(canal_nome: str, tema: str, falas: list,
                                    trend_data: dict, exemplos_cenarios: list) -> Optional[str]:
    """Agent 3b: Gera cenario visual para multi-fala. Cada fala vira um beat no cenario.

    Formato: 'BEAT 1: <visual>. BEAT 2: <visual>. BEAT 3: <visual>. They speak in PT-BR: fala1 / fala2 / fala3.'
    """
    try:
        from llm_client import LLMClient
        client = LLMClient()
        beats_visual = "\n".join(f"- Beat {i+1}: {f}" for i, f in enumerate(falas))
        prompt = f"""Crie um prompt cinematografico em INGLES para Veo 3.1 que descreve 3 cenas (beats) em sequencia:

Canal: {canal_nome}
Tema: {tema}
Beat 1 - GANCHO: {falas[0]}
Beat 2 - CONFLITO: {falas[1] if len(falas) > 1 else falas[0]}
Beat 3 - REVELACAO: {falas[2] if len(falas) > 2 else falas[0]}

Formato OBRIGATORIO no prompt final:
'Beat 1: <curta descricao visual>. Beat 2: <curta descricao visual>. Beat 3: <curta descricao visual>. They speak in Brazilian Portuguese: "{falas[0]} ... {falas[1] if len(falas) > 1 else ''} ... {falas[2] if len(falas) > 2 else ''}". 9:16 vertical portrait, ultra HD, neon vibrant lighting.'

Responda APENAS o prompt final em ingles, sem explicacao."""
        resp = client.send(prompt, max_tokens=400)
        return resp.strip().strip('"').strip("'")
    except Exception as e:
        log.warning(f"[scenario_multi] falhou: {e}")
        return None


def _agent_quality_critic(canal_nome: str, tema: str, fala: str, cenario: str) -> dict:
    """Agent 4: Avalia qualidade. Usa Gemini Pro (sem limite, melhor julgamento)."""
    from llm_client import _call_gemini_native, is_openai_compat, _call_openai_compat

    # Override do modelo para este agent - usa o Pro
    old_model = os.environ.get("LLM_MODEL")
    os.environ["LLM_MODEL"] = "gemini-flash-latest"  # Pro mais recente

    system = (
        "Voce e um critico especialista em conteudo viral TikTok/Reels. "
        "AVISO IMPORTANTE: voce DEVE responder com JSON puro, valido, sem markdown, sem comentarios antes ou depois. "
        "Comece a resposta diretamente com { e termine com }. "
        "NAO adicione explicacoes, NAO envolva em backticks, NAO faca analise previa."
    )
    user = (
        f"Avalie este prompt de video viral:\n"
        f"Canal: {canal_nome}\n"
        f"Tema: {tema}\n"
        f"Fala: {fala}\n"
        f"Cenario: {cenario}\n\n"
        f"Criterios (de 1-10 cada):\n"
        f"1. hook_3_segundos: o primeiro segundo prende atencao?\n"
        f"2. emocao: gera curiosidade, medo, surpresa, identificacao?\n"
        f"3. visual: cenario e cinematico, vibrante, unico?\n"
        f"4. clareza: fala e natural em pt-BR?\n"
        f"5. shareability: pessoas mandariam para amigos?\n\n"
        f"Calcule score = media dos 5 criterios. Se < 7, liste issues e sugestoes.\n"
        f"Responda SOMENTE com o JSON abaixo preenchido (sem texto adicional):\n"
        f'{{"score": 7, "hook_3_segundos": 7, "emocao": 7, "visual": 7, "clareza": 7, "shareability": 7, "issues": ["exemplo"], "sugestoes": ["exemplo"]}}'
    )

    try:
        if is_openai_compat():
            txt = _call_openai_compat(system, user)
        else:
            txt = _call_gemini_native(system, user)
        txt = txt.strip()
        if txt.startswith("```"):
            txt = txt.split("```", 2)[1]
            if txt.startswith("json"):
                txt = txt[4:]
            txt = txt.strip()
        # Extrai primeiro JSON valido (caso tenha texto antes/depois)
        start = txt.find("{")
        end = txt.rfind("}")
        if start >= 0 and end > start:
            txt = txt[start:end+1]
        result = json.loads(txt)
        # Garante score
        if "score" not in result:
            scores = [result.get(k, 0) for k in ["hook_3_segundos", "emocao", "visual", "clareza", "shareability"]]
            result["score"] = sum(scores) // len(scores) if scores else 0
        return result
    except Exception as e:
        log.warning(f"[quality_critic] falhou: {e}")
        # Fallback: tenta extrair score do texto cru
        try:
            import re
            m = re.search(r'"score"\s*:\s*(\d+)', txt)
            if m:
                return {"score": int(m.group(1)), "issues": [], "sugestoes": []}
        except:
            pass
        return {"score": 6, "issues": [f"critic falhou: {e}"], "sugestoes": []}
    finally:
        if old_model:
            os.environ["LLM_MODEL"] = old_model
        else:
            os.environ.pop("LLM_MODEL", None)


# ---------------------------------------------------------------------------
# Teste
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                       format="%(asctime)s [%(name)s] %(message)s",
                       datefmt="%H:%M:%S")
    canal = "Dicas Financeiras"
    tema = "Educacao Financeira"
    print(f"=== Multi-agent pipeline: {canal} ({tema}) ===\n")
    result = run_pipeline(canal, tema, exemplos_falas=[], exemplos_cenarios=[])
    print(f"\n=== RESULTADO ===")
    print(f"Iteracoes: {result['iteracoes']}")
    print(f"Score: {result['score']}/10")
    print(f"Fala: {result['fala']}")
    print(f"Cenario: {result['cenario']}")
    print(f"\nPrompt final:\n{result['prompt_final']}")