# -*- coding: utf-8 -*-
"""6 agentes do Maestro + Replicador de Virais."""
import json
import time
from llm_client import chat, chat_fast, chat_json
from youtube_api import search_shorts, get_video_stats, search_trending
from serp_api import search_trends
from db_local import get_historico_ideias, get_recent_videos, add_ideia, log_execucao

CANAIS = [
    {"nome": "ReCenas IA", "tema": "Releitura de Cenas Famosas"},
    {"nome": "Aulas IA", "tema": "Micro-aulas e Tutoriais"},
    {"nome": "Cassetadas IA", "tema": "Erros da IA (AI Fails)"},
    {"nome": "AlucinaAI", "tema": "Visuais Psicodelicos"},
    {"nome": "Cerebro Digital", "tema": "Trocadilhos Visuais Literais"},
    {"nome": "Fofos e Absurdos", "tema": "Fofura em Situacoes Bizarras"},
    {"nome": "Motivacao IA", "tema": "Citacoes Motivacionais"},
    {"nome": "Curiosidades IA", "tema": "Fatos Rapidos Chocantes"},
    {"nome": "Danca e Musica IA", "tema": "Visualizacao de Musica"},
    {"nome": "Dicas Financeiras", "tema": "Educacao Financeira"},
    {"nome": "Fake News IA", "tema": "Poder da Desinformacao (educativo)"},
    {"nome": "Mitos vs Verdades", "tema": "Desmentindo Mitos"},
    {"nome": "Fatos Bizarros", "tema": "Curiosidades Estranhas"},
    {"nome": "Corpo Humano", "tema": "Fatos Medicos e Biologicos"},
    {"nome": "Segredos do Oceano", "tema": "Talassofobia e Vida Marinha"},
    {"nome": "Dicas Fitness", "tema": "Exercicios e Nutricao"},
    {"nome": "Noticias de IA", "tema": "Noticias sobre Inteligencia Artificial"},
    {"nome": "Recordes Mundiais", "tema": "Visualizacao de Recordes"},
    {"nome": "Podcast Cortes", "tema": "Visualizacao de Cortes de Podcast"},
    {"nome": "Stand-up IA", "tema": "Piadas contadas por IA"},
    {"nome": "E Se...", "tema": "Cenarios Hipoteticos"},
    {"nome": "Humor de IA", "tema": "Humor Nonsense e Surreal"},
    {"nome": "Ilusoes de Otica", "tema": "Ilusoes e Puzzles Visuais"},
    {"nome": "Transformacao", "tema": "Morphing Satisfatorio"},
    {"nome": "Super Slow IA", "tema": "Camera Lenta Extrema"},
    {"nome": "Entrevistas Rua", "tema": "Parodia de Entrevistas de Rua"},
    {"nome": "IA Talk Show", "tema": "Parodia de Talk Shows"},
    {"nome": "Alienigenas", "tema": "ETs em Situacoes Engracadas"},
    {"nome": "Robos Desastrados", "tema": "Robos Tentando Ser Humanos"},
]

HASHTAGS = {
    "humor": "#ia #shortvideo #veo3 #viral #fyp #shorts #humor #video #youtubeshorts #piadas",
    "motivacional": "#ia #shortvideo #veo3 #viral #frases #vida #memes #motivational #superacao #reflexao",
    "curiosidade": "#ia #shortvideo #veo3 #curiosidades #viral #youtubeshorts #shorts #fatos #dados",
    "musica": "#humor #shorts #ia #viral #veo3 #trending #fyp #dancinha #youtubeshorts #video",
    "noticias": "#noticias #ia #shortvideo #veo3 #viral #fyp #shorts #humor #video #youtubeshorts",
    "financeiro": "#ia #investimentos #poupardinheiro #video #youtubeshorts #fyp #shortvideo #veo3",
    "default": "#ia #shortvideo #veo3 #viral #fyp #shorts #humor #video #youtubeshorts #piadas",
}


def _get_canal_rotation():
    import random
    return random.choice(CANAIS)


def agente_analisador(canal):
    historico = get_historico_ideias(canal["nome"], limit=5)
    recentes = get_recent_videos(limit=10)
    hist_text = ""
    if historico:
        hist_text = "Ideias recentes (NAO repetir): " + "; ".join(h["ideia"] for h in historico)
    rec_text = ""
    if recentes:
        rec_text = "Videos recentes: " + "; ".join(v.get("titulo", "?") for v in recentes if v.get("titulo"))
    return {"canal": canal["nome"], "tema": canal["tema"], "historico": hist_text, "recentes": rec_text}


def agente_tendencias(contexto):
    tema = contexto["tema"]
    serp_results = search_trends(f"{tema} viral 2026 shorts")
    yt_trending = search_trending(tema)
    trends_text = ""
    if serp_results:
        trends_text = "Tendencias Google: " + "; ".join(r["title"][:60] for r in serp_results[:5])
    if yt_trending:
        top = sorted(yt_trending.values(), key=lambda x: x.get("views", 0), reverse=True)[:3]
        trends_text += " | YouTube viral: " + "; ".join(
            f"{v['title'][:40]} ({v['views']} views)" for v in top
        )
    return {
        "tendencias": trends_text or "Sem dados de tendencia disponiveis",
        "serp_raw": serp_results[:3],
        "yt_raw": list(yt_trending.values())[:3],
    }


def agente_ideias(contexto, tendencias):
    prompt = (
        "Voce e um estrategista de conteudo viral para YouTube Shorts.\n\n"
        f"Canal: {contexto['canal']}\nTema do canal: {contexto['tema']}\n"
        f"{contexto['historico']}\n{contexto['recentes']}\n"
        f"Tendencias atuais: {tendencias['tendencias']}\n\n"
        "Gere UMA ideia de video SHORT (8-10 segundos) que:\n"
        "1. Se encaixa no tema do canal\n2. NAO repete ideias do historico\n"
        "3. Aproveita alguma tendencia atual se possivel\n"
        "4. Tem alto potencial viral\n5. E viavel de gerar com Veo 3\n\n"
        'Responda SOMENTE em JSON: {"ideia": "descricao curta", "angulo": "o que torna viral", '
        '"categoria": "humor|motivacional|curiosidade|musica|noticias|financeiro"}'
    )
    result = chat_json([{"role": "user", "content": prompt}])
    if isinstance(result, dict):
        return result
    return {"ideia": "Video viral sobre " + contexto["tema"], "angulo": "impacto visual", "categoria": "humor"}


def agente_roteirista(ideia, canal):
    prompt = (
        "Voce e um roteirista de Shorts virais. Escreva o roteiro de AUDIO para video de 8 segundos.\n\n"
        f"Canal: {canal['nome']} ({canal['tema']})\nIdeia: {ideia['ideia']}\n"
        f"Angulo viral: {ideia.get('angulo', '')}\n\n"
        "REGRAS: max 22 palavras dialogo total, PT-BR, 2-3 cenas de ~3s, trilha e SFX.\n\n"
        'JSON: {"cenas": [{"dialogo_pt_br": "texto", "prompt_trilha": "estilo", "prompt_sfx": "efeitos"}], "total_palavras": N}'
    )
    result = chat_json([{"role": "user", "content": prompt}])
    if isinstance(result, dict):
        return result
    return {"cenas": [{"dialogo_pt_br": ideia["ideia"][:20], "prompt_trilha": "epica", "prompt_sfx": "woosh"}], "total_palavras": 5}


def agente_visual(roteiro, ideia, canal):
    cenas_text = json.dumps(roteiro.get("cenas", []), ensure_ascii=False)[:400]
    prompt = (
        "Voce e um diretor visual de Shorts. Projete ACAO VISUAL para cada cena.\n\n"
        f"Canal: {canal['nome']} ({canal['tema']})\nIdeia: {ideia['ideia']}\n"
        f"Roteiro audio: {cenas_text}\n\n"
        "Para CADA cena: acao_visual, direcao_camera, transicao. Prompt vai pro Veo 3.\n\n"
        'JSON: {"cenas_visuais": [{"acao_visual": "...", "direcao_camera": "...", "transicao": "cut|dissolve|zoom"}]}'
    )
    result = chat_json([{"role": "user", "content": prompt}])
    if isinstance(result, dict):
        return result
    return {"cenas_visuais": [{"acao_visual": ideia["ideia"], "direcao_camera": "wide cinematic", "transicao": "cut"}]}


def agente_qa(roteiro, visual, ideia):
    prompt = (
        "Auditor de qualidade. Verifique viabilidade pro Veo 3.\n\n"
        f"Ideia: {ideia['ideia']}\nRoteiro: {json.dumps(roteiro, ensure_ascii=False)[:400]}\n"
        f"Visual: {json.dumps(visual, ensure_ascii=False)[:400]}\n\n"
        "CHECKLIST: 1) PT-BR max 22 palavras? 2) Visual descritivo? 3) Coerente? 4) Viavel Veo? 5) Viral?\n\n"
        'JSON: {"status": "APROVADO" ou "REPROVADO", "justificativa": "...", "acao_recomendada": null}'
    )
    result = chat_json([{"role": "user", "content": prompt}], max_tokens=1024)
    if isinstance(result, dict):
        return result
    return {"status": "APROVADO", "justificativa": "auto-aprovado", "acao_recomendada": None}


def montar_prompt_veo(roteiro, visual, ideia, canal):
    """Gera prompt pro Veo com DIALOGO FALADO como prioridade (Veo 3.1 gera voz em PT-BR)."""
    cenas_visual = visual.get("cenas_visuais", [])
    acoes = [v.get("acao_visual", "") for v in cenas_visual if v.get("acao_visual")]
    cenas_audio = roteiro.get("cenas", [])
    dialogo = " ".join(c.get("dialogo_pt_br", "") for c in cenas_audio if c.get("dialogo_pt_br"))

    # Dialogo falado é prioridade — o Veo 3.1 gera voz quando instruido
    if dialogo:
        fala = f"The person speaks clearly to camera in Brazilian Portuguese: \"{dialogo}\""
    else:
        fala = ""

    # Visual resumido (cabe no que sobrar)
    resumo_visual = ". ".join(acoes)

    if fala:
        # Montar com fala primeiro, visual depois (truncar visual se necessario)
        max_visual = 280 - len(fala) - 3
        if max_visual > 30:
            vis = resumo_visual[:max_visual].rstrip(". ")
            prompt = f"{vis}. {fala}"
        else:
            prompt = fala
    else:
        prompt = resumo_visual

    if len(prompt) > 400:
        prompt = prompt[:397] + "..."
    return prompt


def montar_titulo(ideia):
    categoria = ideia.get("categoria", "humor")
    hashtags = HASHTAGS.get(categoria, HASHTAGS["default"])
    palavra = ideia.get("ideia", "IA").split()[0].upper()
    return f"{palavra} | {hashtags}"


def pipeline_criacao(canal=None):
    start = time.time()
    if not canal:
        canal = _get_canal_rotation()
    print(f"[fabrica] === CRIACAO === Canal: {canal['nome']} ({canal['tema']})")
    contexto = agente_analisador(canal)
    print("[fabrica] 1/6 Contexto OK")
    tendencias = agente_tendencias(contexto)
    print("[fabrica] 2/6 Tendencias OK")
    ideia = agente_ideias(contexto, tendencias)
    print(f"[fabrica] 3/6 Ideia: {ideia.get('ideia', '?')[:60]}")
    for tentativa in range(3):
        roteiro = agente_roteirista(ideia, canal)
        print(f"[fabrica] 4/6 Roteiro ({roteiro.get('total_palavras', '?')} palavras)")
        visual = agente_visual(roteiro, ideia, canal)
        print("[fabrica] 5/6 Visual OK")
        qa = agente_qa(roteiro, visual, ideia)
        print(f"[fabrica] 6/6 QA: {qa.get('status', '?')}")
        if qa.get("status") == "APROVADO":
            break
        print(f"[fabrica] Reprovado tentativa {tentativa+1}/3")
    prompt_veo = montar_prompt_veo(roteiro, visual, ideia, canal)
    titulo = montar_titulo(ideia)
    add_ideia(canal["nome"], ideia.get("ideia", ""), ideia.get("angulo", ""))
    duracao = time.time() - start
    log_execucao("criacao", {"canal": canal["nome"]}, {"titulo": titulo, "prompt": prompt_veo[:200]}, duracao, "ok")
    print(f"[fabrica] Criacao concluida em {duracao:.1f}s")
    return {
        "modo": "criacao", "canal": canal["nome"], "titulo": titulo,
        "prompt_video": prompt_veo, "ideia": ideia, "roteiro": roteiro, "visual": visual,
    }


def pipeline_replica(tema=None, canal=None):
    start = time.time()
    if not canal:
        canal = _get_canal_rotation()
    if not tema:
        tema = canal["tema"]
    print(f"[fabrica] === REPLICA === Buscando virais: {tema}")
    results = search_shorts(f"{tema} #shorts", max_results=20)
    if not results:
        print("[fabrica] Nenhum resultado")
        return None
    top_ids = [r["video_id"] for r in results[:5]]
    stats = get_video_stats(top_ids)
    ranked = sorted(stats.items(), key=lambda x: x[1].get("views", 0), reverse=True)
    for vid_id, info in ranked[:3]:
        prompt = (
            "Analise este video viral e decida se podemos replica-lo com Veo 3.\n\n"
            f"Titulo: {info['title']}\nDescricao: {info['description'][:200]}\n"
            f"Views: {info['views']}\n\n"
            "CRITERIOS: conceito visual simples, nao depende rosto real, sem copyright forte, gancho viral.\n"
            "Se APROVADO, gere prompt pro Veo 3 (8s, 9:16, audio, PT-BR).\n\n"
            'JSON: {"status": "APROVADO|REPROVADO", "justificativa": "...", "prompt_video": "...", "titulo_viral": "..."}'
        )
        result = chat_json([{"role": "user", "content": prompt}])
        if isinstance(result, dict) and result.get("status") == "APROVADO":
            duracao = time.time() - start
            log_execucao("replica", {"tema": tema, "source": vid_id}, result, duracao, "ok")
            print(f"[fabrica] Replica aprovada: {info['title'][:50]}")
            return {
                "modo": "replica", "canal": canal["nome"],
                "titulo": result.get("titulo_viral", info["title"]),
                "prompt_video": result.get("prompt_video", ""),
                "source_url": f"https://www.youtube.com/shorts/{vid_id}",
                "source_titulo": info["title"],
                "views_original": info["views"],
            }
    duracao = time.time() - start
    log_execucao("replica", {"tema": tema}, None, duracao, "nenhum_aprovado")
    print("[fabrica] Nenhum video aprovado")
    return None